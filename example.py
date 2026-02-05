import pygame
#this is the screen defined
screen = pygame.display.set_mode((800,600))

def example_screen_function():
    #this opens a window with the color red and names it
    pygame.display.set_caption("Kar Kart")
    screen.fill((255, 0, 0))