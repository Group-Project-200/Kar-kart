"""pause_menu.py - when game is paused, it appears"""

from __future__ import annotations
from abc import ABC, abstractmethod

import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.screens.gameplay import GamePlay
from karkart.settings import settings
from karkart.ui import Arrow, ArrowContainer, Button, PopUpButton, PopUpContainer, PopUpCard, TitleCard

class PopUpMenu(ABC):
    """Abstract class for all pop-up menus""" 

    @abstractmethod
    def __init__(self, manager, label) -> None:
        self.manager = manager
        self.label = label

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
                self.manager.pop_screen()

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

    def get_label(self):
        return self.label

    def deactivate_black_layer(self):
        self.black_layer = False


class PauseMenu(PopUpMenu):
    """
    List of options to select in the pause menu.
    They call different screens.
    """

    # TODO: add all the features

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        options : list[PopUpCard] = [PopUpButton("Settings", self.manager, state="settings"), PopUpButton("Restart", self.manager, state="race_selector"), PopUpButton("Quit", self.manager)]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(options), 1)

        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        # Creates title.
        self.title = TitleCard("Pause Menu", self.container.get_width())

        # Clicking ESC brings back to game.
        self.screen: str = "game"
        

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)
            
            # Container returns a screen -> update the screen.
            screen = self.container.handle_event(event)
            if screen:
                if screen == "race_selector":
                    self.manager.pop_screen()
                    self.manager.add_screen(GamePlay(self.manager, "game"))
                elif screen == "settings":
                    self.manager.push_screen(self.label)
                    self.manager.get_screen().deactivate_black_layer()
                self.manager.change_screen(screen)


class SettingsMenu(PopUpMenu):
    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        self.width: int = 300
        self.height: int = 450
        self.pause_rect = pygame.Rect(self.x - self.width / 2, self.y - self.height / 2, self.width, self.height)



        # Container that stores left and right arrows and all the selectable options.
        title_cards = []
        main_options = []
        for obj, opt_list in settings.get_objects().items():
            title_cards.append(TitleCard(obj, 150))
            side_options = [TitleCard(x, 150) for x in opt_list]
            new_container = ArrowContainer(0, 0, 250, 150, side_options)
            main_options.append(new_container)

        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(main_options), 1)
        for x in main_options:
            self.container.add_object(x)

        self.container.calculate_padding(x_center=True, y_center=True)

        # Creates title.
        self.title = TitleCard("Settings", self.container.get_width())

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)

            # if self.save_button.is_selected():
            #     if event.key == pygame.K_RETURN:
            #         screen = self.manager.pop_screen()
            #         if screen == "pause":
            #             self.manager.get_screen().deactivate_black_layer()
            
            # Container returns a screen -> update the screen.
            self.container.handle_event(event)
            # if screen:
            #     self.manager.change_screen(screen)

    def set_return_screen(self, screen):

        # Clicking ESC brings back to that screen.
        self.screen = screen
        self.black_layer = True