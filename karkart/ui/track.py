"""Selectable track entry with a cover image and a display name."""

from __future__ import annotations

import pygame

from karkart.constants import Colors


class Track:
    """Wraps a track's cover image, display name, and source folder path."""

    def __init__(self, pic_path: str, name: str, corr_map: str | None = None) -> None:
        self.image = pygame.image.load(pic_path).convert_alpha()
        self.name = name
        self.corr_map = corr_map      # Path to the folder with map layers, or None.

        self.width: int = 0
        self.height: int = 0
        self.x: float | None = None
        self.y: float | None = None

    def handle_event(self, event) -> None:  # noqa: D401 - interface symmetry.
        """Placeholder for future hover/click behaviour."""
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the cover image at the configured position and scale."""
        scaled = pygame.transform.scale(self.image, (self.width, self.height))

        # Pre-multiply the alpha by white so transparent pixels do not leak colour.
        subsurf = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(subsurf, Colors.WHITE, subsurf.get_rect())
        scaled.blit(subsurf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        surface.blit(scaled, (self.x, self.y))
        pygame.draw.rect(surface, Colors.BLACK, pygame.Rect(self.x, self.y, self.width, self.height), 2)

    # -- Accessors --------------------------------------------------------- #

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def get_image(self) -> pygame.Surface:
        return self.image

    def get_name(self) -> str:
        return self.name

    def set_position(self, x: float, y: float) -> None:
        self.x, self.y = x, y

    def set_dimensions(self, width: int, height: int) -> None:
        self.width, self.height = width, height

    def get_map(self) -> str | None:
        return self.corr_map
