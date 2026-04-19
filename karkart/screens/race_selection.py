"""Race mode picker: Time Trial / Race / Championship."""

from __future__ import annotations

import pygame

from karkart.constants import Keys as K, ScreenPositions as sp
from karkart.paths import PICTURES_DIR


_MODE_IMAGE_NAMES: tuple[str, ...] = (
    "trial_mode.png",
    "race_mode_card.png",
    "championship_mode.png",
)
_MODE_LABELS: tuple[str, ...] = ("Time Trial", "Race Mode", "Championship")


class RaceSelector:
    """Horizontal card picker for race modes."""

    CARD_WIDTH = 280
    CARD_HEIGHT = 220
    CARD_GAP = 40

    def __init__(self, manager) -> None:
        self.manager = manager
        self.races = _MODE_LABELS
        self.selected_index = 1

        self.bg = self._try_load_background(PICTURES_DIR / "race_selection_bg.png")

        self.card_y = sp.HEIGHT - self.CARD_HEIGHT - 100
        total_cards_width = self.CARD_WIDTH * len(self.races) + self.CARD_GAP * (len(self.races) - 1)
        self.card_start_x = (sp.WIDTH - total_cards_width) // 2

        self.mode_images = [self._try_load_card(PICTURES_DIR / name) for name in _MODE_IMAGE_NAMES]

    @staticmethod
    def _try_load_background(path) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(path)).convert()
        except (FileNotFoundError, pygame.error):
            return None
        return pygame.transform.scale(image, (sp.WIDTH, sp.HEIGHT))

    @classmethod
    def _try_load_card(cls, path) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(path)).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return None
        return pygame.transform.scale(image, (cls.CARD_WIDTH, cls.CARD_HEIGHT))

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == K.LEFT:
            self.selected_index = (self.selected_index - 1) % len(self.races)
        elif event.key == K.RIGHT:
            self.selected_index = (self.selected_index + 1) % len(self.races)
        elif event.key == pygame.K_RETURN:
            self.manager.change_screen("car")
        elif event.key == pygame.K_ESCAPE:
            self.manager.change_screen("start")

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((50, 100, 200))

        for i, image in enumerate(self.mode_images):
            x = self.card_start_x + i * (self.CARD_WIDTH + self.CARD_GAP)
            card_rect = pygame.Rect(x, self.card_y, self.CARD_WIDTH, self.CARD_HEIGHT)

            if image is not None:
                surface.blit(image, (x, self.card_y))
            else:
                pygame.draw.rect(surface, (220, 200, 160), card_rect, border_radius=8)

            if i == self.selected_index:
                # White outer glow + black inner outline make the selection pop.
                glow_rect = card_rect.inflate(8, 8)
                pygame.draw.rect(surface, (255, 255, 255), glow_rect, 4, border_radius=10)
                pygame.draw.rect(surface, (0, 0, 0), card_rect, 4, border_radius=8)

        pygame.display.set_caption("Kar Kart - Race Selector")
