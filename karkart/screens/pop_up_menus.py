"""
pop_up_menus.py
--------
Create all pop-up menus of the game:

Pause, Settings, Help, and confirmation ones

"""

from __future__ import annotations
from abc import ABC, abstractmethod

import pygame

from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.paths import PIXEL_FONT
from karkart.screens.gameplay import GamePlay
from karkart.screens.screen_object import Screen
from karkart.settings import settings
from karkart.ui import Arrow, ArrowContainer, Button, Container, HelpTextCard, TextButton, PopUpContainer, PopUpCard, SelectContainer, TextCard
from karkart.ui.ui_object import UISelectObject


class PopUpMenu(Screen, ABC):
    """Abstract class for commonalities among all pop-up menus"""

    is_popup: bool = True

    def __init__(self, manager: ScreenManager, label: str, width: float =300, height: float =450) -> None:
        super().__init__(manager, label)

        self.width: int = width
        self.height: int = height

        self.center_x: float = sp.CENTER_X
        self.center_y: float = sp.CCCBOTTOM

        self.x = self.center_x - self.width / 2
        self.y = self.center_y - self.height / 2

        self.container = None
        self.title = None

        self.pause_rect = pygame.Rect(
            self.x, self.y, self.width, self.height
        )

        self.black_layer: bool = True
        self.bl_active: bool = False

    def handle_event(self, event):
        "Clicking ESC closes the screen"

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop_screen()
            if getattr(self.manager.current, "is_popup", False):
                self.manager.current.off_black_layer()

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):
        """Draw black layer and the screen itself"""

        # Condition to avoid repetition and excessive darkening of background.
        if self.black_layer:
            last_screen_label = self.manager.get_prev_screen()
            last_screen = self.manager.screens[last_screen_label]
            dim = pygame.Surface((last_screen.width, last_screen.height))
            dim.fill(Colors.BLACK)
            dim.set_alpha(128)
            surface.blit(dim, (last_screen.x, last_screen.y))
            self.black_layer = False

        pygame.draw.rect(surface, Colors.LIGHT_BLUE, self.pause_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, self.pause_rect, 2, border_radius=8)
        self.title.draw(surface)
        self.container.draw(surface)

        if self.bl_active:
            self.black_layer = True
            self.bl_active = False


    def _find_underlying(self):
        """Find underlying screen."""

        for label in self.manager.stack:
            screen = self.manager.screens.get(label)
            if screen is not None and not getattr(screen, "is_popup", False):
                return screen
        return None

    def get_label(self):
        return self.label

    def on_activate(self) -> None:
        """Activate black layer."""
        self.black_layer = True

    def off_black_layer(self) -> None:
        """Deactivate black layer."""
        self.black_layer = False
        self.bl_active = False


def _stop_game(manager) -> None:
    old = manager.screens.get("game")
    if old and hasattr(old, "on_destroy"):
        old.on_destroy()


def _quit_to_race_selector(manager) -> None:
    _stop_game(manager)
    manager.stack.clear()
    manager.change_screen("race_selector")


class PauseMenu(PopUpMenu):
    """Extension of PopUpMenu for the pop-up pause menu."""

    def __init__(self, manager: ScreenManager, label: str) -> None:
        super().__init__(manager, label)

        # List all buttons.
        options = [
            TextButton("Resume",    self.manager, action="resume"),
            TextButton("Restart",   self.manager, action="restart"),
            TextButton("Quit Race", self.manager, action="quit_mode"),
        ]
        self.container = PopUpContainer(
            self.center_x, self.center_y, self.width, self.height, len(options), 1
        )
        self.container.add_objects(options)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TextCard("Pause Menu", self.container.get_width())

    def handle_event(self, event):
        """Handle closing menu and opening others."""

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.manager.push_screen(self.label)
            self.manager.change_screen("settings")
            self.manager.get_screen().off_black_layer()
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

        elif screen == "quit_mode":
            if self.manager.app_data.current_mode == "Championship":
                target = "championship_quit_confirm"
            else:
                target = "quit_mode"

            self.manager.push_screen(self.label)
            self.manager.change_screen(target)


