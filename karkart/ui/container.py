"""Grid-style containers that lay out child widgets with automatic padding."""

from __future__ import annotations

import logging

import pygame

from karkart.constants import Keys as K


logger = logging.getLogger("container")
logging.basicConfig(level=logging.CRITICAL, format=" %(levelname)s - %(message)s")



class SelectContainer:
    """Grid container with a keyboard-driven selection cursor."""

    def __init__(
        self, center_x: float, center_y: float,
        width: float, height: float,
        rows: int, columns: int,
    ) -> None:
        self.width = width
        self.height = height
        self.x = center_x - self.width / 2
        self.y = center_y - self.height / 2
        self.rows = rows
        self.columns = columns
        self.objects: list = []
        self.selected = 0
        self.padding_x: float = 0.0
        self.padding_y: float = 0.0

    def get_width(self) -> float:
        return self.width

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
        i = 0
        obj = None
        for r in range(rows):
            if r >= rows - 1:
                columns = n - (rows - 1) * columns

            for _ in range(columns):
                obj = self.objects[i]
                obj.set_position(curr_x, curr_y)
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
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            for i, obj in enumerate(self.objects):
                if pygame.Rect(obj.x, obj.y, obj.width, obj.height).collidepoint(pos):
                    if i != self.selected:
                        self.objects[self.selected].unselect()
                        self.back_selected = False
                        if self.back_button:
                            self.back_button.unselect()
                        self.selected = i
                        obj.select()
                    return None
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for i, obj in enumerate(self.objects):
                if pygame.Rect(obj.x, obj.y, obj.width, obj.height).collidepoint(pos):
                    self.objects[self.selected].unselect()
                    self.back_selected = False
                    self.selected = i
                    obj.select()
                    return obj.get_map()
            return None

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

class PauseContainer(SelectContainer):
    """:class:`SelectContainer` adapted to the pause menu."""

    def __init__(
        self, center_x: float, center_y: float,
        width: float, height: float,
        rows: int, columns: int,
    ) -> None:
        super().__init__(center_x, center_y, width, height, rows, columns)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            for i, obj in enumerate(self.objects):
                if pygame.Rect(obj.x, obj.y, obj.width, obj.height).collidepoint(pos):
                    if i != self.selected:
                        self.objects[self.selected].unselect()
                        self.selected = i
                        obj.select()
                    return None
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for i, obj in enumerate(self.objects):
                if pygame.Rect(obj.x, obj.y, obj.width, obj.height).collidepoint(pos):
                    self.objects[self.selected].unselect()
                    self.selected = i
                    obj.select()
                    screen = obj.get_screen()
                    if screen:
                        self.selected = 0
                        return screen
                    return None
            return None

        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_RETURN:
            # Enter on a pause card confirms the option selection.
            screen = self.objects[self.selected].get_screen()
            if screen:
                self.selected = 0
                return screen

        super().handle_event(event)
        return None


PopUpContainer = PauseContainer