# card.py

import pygame

class InteractiveCard:
    def __init__(self, x, y, pic,):

        self.width = self.button_text.get_width() + self.text_font * 3
        self.height = self.button_text.get_height() + self.text_font * 1.5

        self.x = x - self.width/2
        self.y = y - self.height/2

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.manager = manager

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_rect(self):
        return self.rect

    
    