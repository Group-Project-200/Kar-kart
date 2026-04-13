# app_data.py

from ui.track import Track

class AppData:
    def __init__(self):

        # store app data

        self.tracks = []

        tw, th = 100, 66

        self.add_track(Track("./resources/pictures/italy_flag.png", "Italy", tw, th))
        self.add_track(Track("./resources/pictures/uk_flag.png", "UK", tw, th))
        self.add_track(Track("./resources/pictures/belgium_flag.png", "Belgium", tw, th))
        self.add_track(Track("./resources/pictures/spain_flag.png", "Spain", tw, th))
        self.add_track(Track("./resources/pictures/australia_flag.png", "Australia", tw, th))
        self.add_track(Track("./resources/pictures/japan_flag.png", "Japan", tw, th))
        self.add_track(Track("./resources/pictures/china_flag.png", "China", tw, th))
        self.add_track(Track("./resources/pictures/singapore_flag.png", "Singapore", tw, th))
        self.add_track(Track("./resources/pictures/usa_flag.png", "USA", tw, th))
        self.add_track(Track("./resources/pictures/canada_flag.png", "Canada", tw, th))
        self.add_track(Track("./resources/pictures/mexico_flag.png", "Mexico", tw, th))
        self.add_track(Track("./resources/pictures/brazil_flag.png", "Brazil", tw, th))

    def add_track(self, track):

        # add a new track to the program

        self.tracks.append(track)

    def get_tracks(self):

        # get the list of tracks

        return self.tracks