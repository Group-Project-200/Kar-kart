from __future__ import annotations

import math
import pygame

from karkart.constants import Colors
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

        self.base_y = 590
        self.float_amplitude = 6

    def _load_start_frames(self) -> list[pygame.Surface]:
        frames = []

        for i in range(1, 5):
            image = self._try_load_image(
                PICTURES_DIR / f"start_{i}.png",
                convert_alpha=True,
            )
            if image is not None:
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

            glow_strength = 70 + int((math.sin(ticks * 0.006) + 1) * 35)

            glow = pygame.Surface((rect.width + 50, rect.height + 30), pygame.SRCALPHA)
            pygame.draw.rect(
                glow,
                (80, 170, 255, glow_strength),
                glow.get_rect(),
                border_radius=18,
            )
            glow_rect = glow.get_rect(center=rect.center)
            surface.blit(glow, glow_rect)

            shadow = pygame.Surface((rect.width + 16, rect.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow,
                (0, 0, 0, 90),
                shadow.get_rect(),
                border_radius=16,
            )
            shadow_rect = shadow.get_rect(center=(rect.centerx + 3, rect.centery + 5))
            surface.blit(shadow, shadow_rect)

            surface.blit(frame, rect)
        else:
            font = pygame.font.Font(None, 72)
            text = font.render("PRESS ENTER TO START", True, (255, 255, 255))
            text_rect = text.get_rect(center=(center_x, y))

            shadow = font.render("PRESS ENTER TO START", True, (40, 80, 140))
            shadow_rect = shadow.get_rect(center=(center_x + 3, y + 3))

            surface.blit(shadow, shadow_rect)
            surface.blit(text, text_rect)

    @staticmethod
    def _try_load_image(path, *, convert_alpha: bool) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(path))
        except (FileNotFoundError, pygame.error):
            return None

        return image.convert_alpha() if convert_alpha else image.convert()

    def get_label(self):
        return self.label