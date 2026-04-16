# car_selection_screen.py - screen to choose the car

# this file uses:
    # render.py(in game-engine)
    # cust1.png (background img)
    # resources(in game-engine) folder with car_01, car_02... folders which contain car layers img_0.png, img_1.png,...

# last changes made:
    # next button is removed, used 'enter' key instead
    # UI style is changed
    # Added title: "Select Your Car"

# TO-DO:
    # Names of each car below
    # Stats box for each car: Speed-


import pygame

from ui.button import ColorButton
from constants import ScreenPositions as sp

from render import build_render_pipeline, render_preview_debug_frame, RenderSetup
import os


class CarScreen:
    def __init__(self, manager ):
        self.manager = manager     # ALWAYS ADD THE MANAGER

        # initialize buttons  
        #* states will be changed to "map" and "start" when they're implemented
        #removed 'NEXT' button: self.next_btn = CarButton(560, 535, 150, 50, "NEXT →", "map", self.manager)
        self.back_btn = ColorButton(110, sp.H//1.35, 100, 50, "←", "start", self.manager, (254, 214, 30), (204, 219, 213))

        
        
        # load all images together
        self.background = pygame.transform.scale( pygame.image.load("resources/pictures/1cust1.png").convert(), (sp.WIDTH, sp.HEIGHT) )
        
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


        self.selected = 0  #default car

        # implement stats box change
        #car_stats = ["car01_stats", "car02_stats", "car03_stats", "car04_stats",]
        #blit car_stats[self.selected] 


    def handle_event(self, event):  # used for key detection

        # ask buttons to handle event        
        #removed next button: self.next_btn.handle_event(event)
        self.back_btn.handle_event(event)

        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_RIGHT: 
                self.selected = min(len(self.car_slices) - 1, self.selected + 1) 
            elif event.key == pygame.K_LEFT: 
                self.selected = max(0, self.selected - 1)
            elif event.key == pygame.K_RETURN:
                self.manager.change_screen("map")


    def update(self): # add any other object here like the car class as well as its physics
        # example:
        # car.y += 5
        pass # no physics yet

    def draw(self, surface): # use this function to draw anything onto the screen
        # fill surface + call draw for all the objects inside

        pygame.display.set_caption("Car Selection")

        # draw background 
        surface.blit(self.background, (0, 0))

        # draw stats box for car
        surface.blit(self.loaded_statboxes[self.selected], (770, 400))
        pipeline = self.pipelines[self.selected]

        # slowly rotate the preview
        self.preview_angle = (self.preview_angle + 1) % 360

        # center the preview of car 
        ## preview_surface = surface.subsurface(
        ##(sp.W//2, sp.H//2, sp.W//2, sp.H//2)
        ##)

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
        #removed next button: self.next_btn.draw(surface)
        self.back_btn.draw(surface)
       
