# car_selection_screen.py 

    # previous screen: "race_selector"  -> s and return keys
    # next screen: "map"                -> space key 

import pygame

from constants import Keys
from ui.button import ColorButton
from constants import ScreenPositions as sp

from render import build_render_pipeline, render_preview_debug_frame, RenderSetup
import os


class CarScreen:
    def __init__(self, manager):
        self.manager = manager     

        # initialize buttons  
        #* states will be changed to "map" and "start" when they're implemented
        self.back_btn = ColorButton(110, sp.H//1.35, 100, 50, "←", "race_selector", self.manager, (254, 214, 30), (204, 219, 213))
        
        # load all images together
        self.background = pygame.transform.scale( pygame.image.load("resources/pictures/cust1.png").convert(), (sp.WIDTH, sp.HEIGHT) )
        
        self.statbox_paths = [
            "resources/pictures/statsboxes/car01_stats.png", 
            "resources/pictures/statsboxes/car02_stats.png", 
            "resources/pictures/statsboxes/car03_stats.png", 
            "resources/pictures/statsboxes/car04_stats.png"
        ]
        
        self.loaded_statboxes = []
        for path in self.statbox_paths:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (600, 400))
            self.loaded_statboxes.append(img)

        def load_car_slices(folder):
            files = sorted(os.listdir(folder))
            return [pygame.image.load(os.path.join(folder, f)).convert_alpha() for f in files]

        # load all cars from resources
        self.car_slices = [
            load_car_slices("resources/render/car_01"),
            load_car_slices("resources/render/car_02"),
            load_car_slices("resources/render/car_03"),
            load_car_slices("resources/render/car_04"),
        ]

        self.pipelines = []
        for slices in self.car_slices:
            pipeline = build_render_pipeline(
                screen_size=(600, 450),   # preview size
                map_surface= None,
                image_stack= slices,
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

        self.selected = 0  # default car


    def handle_event(self, event):  # used for key detection

        # ask buttons to handle event        
        self.back_btn.handle_event(event)

        if event.type == pygame.KEYDOWN: 
            if event.key == Keys.RIGHT: 
                self.selected = min(len(self.car_slices) - 1, self.selected + 1) 
            elif event.key == Keys.LEFT: 
                self.selected = max(0, self.selected - 1)
            elif event.key == pygame.K_SPACE:

                # save selected car in app_data
                car_name = f"car_{self.selected+1:02d}"

                self.manager.app_data.current_car_name = car_name
                self.manager.app_data.current_car = self.manager.app_data.cars[car_name]

                # check if car selection is saved to app_data:
                # print("SELECTED CAR:", car_name)

                # go to map selection screen
                self.manager.change_screen("map")


    def update(self): 

        pass 

    def draw(self, surface): # this function draws on the screen

        pygame.display.set_caption("Car Selection")

        # draw background 
        surface.blit(self.background, (0, 0))

        # draw stats box for car
        surface.blit(self.loaded_statboxes[self.selected], (770, 400))
        pipeline = self.pipelines[self.selected]

        # slowly rotate the preview
        self.preview_angle = (self.preview_angle + 1) % 360

        # create a transparent surface matching the pipeline's screen_size (600x450)
        preview_surface = pygame.Surface((600, 450), pygame.SRCALPHA)

        render_preview_debug_frame(
            preview_surface,
            pipeline,
            car_rotation=self.preview_angle,
            stack_spread=-8  #arranges the thickness of the car view
        )

        # blit it centered on screen
        preview_rect = preview_surface.get_rect(center=(sp.WIDTH // 2, sp.HEIGHT // 2))
        surface.blit(preview_surface, preview_rect)

        # draw buttons
        self.back_btn.draw(surface)
       