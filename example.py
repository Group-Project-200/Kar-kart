import pygame
#this is the screen defined
screen = pygame.display.set_mode((800,600))

def example_screen_function():
    #this opens a window with the color red and names it
    pygame.display.set_caption("Kar Kart")
    screen.fill((50, 150, 50))

    font = pygame.font.SysFont("arial", 48)
    text = font.render("This is an example screen", True, (255, 255, 255))
    text_rect = text.get_rect(center=(400, 300))
    screen.blit(text, text_rect)

    return "test"