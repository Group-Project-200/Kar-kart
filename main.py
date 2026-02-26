import argparse
import os
import sys
import time
from dataclasses import dataclass, field

import pygame

from car_configs import CAR_HANDLING_BY_CAR_NAME, DEFAULT_CAR_HANDLING
from debug_overlay import DebugOverlayState, draw_runtime_debug_overlay_and_flip
from file_manager import load_image_stack, load_map
from physics_engine import CarHandling, ControlState, PhysicsState, step_physics_with_controls
from preview_debugger import (
    PreviewDebuggerConfig,
    advance_preview_rotation,
    apply_sprite_delta,
    build_preview_visual_settings,
    make_initial_preview_state,
    toggle_preview,
)
from render import (
    CameraFollowSettings,
    CameraState,
    RenderPipeline,
    RenderSetup,
    build_render_pipeline,
    render_frame,
    render_preview_debug_frame,
    update_camera_from_physics,
)


# Central gameplay/render knobs used by startup and the main loop.
@dataclass(frozen=True, slots=True)
class GameConfig:
    fps: int = 60
    dirs: int = 36
    stack_spread: int = -1
    default_resolution: tuple[int, int] = (1280, 720)
    standard_resolutions: tuple[tuple[int, int], ...] = (
        (1280, 720),
        (1920, 1080),
    )
    render_setup: RenderSetup = field(default_factory=RenderSetup)
    camera_follow: CameraFollowSettings = field(default_factory=CameraFollowSettings)

    @property
    def rotation_snap_degrees(self) -> float:
        return 360.0 / self.dirs


def build_game_config() -> GameConfig:
    # Centralized defaults so gameplay/render tuning stays in one place.
    dirs = 36
    render_setup = RenderSetup(
        map_zoom=4.0,
        car_zoom=3.0,
        pixelation_scale=0.40,
    )
    camera_follow = CameraFollowSettings(
        follow_alpha=0.03,
        drift_tilt_factor=0.35,
        max_drift_tilt=10.0,
        snap_delta=180.0,
    )
    return GameConfig(
        dirs=dirs,
        render_setup=render_setup,
        camera_follow=camera_follow,
    )


GAME_CONFIG = build_game_config()

# Runtime defaults used in both gameplay and debugger modes.
DEFAULT_MAP_NAME = "map_01"
DEFAULT_CAR_NAME = "car_01"


@dataclass(slots=True)
class FrameActions:
    toggle_preview: bool = False
    sprite_delta: int = 0


@dataclass(frozen=True, slots=True)
class RuntimeResources:
    map_surface: pygame.Surface | None
    car_folders: tuple[str, ...]
    car_stacks: dict[str, list[pygame.Surface]]
    preview_config: PreviewDebuggerConfig


def parse_resolution(value: str) -> tuple[int, int]:
    try:
        width_str, height_str = value.lower().split("x", maxsplit=1)
        width = int(width_str)
        height = int(height_str)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Resolution must be formatted as WIDTHxHEIGHT.") from exc

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Resolution values must be positive integers.")
    return width, height


def parse_args(config: GameConfig) -> argparse.Namespace:
    # CLI only affects launch mode; gameplay tuning remains in GameConfig.
    parser = argparse.ArgumentParser(
        add_help=False,
        description="Launch options.",
    )
    parser.add_argument(
        "-h",
        "--help",
        "-help",
        action="help",
        help="Show this launch help message and exit.",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=parse_resolution,
        default=config.default_resolution,
        help="Window size as WIDTHxHEIGHT (example: 1920x1080).",
    )
    parser.add_argument(
        "-f",
        "--fullscreen",
        action="store_true",
        help="Launch in fullscreen mode.",
    )
    parser.add_argument(
        "--list-resolutions",
        action="store_true",
        help="Print common resolution presets and exit.",
    )
    return parser.parse_args()


def _quit_game() -> None:
    pygame.quit()
    sys.exit()


