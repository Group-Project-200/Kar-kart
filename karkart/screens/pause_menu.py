"""pause_menu.py - when game is paused, it appears"""

from __future__ import annotations

import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.ui.container import PauseContainer
from karkart.ui.card import PauseCard, TitleCard
from karkart.screens.gameplay import GamePlay

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

        options : list[PauseCard] = [PauseCard("Settings"), PauseCard("Restart", screen="car"), PauseCard("Quit")]
        self.container = PauseContainer(self.x, self.y, self.width, self.height, len(options), 1)

        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        # Creates title and outer rectangle.
        self.title = TitleCard(self.container.get_width(), "Pause Menu")
        self.pause_rect = pygame.Rect(self.x - self.width / 2, self.y - self.height / 2, self.width, self.height)

        self.add_black_layer : bool = True
        

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            # Press ESC -> brings back to game.
            if event.key == pygame.K_ESCAPE:
                self.manager.change_screen("game")
            
            # Container returns a screen -> update the screen.
            screen = self.container.handle_event(event)
            if screen:
                if screen == "car":
                    self.manager.add_screen("game", GamePlay(self.manager))
                self.manager.change_screen(screen)

    def update(self):
        pass

    def draw(self, surface : pygame.Surface):

        # First time calling draw() -> create a semi-transparent black layer.
        if self.add_black_layer:
            black_layer = pygame.Surface((sp.WIDTH, sp.HEIGHT))
            black_layer.fill(Colors.BLACK)
            black_layer.set_alpha(128)
            surface.blit(black_layer, (0, 0))

            self.add_black_layer = False


        pygame.draw.rect(surface, Colors.LIGHT_BLUE, self.pause_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, self.pause_rect, 2, border_radius=8)
        self.container.draw(surface)
        self.title.draw(surface)