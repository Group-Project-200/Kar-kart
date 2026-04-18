# screen_manager.py - managing screens throughout the program
#mohamed- removed 3 function that returns self.data or self.current or self. running because its just calling self.manager.app_data
from app_data import AppData



class ScreenManager:
    def __init__(self, app_data : AppData, screen):

        self.running= True
        self.current = None
        self.app_data = app_data
        self.screen = screen
        self.screens = {}

        # add all the screens in the game

    def change_screen(self, label):

        # change current screen

        self.current = self.screens[label]

    def add_screen(self, label, screen):

        # add a new screen to the program

        self.screens[label] = screen


    def toggle_running(self):

        # toggle program from True to False and viceversa

        self.running = not self.running

