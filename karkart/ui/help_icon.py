"""help_icon.py - includes all the features of the help icon"""

from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR
from karkart.ui.ui_object import UIObject

class HelpIcon(UIObject):
    def __init__(self, manager, screen: str) -> None:
        self.manager = manager
        self.screen: str = screen

        self.x: ScreenPositions = sp.XXLEFT
        self.y: ScreenPositions = sp.XXTOP

        self.radius: int = 30
        self.circle_radius: int = int(self.radius * 1.5)
        self.diameter: int = self.circle_radius * 2
        help_pic = pygame.image.load(PICTURES_DIR / "help_button.png")
        self.pic = pygame.transform.scale(help_pic, (self.diameter, self.diameter))

        self.position: (int, int) = (self.x - self.circle_radius, self.y - self.circle_radius)
        self.circle_position: (int, int) = (self.x, self.y)

    def handle_event(self, event):
        # Press H -> open help and if closed goes back to same string.
        if event.key == pygame.K_h:
            self.manager.change_screen("help")
            self.manager.get_screen().set_return_screen(self.screen)

    def draw(self, surface):
        # Draw circle and help image.
        pygame.draw.circle(surface, Colors.DARK_BLUE, self.circle_position, self.circle_radius)
        pygame.draw.circle(surface, Colors.LIGHT_BLUE, self.circle_position, self.circle_radius, 4)
        pygame.draw.circle(surface, Colors.BLACK, self.circle_position, self.circle_radius, 2)

        surface.blit(self.pic, self.position)
