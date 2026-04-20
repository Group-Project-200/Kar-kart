"""Global runtime state: loaded track metadata and car sprite stacks."""

from __future__ import annotations

import os
from pathlib import Path

import pygame

from karkart.paths import CAR_RENDER_DIR, MAPS_DIR, PICTURES_DIR
from karkart.ui.track import Track


_FLAG_TRACKS: tuple[tuple[str, str], ...] = (
    ("australia_flag.png", "Australia"),
    ("japan_flag.png", "Japan"),
    ("china_flag.png", "China"),
    ("singapore_flag.png", "Singapore"),
    ("usa_flag.png", "USA"),
    ("canada_flag.png", "Canada"),
    ("mexico_flag.png", "Mexico"),
    ("brazil_flag.png", "Brazil"),
)


def load_all_car_stacks() -> dict[str, list[pygame.Surface]]:
    """Load every ``car_*`` folder under ``resources/render`` as a sprite stack."""
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
    """Owns the playable track list and the currently selected car/map."""

    def __init__(self) -> None:
        self.tracks: list[Track] = []
        self.cars: dict[str, list[pygame.Surface]] = load_all_car_stacks()

        # Playable tracks discovered on disk (each has cover + per-layer images).
        for map_folder in sorted(p for p in MAPS_DIR.iterdir() if p.is_dir()):
            cover = map_folder / "cover.png"
            if cover.is_file():
                self.add_track(Track(str(cover), map_folder.name, str(map_folder)))

        # Decorative flag-only tracks (placeholders, no playable layers yet).
        for filename, label in _FLAG_TRACKS:
            self.add_track(Track(str(PICTURES_DIR / filename), label, None))

        default = next((t for t in self.tracks if t.name == "map_2"), None)
        self.current_map: Track | None = default or (self.tracks[0] if self.tracks else None)
        self.current_car_name: str = "car_01"
        self.current_car: list[pygame.Surface] = self.cars[self.current_car_name]

    def add_track(self, track: Track) -> None:
        self.tracks.append(track)

    def get_tracks(self) -> list[Track]:
        return self.tracks

    def set_current_map(self, track: Track) -> None:
        self.current_map = track

    def set_current_car(self, car_name):
        self.current_car_name = car_name
        self.current_car= self.cars[self.current_car_name]

    def return_map_layers(self) -> list[pygame.Surface]:
        """Load every layer image (except ``cover.png``) for the current map."""
        if not (self.current_map and self.current_map.corr_map):
            return []

        path = Path(self.current_map.corr_map)
        image_extensions = (".png", ".jpg", ".jpeg")
        return [
            pygame.image.load(str(path / name)).convert_alpha()
            for name in sorted(os.listdir(path))
            if name.lower().endswith(image_extensions) and name != "cover.png"
        ]
