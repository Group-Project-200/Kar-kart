# start_screen.py - first screen of the program
import pygame
import math

class StartScreen:
    def __init__(self, manager):
        self.manager = manager
        self.FPS = 60
        self.scroll = 0
        self.screen_width = 800
        self.screen_height = 600
        
        self.font = pygame.font.Font(None, 36)
        self.fps = 60.0
        self.frame_count = 0
        self.last_time = pygame.time.get_ticks()
        
        # Try to load background image, fallback to solid color if missing
        try:
            self.bg = pygame.image.load("bp2.png").convert()
            self.bg_width = self.bg.get_width()
        except:
            self.bg = None
            self.bg_width = self.screen_width
        self.tiles = math.ceil(self.screen_width / self.bg_width) + 1
        self.bg_rect = pygame.Rect(0, 0, self.bg_width, self.screen_height)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.manager.quit_game = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.manager.change_screen("car")

    def update(self):
        # Update scrolling background
        self.scroll -= 5
        if abs(self.scroll) > self.bg_width:
            self.scroll = 0
            
        # Manual FPS counter (no clock import needed)
        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time >= 1000:  # Update every second
            self.fps = round(self.frame_count * 1000 / (current_time - self.last_time), 1)
            self.frame_count = 0
            self.last_time = current_time

    def draw(self, surface):
        # Scroll background
        for i in range(0, self.tiles):
            x_pos = i * self.bg_width + self.scroll
            self.bg_rect.x = x_pos
            
            if self.bg:
                surface.blit(self.bg, (x_pos, 0))
            else:
                pygame.draw.rect(surface, (50, 100, 200), self.bg_rect)

        # Title text
        title_font = pygame.font.Font(None, 74)
        title = title_font.render("KAR KART", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width//2, self.screen_height//2))
        surface.blit(title, title_rect)
        
        # Instructions
        small_font = pygame.font.Font(None, 36)
        instr = small_font.render("Press SPACE to continue", True, (255, 255, 255))
        instr_rect = instr.get_rect(center=(self.screen_width//2, self.screen_height//2 + 100))
        surface.blit(instr, instr_rect)
        
        # FPS COUNTER
        fps_text = self.font.render(f"FPS: {self.fps}", True, (255, 255, 255))
        surface.blit(fps_text, (10, 10))

        pygame.display.set_caption(f"Kar Kart - Start Screen (FPS: {self.fps})")
