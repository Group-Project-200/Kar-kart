import sys
import argparse
from dataclasses import dataclass

import pygame

from file_manager import load_image_stack, load_map
from physics_engine import (
    filter_steer_input,
    update_position,
    update_rotation,
    update_speed,
    update_velocity,
)
from render import (
    build_map_cache,
    build_pixel_surface_size,
    build_rotated_cache,
    build_world_scales,
    draw_map,
    present_frame,
    render_stack,
    scale_images,
    snap_degrees,
)

# Window / resolution settings
DEFAULT_RESOLUTION = (1280, 720)
STANDARD_RESOLUTIONS = (
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
)
REFERENCE_HEIGHT = 720

# Rendering scale settings
# Pixelation is post-process only: it does not change map/car relative size.
PIXELATION_SCALE = 0.3

# Simulation / world settings
FPS = 60
BASE_MAP_ZOOM = 7.0
STACK_SPREAD = -1
DIRS = 36
ROTATION_SNAP_DEGREES = 360.0 / DIRS
SLIDE_FACTOR = 0.3
BASE_CAR_DISPLAY_SCALE = 3.0


@dataclass(slots=True)
class InputState:
    left_pressed: bool = False
    right_pressed: bool = False
    steer_input: int = 0
    up_input: bool = False
    down_input: bool = False
    handbrake_input: bool = False


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


def parse_args() -> argparse.Namespace:
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
        default=DEFAULT_RESOLUTION,
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


def _update_steer_hold(
    steer_input: int,
    previous_steer_input: int,
    steer_hold_frames: int,
) -> tuple[int, int]:
    if steer_input == 0:
        return 0, steer_input
    if steer_input != previous_steer_input:
        return 1, steer_input
    return steer_hold_frames + 1, steer_input


def handle_events(state: InputState) -> InputState:
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
                        state.handbrake_input = True
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
                        state.handbrake_input = False
    return state


def main():
    args = parse_args()
    if args.list_resolutions:
        for width, height in STANDARD_RESOLUTIONS:
            print(f"{width}x{height}")
        return

    pygame.init()
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])

    screen_flags = pygame.FULLSCREEN if args.fullscreen else 0
    window_size = (0, 0) if args.fullscreen else args.resolution
    screen = pygame.display.set_mode(window_size, screen_flags)
    screen_size = screen.get_size()

    map_zoom, car_scale = build_world_scales(
        screen_size[1],
        REFERENCE_HEIGHT,
        BASE_MAP_ZOOM,
        BASE_CAR_DISPLAY_SCALE,
    )
    render_size = build_pixel_surface_size(screen_size, PIXELATION_SCALE)
    render_scale = render_size[1] / screen_size[1]
    needs_present_scale = render_size != screen_size
    # Pixelation is post-process only; map/car scale stays consistent.
    draw_map_zoom = map_zoom * render_scale
    draw_car_scale = car_scale * render_scale
    center = (render_size[0] // 2, render_size[1] // 2)

    frame_surface = pygame.Surface(render_size).convert()
    clock = pygame.time.Clock()

    images = scale_images(load_image_stack("car_01"), draw_car_scale)
    map_surface = load_map("maps")
    map_cache = build_map_cache(map_surface, draw_map_zoom)
    rotated_cache = build_rotated_cache(images)

    input_state = InputState()
    rotation = 0.0
    turn_rate = 0.0
    steer_hold_frames = 0
    previous_steer_input = 0
    speed = 0.0
    velocity_x, velocity_y = 0.0, 0.0
    car_x, car_y = 0.0, 0.0

    while True:
        clock.tick(FPS)

        input_state = handle_events(input_state)
        steer_for_physics = filter_steer_input(input_state.steer_input, speed)
        steer_hold_frames, previous_steer_input = _update_steer_hold(
            steer_for_physics,
            previous_steer_input,
            steer_hold_frames,
        )

        rotation, turn_rate = update_rotation(
            rotation,
            turn_rate,
            steer_for_physics,
            steer_hold_frames,
            snap_step_degrees=ROTATION_SNAP_DEGREES,
        )
        speed = update_speed(speed, input_state.up_input, input_state.down_input, turn_rate)
        velocity_x, velocity_y = update_velocity(
            velocity_x,
            velocity_y,
            rotation,
            speed,
            turn_rate,
            slide_factor=SLIDE_FACTOR,
            handbrake_input=input_state.handbrake_input,
        )
        car_x, car_y = update_position(car_x, car_y, velocity_x, velocity_y)

        frame_surface.fill((0, 0, 0))
        dir_idx = snap_degrees(rotation)
        draw_map(frame_surface, map_cache, car_x, car_y, center=center, view_size=render_size)
        render_stack(frame_surface, rotated_cache[dir_idx], center, STACK_SPREAD)

        present_frame(screen, frame_surface, screen_size, needs_present_scale)
        pygame.display.flip()


if __name__ == "__main__":
    main()
