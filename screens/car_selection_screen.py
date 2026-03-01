# car_selection_screen.py - screen to choose the car

# uses:
    # render.py(in game-engine)
    # cust1.png (background img)
    # resources(in game-engine) folder with car_01, car_02... folders which contain car layers img_0.png, img_1.png,...

# changes to make in render.py:
# to make the background of car preview transparent:
    # replace PREVIEW_DEBUG_BG_COLOR = (96, 96, 96) with PREVIEW_DEBUG_BG_COLOR = (0, 0, 0, 0)
    # replace frame_surface.fill(PREVIEW_DEBUG_BG_COLOR) with frame_surface.fill((0, 0, 0, 0)) 
    # change frame_surface = pygame.Surface(render_size).convert() with frame_surface = pygame.Surface(render_size, pygame.SRCALPHA).convert_alpha()

# TO ADD: settings button



import pygame

from ui.button import CarButton
from constants import Colors
from constants import ScreenDimensions as sd

from render import build_render_pipeline, render_preview_debug_frame, RenderSetup
import os


class CarScreen:
    def __init__(self, manager):
        self.manager = manager     # ALWAYS ADD THE MANAGER

        # initialize buttons  
        #* states will be changed to "map" and "start" when they're implemented
        self.next_btn = CarButton(560, 535, 150, 50, "NEXT", "car", self.manager)
        self.back_btn = CarButton(240, 535, 150, 50, "BACK", "car", self.manager)
        
        
        # load all images together
        self.background = pygame.transform.scale( pygame.image.load("cust1.png").convert(), (sd.WIDTH, sd.HEIGHT) )

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

        # ask buttons to handle event        
        self.next_btn.handle_event(event)
        self.back_btn.handle_event(event)

        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_RIGHT: 
                self.selected = min(len(self.car_slices) - 1, self.selected + 1) 
            elif event.key == pygame.K_LEFT: 
                self.selected = max(0, self.selected - 1) 


    def update(self): # add any other object here like the car class as well as its physics
        # example:
        # car.y += 5
        pass # no physics yet

    def draw(self, surface): # use this function to draw anything onto the screen
        # fill surface + call draw for all the objects inside

        pygame.display.set_caption("Car Selection")

        # draw background 
        surface.blit(self.background, (0, 0))

        pipeline = self.pipelines[self.selected]

        # slowly rotate the preview
        self.preview_angle = (self.preview_angle + 1) % 360

        # center the preview of car 
        preview_surface = surface.subsurface(
        (sd.WIDTH//2-300, sd.HEIGHT//2-225 , 600, 450)
        )


        render_preview_debug_frame(
            preview_surface,
            pipeline,
            car_rotation=self.preview_angle,
            stack_spread=1
        )


        # draw buttons
        self.next_btn.draw(surface)
        self.back_btn.draw(surface)
       













