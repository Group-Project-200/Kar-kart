from __future__ import annotations
from abc import ABC, abstractmethod
import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.screens.gameplay import GamePlay
from karkart.settings import settings
from karkart.ui import Arrow, ArrowContainer, Button, PopUpButton, PopUpContainer, PopUpCard, TitleCard
from karkart.ui.ui_object import UISelectObject


class PopUpMenu(ABC):

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
                self.manager.pop_screen()

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

    def get_label(self):
        return self.label

    def deactivate_black_layer(self):
        self.black_layer = False


class PauseMenu(PopUpMenu):

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        options : list[PopUpCard] = [PopUpButton("Settings", self.manager, action="settings"), PopUpButton("Restart", self.manager, action="race_selector"), PopUpButton("Quit", self.manager)]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(options), 1)

        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        # Creates title.
        self.title = TitleCard("Pause Menu", self.container.get_width())

        self.screen: str = "game"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)

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
            if event.key == pygame.K_ESCAPE:
                bindings_label = self.container.get_objects()[0].get_text()
                settings.set_bindings(bindings_label)

                sound = self.container.get_objects()[1].get_text()
                settings.set_sound(sound)

                settings.save()
            
            super().handle_event(event)
            # Container returns a screen -> update the screen.
            screen = self.container.handle_event(event)
            if screen:
                self.manager.change_screen(screen)

    def set_return_screen(self, screen):

        self.screen = screen
        self.black_layer = True


class HelpMenu(PopUpMenu):
    """Controls help menu, opens with H key."""

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        self.width = 1000
        self.height = 600
        self.pause_rect = pygame.Rect(self.x - self.width / 2, self.y - self.height / 2, self.width, self.height)

        # Keep PopUpContainer while rendering all help text in one inner box.
        options = [HelpTextCard(920, 490)]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(options), 1)
        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard("Help Menu", self.container.get_width())

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


class HelpTextCard(UISelectObject):
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

    def get_action(self):
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
