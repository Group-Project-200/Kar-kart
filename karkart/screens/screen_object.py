""" screen_object.py - common screen features"""

from __future__ import annotations
from abc import ABC, abstractmethod

from karkart.constants import Colors, ScreenPositions as sp

class Screen(ABC):

    def __init__(self, manager, label):
        self.manager = manager
        self.label = label

        self.x = 0
        self.y = 0

        self.width = sp.WIDTH
        self.height = sp.HEIGHT

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass

    def get_width(self) -> float:
        return self.width

    def get_height(self) -> float:
        return self.height

    def get_position(self) -> (float, float):
        return(self.x, self.y)

    def get_label(self):
        return self.label