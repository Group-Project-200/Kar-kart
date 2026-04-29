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

    def write(self) -> None:
        """Blit the current countdown digit to the screen (caller flips display)."""
        text_surface = self.font.render(str(self.seconds), True, (255, 255, 255))
        text_rect = text_surface.get_rect(
            center=(self.screen_dimensions[0] // 2, self.screen_dimensions[1] // 2),
        )
        self.screen.blit(text_surface, text_rect)
