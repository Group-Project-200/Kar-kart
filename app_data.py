# app_data.py
import os
from ui.track import Track
from pathlib import Path

#this function is to automatically get the path to the resources file on any laptop and save it to BASE_DIR
def find_project_root(marker="main.py"):
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent /marker).exists():
            return parent
    raise RuntimeError(f"Could not find project root (no {marker} found)")

BASE_DIR = find_project_root()



class AppData:
    def __init__(self):
        #this part gets the names of all the maps in the maps folder
        maps_dir = os.path.join(BASE_DIR, "resources", "maps")
        folders = sorted([
            name for name in os.listdir(maps_dir)
            if os.path.isdir(os.path.join(maps_dir, name))
        ])

        self.tracks = []

        #this part creates tracks with their cover image, names, and file path
        for name in folders:
            img_path = os.path.join(maps_dir, name, "cover.png")
            fldr_path =os.path.join(maps_dir, name)
            self.add_track(Track(img_path, name,fldr_path))



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
        self.current_map = None
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
