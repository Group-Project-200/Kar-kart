"""
app_data.py
--------
Store information of the whole system

"""

from __future__ import annotations

import json
import os
from pathlib import Path
import random

import pygame

from karkart.paths import CAR_RENDER_DIR, MAP_DATA_FILE, MAPS_DIR
from karkart.ui.track import Track


with MAP_DATA_FILE.open() as _f:
    _MAP_DATA_KEYS: frozenset[str] = frozenset(json.load(_f).keys())

# All tracks in the system.
_ALLOWED_TRACKS: frozenset[str] = frozenset(
    {
        "Hells Blaze",
        "Candy Land",
        "Meadow Drift",
        "Lunar Loop",
    }
)


def load_all_car_stacks() -> dict[str, list[pygame.Surface]]:
    """Load whole cars using stacks."""

    if not CAR_RENDER_DIR.is_dir():
        raise RuntimeError(f"Car render folder not found: {CAR_RENDER_DIR}")

    car_stacks: dict[str, list[pygame.Surface]] = {}
    for car_folder in sorted(CAR_RENDER_DIR.iterdir()):
        if not car_folder.is_dir() or not car_folder.name.startswith("car_"):
            continue
        pngs = sorted(p for p in car_folder.iterdir() if p.suffix.lower() == ".png")
        if not pngs:
            continue
        car_stacks[car_folder.name] = [
            pygame.image.load(str(p)).convert_alpha() for p in pngs
        ]

    if not car_stacks:
        raise RuntimeError(f"No car sprites found in {CAR_RENDER_DIR}")

    return car_stacks


class AppData:
    """Store all shared information about the system"""

    def __init__(self) -> None:
        self.tracks: list[Track] = []
        self.cars: dict[str, list[pygame.Surface]] = load_all_car_stacks()
        self.modes: {str : {str : bool}} = {
            "Time Trial": {"Ai": False, "Items": False, "loop": False},
            "Race Mode": {"Ai": True, "Items": True, "loop": False},
            "Championship": {"Ai": True, "Items": True, "loop": True},
        }

        for map_folder in sorted(p for p in MAPS_DIR.iterdir() if p.is_dir()):

            cover = map_folder / "cover.png"
            if (
                cover.is_file()
                and map_folder.name in _MAP_DATA_KEYS
                and map_folder.name in _ALLOWED_TRACKS
            ):

                self.add_track(Track(str(cover), map_folder.name, map_folder))

        self.car_start_pos = 5
        self.current_map= None
        self.current_car_name = None
        self.current_car = None
        self.current_mode = None

        self.randomised_maps_order = None
        self.championship_results = {"Osyra": [0,1], "Driftaroo": [0,2], "Zippa": [0,3], "Khepra": [0,4], "Player 1": [0,5]}

    _INITIAL_RESULTS = {"Osyra": [0,1], "Driftaroo": [0,2], "Zippa": [0,3], "Khepra": [0,4], "Player 1": [0,5]}

    def reset_championship(self) -> None:
        """Reset default championship info."""

        for name, defaults in self._INITIAL_RESULTS.items():
            self.championship_results[name] = list(defaults)
        self.modes["Championship"]["loop"] = True

    def randomise_map_selection(self):
        self.randomised_maps_order = random.sample(self.tracks, 3)
        self.set_current_map(self.randomised_maps_order[0])

    def add_track(self, track: Track) -> None:
        """Add new track to the system."""

        self.tracks.append(track)

    def get_tracks(self) -> list[Track]:
        """Get list of tracks."""

        return self.tracks

    def set_current_map(self, track: Track) -> None:
        """Set map to race on."""

        self.current_map = track

    def set_current_car(self, car_name: str):
        """Set car to drive on."""

        self.current_car_name = car_name
        self.current_car = self.cars[self.current_car_name]

    def return_map_layers(self) -> list[pygame.Surface]:
        """Return all layers of maps."""

        if not (self.current_map and self.current_map.corr_map):
            return []

        path = Path(self.current_map.corr_map)
        image_extensions = (".png", ".jpg", ".jpeg")
        return [
            pygame.image.load(str(path / name)).convert_alpha()
            for name in sorted(os.listdir(path))
            if name.lower().endswith(image_extensions) and name != "cover.png"
        ]
