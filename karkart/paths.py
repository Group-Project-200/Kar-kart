"""Filesystem paths used across the game.

All paths are resolved relative to the project root (the directory that
contains ``main.py``) so the game can be launched from any working directory.
"""

from __future__ import annotations

from pathlib import Path


def _find_project_root(marker: str = "main.py") -> Path:
    """Walk upward from this file until a directory containing *marker* is found."""
    current = Path(__file__).resolve().parent
    for parent in (current, *current.parents):
        if (parent / marker).exists():
            return parent
    raise RuntimeError(f"Could not find project root (no {marker} found)")


PROJECT_ROOT: Path = _find_project_root()
RESOURCES_DIR: Path = PROJECT_ROOT / "resources"
PICTURES_DIR: Path = RESOURCES_DIR / "pictures"
ASSETS_DIR: Path = RESOURCES_DIR / "assets"
MAPS_DIR: Path = RESOURCES_DIR / "maps"
CAR_RENDER_DIR: Path = RESOURCES_DIR / "render"
MAP_DATA_FILE: Path = PROJECT_ROOT / "map_data.json"

PIXEL_FONT: Path = ASSETS_DIR / "pixel_font.ttf"