class SettingsMenu(PopUpMenu):
    """Extension of PopUpMenu for the pop-up settings menu."""

    def __init__(self, manager: ScreenManager, label: str) -> None:
        super().__init__(manager, label)

        self.pause_rect = pygame.Rect(
            self.x, self.y, self.width, self.height
        )

        # Store all setting options.
        main_options = []
        self.option_indexes = []
        for obj, opt_list in settings.get_objects().items():
            title_card = TextCard(obj, 150, font_size=10)
            side_options = [TextCard(x, 150) for x in opt_list]
            setting_height = title_card.get_height() + side_options[0].get_height()+10
            new_container = ArrowContainer(0, 0, 250, setting_height, side_options, title_card)

            main_options.append(new_container)
            self.option_indexes.append(new_container.get_opt_index())

        self.quit_option = TextButton("QUIT GAME!", self.manager, action="quit_confirm", width=250, height=50)
        main_options.append(self.quit_option)

        # Group all setting options.
        self.container = PopUpContainer(self.center_x, self.center_y, self.width, self.height, len(main_options), 1)
        self.container.add_objects(main_options)

        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TextCard("Settings", self.container.get_width())

    def _save_settings(self) -> None:
        """Save all new settings."""

        objs = self.container.get_objects()
        settings.set_bindings(objs[0].get_text())
        settings.set_sound(objs[1].get_text())
        settings.set_music(objs[2].get_text())
        settings.save()

    def handle_event(self, event):
        """Handle changing settings."""

        if event.type == pygame.KEYDOWN:
            changes = False

            # If quit is selected, isolate ENTER only for that button.
            controls_set = {pygame.K_ESCAPE}.union({} if self.quit_option.is_selected() else {pygame.K_RETURN})

            if event.key in controls_set:
                for i in range(len(self.option_indexes)):

                    # Check if any data has changed.
                    if self.option_indexes[i] != self.container.objects[i].get_opt_index():
                        changes = True
                        break

            # Confirm that there are some changes.
            if changes:
                self.manager.push_screen(self.label)
                self.manager.change_screen("confirm_settings")
                self.manager.get_screen().import_new_values(self.option_indexes, self.container.get_objects())

            else:
                super().handle_event(event)

            screen = self.container.handle_event(event)

            if not screen:
                return

            # Make user quit.
            if screen == "quit_confirm":
                self._save_settings()
                target = screen
                self.manager.push_screen(self.label)
                self.manager.change_screen(target)
            elif screen:
                self.manager.change_screen(screen)


class HelpMenu(PopUpMenu):
    """Extension of PopUpMenu for the pop-up help menu."""

    def __init__(self, manager: ScreenManager, label: str) -> None:
        super().__init__(manager, label, width=1000, height=600)

        self.pause_rect = pygame.Rect(
            self.x, self.y, self.width, self.height
        )

        # The whole help content is in here.
        help_card = HelpTextCard(920, 490)

        options = [help_card]
        self.container = Container(
            self.center_x, self.center_y, self.width, self.height, len(options), 1
        )
        self.container.add_objects(options)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TextCard("Help Menu", help_card.get_width())

        self.return_screen: str = "start"

    def handle_event(self, event) -> None:
        """Help closes by pressing H or ESC"""

        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_h, pygame.K_ESCAPE):
            self.manager.pop_screen()

    def set_return_screen(self, screen: str) -> None:
        self.return_screen = screen



