from __future__ import annotations
from abc import ABC, abstractmethod


class UIObject(ABC):
    @abstractmethod
    def __init__(
        self, center_x: float, center_y: float, width: float, height: float
    ) -> None:
        self.width = width
        self.height = height

        self.x = center_x - self.width / 2
        self.y = center_y - self.height / 2

    def get_width(self) -> float:
        return self.width

    def get_height(self) -> float:
        return self.height

    def set_position(self, x: float, y: float):

        self.x = x
        self.y = y