def handle_events(state: ControlState, *, preview_mode: bool) -> tuple[ControlState, FrameActions]:
    # Keep key state normalized so physics can consume a compact control snapshot.
    actions = FrameActions()
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                _quit_game()
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        _quit_game()
                    case pygame.K_p:
                        actions.toggle_preview = True
                    case pygame.K_a:
                        if preview_mode:
                            actions.sprite_delta -= 1
                        else:
                            state.left_pressed = True
                            state.steer_input = 1
                    case pygame.K_d:
                        if preview_mode:
                            actions.sprite_delta += 1
                        else:
                            state.right_pressed = True
                            state.steer_input = -1
                    case pygame.K_w:
                        if not preview_mode:
                            state.up_input = True
                    case pygame.K_s:
                        if not preview_mode:
                            state.down_input = True
                    case pygame.K_SPACE:
                        if not preview_mode:
                            state.drift_input = True
            case pygame.KEYUP:
                match event.key:
                    case pygame.K_a:
                        if not preview_mode:
                            state.left_pressed = False
                            if state.steer_input == 1:
                                state.steer_input = -1 if state.right_pressed else 0
                    case pygame.K_d:
                        if not preview_mode:
                            state.right_pressed = False
                            if state.steer_input == -1:
                                state.steer_input = 1 if state.left_pressed else 0
                    case pygame.K_w:
                        if not preview_mode:
                            state.up_input = False
                    case pygame.K_s:
                        if not preview_mode:
                            state.down_input = False
                    case pygame.K_SPACE:
                        if not preview_mode:
                            state.drift_input = False
    return state, actions


def build_screen(args: argparse.Namespace) -> pygame.Surface:
    screen_flags = pygame.FULLSCREEN if args.fullscreen else 0
    window_size = (0, 0) if args.fullscreen else args.resolution
    return pygame.display.set_mode(window_size, screen_flags)


def discover_car_folders(base_path: str = "resources") -> tuple[str, ...]:
    if not os.path.isdir(base_path):
        return ()

    car_folders = []
    for entry in sorted(os.listdir(base_path)):
        if not entry.startswith("car_"):
            continue
        folder_path = os.path.join(base_path, entry)
        if not os.path.isdir(folder_path):
            continue
        if any(file_name.lower().endswith(".png") for file_name in os.listdir(folder_path)):
            car_folders.append(entry)
    return tuple(car_folders)


def select_default_car_index(car_folders: tuple[str, ...]) -> int:
    if DEFAULT_CAR_NAME in car_folders:
        return car_folders.index(DEFAULT_CAR_NAME)
    return 0


def resolve_car_handling_for_car(car_name: str) -> CarHandling:
    return CAR_HANDLING_BY_CAR_NAME.get(car_name, DEFAULT_CAR_HANDLING)


def resolve_selected_car_handling(car_folders: tuple[str, ...], selected_car_index: int) -> CarHandling:
    return resolve_car_handling_for_car(car_folders[selected_car_index])


def build_preview_config() -> PreviewDebuggerConfig:
    # Single source of truth for preview tuning lives in PreviewDebuggerConfig defaults.
    return PreviewDebuggerConfig()


def load_runtime_resources() -> RuntimeResources:
    map_surface = load_map(DEFAULT_MAP_NAME)
    car_folders = discover_car_folders()
    if not car_folders:
        raise RuntimeError("No car sprite folders found in resources (expected names like car_01).")

    car_stacks = {folder_name: load_image_stack(folder_name) for folder_name in car_folders}
    preview_config = build_preview_config()
    return RuntimeResources(
        map_surface=map_surface,
        car_folders=car_folders,
        car_stacks=car_stacks,
        preview_config=preview_config,
    )


def build_pipeline(
    config: GameConfig,
    screen_size: tuple[int, int],
    *,
    map_surface: pygame.Surface | None,
    image_stack: list[pygame.Surface],
    render_setup: RenderSetup,
):
    return build_render_pipeline(
        screen_size=screen_size,
        map_surface=map_surface,
        image_stack=image_stack,
        setup=render_setup,
        dirs=config.dirs,
    )


