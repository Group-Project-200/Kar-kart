"""Grid-style containers that lay out child widgets with automatic padding."""

from __future__ import annotations

import pygame

from karkart.constants import Colors
from karkart.settings import Keys as K
from karkart.ui.arrow import Arrow
from karkart.ui.card import PopUpCard
from karkart.ui.ui_object import UIObject


class SelectContainer(UIObject):
    """Grid container with a keyboard-driven selection cursor."""

    def __init__(
        self, center_x: float, center_y: float,
        width: float, height: float,
        rows: int, columns: int,
    ) -> None:
        super().__init__(center_x, center_y, width, height)
        self.rows = rows
        self.columns = columns
        self.objects: list = []
        self.selected = 0
        self.padding_x: float = 0.0
        self.padding_y: float = 0.0
        self.max_width: float = 0.0
        self.max_height: float = 0.0

    def add_object(self, obj) -> None:
        self.objects.append(obj)
        self.objects[self.selected].select()
        self.calculate_padding()

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        prev = self.selected
        if event.key == K.LEFT and self.selected % self.columns != 0:
            self.selected -= 1
        elif event.key == K.RIGHT and self.selected % self.columns != self.columns - 1:
            self.selected += 1
        elif event.key == K.UP and self.selected // self.columns != 0:
            self.selected -= self.columns
        elif event.key == K.DOWN and self.selected // self.columns != self.rows - 1:
            self.selected += self.columns
        else:
            return

        self.objects[prev].unselect()
        self.objects[self.selected].select()

    def draw(self, surface: pygame.Surface) -> None:
        """Draw every child at the positions derived from calculated padding.

        .. note:: Always call :meth:`calculate_padding` after adding all objects.
        """
        n = len(self.objects)
        rows, columns = self.rows, self.columns
        curr_x, curr_y = self.x, self.y

        # NOTE: USED FOR DEBUGGING
        # pygame.draw.rect(surface, Colors.YELLOW, (self.x, self.y, self.width, self.height), 5)

        i = 0
        obj = None
        for r in range(rows):
            if r >= rows - 1:
                columns = n - (rows - 1) * columns

            for _ in range(columns):
                obj = self.objects[i]
                adjusted_y = curr_y + (self.max_height - obj.get_height()) / 2
                obj.set_position(curr_x, adjusted_y)
                obj.draw(surface)
                curr_x += obj.get_width() + self.padding_x
                i += 1

            if obj is not None:
                curr_y += obj.get_height() + self.padding_y
            curr_x = self.x

    def calculate_padding(self, x_center: bool = False, y_center: bool = False) -> None:
        first_row = self.objects[: self.columns]
        first_column = self.objects[:: self.columns]

        if x_center:
            self.padding_x = (self.width - sum(obj.get_width() for obj in first_row)) / (self.columns + 1)
            self.x += self.padding_x
        elif self.columns > 1:
            self.padding_x = (self.width - sum(obj.get_width() for obj in first_row)) / (self.columns - 1)
        else:
            self.padding_x = 0

        if y_center:
            self.padding_y = (self.height - sum(obj.get_height() for obj in first_column)) / (self.rows + 1)
            self.y += self.padding_y
        elif self.rows > 1:
            self.padding_y = (self.height - sum(obj.get_height() for obj in first_column)) / (self.rows - 1)
        else:
            self.padding_y = 0

        self.max_width = max(obj.get_width() for obj in self.objects)
        self.max_height = max(obj.get_height() for obj in self.objects)


