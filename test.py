# with code derived from https://www.youtube.com/watch?v=FNw_BQok14A and created by DaFluffyPotato

import sys
import pygame
from file_manager import load_image_stack, load_map
from physics_engine import update_rotation, update_position
from map_draw import draw_map

pygame.init()


screen = pygame.display.set_mode((500, 500))
display = pygame.Surface((100, 100))

# Load image stack using file_manager utility
images = load_image_stack("car_01")

# Placeholder: Load a map (e.g., from 'car_01' folder for now)
map_surface = load_map("maps")

clock = pygame.time.Clock()


frame = 0
left_input = False
right_input = False
up_input = False
rotation = 0.0
spread = -1

# Car state
car_x, car_y = 0.0, 0.0  # Car's world position (centered at start)
car_speed = 0.0
CAR_SPEED_CONST = 2.0  # Constant speed when up arrow is pressed

# --- snapping + caching setup ---
DIRS = 36
STEP_DEG = 360 / DIRS

def snap_degrees(deg: float, dirs: int = DIRS) -> int:
    """Return snapped direction index in [0, dirs-1]."""
    step = 360.0 / dirs
    # normalize to [0, 360)
    deg = deg % 360.0
    # nearest step
    idx = int((deg / step) + 0.5) % dirs
    return idx

# Pre-rotate all slices for all directions once.
# rotated_cache[dir_idx] = list of rotated slice Surfaces (same length as images)
rotated_cache = []
for d in range(DIRS):
    angle = d * STEP_DEG
    rotated_cache.append([pygame.transform.rotate(img, angle) for img in images])

def render_stack_snapped(display, rotated_slices, pos, spread):
    """Render already-rotated slices centered at pos."""
    x, y = pos
    for i, img in enumerate(rotated_slices):
        display.blit(
            img,
            (x - img.get_width() // 2, y - img.get_height() // 2 + i * spread),
        )


while True:
    display.fill((0, 0, 0))
    frame += 1

    # --- Input and physics ---
    rotation = update_rotation(rotation, left_input, right_input)

    # Up arrow sets speed to constant, else speed is zero
    if up_input:
        car_speed = CAR_SPEED_CONST
    else:
        car_speed = 0.0

    car_x, car_y = update_position(car_x, car_y, rotation, car_speed)

    # Snap for rendering only
    dir_idx = snap_degrees(rotation, DIRS)

    # --- Draw map, zoomed and moving under car ---
    draw_map(display, map_surface, car_x, car_y, zoom=2.0, center=(50, 50))

    # Draw car (stack) at center
    render_stack_snapped(display, rotated_cache[dir_idx], (50, 50), spread)

    # --- Event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == pygame.K_LEFT:
                left_input = True
            if event.key == pygame.K_RIGHT:
                right_input = True
            if event.key == pygame.K_UP:
                up_input = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                left_input = False
            if event.key == pygame.K_RIGHT:
                right_input = False
            if event.key == pygame.K_UP:
                up_input = False

    screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
    pygame.display.update()
    clock.tick(60)