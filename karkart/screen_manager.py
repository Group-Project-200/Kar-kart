"""The ``ScreenManager`` swaps the currently active screen and owns shared state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from karkart.app_data import AppData


class ScreenManager:
    """Registers screens by label and routes frame ticks to the active one."""

    def __init__(self, app_data: "AppData", screen_display: pygame.Surface) -> None:
        self.running: bool = True
        self.current: Any = None
        self.app_data = app_data
        self.screen_display = screen_display
        self.screens: dict[str, object] = {}

    def add_screen(self, label: str, screen: object) -> None:
        """Register *screen* under *label* so it can later be activated."""
        self.screens[label] = screen

    def change_screen(self, label: str) -> None:
        """Activate a previously registered screen."""
        self.current = self.screens[label]

    def get_screen(self):
        """Return the currently active screen."""
        return self.current

    def get_app_data(self) -> "AppData":
        return self.app_data

    def is_running(self) -> bool:
        return self.running

    def toggle_running(self) -> None:
        """Flip the running flag (used to request a clean shutdown)."""
        self.running = not self.running
