# screen_manager.py - managing screens throughout the program

from screens.start_screen import StartScreen
from screens.car_selection_screen import CarScreen
from screens.map_selection_screen import MapScreen as MapScreen

class ScreenManager:
    def __init__(self, app_data):

        self.running= True
        self.current = None
        self.app_data = app_data

        self.screens = {}

        # add all the screens in the game

        self.add_screen("start", StartScreen)
        self.add_screen("car", CarScreen)
        self.add_screen("map", MapScreen)

    def get_screen(self):

        # get current screen

        return self.current

    def change_screen(self, label):

        # change current screen

        self.current = self.screens[label](self)

    def add_screen(self, label, screen):

        # add a new screen to the program

        self.screens[label] = screen

    def is_running(self):

        # check if program is still running

        return self.running

    def toggle_running(self):

        # toggle program from True to False and viceversa

        self.running = not self.running

    def get_app_data(self):

        # get app data

        return self.app_data