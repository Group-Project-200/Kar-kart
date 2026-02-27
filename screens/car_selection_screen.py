# car_customization_screen.py - screen to choose the map
# remove comments under ### 

import pygame

from ui.button import Button
from constants import Colors
from constants import ScreenDimensions as sd

class CarScreen:
    def __init__(self, manager):
        self.manager = manager     # ALWAYS ADD THE MANAGER

        ### initialize buttons
        #self.next_btn = Button(sd.CENTER_X, sd.CENTER_Y, 200, 75, "ORANGE", "NEXT", self.manager)
        #self.back_btn = Button(sd.CENTER_X, sd.CENTER_Y, 100, 50, "BACK", "map", self.manager)
        #self.settings_btn = Button(sd.CENTER_X, sd.CENTER_Y, 100, 50, "SETTINGS", "map", self.manager)
        
        #load all images together
        self.background = pygame.transform.scale( pygame.image.load("car_selection_images/cust1.png").convert(), (sd.WIDTH, sd.HEIGHT) )

        self.car_images = [ 
            pygame.transform.scale(pygame.image.load("car_selection_images/amv.png").convert_alpha(), (360, 183)), 
            pygame.transform.scale(pygame.image.load("car_selection_images/ja.png").convert_alpha(), (360, 261)), 
            pygame.transform.scale(pygame.image.load("car_selection_images/tm.png").convert_alpha(), (360, 129)), 
        ]

        self.selected = 0  #default car



    def handle_event(self, event):  # use this template for the key detection

        ### ask buttons to handle event        
        #self.next_btn.handle_event(event)
        #self.back_btn.handle_event(event)
        #self.settings_btn.handle_event(event)

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

        ### draw buttons
        #self.next_btn.draw(surface)
        #self.back_btn.draw(surface)
        #self.settings_btn.draw(surface)


# TO DO: 
    # 'back', 'next', and 'settings' buttons will be added.
       













