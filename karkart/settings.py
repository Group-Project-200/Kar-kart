"""settings.py - these are the saved modifiable settings"""

from __future__ import annotations

import pygame

class Settings:

    """Contains all the settings that can be modified."""

    def __init__(self) -> None:
        self.key_bindings: {str:pygame.key} = {
            "up" : pygame.K_w,
            "down" : pygame.K_s,
            "left" : pygame.K_a,
            "right" : pygame.K_d
        }

    def get_key(self, key: str) -> pygame.key:
        return self.key_bindings[key]

    def set_arrows(self) -> None:
        self.key_bindings["up"] = pygame.K_UP
        self.key_bindings["down"] = pygame.K_DOWN
        self.key_bindings["left"] = pygame.K_LEFT
        self.key_bindings["right"] = pygame.K_RIGHT


class _Keys:
    """Keybindings. Change these to remap movement controls."""

    @property
    def UP(self):
        return settings.get_key("up")

    @property
    def DOWN(self):
        return settings.get_key("down")

    @property
    def LEFT(self):
        return settings.get_key("left")

    @property
    def RIGHT(self):
        return settings.get_key("right")

settings = Settings()
# settings.set_arrows()
Keys = _Keys()