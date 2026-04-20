import pygame

class PowerupRendering:
    def __init__(self, dimensions):
        self.mask = None
        self.x,self.y,self.w, self.h = dimensions
        self.active = True

    def build_mask(self, zoom: float) -> None:
        zw = max(1, int(self.w * zoom))
        zh = max(1, int(self.h * zoom))
        surf = pygame.Surface((zw, zh), pygame.SRCALPHA)
        surf.fill((255, 255, 255, 255))
        self.mask = pygame.mask.from_surface(surf)


    def draw(self, surface: pygame.Surface, center: tuple[int, int], car, zoom: float):
        if not self.active:
            return
        sx = center[0] + int((self.x - car.car_x) * zoom)
        sy = center[1] + int((self.y - car.car_y) * zoom)
        zw = max(1, int(self.w * zoom))
        zh = max(1, int(self.h * zoom))

        pygame.draw.rect(surface, (255, 0, 0), (sx, sy, zw, zh))




class PowerupsManager:
    def __init__(self, powerups):
        self.powerups: list = []