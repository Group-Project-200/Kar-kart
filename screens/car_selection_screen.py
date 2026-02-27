# car_customization_screen.py - screen to choose the map

import pygame

from ui.button import Button
from constants import Colors
from constants import ScreenDimensions as sd

class CarScreen:
    def __init__(self, manager):
        self.manager = manager     # ALWAYS ADD THE MANAGER

        
        #load all images together
        self.background = pygame.transform.scale( pygame.image.load("cust1.png").convert(), (sd.WIDTH, sd.HEIGHT) )

        self.car_images = [ 
            pygame.transform.scale(pygame.image.load("amv.png").convert_alpha(), (360, 183)), 
            pygame.transform.scale(pygame.image.load("ja.png").convert_alpha(), (360, 261)), 
            pygame.transform.scale(pygame.image.load("tm.png").convert_alpha(), (360, 129)), 
        ]

        self.selected = 0  #default car



    def handle_event(self, event):  # use this template for the key detection

        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_RIGHT: 
                self.selected = min(len(self.car_images) - 1, self.selected + 1) 
            elif event.key == pygame.K_LEFT: 
                self.selected = max(0, self.selected - 1) 
                
            # TO DO: go to map screen 
            # if 'next' button is clicked: 
                # self.manager.change_screen("map")

            # TO DO: go to start screen 
            # if 'back' button is clicked: 
                # self.manager.change_screen("start")

    def update(self): # add any other object here like the car class as well as its physics
        # example:
        # car.y += 5
        pass # no physics yet

    def draw(self, surface): # use this function to draw anything onto the screen
        # fill surface + call draw for all the objects inside

        pygame.display.set_caption("Car Selection")

        # draw background 
        surface.blit(self.background, (0, 0))

        # draw selected car in the center 
        car = self.car_images[self.selected] 
        x = sd.WIDTH // 2 - car.get_width() // 2 
        y = sd.HEIGHT // 2 - car.get_height() // 2 
        surface.blit(car, (x, y))


       













