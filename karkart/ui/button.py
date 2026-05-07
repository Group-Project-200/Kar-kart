from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PIXEL_FONT
from karkart.ui.ui_object import UISelectObject


class Button(UISelectObject):
    """Fixed-position pixel-font button that auto-sizes around its text."""

    def __init__(self, text: str, manager, action: str=None, center_x: float=0, center_y: float=0, width: float=0, height: float=0) -> None:
        super().__init__(center_x, center_y, width, height)

        self.manager = manager
        self.action = action

        self.text = text

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
        if self.action:
            if event.key == pygame.K_RETURN:
                self.manager.change_screen(self.action)

    def draw(self, surface: pygame.Surface) -> None:

        pygame.draw.rect(surface, self.color, self.button_rect, border_radius=8)
        pygame.draw.rect(surface, self.bord_2_color, self.button_rect, self.bord_2_thick, border_radius=8)
        pygame.draw.rect(surface, self.bord_color, self.button_rect, self.bord_thick, border_radius=8)
        surface.blit(self.rendered_text, self.center)

    def set_position(self, x, y):
        super().set_position(x, y)
        self.center.x = self.x + (self.width - self.rendered_text.get_width()) / 2
        self.center.y = self.y + (self.height - self.rendered_text.get_height()) / 2
        self.button_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_action(self):
        return self.action

    def get_text(self):
        return self.text

class BackButton(Button):
    def __init__(self, manager, action):
        super().__init__("Back", manager, action, center_x=sp.XLEFT, center_y=sp.XXXBOTTOM)

class TextButton(Button):
    def __init__(self, text, manager, action=None, width=200, height=50):
        super().__init__(text, manager, action, width=width, height=height)

    def handle_event(self, event) -> None:
        return None