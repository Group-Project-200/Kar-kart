"""arrow.py - arrow object for preference selections."""

from __future__ import annotations

import pygame

from karkart.constants import Colors
from karkart.ui.card import PopUpCard
from karkart.ui.ui_object import UIObject

class Arrow(UIObject):
    """Arrow object for preference selections in settings pop-up."""
    
    def __init__(self, center_x: float, center_y: float, width: float, height: float, direction: str):
        super().__init__(center_x, center_y, width, height)

        self.direction = direction

        self.unselect()
        self.thickness = 2

    def draw(self, surface):
        pygame.draw.polygon(surface, self.color, self.points)
        pygame.draw.polygon(surface, Colors.BLACK, self.points, self.thickness)

    def select(self) -> None:
        self.color = Colors.RED

    def unselect(self) -> None:
        self.color = Colors.DARK_BLUE

    def set_position(self, x: float, y: float) -> None:
        """Place the arrow and identify all points."""
        self.x = x
        self.y = y

        if self.direction == "left":
            # self.points = ((self.x + self.width, self.y), (self.x, self.y + self.height / 2), (self.x + self.width, self.y + self.height))
            self.points = ((self.x + self.width, self.y), (self.x, self.y + self.height / 2), (self.x + self.width, self.y + self.height))
        elif self.direction == "right":
            self.points = ((self.x, self.y), (self.x + self.width, self.y + self.height / 2), (self.x, self.y + self.height))