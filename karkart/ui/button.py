"""
button.py
--------
Selectable object
Usage: in screens to determine their transitions

Interaction:
- WASD/ARROWS to move pointer
- RETURN to click on the button

"""

from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PIXEL_FONT
from karkart.ui.ui_object import UISelectObject


class Button(UISelectObject):
    """Fixed-position pixel-font button that auto-sizes around its text."""

    def __init__(
        self,
        text: str,
        manager: ScreenManager,
        action: str = None,
        center_x: float = 0,
        center_y: float = 0,
        width: float = 0,
        height: float = 0,
    ) -> None:
        super().__init__(center_x, center_y, width, height)

        self.manager = manager
        self.action = action

        self.text = text

        # Store font, rendered text, center coordinates, real coordinates and area of the button.
        font_size = 15
        button_font = pygame.font.Font(str(PIXEL_FONT), font_size)
        self.rendered_text = button_font.render(text, True, Colors.WHITE)
        self.center = self.rendered_text.get_rect(center=(center_x, center_y))
        if not self.width:
            self.width = self.rendered_text.get_width() + font_size * 3
        if not self.height:
            self.height = self.rendered_text.get_height() + font_size * 1.5
        self.x = self.center.x - (self.width - self.rendered_text.get_width()) / 2
        self.y = self.center.y - (self.height - self.rendered_text.get_height()) / 2
        self.button_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def handle_event(self, event) -> None:
        """If RETURN is clicked, the screen is changed with the recorded action."""

        if self.action:
            if event.key == pygame.K_RETURN:
                self.manager.change_screen(self.action)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw 3 layers of the button + text."""

        pygame.draw.rect(surface, self.color, self.button_rect, border_radius=8)
        pygame.draw.rect(
            surface,
            self.bord_2_color,
            self.button_rect,
            self.bord_2_thick,
            border_radius=8,
        )
        pygame.draw.rect(
            surface, self.bord_color, self.button_rect, self.bord_thick, border_radius=8
        )
        surface.blit(self.rendered_text, self.center)

    def set_position(self, x: float, y: float) -> None:
        """Function used primarly inside container to modify object position."""

        super().set_position(x, y)
        self.center.x = self.x + (self.width - self.rendered_text.get_width()) / 2
        self.center.y = self.y + (self.height - self.rendered_text.get_height()) / 2
        self.button_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_action(self) -> str:
        return self.action

    def get_text(self) -> str:
        return self.text


class BackButton(Button):
    """Button to go back to previous screen."""

    def __init__(self, manager: ScreenManager, action: str):
        super().__init__(
            "Back", manager, action, center_x=sp.XLEFT, center_y=sp.XXXBOTTOM
        )


class TextButton(Button):
    """Button the contains text inside, too."""

    def __init__(
        self, text: str, manager: ScreenManager, action: str = None, width: float = 200, height: float = 50
    ):
        super().__init__(text, manager, action, width=width, height=height)

    def handle_event(self, event) -> None:
        return None
