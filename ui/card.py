# card.py

import pygame

from constants import ScreenPositions as sp
from constants import Colors

class Card:

    # interactive card

    def __init__(self, x, y, width, height):

        self.width = width
        self.height = height

        self.x = x - self.width/2
        self.y = y - self.height/2

        self.color = Colors.LIGHT_BLUE
        self.bord_color = Colors.BLACK
        self.border = 2

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_rect(self):
        return self.rect

    def draw(self, surface):

        # draw outer rectangle and border

        x, y = self.x, self.y
        width, height = self.width, self.height

        border = self.border

        back_rect = pygame.Rect(x, y, width, height)
        bord_back_rect = pygame.Rect(x-border, y-border, width+border*2, height+border*2)
        pygame.draw.rect(surface, self.color, back_rect, border_radius=8)
        pygame.draw.rect(surface, self.bord_color, back_rect, border, border_radius=8)

class MapCard(Card):

    # extending Card class to fulfill interaction in the map selection screen

    def __init__(self, track, manager):

        # position is (0, 0) by default and is modified later

        self.w, self.h = 120, 120

        super().__init__(0, 0, self.w, self.h)

        self.track = track
        self.manager = manager

        self.inner_color = Colors.DARK_BLUE

    def select(self):
        self.color = Colors.RED
        self.bord_color = Colors.BLACK
        self.inner_color = Colors.DARK_RED
        self.border = 2

    def unselect(self):
        self.color = Colors.LIGHT_BLUE
        self.bord_color = Colors.BLACK
        self.inner_color = Colors.DARK_BLUE
        self.border = 2

    def draw(self, surface):

        # draw inner rectangle, track and names

        super().draw(surface)
        self.track.draw(surface)
        
        name_rect = pygame.Rect(self.x + 10, self.y + 5, self.track.get_width(), 20)
        pygame.draw.rect(surface, self.inner_color, name_rect, border_radius=4)
        pygame.draw.rect(surface, self.bord_color, name_rect, 2, border_radius=4)

        name_font = pygame.font.Font("resources/assets/pixel_font.ttf", 9)
        name_text = name_font.render(self.track.get_name(), True, Colors.WHITE)
        name_center = name_text.get_rect(center=name_rect.center)

        surface.blit(name_text, name_center)

    def set_position(self, x, y):

        # set position of the card later

        track = self.track

        self.x = x
        self.y = y
        self.track.set_position(self.x + (self.width - track.get_width())/2, self.y + 30)

    def get_map(self):
        return self.track.get_map()
    