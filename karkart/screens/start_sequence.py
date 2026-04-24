"""Pre-race countdown overlay."""

from __future__ import annotations

import pygame


class StartSequence:
    """Renders a giant countdown digit and tracks completion state."""

    def __init__(self, screen: pygame.Surface, start_seconds: int = 5) -> None:
        self.seconds = start_seconds
        self.screen = screen
        self.screen_dimensions = screen.get_size()
        self.font = pygame.font.Font(None, 400)
        self.complete: bool = False
        self.last_tick: int = pygame.time.get_ticks()

    def update(self) -> None:
        """Advance the countdown by one second if 1000 ms have elapsed."""
        now = pygame.time.get_ticks()
        if now - self.last_tick >= 1000:
            self.last_tick = now
            self.seconds -= 1
            if self.seconds <= 0:
                self.seconds = 0
                self.complete = True

    def resume(self) -> None:
        """Reset the tick baseline after a pause so the countdown doesn't
        jump by however many seconds the pause menu was open."""
        self.last_tick = pygame.time.get_ticks()

    def write(self) -> None:
        """Blit the current countdown digit to the screen (caller flips display)."""
        text_surface = self.font.render(str(self.seconds), True, (255, 255, 255))
        text_rect = text_surface.get_rect(
            center=(self.screen_dimensions[0] // 2, self.screen_dimensions[1] // 2),
        )
        self.screen.blit(text_surface, text_rect)
