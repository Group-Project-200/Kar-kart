# app_data.py

from ui.track import Track

class AppData:
    def __init__(self):

        # store app data

        self.tracks = []

        self.add_track(Track(r".\resources\maps\map1\0.png", "PRESS ENTER", r".\resources\maps\map1"))
        self.add_track(Track("./resources/pictures/uk_flag.png", "UK"))
        self.add_track(Track("./resources/pictures/belgium_flag.png", "Belgium"))
        self.add_track(Track("./resources/pictures/spain_flag.png", "Spain"))
        self.add_track(Track("./resources/pictures/australia_flag.png", "Australia"))
        self.add_track(Track("./resources/pictures/japan_flag.png", "Japan"))
        self.add_track(Track("./resources/pictures/china_flag.png", "China"))
        self.add_track(Track("./resources/pictures/singapore_flag.png", "Singapore"))
        self.add_track(Track("./resources/pictures/usa_flag.png", "USA"))
        self.add_track(Track("./resources/pictures/canada_flag.png", "Canada"))
        self.add_track(Track("./resources/pictures/mexico_flag.png", "Mexico"))
        self.add_track(Track("./resources/pictures/brazil_flag.png", "Brazil"))

        # current map and car stored here
        # TODO: DEFAULT MUST BE None
        self.current_map = r".\resources\maps\map1"
        self.current_car = None

    def add_track(self, track):

        # add a new track to the program

        self.tracks.append(track)

    def get_tracks(self):

        # get the list of tracks

        return self.tracks

    def set_current_map(self, mapObj):

        # set current map
        
        self.current_map = mapObj

    def get_current_map(self):

        # get current map

        return self.current_map
