# track.py - track object to select

import pygame

from constants import Colors

class Track:

    # track object to select in the map_selection screen and to move to the game

    # arguments:
    #  - picture (1) of the track
    #  - name (2) of the the track
    #  - width (3) and height (4) of the picture

    def __init__(self, pic, name, corr_map=None):

        self.image = pygame.image.load(pic).convert_alpha()
        self.name = name

        self.map = corr_map

        self.width = 0
        self.height = 0

        self.x = None
        self.y = None

    def handle_event(self):
        pass

    def draw(self, surface):

        # process to scale pictures and draw them

        x, y = self.x, self.y

        scaled_img = pygame.transform.scale(self.image, (self.width, self.height))

        subsurf = pygame.Surface(scaled_img.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(subsurf, Colors.WHITE, subsurf.get_rect())

        scaled_img.blit(subsurf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(scaled_img, (x, y))

        bord_rect = pygame.Rect(x, y, self.width, self.height)
        pygame.draw.rect(surface, Colors.BLACK, bord_rect, 2)

    def get_width(self):

        # get width of the track picture

        return self.width

    def get_height(self):

        # get height of the track picture

        return self.height

    def get_image(self):
        
        # get track picture

        return self.image

    def get_name(self):

        return self.name

    def set_position(self, x, y):

        self.x, self.y = x, y

    def set_dimensions(self, width, height):

        # set dimensions, overwriting default (0, 0)

        self.width, self.height = width, height

    def get_map(self):
        return self.map
