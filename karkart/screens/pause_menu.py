"""pause_menu.py - when game is paused, it appears"""

from __future__ import annotations

import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.ui.container import PauseContainer
from karkart.ui.card import PauseCard, TitleCard

class PauseMenu:
    """
    List of options to select.
    They return to different screens.
    """

    def __init__(self, manager) -> None:
        self.manager = manager

        self.width : int = 300
        self.height : int = 450

        self.x : ScreenPosition = sp.CENTER_X
        self.y : ScreenPosition = sp.CCCBOTTOM

        # Resume  -> return to the live game.
        # Restart -> back to the map picker so a fresh race is built.
        # Menu    -> back to the title screen.
        options: list[PauseCard] = [
            PauseCard("Resume", screen="game"),
            PauseCard("Restart", screen="map"),
            PauseCard("Menu", screen="start"),
        ]
        self.container = PauseContainer(self.x, self.y, self.width, self.height, len(options), 1)

        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        # Creates title and outer rectangle.
        self.title = TitleCard(self.container.get_width(), "Pause Menu")
        self.pause_rect = pygame.Rect(self.x - self.width / 2, self.y - self.height / 2, self.width, self.height)

        self.backdrop: pygame.Surface | None = None

    def _reset_selection(self) -> None:
        """Snap the cursor back to the first card and fix visual highlights.

        The container advances its ``selected`` index on click/hover, so after
        we navigate away the wrong card is still visually highlighted. Syncing
        both the logical index and every card's select state here keeps the
        menu consistent the next time it opens.
        """
        for i, card in enumerate(self.container.objects):
            if i == 0:
                card.select()
            else:
                card.unselect()
        self.container.selected = 0

    def handle_event(self, event):
        # ESC always resumes the paused race.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._reset_selection()
            self.manager.change_screen("game")
            return

        # Container resolves keyboard navigation, mouse clicks and hover.
        screen = self.container.handle_event(event)
        if not screen:
            return

        self._reset_selection()
        # Every real navigation leaves the game; the next "game" screen will
        # be freshly constructed by the map picker so stale race state doesn't
        # leak between runs. Nothing extra to do here.
        self.manager.change_screen(screen)

    def update(self):
        pass

    def draw(self, surface: pygame.Surface) -> None:
        if self.backdrop is not None:
            surface.blit(self.backdrop, (0, 0))

        black_layer = pygame.Surface((sp.WIDTH, sp.HEIGHT))
        black_layer.fill(Colors.BLACK)
        black_layer.set_alpha(128)
        surface.blit(black_layer, (0, 0))

        pygame.draw.rect(surface, Colors.LIGHT_BLUE, self.pause_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, self.pause_rect, 2, border_radius=8)
        self.container.draw(surface)
        self.title.draw(surface)