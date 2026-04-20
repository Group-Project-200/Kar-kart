"""Checkpoint: a rectangular region the car must touch in order."""

from __future__ import annotations

import pygame


class Checkpoint:
    """Axis-aligned rectangle that records whether the car has passed through."""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.passed: bool = False

    def check(self, car_x: float, car_y: float, half_size: float = 10.0) -> bool:
        """Return True if the car's footprint overlaps the checkpoint rect.

        Tests a small square around (*car_x*, *car_y*) rather than a single
        point so narrow checkpoints still trigger when the car's edge — not
        just its centre — crosses the rect.
        """
        car_rect = pygame.Rect(
            int(car_x - half_size), int(car_y - half_size),
            int(half_size * 2), int(half_size * 2),
        )
        return self.rect.colliderect(car_rect)
