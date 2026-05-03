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

        font_size = 15
        button_font = pygame.font.Font(str(PIXEL_FONT), font_size)
        self.text = button_font.render(text, True, Colors.WHITE)
        self.center = self.text.get_rect(center=(center_x, center_y))

        if not self.width:
            self.width = self.text.get_width() + font_size * 3
        if not self.height:
            self.height = self.text.get_height() + font_size * 1.5
        self.x = self.center.x - (self.width - self.text.get_width()) / 2
        self.y = self.center.y - (self.height - self.text.get_height()) / 2
        self.button_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def handle_event(self, event) -> None:
        if self.action:
            if event.key == pygame.K_RETURN:
                self.manager.change_screen(self.action)

    def draw(self, surface: pygame.Surface) -> None:

        pygame.draw.rect(surface, self.color, self.button_rect, border_radius=8)
        pygame.draw.rect(surface, self.bord_2_color, self.button_rect, self.bord_2_thick, border_radius=8)
        pygame.draw.rect(surface, self.bord_color, self.button_rect, self.bord_thick, border_radius=8)
        surface.blit(self.text, self.center)

    def set_position(self, x, y):
        super().set_position(x, y)
        self.center.x = self.x + (self.width - self.text.get_width()) / 2
        self.center.y = self.y + (self.height - self.text.get_height()) / 2
        self.button_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_action(self):
        return self.action

class BackButton(Button):
    def __init__(self, manager, action):
        super().__init__("Back", manager, action, center_x=sp.XLEFT, center_y=sp.XXXBOTTOM)

class PopUpButton(Button):
    def __init__(self, text, manager, action=None):
        super().__init__(text, manager, action, width=200, height=50)


class ColorButton(Button):

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        action: str,
        manager,
        color_normal: tuple[int, int, int],
        color_hover: tuple[int, int, int],
    ) -> None:
        super().__init__(x, y, width, height, text, action, manager)
        self.color_normal = color_normal
        self.color_hover = color_hover
        self.keyboard_hovered = False

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.action:
                self.manager.change_screen(self.action)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.keyboard_hovered = not self.keyboard_hovered
            elif event.key == pygame.K_RETURN:
                if self.keyboard_hovered and self.action:
                    self.manager.change_screen(self.action)

    def draw(self, surface: pygame.Surface) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos) or self.keyboard_hovered
        color = self.color_hover if hovered else self.color_normal
        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        button_font = pygame.font.SysFont("arial", 20, bold=True)
        button_text = button_font.render(self.text, True, Colors.BLACK)
        surface.blit(button_text, button_text.get_rect(center=self.rect.center))
