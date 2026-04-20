"""Cards: decorated rectangles used as clickable/selectable UI primitives."""

from __future__ import annotations

import pygame

from karkart.constants import Colors
from karkart.paths import PIXEL_FONT


class Card:
    """A bordered rectangular card. ``(x, y)`` is the *centre*."""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.width = width
        self.height = height
        self.x = x - self.width / 2
        self.y = y - self.height / 2
        self.color = Colors.LIGHT_BLUE
        self.bord_color = Colors.BLACK
        self.border = 2

    def get_width(self) -> float:
        return self.width

    def get_height(self) -> float:
        return self.height

    def draw(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect, border_radius=8)
        pygame.draw.rect(surface, self.bord_color, rect, self.border, border_radius=8)


class MapCard(Card):
    """Selectable card showing a map preview plus the track name."""

    def __init__(self, track, manager) -> None:
        self.w, self.h = 120, 120
        super().__init__(0, 0, self.w, self.h)

        self.track = track
        self.manager = manager
        self.inner_color = Colors.DARK_BLUE

    def select(self) -> None:
        self.color = Colors.RED
        self.inner_color = Colors.DARK_RED
        self.bord_color = Colors.BLACK
        self.border = 2

    def unselect(self) -> None:
        self.color = Colors.LIGHT_BLUE
        self.inner_color = Colors.DARK_BLUE
        self.bord_color = Colors.BLACK
        self.border = 2

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
