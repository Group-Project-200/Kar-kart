import pygame, sys

from screen_manager import ScreenManager
from constants import ScreenPositions as sp
from screens.start_screen import StartScreen
from screens.race_selection_screen import RaceSelector
from screens.car_selection_screen import CarScreen
from screens.map_selection_screen import MapScreen
from screens.gameplay_screen import GamePlay
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

    app_data = AppData()
    manager = ScreenManager(app_data)

    # add all the tracks to screen manager
    # so that we upload them just once before the for-loop
    manager.add_screen("start", StartScreen(manager))
    manager.add_screen("race_selector", RaceSelector(manager))   # ADD THIS
    manager.add_screen("car", CarScreen(manager))
    manager.add_screen("map", MapScreen(manager))
    manager.add_screen("game", GamePlay(manager, screen))

    manager.change_screen("start")


    while manager.running:

        current = manager.current

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