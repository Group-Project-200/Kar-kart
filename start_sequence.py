import time
import pygame


class StartSequence:
    def __init__(self, screen):
        self.seconds = 6
        self.screen= screen
        self.screen_dimensions = screen.get_size()
        self.font= pygame.font.Font(None, 400)
        self.complete = False


    def write(self):
        text_surface = self.font.render(str(self.seconds), True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.screen_dimensions[0] // 2, self.screen_dimensions[1] // 2))
        self.screen.blit(text_surface, text_rect)

