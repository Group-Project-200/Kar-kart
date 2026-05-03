"""settings.py - these are the saved modifiable settings"""

from __future__ import annotations

import pygame, json
from karkart.paths import SETTINGS_FILE

KEY_BINDINGS : {str :{str:pygame.key}} = {
            "WASD" : {
                "up" : pygame.K_w,
                "down" : pygame.K_s,
                "left" : pygame.K_a,
                "right" : pygame.K_d
            },
            "ARROWS" : {
                "up" : pygame.K_UP,
                "down" : pygame.K_DOWN,
                "left" : pygame.K_LEFT,
                "right" : pygame.K_RIGHT
            }
        }

class _Settings:

    """Contains all the settings that can be modified."""

    def __init__(self) -> None:

        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)

        # 1. Preference on keys
        self.bindings_label = data["bindings_label"]
        self.sound = data["sound"]

        self.bindings = KEY_BINDINGS[self.bindings_label]

        self.all_bindings = list(KEY_BINDINGS.keys())
        self.all_sound = ["On", "Off"]
        
    def get_objects(self):
        bind_idx = self.all_bindings.index(self.bindings_label)
        self.all_bindings = self.all_bindings[:bind_idx] + self.all_bindings[bind_idx:]

        sound_idx = self.all_sound.index(self.sound)
        self.all_sound = self.all_sound[:sound_idx] + self.all_sound[sound_idx:]

        return {
            "Controls" : self.all_bindings,
            "Sound" : self.all_sound}
        

    def save(self):
        data = {
            "bindings_label" : self.bindings_label,
            "sound" : self.sound
        }

        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f)


    # --------- Bindings ---------

    def set_bindings(self, label):
        self.bindings_label = label
        self.bindings = self.key_bindings[self.bindings_label]

    def _get_key(self, key: str) -> pygame.key:
        return self.bindings[key]


    # ---------- Sound -----------


class _Keys:
    """Keybindings. Change these to remap movement controls."""

    @property
    def UP(self):
        return settings._get_key("up")

    @property
    def DOWN(self):
        return settings._get_key("down")

    @property
    def LEFT(self):
        return settings._get_key("left")

    @property
    def RIGHT(self):
        return settings._get_key("right")

settings = _Settings()
Keys = _Keys()