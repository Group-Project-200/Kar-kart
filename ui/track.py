# track.py - track object to select

import pygame

class Track:

    # track object to select in the map_selection screen and to move to the game

    # arguments:
    #  - picture (1) of the track
    #  - name (2) of the the track

    def __init__(self, pic, name):

        self.pic = pic
        self.name = name

    def draw(self, surface, x, y, width, height):
        image = pygame.image.load(self.pic).convert_alpha()

        scaled_img = pygame.transform.scale(image, (width, height))

        surface.blit(scaled_img, (x, y))
