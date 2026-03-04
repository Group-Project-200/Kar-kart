# screen_manager.py - managing screens throughout the program

class ScreenManager:
    def __init__(self):
        self.running= True
        self.current = None
        self.screens = {}
        self.tracks = []

    def change_screen(self, label):

        # change current screen

        self.current = self.screens[label](self)

    def add_screen(self, label, screen):

        # add a new screen to the program

        self.screens[label] = screen

    def add_track(self, track):

        # add a new track to the program

        self.tracks.append(track)

    def get_tracks(self):

        # get the list of tracks

        return self.tracks

    def get_screen(self):

        # get current screen

        return self.current

    def is_running(self):

        # check if program is still running

        return self.running

    def toggle_running(self):

        # toggle program from True to False and viceversa

        self.running = not self.running