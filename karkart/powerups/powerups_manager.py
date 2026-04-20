import pygame

class PowerupRendering:
    def __init__(self, dimensions):
        self.area = None
        self.x,self.y,self.w, self.h = dimensions
        self.active = True
        self.area = pygame.Rect(self.x,self.y,self.w,self.h)



    def draw(self, surface: pygame.Surface, center: tuple[int, int], car, zoom: float):
        if not self.active:
            return
        sx = center[0] + int((self.x - car.car_x) * zoom)
        sy = center[1] + int((self.y - car.car_y) * zoom)
        zw = max(1, int(self.w * zoom))
        zh = max(1, int(self.h * zoom))

        pygame.draw.rect(surface, (255, 0, 0), (sx,sy,zw,zh))

    def check(self,car_x: float, car_y: float):
        return self.area.collidepoint(car_x, car_y)



class PowerupsManager:
    def __init__(self, powerups):
        self.powerups: list = []