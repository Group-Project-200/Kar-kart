# button.py - creates a button object to use throughout the whole code

import pygame

from UIobjects.constants import Colors

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
                    self.manager.change_state(self.state(self.manager))


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