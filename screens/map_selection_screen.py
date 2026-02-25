# map_customization_screen.py - screen to choose the map

import pygame, sys

from ui.button import Button
from constants import Colors
from constants import ScreenDimensions as sd

class MapScreen:

    # follow documentation in car_selection_screen.py

    def __init__(self, manager):
        self.manager = manager
        self.button1 = Button(sd.CENTER_X, sd.CENTER_Y, 100, 50, "Blue", "car", self.manager)

    def handle_event(self, event):
        self.button1.handle_event(event) # to change to another screen do take this line

    def update(self):
        pass

    def draw(self, surface):
        pygame.display.set_caption("Kar Kart")

        surface.fill((175, 0, 0))

        self.button1.draw(surface)