"""
icon.py
--------
Non-selectable object
Usage: open settings and help and draw their icons.

Interaction:
- ESC to open/close settings.
- H to open/close help.

"""

from __future__ import annotations
from abc import ABC, abstractmethod

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR
from karkart.ui.ui_object import UISelectObject


class _Icon(UISelectObject, ABC):
    """Abstract class for any icon"""

    @abstractmethod
    def __init__(
        self,
        manager: ScreenManager,
        screen: str,
        next_screen: str,
        img_path: str,
        center_x: float = sp.XXRIGHT,
        center_y: float = sp.XXTOP,
        control=pygame.K_ESCAPE,
    ) -> None:
        self.manager = manager
        self.screen: str = screen
        self.next_screen: str = next_screen
        self.control = control

        super().__init__(center_x, center_y, 0, 0)
        self.unselect()

        self.radius: int = 30
        self.circle_radius: int = int(self.radius * 1.5)
        self.diameter: int = self.circle_radius * 2
        img = pygame.image.load(PICTURES_DIR / img_path)
        self.pic = pygame.transform.scale(img, (self.diameter, self.diameter))

        self.position: (int, int) = (
            self.x - self.circle_radius,
            self.y - self.circle_radius,
        )
        self.circle_position: (int, int) = (self.x, self.y)

    def handle_event(self, event):
        """Open pop-up menu by clicking specific control."""

        if event.key == self.control or (
            event.key == pygame.K_RETURN and self.is_selected()
        ):
            self.manager.push_screen(self.screen)
            self.manager.change_screen(self.next_screen)

    def draw(self, surface):
        """Draw 3 layers of background circle + the picture."""
        
        pygame.draw.circle(
            surface, self.color, self.circle_position, self.circle_radius
        )
        pygame.draw.circle(
            surface, self.bord_2_color, self.circle_position, self.circle_radius, 4
        )
        pygame.draw.circle(
            surface, self.bord_color, self.circle_position, self.circle_radius, 2
        )

        surface.blit(self.pic, self.position)


class SettingsIcon(_Icon):
    """Extension of _Icon for settings object."""

    def __init__(self, manager, screen: str) -> None:
        super().__init__(manager, screen, "settings", "gearicon.png")


class HelpIcon(_Icon):
    """Extension of _Icon for help object."""

    def __init__(self, manager, screen: str) -> None:
        super().__init__(
            manager,
            screen,
            "help",
            "help_button.png",
            center_x=sp.XXLEFT,
            control=pygame.K_h,
        )
