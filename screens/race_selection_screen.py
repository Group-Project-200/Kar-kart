# race_selector.py - race selection screen
import pygame
import math


class RaceSelector:
    def __init__(self, manager):
        self.manager = manager
        self.FPS = 60
        self.scroll = 0
        self.screen_width = 1280
        self.screen_height = 720

        self.font = pygame.font.Font(None, 36)
        self.fps = 60.0
        self.frame_count = 0
        self.last_time = pygame.time.get_ticks()

        self.races = ["Time Trial", "Championship", "Quick Race"]
        self.selected_index = 0

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
            if event.key == pygame.K_LEFT:
                self.selected_index = (self.selected_index - 1) % len(self.races)
            elif event.key == pygame.K_RIGHT:
                self.selected_index = (self.selected_index + 1) % len(self.races)
            elif event.key == pygame.K_RETURN:
                self.manager.change_screen("game")
            elif event.key == pygame.K_ESCAPE:
                self.manager.change_screen("start")


    def update(self):
        self.scroll -= 2.5
        if abs(self.scroll) > self.bg_width:
            self.scroll = 0

        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time >= 1000:
            self.fps = round(self.frame_count * 1000 / (current_time - self.last_time), 1)
            self.frame_count = 0
            self.last_time = current_time


    def draw(self, surface):
        # Scrolling background
        for i in range(self.tiles):
            x_pos = i * self.bg_width + self.scroll
            self.bg_rect.x = x_pos
            if self.bg:
                surface.blit(self.bg, (x_pos, 0))
            else:
                pygame.draw.rect(surface, (50, 100, 200), self.bg_rect)

        # Dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        # Title
        title_font = pygame.font.Font(None, 74)
        title = title_font.render("SELECT RACE MODE", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, 180))
        surface.blit(title, title_rect)

        # Left arrow
        arrow_font = pygame.font.Font(None, 74)
        left_arrow = arrow_font.render("<", True, (255, 255, 255))
        surface.blit(left_arrow, (360, self.screen_height // 2 - 30))

        # Selected race mode
        option_font = pygame.font.Font(None, 64)
        label = option_font.render(self.races[self.selected_index], True, (255, 220, 0))
        label_rect = label.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        surface.blit(label, label_rect)

        # Right arrow
        right_arrow = arrow_font.render(">", True, (255, 255, 255))
        surface.blit(right_arrow, (self.screen_width - 400, self.screen_height // 2 - 30))

        # Instructions
        small_font = pygame.font.Font(None, 36)
        instr = small_font.render("LEFT / RIGHT to browse   ENTER to confirm   ESC to go back", True, (180, 180, 180))
        instr_rect = instr.get_rect(center=(self.screen_width // 2, self.screen_height - 60))
        surface.blit(instr, instr_rect)

        # FPS counter
        fps_text = self.font.render(f"FPS: {self.fps}", True, (255, 255, 255))
        surface.blit(fps_text, (10, 10))

        pygame.display.set_caption(f"Kar Kart - Race Selector (FPS: {self.fps})")