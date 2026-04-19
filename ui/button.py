# button.py - creates a button object to use throughout the whole code

import pygame

from constants import Colors
from constants import ScreenPositions as sp

class Button:

    # Button object is used to change screen and open pop-up's

    # initializing a Button object requires:
    #  - x (1) and y (2) coordinates
    #    (THEY ARE THE COORDINATES AT THE CENTRE, REALLY IMPORTANT!!!!)
    #  - width (3) and height (4) of the button
    #  - text (5) to print inside the button
    #  - state (6) that will be set after pushing the button
    #  - screen manager (7) to pass through states

    def __init__(self, x, y, width, height, text, state, manager):

        self.x = x - width/2
        self.y = y - height/2

        self.rect = pygame.Rect(self.x, self.y, width, height)

        self.width = width
        self.height = height

        self.text = text
        self.state = state

        self.manager = manager


    def handle_event(self, event):

        # handles each event
        # the following events are recorded:
        #  1. if the mouse is pressed on the button area, the new state is set

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.state:
                    self.manager.change_screen(self.state)


    def draw(self, surface):

        # draws the button and the text on the surface

        mouse_pos = pygame.mouse.get_pos()

        # hovering is managed underneath
        if self.rect.collidepoint(mouse_pos):
            color = Colors.WHITE    # hovering color
        else:
            color = Colors.GRAY     # NOT hovering color

        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        # button_center finds the center of the button but taking in consideration the 
        button_font = pygame.font.SysFont("arial", 20, bold=True)
        button_text = button_font.render(self.text, True, Colors.BLACK)
        button_center = button_text.get_rect(center=self.rect.center)

        # show the text at the center of the button
        surface.blit(button_text, button_center)


class PaddingButton:
    def __init__(self, text, state, manager):

        # works in a similar way as the button above, but following modifications were made:
        #  - takes text_font (3) instead of width and height
        #  - calculates automatic padding based on font

        self.text = text
        self.state = state
        self.manager = manager

        self.unselect()


    def handle_event(self, event):

        # handles each event
        # the following events are recorded:
        #  1. if the return button is pressed, the screen is changed

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.manager.change_screen(self.state)


    def draw(self, surface):

        # draws the button and the text on the surface

        font_size = 15

        button_font = pygame.font.Font("resources/assets/pixel_font.ttf", font_size)
        button_text = button_font.render(self.text, True, Colors.WHITE)
        button_center = button_text.get_rect(center=(sp.XLEFT, sp.XXXBOTTOM))

        button_width = button_text.get_width() + font_size * 3
        button_height = button_text.get_height() + font_size * 1.5

        button_x = button_center.x - (button_width - button_text.get_width()) / 2
        button_y = button_center.y - (button_height - button_text.get_height()) / 2
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        pygame.draw.rect(surface, self.inner_color, button_rect, border_radius=8)
        pygame.draw.rect(surface, self.color, button_rect, 4, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, button_rect, 2, border_radius=8)

        # button_center finds the center of the button but taking in consideration the 

        # show the text at the center of the button
        surface.blit(button_text, button_center)
        
    def unselect(self):
        self.color = Colors.LIGHT_BLUE
        self.inner_color = Colors.DARK_BLUE

    def select(self):
        self.color = Colors.RED
        self.inner_color = Colors.DARK_RED


class ColorButton:

    # Button Class is modified with 2 new parameters to ease the color selections of button

    # initializing a Button object requires:
    #  - x (1) and y (2) coordinates
    #    (THEY ARE THE COORDINATES AT THE CENTRE, REALLY IMPORTANT!!!!)
    #  - width (3) and height (4) of the button
    #  - text (5) to print inside the button
    #  - state (6) that will be set after pushing the button
    #  - screen manager (7) to pass through states
    #  - colnor (8) visible color of button
    #  - colhov (9) hovering color of button

    def __init__(self, x, y, width, height, text, state, manager, colnor, colhov):

        self.x = x - width/2
        self.y = y - height/2

        self.rect = pygame.Rect(self.x, self.y, width, height)

        self.width = width
        self.height = height

        self.text = text
        self.state = state

        self.manager = manager

        self.colnor = colnor
        self.colhov = colhov

        self.keyboard_hovered = False  # tracks keyboard hover state



    def handle_event(self, event):

        # handles each event
        # the following events are recorded:
        #  1. if the mouse is pressed on the button area, the new state is set

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.state:
                    self.manager.change_screen(self.state)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:                  # S key is used for hovering
                self.keyboard_hovered = not self.keyboard_hovered
            if event.key == pygame.K_RETURN:             # Enter clicks if hovered
                if self.keyboard_hovered and self.state:
                    self.manager.change_screen(self.state)

    def draw(self, surface):

        # draws the button and the text on the surface

        mouse_pos = pygame.mouse.get_pos()

        # hovering is managed underneath
        if self.rect.collidepoint(mouse_pos) or self.keyboard_hovered:
            color = self.colhov    # hovering color
        else:
            color = self.colnor     # NOT hovering color

        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        # button_center finds the center of the button but taking in consideration the 
        button_font = pygame.font.SysFont("arial", 20, bold=True)
        button_text = button_font.render(self.text, True, Colors.BLACK)
        button_center = button_text.get_rect(center=self.rect.center)

        # show the text at the center of the button
        surface.blit(button_text, button_center)
