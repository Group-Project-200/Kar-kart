"""ui_object - stores all attributes and functions that an UI object must have"""

from __future__ import annotations
from abc import ABC, abstractmethod

from karkart.constants import Colors

class UIObject(ABC):
    @abstractmethod
    def __init__(self, center_x: float, center_y: float, width: float, height: float) -> None:
        self.width = width
        self.height = height

        self.x = center_x - self.width / 2
        self.y = center_y - self.height / 2

    def get_width(self) -> float:
        return self.width

    def get_height(self) -> float:
        return self.height

    def set_position(self, x: float, y: float):
        """Set a new position for the object"""
        self.x = x
        self.y = y

class UISelectObject(UIObject, ABC):
    @abstractmethod
    def __init__(self, center_x: float, center_y: float, width: float, height: float) -> None:
        super().__init__(center_x, center_y, width, height)

        self.unselect()
        self.bord_color = Colors.BLACK
        self.bord_thick = 2
        self.bord_2_thick = 4

    def select(self) -> None:
        self.bord_2_color = Colors.RED
        self.color = Colors.DARK_RED
        self.selected = True

    def unselect(self) -> None:
        self.bord_2_color = Colors.LIGHT_BLUE
        self.color = Colors.DARK_BLUE
        self.selected = False

    def is_selected(self) -> bool:
        return self.selected