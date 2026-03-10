# map_customization_screen.py - screen to choose the map

import pygame, sys

from ui.button import PaddingButton as Button
from ui.container import Container
from constants import Colors
from constants import ScreenPositions as sp
from ui.track import Track

class MapScreen:

    # follow documentation in car_selection_screen.py

    def __init__(self, manager):
        self.manager = manager
        # self.button1 = Button(sp.CENTER_X, sp.XBOTTOM, 32, "PLAY", "car", self.manager)
        self.container1 = Container(sp.CENTER_X, sp.CENTER_Y, sp.WIDTH/4*3, sp.HEIGHT/4*3, 4, 3, "columns")

        # importing tracks from manager

        app_data = self.manager.get_app_data()

        for track in app_data.get_tracks():
            self.container1.add_object(track)

    def handle_event(self, event):

        # to change to another screen do take this line
        # self.button1.handle_event(event)
        pass

    def update(self):
        pass

    def draw(self, surface):
        pygame.display.set_caption("Kar Kart")

        surface.fill(Colors.LIGHT_BLUE)

        # self.button1.draw(surface)
        self.container1.draw(surface)