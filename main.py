import pygame, sys

from screen_manager import ScreenManager
from screens.start_screen import StartScreen
from constants import ScreenDimensions as sd

from screens.start_screen import StartScreen
from screens.car_selection_screen import CarScreen
from screens.map_selection_screen import MapScreen

# this import imports the file that contains the second example screen

# defining the screen and the clock used in the game loop
pygame.init()
clock = pygame.time.Clock()

<<<<<<< Updated upstream



def example_screen_function():
    #this opens a window with the color grey and names it
    pygame.display.set_caption("Kar Kart")
    screen.fill((30, 30, 30))

=======
# put WIDTH and HEIGHT as constants
screen = pygame.display.set_mode((sd.WIDTH, sd.HEIGHT))    # please if you change the screen add a comment to tell us
>>>>>>> Stashed changes


def main():

    # implemented a whole new system where there is:
    #  - a ScreenManager object, that records all screens in the program in a dictionary
    # that was done because importing a screen in multiple screens raises an ImportError

    # created a file per screen:
    # 1. implemented proper OOP programming practices
    # 2. easier to modify each screen individually

    # READ ScreenManager for the new functions i created (implementing encapsulation)
    # they do exactly the same as the original code but it just follows better practices

    manager = ScreenManager()

    manager.add_screen("start", StartScreen)
    manager.add_screen("car", CarScreen)
    manager.add_screen("map", MapScreen)

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