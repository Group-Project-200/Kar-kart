from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from karkart.app_data import AppData

class ScreenManager:

    def __init__(self, app_data: "AppData", screen_display: pygame.Surface) -> None:
        self.running: bool = True
        self.current: Any = None
        self.app_data = app_data
        self.screen_display = screen_display
        self.screens: dict[str, object] = {}

    def add_screen(self, label: str, screen: object) -> None:

        prior = self.screens.get(label)
        if prior is not None and hasattr(prior, "on_destroy"):
            prior.on_destroy()
        self.screens[label] = screen

    def change_screen(self, label: str) -> None:

        outgoing = self.current
        if outgoing is not None and hasattr(outgoing, "on_deactivate"):
            outgoing.on_deactivate()
        self.current = self.screens[label]
        if hasattr(self.current, "update_resources"):
            self.current.update_resources()

    def get_screen(self):

        return self.current

    def get_app_data(self) -> "AppData":
        return self.app_data

    def is_running(self) -> bool:
        return self.running

    def toggle_running(self) -> None:

        self.running = not self.running
