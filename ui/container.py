
import pygame, logging

from constants import Colors
from constants import Keys as K

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


class SelectContainer:

    # TO SELECT AN OBJECT

    def __init__(self, center_x, center_y, width, height, rows, columns):

        self.width = width
        self.height = height

        self.x = center_x - self.width/2
        self.y = center_y - self.height/2

        self.rows = rows
        self.columns = columns

        self.objects = []

        self.selected = 0

    def add_object(self, obj):

        # simply add an object (1) to the container
        # OBJECTS MUST HAVE WIDTH AND HEIGHT ATTRIBUTES

        self.objects.append(obj)
        self.objects[self.selected].select()

        self.calculate_padding()

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:
            prev = self.selected
            if event.key == K.LEFT and self.selected % self.columns != 0:
                self.selected -= 1
            elif event.key == K.RIGHT and self.selected % self.columns != self.columns-1:
                self.selected += 1
            elif event.key == K.UP and self.selected // self.columns != 0:
                self.selected -= self.columns
            elif event.key == K.DOWN and self.selected // self.columns != self.rows-1:
                self.selected += self.columns
            else:
                return
            self.objects[prev].unselect()
            self.objects[self.selected].select()


    def draw(self, surface):

        # NOTE: ALWAYS CALL calculate_padding() AFTER ADDING ALL OBJECTS

        # TODO: REMOVE
        # example_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # pygame.draw.rect(surface, Colors.WHITE, example_rect, 2)

        n = len(self.objects)

        padding_x, padding_y = self.padding_x, self.padding_y


        first_row = self.objects[:self.columns]
        first_column = self.objects[::self.columns]

        rows, columns = self.rows, self.columns

    
        curr_x, curr_y = self.x, self.y

        i = 0

        for r in range(rows):

            # if the last column/row don't have the same number of objects as the others,
            # the number is adjusted
            if r >= rows-1:
                columns = n - (rows-1)*columns

            for c in range(columns):
                obj = self.objects[i]

                logging.info(f"OBJECT: {i+1}, {curr_x, curr_y}")

                # draw an object
                obj.set_position(curr_x, curr_y)
                obj.draw(surface)

                # adjust coordinates for next object
                curr_x += obj.get_width() + padding_x

                i += 1

            # adjust coordinates for next row/column
            # curr_x = self.x + padding_x
            curr_y += obj.get_height() + padding_y
            curr_x = self.x

    def get_width(self):
        return self.width

    def calculate_padding(self, x_center=False, y_center=False):
        n = len(self.objects)
        logger.debug(n)

        # records which elements of self.objects will create the first row and column, AND
        # which is the order of creation (either rows or columns)
        # depending on self.first (if "rows" or "columns")

        first_row = self.objects[:self.columns]
        first_column = self.objects[::self.columns]

        if x_center:
            self.padding_x = (self.width - sum(obj.get_width() for obj in first_row)) / (self.columns + 1)
            self.x += self.padding_x

        else:
            if self.columns > 1:
                self.padding_x = (self.width - sum(obj.get_width() for obj in first_row)) / (self.columns - 1)
            else:
                self.padding_x = 0

        if y_center:
            self.padding_y = (self.height - sum(obj.get_height() for obj in first_column)) / (self.rows + 1)
            self.y += self.padding_y

        else:
            if self.rows > 1:
                self.padding_y = (self.height - sum(obj.get_height() for obj in first_column)) / (self.rows - 1)
            else:
                self.padding_y = 0

class MapContainer(SelectContainer):

    # extending SelectContainer for map selection screen

    def __init__(self, center_x, center_y, width, height, rows, columns):
        super().__init__(center_x, center_y, width, height, rows, columns)
        self.back_button = None
        self.back_selected = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_RETURN:

                if not self.back_selected:

                    # if press return and BACK not selected, we're getting a map

                    return self.objects[self.selected].get_map()

                elif self.back_selected:

                    # if press return and BACK selected, we're pressing to go back to previous screen

                    self.selected = 0
                    self.back_selected = False
                    self.back_button.unselect()
                    self.objects[self.selected].select()

                    # goes back to car screen
                    self.back_button.handle_event(event)


            elif event.key == K.DOWN and self.selected // self.columns == self.rows-1 and not self.back_selected:

                # if we're in the last row, we click DOWN and go to the BACK button

                self.back_selected = True
                self.back_button.select()
                self.objects[self.selected].unselect()

            elif event.key == K.UP and self.back_selected:

                # if we're in the back button, we click UP and go to the object in the bottom left corner

                self.back_selected = False
                self.back_button.unselect()
                self.selected = self.columns*self.rows - self.columns
                self.objects[self.selected].select()

            elif not self.back_selected:

                # if any other button pressed and BACK not selected, we go to the other events

                super().handle_event(event)
                
    def add_back_button(self, button):

        # add a button to go back to the previous screen

        self.back_button = button