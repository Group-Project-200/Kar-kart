"""Kar-Kart entry point.

Run this file to launch the game::

    python main.py
"""

from __future__ import annotations

import sys

import pygame

from karkart.app_data import AppData
from karkart.constants import ScreenPositions as sp
from karkart.settings import settings
from karkart.screens.pop_up_menus import (
    ChampionshipQuitConfirmMenu,
    HelpMenu,
    PauseMenu,
    QuitConfirmMenu,
    SettingsMenu,
)
from karkart.screen_manager import ScreenManager
from karkart.screens.car_selection import CarScreen
from karkart.screens.map_selection import MapScreen
from karkart.screens.race_selection import RaceSelector
from karkart.screens.start import StartScreen
from karkart.screens.leaderboard import LeaderboardScreen
from karkart.audio import AudioManager


TARGET_FPS = 60
_FRAME_BUDGET_MS: float = 1000.0 / TARGET_FPS  # ≈ 16.67 ms


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((sp.WIDTH, sp.HEIGHT))
    clock = pygame.time.Clock()

    # Shared runtime state + router for swapping between screens.
    app_data = AppData()
    manager = ScreenManager(app_data, screen)

    # Register every screen up-front so they only load assets once.
    manager.add_screen(StartScreen(manager, "start"))
    manager.add_screen(SettingsMenu(manager, "settings"))
    manager.add_screen(HelpMenu(manager, "help"))
    manager.add_screen(RaceSelector(manager, "race_selector"))
    manager.add_screen(CarScreen(manager, "car"))
    manager.add_screen(MapScreen(manager, "map"))

    manager.add_screen(PauseMenu(manager, "pause"))
    manager.add_screen(QuitConfirmMenu(manager, "quit_confirm"))
    manager.add_screen(ChampionshipQuitConfirmMenu(manager, "championship_quit_confirm"))
    manager.add_screen(LeaderboardScreen(manager, "leaderboard"))

    manager.change_screen("start")

    AudioManager.initiate_music()

    if settings.is_sound_active():
        AudioManager.start_background_music(settings.music)

    # When a frame blows the 16.7 ms budget, the next tick holds the prior
    # image on screen instead of rendering again. Physics still updates, so
    # the car state is correct — only the visual is one frame stale.
    skip_next_render: bool = False

    while manager.is_running():
        current = manager.get_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                manager.toggle_running()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                manager.toggle_running()

            current.handle_event(event)

        current.update()

        if not skip_next_render:
            current.draw(screen)
            pygame.display.update()

        elapsed = clock.tick(TARGET_FPS)
        skip_next_render = elapsed > _FRAME_BUDGET_MS * 1.15

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
