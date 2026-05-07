from __future__ import annotations
from abc import ABC, abstractmethod

import pygame

from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.paths import PIXEL_FONT
from karkart.screens.gameplay import GamePlay
from karkart.settings import settings
from karkart.ui import ArrowContainer, PopUpButton, PopUpContainer, TitleCard
from karkart.ui.ui_object import UISelectObject


class PopUpMenu(ABC):

    is_popup: bool = True

    @abstractmethod
    def __init__(self, manager, label) -> None:
        self.manager = manager
        self.label = label

        self.width: int = 300
        self.height: int = 450

        self.x: float = sp.CENTER_X
        self.y: float = sp.CCCBOTTOM

        self.container = None
        self.title = None

        self.pause_rect = pygame.Rect(
            self.x - self.width / 2, self.y - self.height / 2, self.width, self.height
        )

        self.black_layer: bool = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop_screen()

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):
        if self.black_layer:
            underlying = self._find_underlying()
            if underlying is not None:
                underlying.draw(surface)
            dim = pygame.Surface((sp.WIDTH, sp.HEIGHT))
            dim.fill(Colors.BLACK)
            dim.set_alpha(128)
            surface.blit(dim, (0, 0))
            self.black_layer = False

        pygame.draw.rect(surface, Colors.LIGHT_BLUE, self.pause_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, self.pause_rect, 2, border_radius=8)
        self.title.draw(surface)
        self.container.draw(surface)

    def _find_underlying(self):
        for label in self.manager.stack:
            screen = self.manager.screens.get(label)
            if screen is not None and not getattr(screen, "is_popup", False):
                return screen
        return None

    def get_label(self):
        return self.label

    def on_activate(self):
        self.black_layer = True


def _stop_game(manager) -> None:
    old = manager.screens.get("game")
    if old and hasattr(old, "on_destroy"):
        old.on_destroy()


def _quit_to_race_selector(manager) -> None:
    _stop_game(manager)
    manager.stack.clear()
    manager.change_screen("race_selector")


class PauseMenu(PopUpMenu):

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        options = [
            PopUpButton("Resume",    self.manager, action="resume"),
            PopUpButton("Restart",   self.manager, action="restart"),
            PopUpButton("Quit Race", self.manager, action="quit_confirm"),
        ]
        self.container = PopUpContainer(
            self.x, self.y, self.width, self.height, len(options), 1
        )
        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard("Pause Menu", self.container.get_width())

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.manager.push_screen(self.label)
            self.manager.change_screen("settings")
            return

        screen = self.container.handle_event(event)
        if not screen:
            return

        if screen == "resume":
            self.manager.pop_screen()

        elif screen == "restart":
            _stop_game(self.manager)
            self.manager.add_screen(GamePlay(self.manager, "game"))
            self.manager.pop_screen()

        elif screen == "quit_confirm":
            target = (
                "championship_quit_confirm"
                if self.manager.app_data.current_mode == "Championship"
                else "quit_confirm"
            )
            self.manager.push_screen(self.label)
            self.manager.change_screen(target)


class SettingsMenu(PopUpMenu):

    _CONTAINER_HEIGHT = 320

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        self.y -= 30
        self.width: int = 340
        self.height: int = 380
        self.pause_rect = pygame.Rect(
            self.x - self.width / 2, self.y - self.height / 2, self.width, self.height
        )

        main_options = []
        for obj, opt_list in settings.get_objects().items():
            title_card = TitleCard(obj, 150, font_size=10)
            side_options = [TitleCard(x, 150) for x in opt_list]
            main_options.append(ArrowContainer(0, 0, 250, 80, side_options, title_card))
        main_options.append(
            PopUpButton("Quit", self.manager, action="quit_confirm", width=250, height=50)
        )

        container_y = self.y - (self.height - self._CONTAINER_HEIGHT) / 2
        self.container = PopUpContainer(
            self.x, container_y, self.width, self._CONTAINER_HEIGHT, len(main_options), 1
        )
        for opt in main_options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard("Settings", self.container.get_width())

        hint_font = pygame.font.Font(str(PIXEL_FONT), 12)
        self._esc_hint_text = hint_font.render("ESC to save", True, Colors.WHITE)
        hint_w, hint_h = 200, 36
        hint_x = sp.CENTER_X - hint_w / 2
        hint_y = self.pause_rect.bottom - hint_h - 12
        self._esc_hint_rect = pygame.Rect(hint_x, hint_y, hint_w, hint_h)
        self._esc_hint_text_pos = self._esc_hint_text.get_rect(
            center=self._esc_hint_rect.center
        )

    def _save_settings(self) -> None:
        objs = self.container.get_objects()
        settings.set_bindings(objs[0].get_text())
        settings.set_sound(objs[1].get_text())
        settings.set_music(objs[2].get_text())
        settings.save()

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        pygame.draw.rect(surface, Colors.DARK_BLUE, self._esc_hint_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.LIGHT_BLUE, self._esc_hint_rect, 4, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, self._esc_hint_rect, 2, border_radius=8)
        surface.blit(self._esc_hint_text, self._esc_hint_text_pos)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self._save_settings()
            self.manager.pop_screen()
            return

        screen = self.container.handle_event(event)
        if screen == "quit_confirm":
            self._save_settings()
            target = (
                "championship_quit_confirm"
                if self.manager.app_data.current_mode == "Championship"
                else "quit_confirm"
            )
            self.manager.push_screen(self.label)
            self.manager.change_screen(target)
        elif screen:
            self.manager.change_screen(screen)


class HelpMenu(PopUpMenu):
    """Controls help menu, opens with H key."""

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        self.width = 1000
        self.height = 600
        self.pause_rect = pygame.Rect(
            self.x - self.width / 2, self.y - self.height / 2, self.width, self.height
        )

        options = [HelpTextCard(920, 490)]
        self.container = PopUpContainer(
            self.x, self.y, self.width, self.height, len(options), 1
        )
        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard("Help Menu", self.container.get_width())

        self.return_screen: str = "start"

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_h, pygame.K_ESCAPE):
            self.manager.pop_screen()

    def set_return_screen(self, screen: str) -> None:
        self.return_screen = screen


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
            "ESC: Open Settings Menu/Save and close",
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


class _BaseQuitConfirmMenu(PopUpMenu):
    """Two-button (No / Yes) confirmation dialog. Subclasses override _on_yes."""

    TITLE: str = ""

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        self.width = 480
        self.height = 130
        self.pause_rect = pygame.Rect(
            self.x - self.width / 2,
            self.y - self.height / 2,
            self.width,
            self.height,
        )

        options = [
            PopUpButton("No",  manager, action="no"),
            PopUpButton("Yes", manager, action="yes"),
        ]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, 1, 2)
        for opt in options:
            self.container.add_object(opt)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard(self.TITLE, self.container.get_width())

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        super().handle_event(event)
        screen = self.container.handle_event(event)
        if screen == "yes":
            self._on_yes()
        elif screen == "no":
            self.manager.pop_screen()

    def _on_yes(self) -> None:
        if "game" in self.manager.stack:
            _quit_to_race_selector(self.manager)
        else:
            self.manager.toggle_running()


class QuitConfirmMenu(_BaseQuitConfirmMenu):
    TITLE = "Are you sure?"


class ChampionshipQuitConfirmMenu(_BaseQuitConfirmMenu):
    TITLE = "Quit Championship?"

    def _on_yes(self) -> None:
        self.manager.app_data.reset_championship()
        leaderboard = self.manager.screens.get("leaderboard")
        if leaderboard and hasattr(leaderboard, "counter"):
            leaderboard.counter = 0
        super()._on_yes()
