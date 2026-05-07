from __future__ import annotations
from abc import ABC, abstractmethod

import pygame

from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.paths import PIXEL_FONT
from karkart.ui.ui_object import UISelectObject


class Card(UISelectObject, ABC):
    """A bordered rectangular card. ``(x, y)`` is the *centre*."""

    @abstractmethod
    def __init__(
        self, center_x: float, center_y: float, width: float, height: float
    ) -> None:
        super().__init__(center_x, center_y, width, height)
        self.text = None

    def draw(self, surface: pygame.Surface) -> None:
        self.outer_card = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bord_2_color, self.outer_card, border_radius=8)
        pygame.draw.rect(
            surface, self.bord_color, self.outer_card, self.bord_thick, border_radius=8
        )

    def get_text(self):
        return self.text


class MapCard(Card):

    def __init__(self, track, manager) -> None:
        self.width, self.height = 220, 190
        super().__init__(0, 0, self.width, self.height)

        self.track = track
        self.manager = manager

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        self.track.draw(surface)

        name_rect = pygame.Rect(self.x + (self.width-self.track.get_width()) / 2, self.y + 5, self.track.get_width(), 20)
        pygame.draw.rect(surface, self.color, name_rect, border_radius=4)
        pygame.draw.rect(
            surface, self.bord_color, name_rect, self.bord_thick, border_radius=4
        )

        name_font = pygame.font.Font(str(PIXEL_FONT), 9)
        name_text = name_font.render(self.track.get_name(), True, Colors.WHITE)
        surface.blit(name_text, name_text.get_rect(center=name_rect.center))

    def set_position(self, x: float, y: float) -> None:

        self.x = x
        self.y = y
        self.track.set_position(
            self.x + (self.width - self.track.get_width()) / 2,
            self.y + 30,
        )

    def get_action(self):
        return self.track


class PopUpCard(Card):
    """Selectable card showing an option in the pause menu."""

    def __init__(
        self,
        text: str,
        action: Screen | None = None,
        width: int | None = 200,
        height: int | None = 50,
    ) -> None:
        super().__init__(0, 0, width, height)
        self.text = text
        self.action = action

    def handle_event(self, event):
        pass

    def draw(self, surface: pygame.Surface) -> None:
        self.outer_card = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, self.outer_card, border_radius=8)
        super().draw(surface)

        name_font = pygame.font.Font(str(PIXEL_FONT), 12)
        name_text = name_font.render(self.text, True, Colors.WHITE)
        surface.blit(name_text, name_text.get_rect(center=self.outer_card.center))

    def get_action(self):
        return self.action

    def get_text(self):
        return self.text


class TextCard(Card):
    """
    Text card of selection screens.
    """

    def __init__(self, text: str, width: int, height=None, font_size=15) -> None:
        super().__init__(0, 0, 0, 0)
        self.text = text

        instr_font = pygame.font.Font(str(PIXEL_FONT), font_size)
        self.render_text = instr_font.render(text, True, Colors.WHITE)
        self.center = self.render_text.get_rect(center=(sp.CENTER_X, sp.XTOP))

        self.width = width

        if height:
            self.height = height
        else:
            self.height = self.render_text.get_height() + font_size * 1.5
        self.x = self.center.x - (self.width - self.render_text.get_width()) / 2
        self.y = self.center.y - (self.height - self.render_text.get_height()) / 2
        self.instr_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.instr_rect, border_radius=8)
        pygame.draw.rect(
            surface,
            self.bord_2_color,
            self.instr_rect,
            self.bord_2_thick,
            border_radius=8,
        )
        pygame.draw.rect(
            surface, self.bord_color, self.instr_rect, self.bord_thick, border_radius=8
        )
        surface.blit(self.render_text, self.center)

    def set_position(self, x, y):
        super().set_position(x, y)
        self.center.x = self.x + (self.width - self.render_text.get_width()) / 2
        self.center.y = self.y + (self.height - self.render_text.get_height()) / 2
        self.instr_rect = pygame.Rect(self.x, self.y, self.width, self.height)

class HelpTextCard(Card):
    """Single card that draws help text block."""

    def __init__(self, width: int, height: int) -> None:
        super().__init__(sp.CENTER_X, sp.CENTER_Y, width, height)
        self.unselect()
        self.font = pygame.font.Font(None, 30)
        self.lines = [
            "Navigation Buttons:",
            "WASD/Arrow Keys: Selection",
            "RETURN: Confirm selection/Next screen",
            "ESC: Open Settings Menu/Save and close",
            "H: Help Menu",
            "",
            "Game Play Buttons:",
            "W/S: Accelerate / Brake & Reverse  ",
            "A/D: Steer Left / Right ",
            "SPACE: Hold to Drift, Release for Boost  ",
            "ESC: Pause Menu",
            "",
            "Press H or ESC to close Help Menu",
        ]

    def get_action(self):
        return None
    
    def get_text(self):
        return self.lines

    def handle_event(self, event) -> None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect, border_radius=8)
        pygame.draw.rect(surface, self.bord_color, rect, self.bord_thick, border_radius=8)

        line_y = self.y + 20
        line_x = self.x + 24
        for line in self.lines:
            line_surface = self.font.render(line, True, Colors.WHITE)
            surface.blit(line_surface, (line_x, line_y))
            line_y += 32
