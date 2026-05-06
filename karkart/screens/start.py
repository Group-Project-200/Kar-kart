from __future__ import annotations

import math

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR, PIXEL_FONT
from karkart.ui.help_icon import HelpIcon
from karkart.ui.settings_icon import SettingsIcon


class StartScreen:

    def __init__(self, manager, label) -> None:
        self.manager = manager
        self.label = label

        self.bg = self._try_load_image(PICTURES_DIR / "bp2.png", convert_alpha=False)

        self.settings_icon = SettingsIcon(self.manager, "start")
        self.help_icon = HelpIcon(self.manager, "start")

        self.start_font = self._load_font(22)
        self.small_font = self._load_font(11)

        self.start_rect = pygame.Rect(0, 0, 470, 62)
        self.start_rect.center = (sp.CENTER_X, sp.HEIGHT - 95)

    def _load_font(self, size: int) -> pygame.font.Font:
        try:
            return pygame.font.Font(str(PIXEL_FONT), size)
        except (FileNotFoundError, OSError, pygame.error):
            return pygame.font.SysFont("arial", size, bold=True)

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return None

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)

        if event.key == pygame.K_SPACE:
            self.manager.change_screen("race_selector")

    def update(self) -> None:
        pass

    def _draw_alpha_rect(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int, int],
        border_radius: int = 0,
    ) -> None:
        temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(temp, color, temp.get_rect(), border_radius=border_radius)
        surface.blit(temp, rect.topleft)

    def _draw_start_button(self, surface: pygame.Surface) -> None:
        ticks = pygame.time.get_ticks()
        mouse_over = self.start_rect.collidepoint(pygame.mouse.get_pos())

        pulse = int(35 + 25 * math.sin(ticks * 0.006))

        draw_rect = self.start_rect.copy()
        if mouse_over:
            draw_rect.y -= 4
            glow_alpha = 120 + pulse
            fill = (255, 215, 85, 185)
            border = (255, 250, 210)
            text_color = (45, 28, 10)
        else:
            glow_alpha = 60 + pulse
            fill = (55, 95, 135, 165)
            border = (170, 220, 255)
            text_color = (255, 245, 220)

        shadow_rect = draw_rect.move(0, 6)
        self._draw_alpha_rect(surface, shadow_rect, (0, 0, 0, 95), 12)

        glow_rect = draw_rect.inflate(18, 14)
        self._draw_alpha_rect(surface, glow_rect, (255, 225, 100, glow_alpha), 16)

        self._draw_alpha_rect(surface, draw_rect, fill, 12)
        pygame.draw.rect(surface, border, draw_rect, 4, border_radius=12)
        pygame.draw.rect(surface, (35, 25, 18), draw_rect, 2, border_radius=12)

        text = "PRESS SPACE TO START"
        shadow = self.start_font.render(text, False, (55, 35, 18))
        label = self.start_font.render(text, False, text_color)

        label_rect = label.get_rect(center=draw_rect.center)
        surface.blit(shadow, label_rect.move(3, 3))
        surface.blit(label, label_rect)

        hint = self.small_font.render("ENTER THE RACE", False, (255, 245, 210))
        hint_shadow = self.small_font.render("ENTER THE RACE", False, (70, 40, 20))
        hint_rect = hint.get_rect(center=(draw_rect.centerx, draw_rect.bottom + 22))

        surface.blit(hint_shadow, hint_rect.move(2, 2))
        surface.blit(hint, hint_rect)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Kar Kart")

        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(Colors.BLACK)

        self._draw_start_button(surface)

        self.help_icon.draw(surface)
        self.settings_icon.draw(surface)

    @staticmethod
    def _try_load_image(path, *, convert_alpha: bool) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(path))
        except (FileNotFoundError, pygame.error):
            return None

        return image.convert_alpha() if convert_alpha else image.convert()

    def get_label(self):
        return self.label