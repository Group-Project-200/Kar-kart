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
        """Register *screen* under *label*; replaces any prior screen.

        If a screen was already registered under *label*, give it a chance
        to clean up via ``on_destroy`` (e.g. tear down threads). Required
        because PauseMenu's "Restart" path overwrites ``"game"`` with a
        fresh ``GamePlay`` and the old instance's worker threads would
        otherwise keep running until process exit.
        """
        prior = self.screens.get(label)
        if prior is not None and hasattr(prior, "on_destroy"):
            prior.on_destroy()
        self.screens[label] = screen

    def change_screen(self, label: str) -> None:
        """Activate a previously registered screen.

        Calls ``on_deactivate`` on the outgoing screen (used by gameplay
        to pause its worker threads while a popup is open) and
        ``update_resources`` on the incoming one (used by gameplay to
        resume them).
        """
        outgoing = self.current
        if outgoing is not None and hasattr(outgoing, "on_deactivate"):
            outgoing.on_deactivate()
        self.current = self.screens[label]
        if hasattr(self.current, "update_resources"):
            self.current.update_resources()

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
