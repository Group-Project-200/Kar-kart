# car_customization_screen.py - screen to choose the map

import pygame

from ui.button import Button
from constants import Colors
from constants import ScreenPositions as sp

class CarScreen:
    def __init__(self, manager):
        self.manager = manager     # ALWAYS ADD THE MANAGER

        # initialize buttons  
        #* states will be changed to "map" and "start" when they're implemented
        self.next_btn = CarButton(560, 535, 150, 50, "NEXT", "map", self.manager)
        self.back_btn = CarButton(240, 535, 150, 50, "BACK", "start", self.manager)
        
        
        # load all images together
        self.background = pygame.transform.scale( pygame.image.load("cust1.png").convert(), (sp.WIDTH, sp.HEIGHT) )

        def load_car_slices(folder):
            files = sorted(os.listdir(folder))
            return [pygame.image.load(os.path.join(folder, f)).convert_alpha() for f in files]

        # load all cars from resources
        self.car_slices = [
            load_car_slices("resources/car_01"),
            load_car_slices("resources/car_02"),
            load_car_slices("resources/car_03"),
            load_car_slices("resources/car_04"),
        ]

        self.pipelines = []
        for slices in self.car_slices:
            pipeline = build_render_pipeline(
                screen_size=(600, 450),   # preview size
                map_surface=None,
                image_stack=slices,
                setup=RenderSetup(
                    map_zoom=1.0,
                    # car size
                    car_zoom=9.0,
                    pixelation_scale=1.0
                ),
                dirs=36
            )
            self.pipelines.append(pipeline)
        
        self.preview_angle = 0


        self.selected = 0  #default car



    def handle_event(self, event):  # use this template for the key detection

        # ask button1 to handle event
        
        self.button1.handle_event(event)

    def update(self): # add any other object here like the car class as well as its physics
        # example:
        # car.y += 5
        pass

    def draw(self, surface): # use this function to draw anything onto the screen
        
        # fill surface + call draw for all the objects inside

        pygame.display.set_caption("Kar Kart")

        surface.fill((0, 0, 175))

        self.button1.draw(surface)
