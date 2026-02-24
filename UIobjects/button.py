# button.py - creates a button object to use throughout the whole code

import pygame

class Button:
    def __init__(self, x, y, width, height, text, event):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.event = event

    def draw(self, surface):
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=8)