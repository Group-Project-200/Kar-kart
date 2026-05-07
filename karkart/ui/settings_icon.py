from __future__ import annotations
from abc import ABC, abstractmethod

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR
from karkart.ui.ui_object import UISelectObject

class _Icon(UISelectObject, ABC):

    @abstractmethod
    def __init__(self, manager, screen: str, next_screen, img_path) -> None:
        self.manager = manager
        self.screen: str = screen
        self.next_screen: str = next_screen

        super().__init__(sp.XXRIGHT, sp.XXTOP, 0, 0)

        self.radius: int = 30
        self.circle_radius: int = int(self.radius * 1.5)
        self.diameter: int = self.circle_radius * 2
        img = pygame.image.load(PICTURES_DIR / img_path)
        self.pic = pygame.transform.scale(img, (self.diameter, self.diameter))

        self.position: (int, int) = (self.x - self.circle_radius, self.y - self.circle_radius)
        self.circle_position: (int, int) = (self.x, self.y)

    def handle_event(self, event):
        if event.key == pygame.K_ESCAPE or (
            event.key == pygame.K_RETURN and self.is_selected()):
            if not getattr(self.manager.get_screen(), "is_popup", False):
                self.manager.push_screen(self.screen)
                self.manager.change_screen(self.next_screen)
    
    def draw(self, surface):
        # Draw circle and help image.
        pygame.draw.circle(
            surface, Colors.DARK_BLUE, self.circle_position, self.circle_radius
        )
        pygame.draw.circle(
            surface, Colors.LIGHT_BLUE, self.circle_position, self.circle_radius, 4
        )
        pygame.draw.circle(
            surface, Colors.BLACK, self.circle_position, self.circle_radius, 2
        )

        surface.blit(self.pic, self.position)

class SettingsIcon(_Icon):
    def __init__(self, manager, screen: str) -> None:
        super().__init__(manager, screen, "settings", "gearicon.png")

class HelpIcon(_Icon):
    def __init__(self, manager, screen: str) -> None:
        super().__init__(manager, screen, "settings", "gearicon.png")