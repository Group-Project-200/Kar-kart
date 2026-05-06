from __future__ import annotations

import math

import pygame

from karkart.paths import PIXEL_FONT


class StartSequence:

    def __init__(self, screen: pygame.Surface, start_seconds: int = 5) -> None:
        self.seconds = start_seconds
        self.screen = screen
        self.screen_dimensions = screen.get_size()

        self.complete: bool = False
        self.last_tick: int = pygame.time.get_ticks()
        self.start_seconds = start_seconds

        self.font = self._load_font(170)
        self.small_font = self._load_font(34)

        self.go_time: int | None = None
        self.show_go_for_ms = 700

    def _load_font(self, size: int) -> pygame.font.Font:
        try:
            return pygame.font.Font(str(PIXEL_FONT), size)
        except (FileNotFoundError, OSError, pygame.error):
            return pygame.font.SysFont("arial", size, bold=True)

    def update(self) -> None:
        now = pygame.time.get_ticks()

        if self.go_time is not None:
            if now - self.go_time >= self.show_go_for_ms:
                self.complete = True
            return

        if now - self.last_tick >= 1000:
            self.last_tick = now
            self.seconds -= 1

            if self.seconds <= 0:
                self.seconds = 0
                self.go_time = now

    def resume(self) -> None:
        self.last_tick = pygame.time.get_ticks()

    def _current_text(self) -> str:
        if self.go_time is not None:
            return "GO!"

        return str(self.seconds)

    def _current_color(self) -> tuple[int, int, int]:
        if self.go_time is not None:
            return (90, 255, 90)

        if self.seconds >= 3:
            return (255, 70, 70)

        if self.seconds == 2:
            return (255, 170, 60)

        return (255, 235, 80)

    def _scale_for_animation(self) -> float:
        now = pygame.time.get_ticks()

        if self.go_time is not None:
            elapsed = now - self.go_time
        else:
            elapsed = now - self.last_tick

        progress = min(1.0, elapsed / 1000)

        # starts big, settles quickly
        bounce = 1.0 + 0.35 * math.exp(-progress * 5.0)
        return bounce

    def _draw_overlay(self) -> None:
        overlay = pygame.Surface(self.screen_dimensions, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 95))
        self.screen.blit(overlay, (0, 0))

    def _draw_count_text(self) -> None:
        text = self._current_text()
        color = self._current_color()

        main_text = self.font.render(text, False, color)
        shadow_text = self.font.render(text, False, (45, 25, 15))
        outline_text = self.font.render(text, False, (255, 255, 255))

        scale = self._scale_for_animation()

        width = int(main_text.get_width() * scale)
        height = int(main_text.get_height() * scale)

        main_text = pygame.transform.scale(main_text, (width, height))
        shadow_text = pygame.transform.scale(shadow_text, (width, height))
        outline_text = pygame.transform.scale(outline_text, (width, height))

        center = (
            self.screen_dimensions[0] // 2,
            self.screen_dimensions[1] // 2 - 30,
        )

        text_rect = main_text.get_rect(center=center)

        # fake outline
        for ox, oy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
            self.screen.blit(outline_text, text_rect.move(ox, oy))

        self.screen.blit(shadow_text, text_rect.move(7, 7))
        self.screen.blit(main_text, text_rect)

    def _draw_sub_text(self) -> None:
        if self.go_time is not None:
            text = "START!"
        else:
            text = "GET READY"

        label = self.small_font.render(text, False, (255, 245, 210))
        shadow = self.small_font.render(text, False, (60, 35, 20))

        label_rect = label.get_rect(
            center=(
                self.screen_dimensions[0] // 2,
                self.screen_dimensions[1] // 2 + 140,
            )
        )

        self.screen.blit(shadow, label_rect.move(3, 3))
        self.screen.blit(label, label_rect)

    def write(self) -> None:
        if self.complete:
            return

        self._draw_overlay()
        self._draw_count_text()
        self._draw_sub_text()