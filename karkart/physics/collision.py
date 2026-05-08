from __future__ import annotations

import math

import pygame


_NORMAL_SAMPLE_DIRECTIONS: tuple[tuple[float, float], ...] = tuple(
    (math.cos(math.radians(a)), math.sin(math.radians(a)))
    for a in range(0, 360, 360 // 16)
)

"""this is the collision detector for our game that checks for collisions between the player and the map"""
class CollisionDetector:

    def __init__(
        self,
        map_masks: list[pygame.mask.Mask],
        car_masks: list[pygame.mask.Mask],
    ) -> None:

        self.car_masks = car_masks
        self.layers = [map_masks[0]]
        self.current_car_mask: pygame.mask.Mask | None = None

    def _offset(self, car_map_pos: tuple[int, int]) -> tuple[int, int]:
        assert self.current_car_mask is not None
        car_w, car_h = self.current_car_mask.get_size()
        return car_map_pos[0] - car_w // 2, car_map_pos[1] - car_h // 2

    def border_check(self, direction_index: int, car_map_pos: tuple[int, int]) -> bool:

        self.current_car_mask = self.car_masks[direction_index]
        offset = self._offset(car_map_pos)
        return any(
            layer.overlap(self.current_car_mask, offset) for layer in self.layers
        )

    def estimate_normal(
        self,
        car_map_pos: tuple[int, int],
        radius: int = 20,
    ) -> tuple[float, float] | None:

        if not self.layers:
            return None
        mask = self.layers[0]
        mask_w, mask_h = mask.get_size()
        cx, cy = car_map_pos

        fx = fy = 0.0
        free_count = 0
        solid_count = 0
        for dx, dy in _NORMAL_SAMPLE_DIRECTIONS:
            sx = int(cx + dx * radius)
            sy = int(cy + dy * radius)
            if not (0 <= sx < mask_w and 0 <= sy < mask_h):

                solid_count += 1
                continue
            if mask.get_at((sx, sy)):
                solid_count += 1
            else:
                fx += dx
                fy += dy
                free_count += 1

        if free_count == 0 or solid_count == 0:
            return None
        length = math.hypot(fx, fy)
        if length < 1e-6:
            return None
        return fx / length, fy / length

"""these functions are made to push the player out of the collision overlap and return him to a position 
where the game is playable. this was created because the player used to get stuck into the walls after a collision"""
def apply_wall_bounce(
    vx: float,
    vy: float,
    normal: tuple[float, float],
    restitution: float,
) -> tuple[float, float]:
    # bounce velocity off wall; restitution < 1 absorbs some energy
    nx, ny = normal
    dot = vx * nx + vy * ny
    if dot >= 0.0:
        return vx, vy
    factor = (1.0 + restitution) * dot
    return vx - factor * nx, vy - factor * ny


def push_out_of_wall(
    car_x: float,
    car_y: float,
    normal: tuple[float, float],
    step: float = 6.0,
) -> tuple[float, float]:
    # push position clear of the wall along its normal
    nx, ny = normal
    return car_x + nx * step, car_y + ny * step
