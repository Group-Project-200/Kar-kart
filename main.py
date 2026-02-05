import pygame
import sys

#this import imports the file that contains the second example screen
import example

#defining the screen and the clock used in the game loop
pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((800,600))    #please if you change the screen add a comment ot tell us




def example_screen_function():
    #this opens a window with the color grey and names it
    pygame.display.set_caption("Kar Kart")
    screen.fill((30, 30, 30))



def main():


    game_state = "start"
    running= True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


        if game_state == "start":
            example_screen_function()
        elif game_state == "test":
            example.example_screen_function()

        pygame.display.flip()

        clock.tick(60)
    pygame.quit()
    sys.exit()



if __name__ == "__main__":
    main()