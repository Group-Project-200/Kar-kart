# app_data.py

import os
import pygame

from ui.track import Track
from constants import BASE_DIR


def load_all_car_stacks() -> dict[str, list[pygame.Surface]]:
    base_path = os.path.join(BASE_DIR, "resources", "render")

    if not os.path.isdir(base_path):
        raise RuntimeError(f"Car render folder not found: {base_path}")

    car_stacks = {}
    for name in sorted(os.listdir(base_path)):
        if not name.startswith("car_"):
            continue
        folder = os.path.join(base_path, name)
        if not os.path.isdir(folder):
            continue
        pngs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".png"))
        if not pngs:
            continue
        car_stacks[name] = [
            pygame.image.load(os.path.join(folder, f)).convert_alpha()
            for f in pngs
        ]

    if not car_stacks:
        raise RuntimeError(f"No car sprites found in {base_path}")

    return car_stacks


class AppData:
    def __init__(self):
        maps_dir = os.path.join(BASE_DIR, "resources", "maps")
        folders = sorted([
            name for name in os.listdir(maps_dir)
            if os.path.isdir(os.path.join(maps_dir, name))
        ])

        self.tracks = []
        self.cars = load_all_car_stacks()

        for name in folders:
            img_path = os.path.join(maps_dir, name, "cover.png")
            fldr_path = os.path.join(maps_dir, name)
            if os.path.isfile(img_path):
                self.add_track(Track(img_path, name, fldr_path))

        def _flag(filename):
            return os.path.join(BASE_DIR, "resources", "pictures", filename)

        self.add_track(Track(_flag("uk_flag.png"), "UK", None))
        self.add_track(Track(_flag("belgium_flag.png"), "Belgium", None))
        self.add_track(Track(_flag("spain_flag.png"), "Spain", None))
        self.add_track(Track(_flag("australia_flag.png"), "Australia", None))
        self.add_track(Track(_flag("japan_flag.png"), "Japan", None))
        self.add_track(Track(_flag("china_flag.png"), "China", None))
        self.add_track(Track(_flag("singapore_flag.png"), "Singapore", None))
        self.add_track(Track(_flag("usa_flag.png"), "USA", None))
        self.add_track(Track(_flag("canada_flag.png"), "Canada", None))
        self.add_track(Track(_flag("mexico_flag.png"), "Mexico", None))
        self.add_track(Track(_flag("brazil_flag.png"), "Brazil", None))

        default = next((t for t in self.tracks if t.name == "map_2"), None)
        self.current_map: Track | None = default or (self.tracks[0] if self.tracks else None)
        self.current_car_name: str | None = "car_01"
        self.current_car = self.cars[self.current_car_name]

    def add_track(self, track):
        self.tracks.append(track)

    def return_map_layers(self):
        if self.current_map and self.current_map.path:
            path = self.current_map.path
            image_exts = (".png", ".jpg", ".jpeg")
            return [
                pygame.image.load(os.path.join(path, f)).convert_alpha()
                for f in sorted(os.listdir(path))
                if f.lower().endswith(image_exts) and f != "cover.png"
            ]
        return []
