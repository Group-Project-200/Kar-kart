"""Reusable button widgets used across multiple screens."""

from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PIXEL_FONT


class Button:
    """A rectangular mouse-click button that switches the active screen on press.

    Coordinates ``x`` and ``y`` refer to the *centre* of the button.
    """

    def __init__(self, x: float, y: float, width: float, height: float,
                 text: str, state: str, manager) -> None:
        self.x = x - width / 2
        self.y = y - height / 2
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, width, height)
        self.text = text
        self.state = state
        self.manager = manager

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.state:
                self.manager.change_screen(self.state)

    def draw(self, surface: pygame.Surface) -> None:
        mouse_pos = pygame.mouse.get_pos()
        color = Colors.WHITE if self.rect.collidepoint(mouse_pos) else Colors.GRAY
        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        button_font = pygame.font.SysFont("arial", 20, bold=True)
        button_text = button_font.render(self.text, True, Colors.BLACK)
        surface.blit(button_text, button_text.get_rect(center=self.rect.center))


class PaddingButton:
    """Fixed-position pixel-font button that auto-sizes around its text."""

    def __init__(self, text: str, state: str, manager) -> None:
        self.text = text
        self.state = state
        self.manager = manager
        self.unselect()

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.manager.change_screen(self.state)

    def draw(self, surface: pygame.Surface) -> None:
        font_size = 15
        button_font = pygame.font.Font(str(PIXEL_FONT), font_size)
        button_text = button_font.render(self.text, True, Colors.WHITE)
        button_center = button_text.get_rect(center=(sp.XLEFT, sp.XXXBOTTOM))

        button_width = button_text.get_width() + font_size * 3
        button_height = button_text.get_height() + font_size * 1.5
        button_x = button_center.x - (button_width - button_text.get_width()) / 2
        button_y = button_center.y - (button_height - button_text.get_height()) / 2
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        pygame.draw.rect(surface, self.inner_color, button_rect, border_radius=8)
        pygame.draw.rect(surface, self.color, button_rect, 4, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, button_rect, 2, border_radius=8)
        surface.blit(button_text, button_center)

    def unselect(self) -> None:
        self.color = Colors.LIGHT_BLUE
        self.inner_color = Colors.DARK_BLUE

    def select(self) -> None:
        self.color = Colors.RED
        self.inner_color = Colors.DARK_RED


class ColorButton(Button):
    """:class:`Button` variant with custom idle/hover colours and keyboard focus."""

    def __init__(
        self, x: float, y: float, width: float, height: float,
        text: str, state: str, manager,
        color_normal: tuple[int, int, int], color_hover: tuple[int, int, int],
    ) -> None:
        super().__init__(x, y, width, height, text, state, manager)
        self.color_normal = color_normal
        self.color_hover = color_hover
        self.keyboard_hovered = False

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.state:
                self.manager.change_screen(self.state)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:          # Toggle keyboard hover.
                self.keyboard_hovered = not self.keyboard_hovered
            elif event.key == pygame.K_RETURN:   # Enter confirms when hovered.
                if self.keyboard_hovered and self.state:
                    self.manager.change_screen(self.state)

    def draw(self, surface: pygame.Surface) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos) or self.keyboard_hovered
        color = self.color_hover if hovered else self.color_normal
        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        button_font = pygame.font.SysFont("arial", 20, bold=True)
        button_text = button_font.render(self.text, True, Colors.BLACK)
        surface.blit(button_text, button_text.get_rect(center=self.rect.center))
