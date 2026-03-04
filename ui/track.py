# track.py - track object to select

import pygame

from constants import Colors

class Track:

    # track object to select in the map_selection screen and to move to the game

    # arguments:
    #  - picture (1) of the track
    #  - name (2) of the the track
    #  - width (3) and height (4) of the picture

    def __init__(self, pic, name, width, height):

        self.image = image = pygame.image.load(pic).convert_alpha()
        self.name = name

        self.width = width
        self.height = height

    def get_width(self):

        # get width of the track picture

        return self.width

    def get_height(self):

        # get height of the track picture

        return self.height

    def handle_event(self):
        pass

    def draw(self, surface, x, y):

        # process to scale pictures and draw them

        scaled_img = pygame.transform.scale(self.image, (self.width, self.height))

        subsurf = pygame.Surface(scaled_img.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(subsurf, Colors.WHITE, subsurf.get_rect(), border_radius=8)

        scaled_img.blit(subsurf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(scaled_img, (x, y))
