# map_customization_screen.py - screen to choose the map

import pygame, sys

from ui.button import PaddingButton as Button
from ui.container import SelectContainer
from constants import Colors
from constants import ScreenPositions as sp
from ui.track import Track
from ui.button import ColorButton


class MapScreen:

    # follow documentation in car_selection_screen.py

    def __init__(self, manager):
        self.manager = manager

        # self.button1 = Button(sp.CENTER_X, sp.XBOTTOM, 32, "PLAY", "car", self.manager)
        self.back_btn = ColorButton(110, sp.H//1.35, 100, 50, "←", "car", self.manager, (254, 214, 30), (204, 219, 213)) # ColorButton(110, sp.H//2, 100, 50, "←", "car", self.manager, (57, 155, 250), (204, 219, 213))
        self.container1 = SelectContainer(sp.CENTER_X, sp.CCCBOTTOM, sp.WIDTH/4*3, sp.HEIGHT/4*3, 4, 3, "columns")

        # load bg image
        self.background = pygame.transform.scale( pygame.image.load("resources/pictures/cust2.png").convert(), (sp.WIDTH, sp.HEIGHT) )


        # importing tracks from manager
        app_data = self.manager.get_app_data()

        for track in app_data.get_tracks():
            self.container1.add_object(track)

    def handle_event(self, event):

        # to change to another screen do take this line
        # self.button1.handle_event(event)
        self.back_btn.handle_event(event)
        
        self.container1.handle_event(event)

    def update(self):
        pass

    def draw(self, surface):
        pygame.display.set_caption("Map Selection")

        # draw background 
        surface.blit(self.background, (0, 0))

        # self.button1.draw(surface)
        self.back_btn.draw(surface)
        self.container1.draw(surface)