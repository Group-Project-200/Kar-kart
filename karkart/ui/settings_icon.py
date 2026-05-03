from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR
from karkart.ui.ui_object import UISelectObject

class SettingsIcon(UISelectObject):
    def __init__(self, manager, screen: str) -> None:
        self.manager = manager
        self.screen: str = screen

        super().__init__(sp.XXRIGHT, sp.XXTOP, 0, 0)

        self.radius: int = 30
        self.circle_radius: int = int(self.radius * 1.5)
        self.diameter: int = self.circle_radius * 2
        gear = pygame.image.load(PICTURES_DIR / "gearicon.png")
        self.pic = pygame.transform.scale(gear, (self.diameter, self.diameter))

        self.position: (int, int) = (self.x - self.circle_radius, self.y - self.circle_radius)
        self.circle_position: (int, int) = (self.x, self.y)

    def handle_event(self, event):
        if event.key == pygame.K_ESCAPE:
            self.manager.push_screen(self.manager.get_screen().get_label())
            self.manager.change_screen("settings")
    
    def draw(self, surface):

        # Draw circle and gear image.
        pygame.draw.circle(surface, self.color, self.circle_position, self.radius*1.5)
        pygame.draw.circle(surface, self.bord_2_color, self.circle_position, self.radius*1.5, self.bord_2_thick)
        pygame.draw.circle(surface, self.bord_color, self.circle_position, self.radius*1.5, self.bord_thick)

        surface.blit(self.pic, self.position)
