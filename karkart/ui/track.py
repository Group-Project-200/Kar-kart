from __future__ import annotations

import pygame

from karkart.constants import Colors
from karkart.ui.ui_object import UIObject


class Track(UIObject):

    def __init__(self, pic_path: str, name: str, corr_map: str | None = None) -> None:
        self.image = pygame.image.load(pic_path).convert_alpha()
        self.name = name
        self.corr_map = corr_map

        super().__init__(0, 0, 0, 0)

    def handle_event(self, event) -> None:

        return None

    def draw(self, surface: pygame.Surface) -> None:

        scaled = pygame.transform.scale(self.image, (self.width, self.height))

        subsurf = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(subsurf, Colors.WHITE, subsurf.get_rect())
        scaled.blit(subsurf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        surface.blit(scaled, (self.x, self.y))
        pygame.draw.rect(
            surface,
            Colors.BLACK,
            pygame.Rect(self.x, self.y, self.width, self.height),
            2,
        )

    def get_image(self) -> pygame.Surface:
        return self.image

    def get_name(self) -> str:
        return self.name

    def set_dimensions(self, width: int, height: int) -> None:
        self.width, self.height = width, height

    def get_state(self) -> str | None:
        return self.corr_map
