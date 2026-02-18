import sys
import argparse
import pygame

from file_manager import load_image_stack, load_map
from physics_engine import (
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


def parse_args():
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


def handle_events(
    left_pressed: bool,
    right_pressed: bool,
    steer_input: int,
    up_input: bool,
    down_input: bool,
    handbrake_input: bool,
):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_a:
                left_pressed = True
                steer_input = 1
            elif event.key == pygame.K_d:
                right_pressed = True
                steer_input = -1
            elif event.key == pygame.K_w:
                up_input = True
            elif event.key == pygame.K_s:
                down_input = True
            elif event.key == pygame.K_SPACE:
                handbrake_input = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                left_pressed = False
                if steer_input == 1:
                    steer_input = -1 if right_pressed else 0
            elif event.key == pygame.K_d:
                right_pressed = False
                if steer_input == -1:
                    steer_input = 1 if left_pressed else 0
            elif event.key == pygame.K_w:
                up_input = False
            elif event.key == pygame.K_s:
                down_input = False
            elif event.key == pygame.K_SPACE:
                handbrake_input = False
    return left_pressed, right_pressed, steer_input, up_input, down_input, handbrake_input


def main():
    args = parse_args()
    if args.list_resolutions:
        for width, height in STANDARD_RESOLUTIONS:
            print(f"{width}x{height}")
        return

    pygame.init()
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])

    screen_flags = pygame.FULLSCREEN if args.fullscreen else 0
    requested_screen_size = (0, 0) if args.fullscreen else args.resolution
    screen = pygame.display.set_mode(requested_screen_size, screen_flags)
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
    # Draw at reduced resolution for pixelation, while compensating zoom/size to preserve final scale.
    draw_map_zoom = map_zoom * render_scale
    draw_car_scale = car_scale * render_scale
    center = (render_size[0] // 2, render_size[1] // 2)

    frame_surface = pygame.Surface(render_size).convert()
    clock = pygame.time.Clock()

    images = scale_images(load_image_stack("car_01"), draw_car_scale)
    map_surface = load_map("maps")
    map_cache = build_map_cache(map_surface, draw_map_zoom)
    rotated_cache = build_rotated_cache(images)

    left_pressed = False
    right_pressed = False
    steer_input = 0
    up_input = False
    down_input = False
    handbrake_input = False
    rotation = 0.0
    turn_rate = 0.0
    steer_hold_frames = 0
    previous_steer_input = 0
    speed = 0.0
    velocity_x, velocity_y = 0.0, 0.0
    car_x, car_y = 0.0, 0.0

    while True:
        clock.tick(FPS)

        left_pressed, right_pressed, steer_input, up_input, down_input, handbrake_input = handle_events(
            left_pressed,
            right_pressed,
            steer_input,
            up_input,
            down_input,
            handbrake_input,
        )

        if steer_input == 0:
            steer_hold_frames = 0
        elif steer_input != previous_steer_input:
            steer_hold_frames = 1
        else:
            steer_hold_frames += 1
        previous_steer_input = steer_input

        rotation, turn_rate = update_rotation(
            rotation,
            turn_rate,
            steer_input,
            steer_hold_frames,
            snap_step_degrees=ROTATION_SNAP_DEGREES,
        )
        speed = update_speed(speed, up_input, down_input, turn_rate)
        velocity_x, velocity_y = update_velocity(
            velocity_x,
            velocity_y,
            rotation,
            speed,
            turn_rate,
            slide_factor=SLIDE_FACTOR,
            handbrake_input=handbrake_input,
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
