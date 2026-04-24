"""settings_icon.py - includes all the features of the settings icon"""

from __future__ import annotations

import pygame

from karkart.paths import PICTURES_DIR
from karkart.constants import Colors, ScreenPositions as sp

class SettingsIcon:
    def __init__(self, manager, screen: str) -> None:
        self.manager = manager
        self.screen: str = screen

        self.x: ScreenPositions = sp.XXRIGHT
        self.y: ScreenPositions = sp.XXTOP


        self.radius: int = 30
        self.diameter: int = self.radius * 2
        gear = pygame.image.load(PICTURES_DIR / "gearicon.png")
        self.pic = pygame.transform.scale(gear, (self.diameter, self.diameter))

        self.position: (int, int) = (self.x - self.radius, self.y - self.radius)
        self.circle_position: (int, int) = (self.x, self.y)

    def handle_event(self, event):
        # Press ESC -> open settings and if closed goes back to same string.
        if event.key == pygame.K_ESCAPE:
            self.manager.change_screen("settings")
            self.manager.get_screen().set_return_screen(self.screen)
    
    def draw(self, surface):

        # Draw circle and gear image.
        pygame.draw.circle(surface, Colors.DARK_BLUE, self.circle_position, self.radius*1.5)
        pygame.draw.circle(surface, Colors.LIGHT_BLUE, self.circle_position, self.radius*1.5, 4)
        pygame.draw.circle(surface, Colors.BLACK, self.circle_position, self.radius*1.5, 2)

        surface.blit(self.pic, self.position)