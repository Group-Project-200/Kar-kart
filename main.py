import argparse
import sys
from dataclasses import dataclass, field

import pygame

from file_manager import load_image_stack, load_map
from physics_engine import CarHandling, ControlState, PhysicsState, step_physics_with_controls
from render import (
    CameraFollowSettings,
    CameraState,
    LayerPixelation,
    RenderSetup,
    build_render_pipeline,
    render_frame,
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
        (1366, 768),
        (1600, 900),
        (1920, 1080),
    )
    render_setup: RenderSetup = field(default_factory=RenderSetup)
    camera_follow: CameraFollowSettings = field(default_factory=CameraFollowSettings)
    car_handling: CarHandling = field(default_factory=CarHandling)

    @property
    def rotation_snap_degrees(self) -> float:
        return 360.0 / self.dirs


def build_game_config() -> GameConfig:
    # Centralized defaults so gameplay/render tuning stays in one place.
    dirs = 36
    pixelation_scale = 0.35
    layer_pixelation = LayerPixelation(
        map_scale=pixelation_scale,
        car_scale=pixelation_scale,
        swap_layers=False,
    )
    render_setup = RenderSetup(
        reference_height=720,
        base_map_zoom=3.0,
        base_car_scale=3.0,
        pixelation_scale=pixelation_scale,
        layer_pixelation=layer_pixelation,
        dirs=dirs,
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
        car_handling=CarHandling(),
    )


GAME_CONFIG = build_game_config()


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


def handle_events(state: ControlState) -> ControlState:
    # Keep key state normalized so physics can consume a compact control snapshot.
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                _quit_game()
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        _quit_game()
                    case pygame.K_a:
                        state.left_pressed = True
                        state.steer_input = 1
                    case pygame.K_d:
                        state.right_pressed = True
                        state.steer_input = -1
                    case pygame.K_w:
                        state.up_input = True
                    case pygame.K_s:
                        state.down_input = True
                    case pygame.K_SPACE:
                        state.drift_input = True
            case pygame.KEYUP:
                match event.key:
                    case pygame.K_a:
                        state.left_pressed = False
                        if state.steer_input == 1:
                            state.steer_input = -1 if state.right_pressed else 0
                    case pygame.K_d:
                        state.right_pressed = False
                        if state.steer_input == -1:
                            state.steer_input = 1 if state.left_pressed else 0
                    case pygame.K_w:
                        state.up_input = False
                    case pygame.K_s:
                        state.down_input = False
                    case pygame.K_SPACE:
                        state.drift_input = False
    return state


def build_screen(args: argparse.Namespace) -> pygame.Surface:
    screen_flags = pygame.FULLSCREEN if args.fullscreen else 0
    window_size = (0, 0) if args.fullscreen else args.resolution
    return pygame.display.set_mode(window_size, screen_flags)


def build_pipeline(config: GameConfig, screen_size: tuple[int, int]):
    return build_render_pipeline(
        screen_size=screen_size,
        map_surface=load_map("maps"),
        image_stack=load_image_stack("car_01"),
        setup=config.render_setup,
    )


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
    render_pipeline = build_pipeline(config, screen.get_size())

    controls = ControlState()
    physics_state = PhysicsState()
    camera_state = CameraState(angle=physics_state.rotation)

    # Fixed-rate frame loop: input -> physics -> camera follow -> render.
    while True:
        clock.tick(config.fps)

        controls = handle_events(controls)
        # Physics owns movement; main only wires inputs and chosen car handling.
        physics_state = step_physics_with_controls(
            physics_state,
            controls,
            handling=config.car_handling,
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
            stack_spread=config.stack_spread,
        )
        pygame.display.flip()


if __name__ == "__main__":
    main()
