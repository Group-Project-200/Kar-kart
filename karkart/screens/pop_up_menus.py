"""pause_menu.py - when game is paused, it appears"""

from __future__ import annotations
from abc import ABC, abstractmethod

import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.ui.container import PopUpContainer
from karkart.ui.card import PopUpCard, TitleCard
from karkart.screens.gameplay import GamePlay

class PopUpMenu(ABC):
    """Abstract class for all pop-up menus""" 

    @abstractmethod
    def __init__(self, manager) -> None:
        self.manager = manager

        self.width: int = 300
        self.height: int = 450

        self.x: ScreenPosition = sp.CENTER_X
        self.y: ScreenPosition = sp.CCCBOTTOM

        self.container = None
        self.title = None

        # Creates outer rectangle.
        self.pause_rect = pygame.Rect(self.x - self.width / 2, self.y - self.height / 2, self.width, self.height)

        # Activated when pressing ESC to draw a black layer next time pop-up is open.
        self.activate_black_layer: bool = False

        self.black_layer: bool = True
        self.screen: str | None = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            # Press ESC -> brings back to original screen.
            if event.key == pygame.K_ESCAPE:
                self.activate_black_layer = True
                self.manager.change_screen(self.screen)

    def update(self):
        pass

    def draw(self, surface : pygame.Surface):

        # First time calling draw() -> create a semi-transparent black layer.
        if self.black_layer:
            black_layer = pygame.Surface((sp.WIDTH, sp.HEIGHT))
            black_layer.fill(Colors.BLACK)
            black_layer.set_alpha(128)
            surface.blit(black_layer, (0, 0))

            self.black_layer = False

        # Draw title, container and outer rectangle.
        pygame.draw.rect(surface, Colors.LIGHT_BLUE, self.pause_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, self.pause_rect, 2, border_radius=8)
        self.container.draw(surface)
        self.title.draw(surface)

        if self.activate_black_layer:
            self.black_layer = True
            self.activate_black_layer = False


class PauseMenu(PopUpMenu):
    """
    List of options to select in the pause menu.
    They call different screens.
    """

    # TODO: add all the features

    def __init__(self, manager) -> None:
        super().__init__(manager)

        options : list[PopUpCard] = [PopUpCard("Settings"), PopUpCard("Restart", screen="car"), PopUpCard("Quit")]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(options), 1)

        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        # Creates title.
        self.title = TitleCard(self.container.get_width(), "Pause Menu")

        # Clicking ESC brings back to game.
        self.screen: str = "game"
        

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)
            
            # Container returns a screen -> update the screen.
            screen = self.container.handle_event(event)
            if screen:
                if screen == "car":
                    self.manager.add_screen("game", GamePlay(self.manager))
                self.manager.change_screen(screen)


class SettingsMenu(PopUpMenu):
    def __init__(self, manager) -> None:
        super().__init__(manager)

        options : list[PopUpCard] = [PopUpCard("Keys"), PopUpCard("Other Keys"), PopUpCard("Audio")]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, 3, 1)

        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        # Creates title.
        self.title = TitleCard(self.container.get_width(), "Settings")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)
            
            # Container returns a screen -> update the screen.
            screen = self.container.handle_event(event)
            if screen:
                if screen == "car":
                    self.manager.add_screen("game", GamePlay(self.manager))
                self.manager.change_screen(screen)

    def set_return_screen(self, screen):

        # Clicking ESC brings back to that screen.
        self.screen = screen
        self.black_layer = True