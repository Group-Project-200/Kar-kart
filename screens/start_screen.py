# start_screen.py - first screen of the program
import pygame, math, os

class StartScreen:
    def __init__(self, manager):
        self.manager = manager
        self.FPS = 60
        self.screen_width = 800
        self.screen_height = 600
        
        self.font = pygame.font.Font(None, 36)
        self.fps = 60.0
        self.frame_count = 0
        self.last_time = pygame.time.get_ticks()
        
        # Try to load background image, fallback to solid color if missing
        try:
            file_path = os.path.join(".", "resources", "pictures", "bp2.png")
            self.bg = pygame.image.load(file_path).convert()
            self.bg_width = self.bg.get_width()
        except:
            self.bg = None
            self.bg_width = self.screen_width

        try:
            self.gear_icon = pygame.image.load("gearicon3.png")
            self.gear_icon = pygame.transform.scale(self.gear_icon, (64, 64))
            self.gear_icon = self.gear_icon.convert_alpha()  # Essential for PNG transparency
        except:
            self.gear_icon = None



    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.manager.quit_game = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.manager.change_screen("race_selector")

    def update(self):
            
        # Manual FPS counter (no clock import needed)
        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time >= 1000:  # Update every second
            self.fps = round(self.frame_count * 1000 / (current_time - self.last_time), 1)
            self.frame_count = 0
            self.last_time = current_time

    def draw(self, surface):

            
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((50, 100, 200))
        

        # Gear Icon top right corner
        if self.gear_icon:
            gear_pos = (self.screen_width - 64 - 10, 10)
            surface.blit(self.gear_icon, gear_pos)

        pygame.display.set_caption(f"Kar Kart - Start Screen (FPS: {self.fps})")
