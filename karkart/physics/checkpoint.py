"""Checkpoint: a rectangular region the car must touch in order."""

from __future__ import annotations

import pygame


class Checkpoint:
    """Axis-aligned rectangle that records whether the car has passed through."""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.passed: bool = False

    def check(self, car_x: float, car_y: float) -> bool:
        """Return True if (*car_x*, *car_y*) lies inside the checkpoint rect."""
        return self.rect.collidepoint(car_x, car_y)
