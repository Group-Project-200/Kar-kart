
import pygame

from constants import Colors

class Container:

    # groups multiple objects together

    # arguments:
    #  - central x (1) and y (2) coordinates
    #  - width (3) and height (4) of the container

    # add up to 16 objects to the container

    def __init__(self, center_x, center_y, width, height):

        self.width = width
        self.height = height

        self.x = center_x - self.width/2
        self.y = center_y - self.height/2

        self.objects = []

    def add_object(self, obj):

        # simply add an object (1) to the container

        self.objects.append(obj)

    def draw(self, surface):

        n = len(self.objects)

        if n >= 13:
            rows = 4
        elif n >= 9:
            rows = 3
        elif n >= 3:
            rows = 2
        elif n >= 1:
            rows = 1
        else:
            rows = 0
            return

        if n >= 7:
            columns = 4
        elif n >= 5:
            columns = 3
        elif n >= 2:
            columns = 2
        elif n == 1:
            columns = 1
        else:
            columns = 0

        if self.width/(2*columns) <= self.height/(2*rows)*2:
            width = self.width/(2*columns)
            height = width/2
        else:
            height = self.height/(2*rows)
            width = height/2

        i = 0
        for r in range(rows):
            if r >= rows-1:
                columns = n - (rows-1)*columns
            for c in range(columns):
                obj = self.objects[i]
                # print(f"Row: {r}, Column: {c}")

                obj_x = self.x + self.width/2 - width*(columns-1) + width*(c*2) - width/2
                obj_y = self.y + self.height/(rows*2)*(1+r*2) - height/2

                # card = pygame.Rect(obj_x, obj_y, width, height)
                # pygame.draw.rect(surface, Colors.BLUE, card)

                if type(obj) != str:
                    obj.draw(surface, obj_x, obj_y, width, height)

                i += 1

