from __future__ import annotations
from abc import ABC, abstractmethod
import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp
from karkart.screens.gameplay import GamePlay
from karkart.settings import settings
from karkart.ui import Arrow, ArrowContainer, Button, Container, PopUpButton, PopUpContainer, PopUpCard, SelectContainer, TitleCard
from karkart.ui.ui_object import UISelectObject


class PopUpMenu(ABC):

    @abstractmethod
    def __init__(self, manager, label, width=300, height=450) -> None:
        self.manager = manager
        self.label = label

        self.width: int = width
        self.height: int = height

        self.x: ScreenPosition = sp.CENTER_X
        self.y: ScreenPosition = sp.CCCBOTTOM

        self.container = None
        self.title = None

        self.pause_rect = pygame.Rect(
            self.x - self.width / 2, self.y - self.height / 2, self.width, self.height
        )

        self.active_black_layer: bool = False

        self.black_layer: bool = True
        self.screen: str | None = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.active_black_layer = True
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
        self.title.draw(surface)
        self.container.draw(surface)

        if self.active_black_layer:
            self.black_layer = True
            self.active_black_layer = False

    def get_label(self):
        return self.label

    def activate_black_layer(self):
        self.active_black_layer = True

    def deactivate_black_layer(self):
        self.black_layer = False


class PauseMenu(PopUpMenu):

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        options : list[PopUpCard] = [
            PopUpButton("Settings", self.manager, action="settings"),
            PopUpButton("Change car", self.manager, action="car"),
            PopUpButton("Change mode", self.manager, action="race_selector"),
            PopUpButton("Quit", self.manager, action="end")]
        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(options), 1)

        self.container.add_objects(options)
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
                elif screen == "end":
                    self.manager.toggle_running()
                    return
                self.manager.change_screen(screen)


class SettingsMenu(PopUpMenu):
    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        self.width: int = 300
        self.height: int = 450
        self.pause_rect = pygame.Rect(self.x - self.width / 2, self.y - self.height / 2, self.width, self.height)

        # Container that stores left and right arrows and all the selectable options.
        main_options = []
        self.option_indexes = []
        for obj, opt_list in settings.get_objects().items():
            title_card = (TitleCard(obj, 150, font_size=10))
            side_options = [TitleCard(x, 150) for x in opt_list]
            setting_height = title_card.get_height() + side_options[0].get_height()+10
            new_container = ArrowContainer(0, 0, 250, setting_height, side_options, title_card)

            main_options.append(new_container)
            self.option_indexes.append(new_container.get_opt_index())

        self.container = PopUpContainer(self.x, self.y, self.width, self.height, len(main_options), 1)
        self.container.add_objects(main_options)

        self.container.calculate_padding(x_center=True, y_center=True)

        # Creates title.
        self.title = TitleCard("Settings", self.container.get_width())

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            changes = False
            if event.key in {pygame.K_ESCAPE, pygame.K_RETURN}:
                for i in range(len(self.option_indexes)):
                    if self.option_indexes[i] != self.container.objects[i].get_opt_index():
                        changes = True
                        break

            if changes:
                self.activate_black_layer()
                self.manager.push_screen(self.label)
                self.manager.change_screen("confirm_settings")
                self.manager.get_screen().deactivate_black_layer()
                self.manager.get_screen().activate_confirm_black_layer(self.x, self.y, self.width, self.height)
                self.manager.get_screen().import_new_values(self.option_indexes, self.container.get_objects())

            else:
                super().handle_event(event)



            self.container.handle_event(event)

    def set_return_screen(self, screen):

        self.screen = screen
        self.black_layer = True

class ConfirmSettingsMenu(PopUpMenu):
    def __init__(self, manager, label) -> None:
        super().__init__(manager, label, height=200)

        self.confirm_black_layer: bool = True
        self.blc_active: bool = False


        self.yes_card = PopUpButton("Yes", self.manager, width=100, height=100)
        self.no_card = PopUpButton("No", self.manager, width=100, height=100)

        yes_no = [self.yes_card, self.no_card]
        self.yes_no_container = PopUpContainer(0, 0, 260, 100, 1, len(yes_no))
        self.yes_no_container.add_objects(yes_no)

        self.description = TitleCard("Confirm the settings?", width=260, font_size=12)

        objects = [self.description, self.yes_no_container]
        self.container = Container(self.x, self.y, self.width, self.height, 2, 1)
        self.container.add_objects(objects)

        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard("Settings", self.container.get_width())

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        
        if event.key == pygame.K_RETURN:
            if self.yes_card.is_selected():
                set_list = [obj.get_text() for obj in self.objects]
                settings.change(set_list)

                settings.save()

                for i, obj in enumerate(self.objects):
                    self.option_indexes[i] = obj.get_opt_index()
            
            elif self.no_card.is_selected():
                for i, obj in enumerate(self.objects):
                    obj.set_opt_index(self.option_indexes[i])

            self.yes_card.select()
            self.no_card.unselect()
            self.manager.pop_screen()
            self.manager.pop_screen()

        self.yes_no_container.handle_event(event)

    def draw(self, surface):
        if self.confirm_black_layer:
            black_layer = pygame.Surface((self.bl_width, self.bl_height))
            black_layer.fill(Colors.BLACK)
            black_layer.set_alpha(128)
            surface.blit(black_layer, (self.bl_x - self.bl_width/2, self.bl_y - self.bl_height/2))

            self.confirm_black_layer = False

        super().draw(surface)

        if self.blc_active:
            self.confirm_black_layer = True
            self.blc_active = False

    def activate_confirm_black_layer(self, x, y, width, height):
        self.blc_active = True

        self.bl_x = x
        self.bl_y = y
        self.bl_width = width
        self.bl_height = height

    def import_new_values(self, option_indexes, objects):
        self.option_indexes = option_indexes
        self.objects = objects


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
        self.container.add_objects(options)
        self.container.calculate_padding(x_center=True, y_center=True)

        self.title = TitleCard("Help Menu", self.container.get_width())

        # Returned screen is set by HelpIcon right before opening.
        self.screen = "start"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            super().handle_event(event)
            self.container.handle_event(event)
            if event.key == pygame.K_h:
                self.active_black_layer = True
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
    
    def get_text(self):
        return self.lines

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
