import pygame, sys

from screen_manager import ScreenManager
from constants import ScreenPositions as sp

from app_data import AppData


# defining the screen and the clock used in the game loop

pygame.init()

clock = pygame.time.Clock()


# put WIDTH and HEIGHT as constants

screen = pygame.display.set_mode((sp.WIDTH, sp.HEIGHT))    # please if you change the screen add a comment to tell us



def main():

    # implemented a whole new system where there is:
    #  - a ScreenManager object, that records all screens in the program in a dictionary
    # that was done because importing a screen in multiple screens raises an ImportError


    # created a file per screen:
    # 1. implemented proper OOP programming practices
    # 2. easier to modify each screen individually


    # READ ScreenManager for the new functions i created (implementing encapsulation)
    # they do exactly the same as the original code but it just follows better practices


    manager = ScreenManager(AppData())

    # add all the tracks to scrren manager
    # so that we upload them just once before the for-loop


    manager.change_screen("start")


    while manager.is_running():

        current = manager.get_screen()

        for event in pygame.event.get():

            # updates the event input
            # NEW: put handle_event inside the for-loop and changed the name from "handle_events"

            current.handle_event(event)

            if event.type == pygame.QUIT:
                manager.toggle_running()

        #updates the screen
        current.update()

        #draws the screen
        current.draw(screen)

        pygame.display.update()

        clock.tick(60)

    pygame.quit()
    sys.exit()




if __name__ == "__main__":
    main()