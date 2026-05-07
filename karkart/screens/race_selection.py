from __future__ import annotations

import math

import pygame

from karkart.constants import ScreenPositions as sp
from karkart.paths import PICTURES_DIR
from karkart.screens.screen_object import Screen
from karkart.settings import Keys as K
from karkart.ui import SettingsIcon, TextCard
from karkart.ui.help_icon import HelpIcon


_MODE_IMAGE_NAMES: tuple[str, ...] = (
    "trial_mode.png",
    "race_mode_card.png",
    "championship_mode.png",
)
_MODE_LABELS: tuple[str, ...] = ("Time Trial", "Race Mode", "Championship")


class RaceSelector(Screen):

    CARD_WIDTH = 280
    CARD_HEIGHT = 220
    CARD_GAP = 40

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        self.races = _MODE_LABELS
        self.selected_index = 1

        self.bg = self._try_load_background(PICTURES_DIR / "race_selection_bg.png")

        self.card_y = sp.HEIGHT - self.CARD_HEIGHT - 105
        total_cards_width = self.CARD_WIDTH * len(self.races) + self.CARD_GAP * (
            len(self.races) - 1
        )
        self.card_start_x = (sp.WIDTH - total_cards_width) // 2

        self.mode_images = [
            self._try_load_card(PICTURES_DIR / name) for name in _MODE_IMAGE_NAMES
        ]

        self.instruction_card = TextCard(
            "SELECT WITH ARROWS/WASD, CONFIRM WITH ENTER",
            width=760,
            height=46,
            font_size=11,
        )
        self.instruction_card.set_position(
            sp.CENTER_X - self.instruction_card.get_width() / 2,
            sp.HEIGHT - 58,
        )

        self.settings_icon = SettingsIcon(self.manager, "car")
        self.help_icon = HelpIcon(self.manager, "race_selector")

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

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)

        if event.key in (K.LEFT, pygame.K_a):
            self.selected_index = (self.selected_index - 1) % len(self.races)

        elif event.key in (K.RIGHT, pygame.K_d):
            self.selected_index = (self.selected_index + 1) % len(self.races)

        elif event.key == pygame.K_RETURN:
            self.manager.app_data.current_mode = self.races[self.selected_index]
            self.manager.change_screen("car")

    def update(self) -> None:
        pass

    def _draw_card_shadow(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        selected: bool,
    ) -> None:
        if selected:
            shadow = pygame.Surface((rect.width + 24, rect.height + 24), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow,
                (0, 0, 0, 120),
                shadow.get_rect(),
                border_radius=18,
            )
            surface.blit(shadow, (rect.x - 12, rect.y + 10))
        else:
            shadow = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow,
                (0, 0, 0, 80),
                shadow.get_rect(),
                border_radius=12,
            )
            surface.blit(shadow, (rect.x - 5, rect.y + 8))

    def _draw_selected_glow(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        ticks = pygame.time.get_ticks()
        pulse = int(45 + 35 * math.sin(ticks * 0.006))

        glow_rect = rect.inflate(24, 24)
        glow = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)

        pygame.draw.rect(
            glow,
            (255, 230, 100, 85 + pulse),
            glow.get_rect(),
            border_radius=18,
        )
        surface.blit(glow, glow_rect.topleft)

        pygame.draw.rect(
            surface,
            (255, 255, 255),
            glow_rect,
            4,
            border_radius=18,
        )

        pygame.draw.rect(
            surface,
            (255, 210, 60),
            rect.inflate(10, 10),
            4,
            border_radius=14,
        )

    def _draw_unselected_overlay(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        surface.blit(overlay, rect.topleft)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Kar Kart - Race Selector")

        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((50, 100, 200))

        self.instruction_card.draw(surface)

        for i, image in enumerate(self.mode_images):
            selected = i == self.selected_index

            x = self.card_start_x + i * (self.CARD_WIDTH + self.CARD_GAP)
            y = self.card_y

            if selected:
                scale = 1.08
                y -= 18
            else:
                scale = 0.94
                y += 10

            width = int(self.CARD_WIDTH * scale)
            height = int(self.CARD_HEIGHT * scale)

            card_rect = pygame.Rect(0, 0, width, height)
            card_rect.center = (
                x + self.CARD_WIDTH // 2,
                y + self.CARD_HEIGHT // 2,
            )

            self._draw_card_shadow(surface, card_rect, selected)

            if selected:
                self._draw_selected_glow(surface, card_rect)

            if image is not None:
                card_image = pygame.transform.smoothscale(image, (width, height))
                surface.blit(card_image, card_rect.topleft)
            else:
                pygame.draw.rect(surface, (220, 200, 160), card_rect, border_radius=8)

            if selected:
                pygame.draw.rect(surface, (0, 0, 0), card_rect, 4, border_radius=10)
            else:
                self._draw_unselected_overlay(surface, card_rect)

        self.help_icon.draw(surface)
        self.settings_icon.draw(surface)

    def get_label(self) -> str:
        return self.label