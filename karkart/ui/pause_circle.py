# pause circle

import pygame
from karkart.constants import Colors
from karkart.constants import ScreenPositions as sp

class PauseCircle:
    
    def __init__(self):
        self.radius = 30

        self.x = sp.XXRIGHT - self.radius / 2
        self.y = sp.XXTOP - self.radius / 2
        self.position = (self.x, self.y)

    def draw(self, surface):
        pygame.draw.circle(surface, Colors.WHITE, self.position, self.radius)