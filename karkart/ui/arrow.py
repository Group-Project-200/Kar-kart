"""
arrow.py
--------
Selectable object
Usage: in Arrow Container to decide on settings

"""

from __future__ import annotations

import pygame

from karkart.constants import Colors
from karkart.ui.card import PopUpCard
from karkart.ui.ui_object import UISelectObject

class Arrow(UISelectObject):
    """Arrow object for preference selections in settings pop-up."""
    
    def __init__(self, center_x: float, center_y: float, width: float, height: float, direction: str):
        super().__init__(center_x, center_y, width, height)
        self.direction = direction

    def draw(self, surface):
        """Draw 3 layers of the arrow"""
        pygame.draw.polygon(surface, self.color, self.points)
        pygame.draw.polygon(surface, self.bord_2_color, self.points, self.bord_2_thick)
        pygame.draw.polygon(surface, self.bord_color, self.points, self.bord_thick)

    def set_position(self, x: float, y: float) -> None:
        """Place the arrow in the correct direction and identify all points."""

        super().set_position(x, y)

        self.x = x
        self.y = y

        # Based on direction, points are decided to draw the polygons
        if self.direction == "left":

            self.points: (float, float, float) = (
                (self.x + self.width, self.y),
                (self.x, self.y + self.height / 2),
                (self.x + self.width, self.y + self.height),
            )
        elif self.direction == "right":
            self.points: (float, float, float) = (
                (self.x, self.y),
                (self.x + self.width, self.y + self.height / 2),
                (self.x, self.y + self.height),
            )
