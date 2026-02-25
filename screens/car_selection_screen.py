# car_customization_screen.py - screen to choose the map

import pygame

from ui.button import Button
from constants import Colors
from constants import ScreenDimensions as sd

class CarScreen:
    def __init__(self, manager):
        self.manager = manager     # ALWAYS ADD THE MANAGER
        self.button1 = Button(sd.CENTER_X, sd.CENTER_Y, 100, 50, "Red", "map", self.manager)

    def handle_event(self, event):  # use this template for the key detection

        # ask button1 to handle event
        
        self.button1.handle_event(event)

    def update(self): # add any other object here like the car class as well as its physics
        # example:
        # car.y += 5
        pass

    def draw(self, surface): # use this function to draw anything onto the screen
        
        # fill surface + call draw for all the objects inside

        pygame.display.set_caption("Kar Kart")

        surface.fill((0, 0, 175))

        self.button1.draw(surface)
