"""
screen_manager.py
--------
Handles screen changing and everything 
related to it throughout the system.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from karkart.app_data import AppData


class ScreenManager:
    """Store shared information across screens and transition between them"""

    def __init__(self, app_data: "AppData", screen_display: pygame.Surface) -> None:
        self.running: bool = True
        self.current: Any = None
        self.app_data = app_data
        self.screen_display = screen_display

        self.screens: dict[str, object] = {}
        self.stack = []

    def add_screen(self, screen: object) -> None:
        """Register *screen* under *label* so it can later be activated."""

        self.screens[screen.get_label()] = screen

    def change_screen(self, label: str) -> None:
        """Change current screen."""

        outgoing = self.current
        if outgoing is not None and hasattr(outgoing, "on_deactivate"):
            outgoing.on_deactivate()
        self.current = self.screens[label]
        if hasattr(self.current, "update_resources"):
            self.current.update_resources()
        if hasattr(self.current, "on_activate"):
            self.current.on_activate()

    def push_screen(self, label: str) -> None:
        """Push a new screen into stack to come back to it."""

        self.stack.append(label)

    def pop_screen(self) -> str:
        """Pop an old screen from stack."""

        self.current = self.screens[self.stack.pop()]
        if hasattr(self.current, "on_activate"):
            self.current.on_activate()
        return self.current.get_label()

    def get_screen(self) -> str:
        """Get name of current screen."""

        return self.current

    def get_prev_screen(self) -> str:
        """Get name of previous screen."""

        return self.stack[-1]

    def get_app_data(self) -> "AppData":
        """Get system app_data."""

        return self.app_data

    def is_running(self) -> bool:
        """Check if program is running."""

        return self.running

    def toggle_running(self) -> None:
        """Toggle running variable."""

        self.running = not self.running
