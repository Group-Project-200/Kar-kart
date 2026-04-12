
import pygame, logging

from constants import Colors

logger = logging.getLogger("container")
logging.basicConfig(level=logging.CRITICAL, format= ' %(levelname)s - %(message)s')


class Container:

    # groups multiple objects together

    # arguments:
    #  - central x (1) and y (2) coordinates
    #  - width (3) and height (4) of the container
    #  - rows (5) and columns (6) of the container
    #  - first (7) part of the container to fill (either "rows" or "columns")

    # add up to 16 objects to the container

    def __init__(self, center_x, center_y, width, height, rows, columns, first="rows"):

        self.width = width
        self.height = height

        self.x = center_x - self.width/2
        self.y = center_y - self.height/2

        self.rows = rows
        self.columns = columns

        self.first = first

        self.objects = []

    def add_object(self, obj):

        # simply add an object (1) to the container
        # OBJECTS MUST HAVE WIDTH AND HEIGHT ATTRIBUTES

        self.objects.append(obj)

    def draw(self, surface):

        n = len(self.objects)
        logger.debug(n)

        # records which elements of self.objects will create the first row and column, AND
        # which is the order of creation (either rows or columns)
        # depending on self.first (if "rows" or "columns")

        if self.first == "rows":
            first_row = self.objects[:self.rows]
            first_column = self.objects[::self.rows]

            first = self.rows
            second = self.columns
        
        elif self.first == "columns":
            first_row = self.objects[::self.rows]
            first_column = self.objects[:self.rows]

            first = self.columns
            second = self.rows

        try:

            # calculate padding based on:
            # + the toal dimension of the container
            # - sum of the dimension of all the objects in first_row or first_column
            # / columns OR rows + 1 (one more space after the last object)

            padding_x = (self.width - sum(obj.get_width() for obj in first_row)) / (self.columns + 1) 
            padding_y = (self.height - sum(obj.get_height() for obj in first_column)) / (self.rows + 1)

        except Exception as e:

            # if an object doesn't have WIDTH and HEIGHT, OR
            # if an object doesn't implement GET_WIDTH() and GET_HEIGHT()

            raise TypeError("The object added doesn't have width and height OR doesn't implement get_width() and get_height()")

        logging.info(f"The size of the container is {self.width, self.height}")
        logging.info(f"Padding is {padding_x, padding_y}")

        # first x and y coordinates of the first object
        curr_x, curr_y = self.x + padding_x, self.y + padding_y

        i = 0

        for f in range(first):

            # if the last column/row don't have the same number of objects as the others,
            # the number is adjusted
            if f >= first-1:
                second = n - (first-1)*second

            for s in range(second):
                obj = self.objects[i]

                logging.info(f"OBJECT: {i+1}, {curr_x, curr_y}")

                # draw an object
                obj.draw(surface, curr_x, curr_y)

                # adjust coordinates for next object
                if self.first == "rows":
                    curr_x += obj.get_width() + padding_x
                else:
                    curr_y += obj.get_height() + padding_y

                i += 1

            # adjust coordinates for next row/column
            if self.first == "columns":
                curr_x += obj.get_width() + padding_x
                curr_y = self.y + padding_y
            else:
                curr_x = self.x + padding_x
                curr_y += obj.get_height() + padding_y

