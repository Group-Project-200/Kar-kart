# map_customization_screen.py - screen to choose the map

import pygame, sys

from ui.button import PaddingButton as Button
from ui.container import SelectContainer
from constants import Colors
from constants import ScreenPositions as sp
from ui.track import Track

class MapScreen:

    # follow documentation in car_selection_screen.py

    def __init__(self, manager):
        self.manager = manager
        # self.button1 = Button(sp.CENTER_X, sp.XBOTTOM, 32, "PLAY", "car", self.manager)
        self.container1 = SelectContainer(sp.CENTER_X, sp.CCCBOTTOM, sp.WIDTH/4*3, sp.HEIGHT/4*3, 4, 3, "columns")

        # importing tracks from manager

        app_data = self.manager.get_app_data()

        for track in app_data.get_tracks():
            self.container1.add_object(track)

    def handle_event(self, event):

        # to change to another screen do take this line
        # self.button1.handle_event(event)
        
        self.container1.handle_event(event)

    def update(self):
        pass

    def draw(self, surface):
        pygame.display.set_caption("Kar Kart")

        surface.fill(Colors.LIGHT_BLUE)

        instr_font = pygame.font.SysFont("arial", 20, bold=True)
        instr_text = instr_font.render("Select the track you want to race on", True, Colors.BLACK)
        instr_center = instr_text.get_rect(center=(sp.CENTER_X, sp.XXTOP))
        surface.blit(instr_text, instr_center)

        # self.button1.draw(surface)
        self.container1.draw(surface)