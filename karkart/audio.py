"""audio.py - background music"""

import pygame
import os

# get path to Kar-Kart folder (one level up from 'audio.py') to get resources/music/backup_plan.wav
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class AudioManager:
    @staticmethod
    def start_background_music():
        """Initializes and plays the global background music."""
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # build path starting in Kar-Kart directory
        music_path = os.path.join(BASE_DIR, "resources", "music", "backup_plan.wav")
        
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1) # -1 loops forever
        except pygame.error as e:
            print(f"Error: Music file not found")         

    @staticmethod
    # can be used to control volume (0.0 to 1.0) from settings later
    def set_volume(volume):
        pygame.mixer.music.set_volume(volume)