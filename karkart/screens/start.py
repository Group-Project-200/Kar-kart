"""The title/start screen shown at launch."""

from __future__ import annotations

import pygame

from karkart.constants import ScreenPositions as sp
from karkart.paths import PICTURES_DIR


class StartScreen:
    """Press SPACE to continue, or close the window to quit."""

    def __init__(self, manager) -> None:
        self.manager = manager
        self.font = pygame.font.Font(None, 36)

        # FPS counter state.
        self.fps: float = 60.0
        self.frame_count: int = 0
        self.last_time: int = pygame.time.get_ticks()

        self.bg = self._try_load_image(PICTURES_DIR / "bp2.png", convert_alpha=False)

        gear = self._try_load_image(PICTURES_DIR / "gearicon3.png", convert_alpha=True)
        if gear is not None:
            gear = pygame.transform.scale(gear, (64, 64))
        self.gear_icon = gear

    @staticmethod
    def _try_load_image(path, *, convert_alpha: bool) -> pygame.Surface | None:
        """Best-effort image load: return ``None`` on any file/pygame error."""
        try:
            image = pygame.image.load(str(path))
        except (FileNotFoundError, pygame.error):
            return None
        return image.convert_alpha() if convert_alpha else image.convert()

    def handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            self.manager.toggle_running()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.manager.change_screen("race_selector")

    def update(self) -> None:
        # Manual FPS counter - updates once per second.
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

        if self.gear_icon is not None:
            gear_pos = (sp.WIDTH - 64 - 10, 10)
            surface.blit(self.gear_icon, gear_pos)

        pygame.display.set_caption(f"Kar Kart - Start Screen (FPS: {self.fps})")
