import pygame
import random
from karkart.powerups.powerup import SpeedBoost


class PowerupsManager:
    def __init__(self, player):
        self.powerups: list = [SpeedBoost(), SpeedBoost(),SpeedBoost()]
        self.current = None
        self.current_player = player
        self.active =True

    def choose_random_powerup(self):
        self.current = random.choice(self.powerups)
        return self.current

class PowerupRendering:
    def __init__(self, dimensions, powerups_manager: PowerupsManager):
        self.area = None
        self.x,self.y,self.w, self.h = dimensions
        self.active = True
        self.area = pygame.Rect(self.x,self.y,self.w,self.h)
        self.manager = powerups_manager

    def draw(self, surface: pygame.Surface, center: tuple[int, int], car_x: float, car_y: float, zoom: float):
        if not self.active:
            return
        sx = center[0] + int((self.x - car_x) * zoom)
        sy = center[1] + int((self.y - car_y) * zoom)
        zw = max(1, int(self.w * zoom))
        zh = max(1, int(self.h * zoom))

        pygame.draw.rect(surface, (255, 0, 0), (sx,sy,zw,zh))

    def check(self,car_x: float, car_y: float):
        collision= self.area.collidepoint(car_x, car_y)
        if not self.active:
            return False
        if collision:
            self.active = False
            return True
        return False