class _BaseQuitConfirmMenu(PopUpMenu):
    """
    Two-button (No / Yes) confirmation dialog.
    Subclasses override _on_yes and/or _on_no and/or _return_pressed.
    """

    def __init__(self, manager: ScreenManager, label: str, text="") -> None:
        super().__init__(manager, label, height=200)

        self.text = text

        # Create Yes and No cards + their container.
        self.yes_card = TextButton("Yes", self.manager, width=100, height=100)
        self.no_card = TextButton("No", self.manager, width=100, height=100)
        no_yes = [self.no_card, self.yes_card]
        self.no_yes_container = PopUpContainer(0, 0, 260, 100, 1, len(no_yes))
        self.no_yes_container.add_objects(no_yes)

        # Create bigger container with the description, too.
        self.description = TextCard(self.text, width=260, font_size=12)
        objects = [self.description, self.no_yes_container]
        self.container = Container(self.center_x, self.center_y, self.width, self.height, 2, 1)
        self.container.add_objects(objects)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TextCard("Confirm pop-up", self.container.get_width())

    def handle_event(self, event) -> None:
        """
        Handle event if:
         - Yes is selected,
         - No is selected,
         - Any of them is selected.
        """

        if event.type != pygame.KEYDOWN:
            return
        
        if event.key == pygame.K_RETURN:
            if self.yes_card.is_selected():
                self._on_yes()
            
            elif self.no_card.is_selected():
                self._on_no()
            
            self._return_pressed()

        self.no_yes_container.handle_event(event)

    def _on_yes(self) -> None:
        """What happens if Yes is clicked."""

        # If it happens in game, it goes back to race selector.
        if "game" in self.manager.stack:
            _quit_to_race_selector(self.manager)
        else:
            self.manager.toggle_running()

    def _on_no(self) -> None:
        """What happens if No is clicked."""

        self.manager.pop_screen()
        if getattr(self.manager.current, "is_popup", False):
            self.manager.current.off_black_layer()

    def _return_pressed(self) -> None:
        """What happens if ENTER is pressed."""

        self.yes_card.unselect()
        self.no_card.select()

class ConfirmSettingsMenu(_BaseQuitConfirmMenu):
    """Extension of _BaseQuitConfirmMenu for confirming settings."""

    def __init__(self, manager: ScreenManager, label: str) -> None:
        text = "Confirm settings?"
        super().__init__(manager, label, text)

    def _on_yes(self) -> None:
        set_list = [obj.get_text() for obj in self.objects]
        settings.change(set_list)

        settings.save()

        for i, obj in enumerate(self.objects[:-1]):
            self.option_indexes[i] = obj.get_opt_index()

    def _on_no(self) -> None:
        for i, obj in enumerate(self.objects[:-1]):
            obj.set_opt_index(self.option_indexes[i])

    def _return_pressed(self) -> None:
        self.yes_card.unselect()
        self.no_card.select()
        self.manager.pop_screen()
        self.manager.pop_screen()
        if getattr(self.manager.current, "is_popup", False):
            self.manager.current.off_black_layer()

    def import_new_values(self, option_indexes, objects):
        self.option_indexes = option_indexes
        self.objects = objects

class QuitConfirmMenu(_BaseQuitConfirmMenu):
    """Extension of _BaseQuitConfirmMenu for confirming quitting GAME."""

    def __init__(self, manager: ScreenManager, label: str) -> None:
        text = "Are you sure?"
        super().__init__(manager, label, text)

    def _on_yes(self) -> None:
        self.manager.toggle_running()

class ModeQuitConfirmMenu(_BaseQuitConfirmMenu):
    """Extension of _BaseQuitConfirmMenu for confirming quitting MODE."""

    def __init__(self, manager: ScreenManager, label: str) -> None:
        text = "Quit Race?"
        super().__init__(manager, label, text)

    def _on_yes(self) -> None:
        self.manager.add_screen(GamePlay(self.manager,"game"))
        super()._on_yes()

class ChampionshipQuitConfirmMenu(_BaseQuitConfirmMenu):
    """Extension of _BaseQuitConfirmMenu for confirming quitting CHAMPIONSHIP."""

    def __init__(self, manager: ScreenManager, label: str) -> None:
        text = "Quit Championship?"
        super().__init__(manager, label, text)

    def _on_yes(self) -> None:
        self.manager.app_data.reset_championship()
        leaderboard = self.manager.screens.get("leaderboard")
        if leaderboard and hasattr(leaderboard, "counter"):
            leaderboard.counter = 0
        super()._on_yes()
