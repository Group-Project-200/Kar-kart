from __future__ import annotations
from abc import ABC, abstractmethod

import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.ui import Arrow, ArrowContainer, PopUpContainer, PopUpCard, TitleCard
from karkart.screens.gameplay import GamePlay


class PopUpMenu(ABC):

    @abstractmethod
    def __init__(self, manager) -> None:
        self.manager = manager

        self.width: int = 300
        self.height: int = 450

        self.x: ScreenPosition = sp.CENTER_X
        self.y: ScreenPosition = sp.CCCBOTTOM

        self.container = None
        self.title = None

        self.pause_rect = pygame.Rect(
            self.x - self.width / 2, self.y - self.height / 2, self.width, self.height
        )

        self.activate_black_layer: bool = False

        self.black_layer: bool = True
        self.screen: str | None = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.activate_black_layer = True
                self.manager.change_screen(self.screen)

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):

        if self.black_layer:
            black_layer = pygame.Surface((sp.WIDTH, sp.HEIGHT))
            black_layer.fill(Colors.BLACK)
            black_layer.set_alpha(128)
            surface.blit(black_layer, (0, 0))

            self.black_layer = False

        pygame.draw.rect(surface, Colors.LIGHT_BLUE, self.pause_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, self.pause_rect, 2, border_radius=8)
        self.container.draw(surface)
        self.title.draw(surface)

        if self.activate_black_layer:
            self.black_layer = True
            self.activate_black_layer = False


class PauseMenu(PopUpMenu):

    def __init__(self, manager) -> None:
        super().__init__(manager)

        options: list[PopUpCard] = [
            PopUpCard("Settings"),
            PopUpCard("Restart", state="car"),
            PopUpCard("Quit"),
        ]
        self.container = PopUpContainer(
            self.x, self.y, self.width, self.height, len(options), 1
        )

        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard(self.container.get_width(), "Pause Menu")

        self.screen: str = "game"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)

            screen = self.container.handle_event(event)
            if screen:
                if screen == "car":
                    self.manager.add_screen("game", GamePlay(self.manager))
                self.manager.change_screen(screen)


class SettingsMenu(PopUpMenu):
    def __init__(self, manager) -> None:
        super().__init__(manager)

        key_options: list[Any] = [
            PopUpCard("WASD", width=150),
            PopUpCard("Arrows", width=150),
        ]
        self.keys = ArrowContainer(0, 0, 250, 150, key_options)

        options = [self.keys, PopUpCard("Save", width=250)]
        self.container = PopUpContainer(
            self.x, self.y, self.width, self.height, len(options), 1
        )
        for x in options:
            self.container.add_object(x)

        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard(self.container.get_width(), "Settings")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)

            screen = self.container.handle_event(event)
            if screen:
                if screen == "car":
                    self.manager.add_screen("game", GamePlay(self.manager))
                self.manager.change_screen(screen)

    def set_return_screen(self, screen):

        self.screen = screen
        self.black_layer = True
