"""Pixel-perfect collision test between the car sprite and map layers."""

from __future__ import annotations

import math

import pygame


# Directions sampled when estimating a wall normal (unit vectors, 16-way).
_NORMAL_SAMPLE_DIRECTIONS: tuple[tuple[float, float], ...] = tuple(
    (math.cos(math.radians(a)), math.sin(math.radians(a)))
    for a in range(0, 360, 360 // 16)
)


class CollisionDetector:
    """Tests whether the rotated car mask overlaps any map collision layer."""

    def __init__(
        self,
        map_masks: list[pygame.mask.Mask],
        car_masks: list[pygame.mask.Mask],
    ) -> None:
        # ``car_masks`` is indexed by the discrete heading (one mask per direction).
        # Only the first map layer is treated as solid for collisions.
        self.car_masks = car_masks
        self.layers = [map_masks[0]]
        self.current_car_mask: pygame.mask.Mask | None = None

    def _offset(self, car_map_pos: tuple[int, int]) -> tuple[int, int]:
        assert self.current_car_mask is not None
        car_w, car_h = self.current_car_mask.get_size()
        return car_map_pos[0] - car_w // 2, car_map_pos[1] - car_h // 2

    def border_check(self, direction_index: int, car_map_pos: tuple[int, int]) -> bool:
        """Return True if the car overlaps a collision layer at its current pose."""
        self.current_car_mask = self.car_masks[direction_index]
        offset = self._offset(car_map_pos)
        return any(layer.overlap(self.current_car_mask, offset) for layer in self.layers)

    def estimate_normal(
        self,
        car_map_pos: tuple[int, int],
        radius: int = 20,
    ) -> tuple[float, float] | None:
        """Approximate the outward wall normal at *car_map_pos*.

        Samples the collision mask at 16 points evenly spaced around the car
        at distance *radius* (in map pixels). The outward normal is taken as
        the average of the directions that are *free* (no wall), which points
        away from the solid side into open space.

        Returns ``None`` if the result is degenerate (car fully surrounded or
        fully free — nothing sensible to reflect off).
        """
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
                # Treat out-of-bounds as solid (map edge behaves like a wall).
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