def rebuild_runtime_render_state(
    config: GameConfig,
    screen_size: tuple[int, int],
    *,
    resources: RuntimeResources,
    preview_enabled: bool,
    selected_car_index: int,
) -> tuple[int, RenderPipeline]:
    # Preview-specific visual math and runtime pipeline construction are centralized here.
    render_setup, stack_spread = build_preview_visual_settings(
        config.render_setup,
        config.stack_spread,
        preview_enabled=preview_enabled,
        config=resources.preview_config,
    )
    pipeline = build_pipeline(
        config,
        screen_size,
        map_surface=None if preview_enabled else resources.map_surface,
        image_stack=resources.car_stacks[resources.car_folders[selected_car_index]],
        render_setup=render_setup,
    )
    return stack_spread, pipeline


def main() -> None:
    config = GAME_CONFIG
    args = parse_args(config)
    # Utility mode for listing common presets without opening a window.
    if args.list_resolutions:
        for width, height in config.standard_resolutions:
            print(f"{width}x{height}")
        return

    pygame.init()
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])

    screen = build_screen(args)
    clock = pygame.time.Clock()
    resources = load_runtime_resources()
    preview_state = make_initial_preview_state(select_default_car_index(resources.car_folders))
    active_car_handling = resolve_selected_car_handling(
        resources.car_folders,
        preview_state.selected_car_index,
    )
    active_stack_spread, render_pipeline = rebuild_runtime_render_state(
        config,
        screen.get_size(),
        resources=resources,
        preview_enabled=preview_state.enabled,
        selected_car_index=preview_state.selected_car_index,
    )

    controls = ControlState()
    physics_state = PhysicsState()
    camera_state = CameraState(angle=physics_state.rotation)
    debug_overlay_state = DebugOverlayState()

    # Fixed-rate frame loop: input -> physics -> camera follow -> render.
    while True:
        clock.tick(config.fps)
        frame_start_time = time.perf_counter()

        controls, actions = handle_events(controls, preview_mode=preview_state.enabled)
        rebuild_required = False

        if actions.toggle_preview:
            toggle_preview(preview_state)
            controls = ControlState()
            camera_state.angle = physics_state.rotation
            rebuild_required = True

        if preview_state.enabled and apply_sprite_delta(
            preview_state,
            sprite_delta=actions.sprite_delta,
            sprite_count=len(resources.car_folders),
        ):
            rebuild_required = True

        if rebuild_required:
            active_car_handling = resolve_selected_car_handling(
                resources.car_folders,
                preview_state.selected_car_index,
            )
            active_stack_spread, render_pipeline = rebuild_runtime_render_state(
                config,
                screen.get_size(),
                resources=resources,
                preview_enabled=preview_state.enabled,
                selected_car_index=preview_state.selected_car_index,
            )

        if preview_state.enabled:
            advance_preview_rotation(preview_state, resources.preview_config)
            render_preview_debug_frame(
                screen,
                render_pipeline,
                car_rotation=preview_state.rotation_degrees,
                stack_spread=active_stack_spread,
            )
            frame_runtime_ms = (time.perf_counter() - frame_start_time) * 1000.0
            draw_runtime_debug_overlay_and_flip(
                screen,
                debug_overlay_state,
                frame_runtime_ms=frame_runtime_ms,
                speed=0.0,
                drift_frames=0,
                boost_level=0,
            )
            continue

        # Physics owns movement; main only wires inputs and chosen car handling.
        physics_state = step_physics_with_controls(
            physics_state,
            controls,
            handling=active_car_handling,
            snap_step_degrees=config.rotation_snap_degrees,
        )
        update_camera_from_physics(
            camera_state,
            physics_rotation=physics_state.rotation,
            physics_drift_direction=physics_state.drift_direction,
            physics_drift_skew_degrees=physics_state.drift_skew_degrees,
            settings=config.camera_follow,
        )
        render_frame(
            screen,
            render_pipeline,
            car_x=physics_state.car_x,
            car_y=physics_state.car_y,
            car_rotation=physics_state.rotation,
            camera_angle=camera_state.angle,
            stack_spread=active_stack_spread,
        )
        frame_runtime_ms = (time.perf_counter() - frame_start_time) * 1000.0
        draw_runtime_debug_overlay_and_flip(
            screen,
            debug_overlay_state,
            frame_runtime_ms=frame_runtime_ms,
            speed=physics_state.speed,
            drift_frames=physics_state.drift_charge_frames,
            boost_level=physics_state.boost_level,
        )


if __name__ == "__main__":
    main()
