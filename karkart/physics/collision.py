"""Pixel-perfect collision test between the car sprite and map layers."""

from __future__ import annotations

import pygame


class CollisionDetector:
    """Tests whether the rotated car mask overlaps any map collision layer."""

    def __init__(
        self,
        map_masks: list[pygame.mask.Mask],
        car_masks: list[pygame.mask.Mask],
        item
    ) -> None:
        # ``car_masks`` is indexed by the discrete heading (one mask per direction).
        # Only the first map layer is treated as solid for collisions.
        self.car_masks = car_masks
        self.layers = [map_masks[0]]
        self.current_car_mask: pygame.mask.Mask | None = None
        self.item_mask = item.mask
        self.item_x,self.item_y = item.x, item.y

    def _offset(self, car_map_pos: tuple[int, int]) -> tuple[int, int]:
        assert self.current_car_mask is not None
        car_w, car_h = self.current_car_mask.get_size()
        return car_map_pos[0] - car_w // 2, car_map_pos[1] - car_h // 2

    def border_check(self, direction_index: int, car_map_pos: tuple[int, int]) -> bool:
        """Return True if the car overlaps a collision layer at its current pose."""
        self.current_car_mask = self.car_masks[direction_index]
        offset = self._offset(car_map_pos)
        return any(layer.overlap(self.current_car_mask, offset) for layer in self.layers)

    def item_check(self,direction_index: int, car_map_pos: tuple[int, int]):
        self.current_car_mask = self.car_masks[direction_index]
        car_top_left = self._offset(car_map_pos)

        offset = (
            car_top_left[0] - self.item_x,
            car_top_left[1] - self.item_y,
        )
        print(self.item_mask)
        return self.item_mask.overlap(self.current_car_mask, offset)