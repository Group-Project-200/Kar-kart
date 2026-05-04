from __future__ import annotations

import pygame, json
from karkart.audio import AudioManager
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

    def __init__(self) -> None:

        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)

        # 1. Preference on keys
        self.bindings_label = data["bindings_label"]
        self.sound = data["sound"]
        self.music = data["music"]

        self.bindings = KEY_BINDINGS[self.bindings_label]

        self.all_bindings = list(KEY_BINDINGS.keys())
        self.all_sound = ["On", "Off"]
        self.all_music = ["Music 1", "Music 2", "Music 3"]

        
    def get_objects(self):
        bind_idx = self.all_bindings.index(self.bindings_label)
        self.all_bindings = self.all_bindings[bind_idx:] + self.all_bindings[:bind_idx]

        sound_idx = self.all_sound.index(self.sound)
        self.all_sound = self.all_sound[sound_idx:] + self.all_sound[:sound_idx]

        music_idx = self.all_music.index(self.music)
        self.all_music = self.all_music[music_idx:] + self.all_music[:music_idx]


        return {
            "Controls" : self.all_bindings,
            "Sound" : self.all_sound,
            "Music" : self.all_music}
        

    def save(self):
        data = {
            "bindings_label" : self.bindings_label,
            "sound" : self.sound,
            "music" : self.music
        }

        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f)


    # --------- Bindings ---------

    def set_bindings(self, label):
        self.bindings_label = label
        self.bindings = KEY_BINDINGS[self.bindings_label]

    def _get_key(self, key: str) -> pygame.key:
        return self.bindings[key]


    # ---------- Sound -----------
    
    def set_sound(self, label):
        if self.sound != label:
            self.sound = label
            
            if self.is_sound_active():
                AudioManager.start_background_music(self.music)
            else:
                AudioManager.stop_background_music()

    def is_sound_active(self) -> bool:
        return True if self.sound == "On" else False
    
    # ---------- Music -----------
    def set_music(self, label):
        if self.music != label:
            self.music = label
            if self.is_sound_active():
                AudioManager.start_background_music(self.music)
    
    def is_sound_active(self) -> bool:
        return self.sound == "On"


class _Keys:

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