class MapContainer(SelectContainer):
    """:class:`SelectContainer` with an extra keyboard-focusable Back button."""

    def __init__(
        self, center_x: float, center_y: float,
        width: float, height: float,
        rows: int, columns: int,
    ) -> None:
        super().__init__(center_x, center_y, width, height, rows, columns)
        self.back_button = None
        self.back_selected = False

    def add_back_button(self, button) -> None:
        self.back_button = button

    def handle_event(self, event):
        # if event.type == pygame.MOUSEMOTION:
        #     pos = event.pos
        #     for i, obj in enumerate(self.objects):
        #         if pygame.Rect(obj.x, obj.y, obj.width, obj.height).collidepoint(pos):
        #             if i != self.selected:
        #                 self.objects[self.selected].unselect()
        #                 self.back_selected = False
        #                 if self.back_button:
        #                     self.back_button.unselect()
        #                 self.selected = i
        #                 obj.select()
        #             return None
        #     return None

        # if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        #     pos = event.pos
        #     for i, obj in enumerate(self.objects):
        #         if pygame.Rect(obj.x, obj.y, obj.width, obj.height).collidepoint(pos):
        #             self.objects[self.selected].unselect()
        #             self.back_selected = False
        #             self.selected = i
        #             obj.select()
        #             return obj.get_map()
        #     return None

        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_RETURN:
            if not self.back_selected:
                # Enter on a map card confirms the map selection.
                return self.objects[self.selected].get_map()
            # Enter on Back returns to the previous screen via the button itself.
            self.selected = 0
            self.back_selected = False
            self.back_button.unselect()
            self.objects[self.selected].select()
            self.back_button.handle_event(event)
            return None

        if (
            event.key == K.DOWN
            and self.selected // self.columns == self.rows - 1
            and not self.back_selected
        ):
            self.back_selected = True
            self.back_button.select()
            self.objects[self.selected].unselect()
            return None

        if event.key == K.UP and self.back_selected:
            self.back_selected = False
            self.back_button.unselect()
            self.selected = self.columns * self.rows - self.columns
            self.objects[self.selected].select()
            return None

        if not self.back_selected:
            super().handle_event(event)
        return None

class PopUpContainer(SelectContainer):
    """:class:`SelectContainer` adapted to the pause menu."""

    def __init__(
        self, center_x: float, center_y: float,
        width: float, height: float,
        rows: int, columns: int,
    ) -> None:
        super().__init__(center_x, center_y, width, height, rows, columns)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        self.objects[self.selected].handle_event(event)

        if event.key == pygame.K_RETURN:
            # Enter on a pop-up card confirms the option selection.
            state = self.objects[self.selected].get_state()
            if state:
                self.objects[self.selected].unselect()
                self.selected = 0
                self.objects[self.selected].select()
                return state
        elif event.key == pygame.K_ESCAPE:
            self.objects[self.selected].unselect()
            self.selected = 0
            self.objects[self.selected].select()

        super().handle_event(event)
        return None

class ArrowContainer(SelectContainer):
    """:class:`SelectContainer` adapted to arrow selector."""

    def __init__(
        self, center_x: float, center_y: float,
        width: float, height: float,
        options: list[PopUpCard]
    ) -> None:

        super().__init__(center_x, center_y, width, height, 1, 3)

        # List containing all the selectable options.
        self.options = options
        
        self.opt_index = 0
        self.objects = [Arrow(0, 0, 30, 30, "left"), self.options[self.opt_index], Arrow(0, 0, 30, 30, "right")]
        self.select()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_RETURN:
            
            # RETURN changes the selected option based on the arrow pressed
            if self.selected == 2:
                self.opt_index = (self.opt_index + 1) % len(self.options)
                self.objects[1] = self.options[self.opt_index]
            elif self.selected == 0:
                self.opt_index = (self.opt_index - 1) % len(self.options)
                self.objects[1] = self.options[self.opt_index]
            return None

        # LEFT and RIGHT move from an arrow to the other, skipping the card in the middle.
        prev = self.selected
        if event.key == K.LEFT and self.selected != 0:
            self.selected -= 2
        elif event.key == K.RIGHT and self.selected != 2:
            self.selected += 2

        self.objects[prev].unselect()
        self.objects[self.selected].select()

    def select(self):
        self.selected = 2
        self.objects[self.selected].select()

    def unselect(self):
        self.objects[self.selected].unselect()

    def set_position(self, x, y):
        super().set_position(x, y)
        self.calculate_padding(x_center=True, y_center=True)

    def get_state(self):
        pass
