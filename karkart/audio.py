"""audio.py - background music"""

import pygame
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MUSIC_PATHS = {
    "Music 1": os.path.join(BASE_DIR, "resources", "music", "backup_plan.wav"),
    "Music 2": os.path.join(BASE_DIR, "resources", "music", "asphalt.mp3"),
    "Music 3": os.path.join(BASE_DIR, "resources", "music", "10 - buffy - old fashion - outro party.mp3"),
}

class AudioManager:

    def initiate_music():
        """Initializes the global background music."""
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    @staticmethod
    def start_background_music(music_label: str = "Music 1"):
        AudioManager.initiate_music()
        try:
            pygame.mixer.music.load(MUSIC_PATHS[music_label])
            pygame.mixer.music.play(-1)
        except (pygame.error, KeyError):
            print(f"Error: Music '{music_label}' file not found")

    @staticmethod
    def stop_background_music():
        pygame.mixer.music.stop()        
