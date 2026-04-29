"""pause_menu.py - when game is paused, it appears"""

from __future__ import annotations
from abc import ABC, abstractmethod
import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.ui import Arrow, ArrowContainer, PopUpContainer, PopUpCard, TitleCard
from karkart.ui.ui_object import UIObject
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

        options : list[PopUpCard] = [PopUpCard("Settings"), PopUpCard("Restart", state="car"), PopUpCard("Quit")]
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

        # Container that stores left and right arrows and all the selectable options.
        key_options : list[Any] = [PopUpCard("WASD", width=150), PopUpCard("Arrows", width=150)]
        self.keys = ArrowContainer(0, 0, 250, 150, key_options)

        # Container for all the settings.
        options = [self.keys, PopUpCard("Save", width=250)]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(options), 1)
        for x in options:
            self.container.add_object(x)

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


class HelpMenu(PopUpMenu):
    """Controls help menu, opens with H key."""

    def __init__(self, manager) -> None:
        super().__init__(manager)

        self.width = 1000
        self.height = 600
        self.pause_rect = pygame.Rect(self.x - self.width / 2, self.y - self.height / 2, self.width, self.height)

        # Keep PopUpContainer while rendering all help text in one inner box.
        options = [HelpTextCard(920, 490)]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(options), 1)
        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard(self.container.get_width(), "Help Menu")

        # Returned screen is set by HelpIcon right before opening.
        self.screen = "start"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)
            self.container.handle_event(event)
            if event.key == pygame.K_h:
                self.activate_black_layer = True
                self.manager.change_screen(self.screen)

    def set_return_screen(self, screen: str) -> None:
        self.screen = screen
        self.black_layer = True


class HelpTextCard(UIObject):
    """Single card that draws help text block."""

    def __init__(self, width: int, height: int) -> None:
        super().__init__(0, 0, width, height)
        self.color = Colors.DARK_BLUE
        self.bord_color = Colors.BLACK
        self.border = 2
        self.font = pygame.font.Font(None, 30)
        self.lines = [
            "Navigation Buttons:",
            "WASD/Arrow Keys: Selection",
            "RETURN: Confirm selection/Next screen",
            "ESC: Settings Menu",
            "H: Help Menu",
            "",
            "Game Play Buttons:",
            "W/S: Accelerate / Brake & Reverse  ",
            "A/D: Steer Left / Right ",
            "SPACE: Hold to Drift, Release for Boost  ",
            "ESC: Pause Menu",
            "",
            "Press H or ESC to close Help Menu",
        ]

    def select(self) -> None:
        self.color = Colors.DARK_BLUE

    def unselect(self) -> None:
        self.color = Colors.DARK_BLUE

    def get_state(self):
        return None

    def handle_event(self, event) -> None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect, border_radius=8)
        pygame.draw.rect(surface, self.bord_color, rect, self.border, border_radius=8)

        line_y = self.y + 20
        line_x = self.x + 24
        for line in self.lines:
            line_surface = self.font.render(line, True, Colors.WHITE)
            surface.blit(line_surface, (line_x, line_y))
            line_y += 32