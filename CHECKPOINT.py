import pygame

class Checkpoint:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.passed = False

    def check(self, car_x, car_y):
        if self.rect.collidepoint(car_x, car_y):
            print("true")