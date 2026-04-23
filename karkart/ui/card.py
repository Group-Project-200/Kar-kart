"""Cards: decorated rectangles used as clickable/selectable UI primitives."""

from __future__ import annotations
from abc import ABC, abstractmethod

import pygame

from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.paths import PIXEL_FONT
from karkart.ui.ui_object import UIObject


class Card(UIObject, ABC):
    """A bordered rectangular card. ``(x, y)`` is the *centre*."""
    @abstractmethod
    def __init__(self, center_x: float, center_y: float, width: float, height: float) -> None:
        super().__init__(center_x, center_y, width, height)

        self.unselect()
        self.inner_color = Colors.DARK_BLUE
        self.bord_color = Colors.BLACK
        self.border = 2

    def draw(self, surface: pygame.Surface) -> None:
        self.outer_card = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, self.outer_card, border_radius=8)
        pygame.draw.rect(surface, self.bord_color, self.outer_card, self.border, border_radius=8)

    def select(self) -> None:
        self.color = Colors.RED
        self.inner_color = Colors.DARK_RED

    def unselect(self) -> None:
        self.color = Colors.LIGHT_BLUE
        self.inner_color = Colors.DARK_BLUE


class MapCard(Card):
    """Selectable card showing a map preview plus the track name."""

    def __init__(self, track, manager) -> None:
        self.w, self.h = 120, 120
        super().__init__(0, 0, self.w, self.h)

        self.track = track
        self.manager = manager

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        self.track.draw(surface)

        name_rect = pygame.Rect(self.x + 10, self.y + 5, self.track.get_width(), 20)
        pygame.draw.rect(surface, self.inner_color, name_rect, border_radius=4)
        pygame.draw.rect(surface, self.bord_color, name_rect, 2, border_radius=4)

        name_font = pygame.font.Font(str(PIXEL_FONT), 9)
        name_text = name_font.render(self.track.get_name(), True, Colors.WHITE)
        surface.blit(name_text, name_text.get_rect(center=name_rect.center))

    def set_position(self, x: float, y: float) -> None:
        """Place the card and re-position its track preview inside it."""
        self.x = x
        self.y = y
        self.track.set_position(
            self.x + (self.width - self.track.get_width()) / 2,
            self.y + 30,
        )

    def get_map(self):
        return self.track


class PopUpCard(Card):
    """Selectable card showing an option in the pause menu."""
    
    def __init__(self, text: str, state: Screen | None =None, width: int | None =200, height: int | None =50) -> None:
        super().__init__(0, 0, width, height)
        self.color = self.inner_color
        self.text = text
        self.state = state

    def handle_event(self, event):
        pass

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)

        name_font = pygame.font.Font(str(PIXEL_FONT), 12)
        name_text = name_font.render(self.text, True, Colors.WHITE)
        surface.blit(name_text, name_text.get_rect(center=self.outer_card.center))

    def get_state(self):
        return self.state

    def get_text(self):
        return self.text

    def unselect(self) -> None:
        super().select()
        self.color = Colors.DARK_BLUE

class TitleCard:
    """
    Title card of selection screens.
    NOT CHILD OF CARD.
    """

    def __init__(self, container_width: int, text: str) -> None:
        font_size = 15
        instr_font = pygame.font.Font(str(PIXEL_FONT), font_size)
        self.instr_text = instr_font.render(text, True, Colors.WHITE)
        self.instr_center = self.instr_text.get_rect(center=(sp.CENTER_X, sp.XTOP))

        instr_width = container_width
        instr_height = self.instr_text.get_height() + font_size * 1.5
        instr_x = self.instr_center.x - (instr_width - self.instr_text.get_width()) / 2
        instr_y = self.instr_center.y - (instr_height - self.instr_text.get_height()) / 2
        self.instr_rect = pygame.Rect(instr_x, instr_y, instr_width, instr_height)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, Colors.DARK_BLUE, self.instr_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.LIGHT_BLUE, self.instr_rect, 4, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, self.instr_rect, 2, border_radius=8)
        surface.blit(self.instr_text, self.instr_center)