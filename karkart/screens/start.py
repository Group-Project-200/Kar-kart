from __future__ import annotations

import math

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR
from karkart.ui.help_icon import HelpIcon
from karkart.ui.settings_icon import SettingsIcon


class StartScreen:

    def __init__(self, manager, label) -> None:
        self.manager = manager
        self.label = label

        self.bg = self._try_load_image(PICTURES_DIR / "bp2.png", convert_alpha=False)

        self.settings_icon = SettingsIcon(self.manager, "start")
        self.help_icon = HelpIcon(self.manager, "start")

        self.start_frames = self._load_start_frames()
        self.current_frame = 0
        self.frame_delay = 140
        self.last_frame_time = pygame.time.get_ticks()

        self.base_y = sp.HEIGHT - 100
        self.float_amplitude = 5

    def _scale_prompt(self, image: pygame.Surface) -> pygame.Surface:
        max_width = 560
        max_height = 90

        width, height = image.get_size()
        scale = min(max_width / width, max_height / height)

        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))

        return pygame.transform.smoothscale(image, (new_width, new_height))

    def _load_start_frames(self) -> list[pygame.Surface]:
        frames = []

        for i in range(1, 5):
            image = self._try_load_image(
                PICTURES_DIR / f"start_{i}.png",
                convert_alpha=True,
            )

            if image is not None:
                image = self._scale_prompt(image)
                frames.append(image)

        return frames

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return None

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)

        if event.key == pygame.K_RETURN:
            self.manager.change_screen("race_selector")

    def update(self) -> None:
        now = pygame.time.get_ticks()

        if self.start_frames and now - self.last_frame_time >= self.frame_delay:
            self.last_frame_time = now
            self.current_frame = (self.current_frame + 1) % len(self.start_frames)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Kar Kart")

        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(Colors.BLACK)

        self._draw_start_prompt(surface)

        self.help_icon.draw(surface)
        self.settings_icon.draw(surface)

    def _draw_start_prompt(self, surface: pygame.Surface) -> None:
        center_x = surface.get_width() // 2

        ticks = pygame.time.get_ticks()
        float_offset = math.sin(ticks * 0.004) * self.float_amplitude
        y = self.base_y + float_offset

        if self.start_frames:
            frame = self.start_frames[self.current_frame]
            rect = frame.get_rect(center=(center_x, y))

            glow_strength = 55 + int((math.sin(ticks * 0.006) + 1) * 25)

            glow = pygame.Surface((rect.width + 38, rect.height + 22), pygame.SRCALPHA)
            pygame.draw.rect(
                glow,
                (80, 170, 255, glow_strength),
                glow.get_rect(),
                border_radius=16,
            )
            glow_rect = glow.get_rect(center=rect.center)
            surface.blit(glow, glow_rect)

            shadow = pygame.Surface((rect.width + 12, rect.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow,
                (0, 0, 0, 75),
                shadow.get_rect(),
                border_radius=14,
            )
            shadow_rect = shadow.get_rect(center=(rect.centerx + 3, rect.centery + 4))
            surface.blit(shadow, shadow_rect)

            surface.blit(frame, rect)

    @staticmethod
    def _try_load_image(path, *, convert_alpha: bool) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(path))
        except (FileNotFoundError, pygame.error):
            return None

        return image.convert_alpha() if convert_alpha else image.convert()

    def get_label(self):
        return self.label