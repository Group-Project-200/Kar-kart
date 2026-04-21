"""pause_menu.py - when game is paused, it appears"""

import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp

class PauseMenu:
    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        s = pygame.Surface((sp.WIDTH, sp.HEIGHT), pygame.SRCALPHA)

        s.fill((0, 0, 0, 120))

        s.blit(surface, (0, 0))

        pygame.draw.rect(surface, (255, 255, 255), (300, 200, 400, 200))