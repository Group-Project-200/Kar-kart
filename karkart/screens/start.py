from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.ui.help_icon import HelpIcon
from karkart.paths import PICTURES_DIR, PIXEL_FONT
from karkart.ui.settings_icon import SettingsIcon


class StartScreen:

    def __init__(self, manager, label) -> None:
        self.manager = manager
        self.label = label

        self.font = pygame.font.Font(None, 36)

        self.fps: float = 60.0
        self.frame_count: int = 0
        self.last_time: int = pygame.time.get_ticks()

        self.bg = self._try_load_image(PICTURES_DIR / "bp2.png", convert_alpha=False)

        self.settings_icon = SettingsIcon(self.manager, "start")
        self.help_icon = HelpIcon(self.manager, "start")

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return None

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)
        if event.key == pygame.K_SPACE:
            self.manager.change_screen("race_selector")

    def update(self) -> None:

        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.last_time
        if elapsed >= 1000:
            self.fps = round(self.frame_count * 1000 / elapsed, 1)
            self.frame_count = 0
            self.last_time = current_time

    def draw(self, surface: pygame.Surface) -> None:
        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((50, 100, 200))

        self.help_icon.draw(surface)
        self.settings_icon.draw(surface)
        pygame.display.set_caption(f"Kar Kart - Start Screen (FPS: {self.fps})")

        ### Help button instruction   
        font_size = 15
        instr_font = pygame.font.Font(str(PIXEL_FONT), font_size)     
        instr_text = instr_font.render("Press H for Help(?)", True, Colors.WHITE)
        instr_center = instr_text.get_rect(center=(sp.CENTER_X, sp.XXXBOTTOM))

        instr_height = instr_text.get_height() + font_size * 1.5

        surface.blit(instr_text, instr_center)

    @staticmethod
    def _try_load_image(path, *, convert_alpha: bool) -> pygame.Surface | None:

        try:
            image = pygame.image.load(str(path))
        except (FileNotFoundError, pygame.error):
            return None
        return image.convert_alpha() if convert_alpha else image.convert()

    def get_label(self):
        return self.label