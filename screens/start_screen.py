# start_screen.py - first screen of the program

import pygame

class StartScreen:
    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):

        # TODO: IMPLEMENT IT, at the moment it just directly changes to car_selection_screen

        pygame.display.set_caption("Kar Kart")

        # remove this after you are done
        self.manager.change_screen("car")