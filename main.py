"""Kar-Kart entry point.

Run this file to launch the game::

    python main.py
"""

from __future__ import annotations

import sys

import pygame

from karkart.app_data import AppData
from karkart.constants import ScreenPositions as sp
from karkart.screen_manager import ScreenManager
from karkart.screens.car_selection import CarScreen
from karkart.screens.gameplay import GamePlay
from karkart.screens.map_selection import MapScreen
from karkart.screens.race_selection import RaceSelector
from karkart.screens.start import StartScreen
from karkart.screens.pause_menu import PauseMenu


TARGET_FPS = 60


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((sp.WIDTH, sp.HEIGHT))
    clock = pygame.time.Clock()

    # Shared runtime state + router for swapping between screens.
    app_data = AppData()
    manager = ScreenManager(app_data, screen)

    # Register every screen up-front so they only load assets once.
    manager.add_screen("start", StartScreen(manager))
    manager.add_screen("race_selector", RaceSelector(manager))
    manager.add_screen("car", CarScreen(manager))
    manager.add_screen("map", MapScreen(manager))
    manager.add_screen("game", GamePlay(manager))
    manager.add_screen("pause", PauseMenu(manager))
    manager.change_screen("start")

    while manager.is_running():
        current = manager.get_screen()

        for event in pygame.event.get():
            current.handle_event(event)
            if event.type == pygame.QUIT:
                manager.toggle_running()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                manager.toggle_running()

        current.update()
        current.draw(screen)

        pygame.display.update()
        clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
