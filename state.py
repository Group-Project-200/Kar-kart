import pygame
import sys

from UIobjects.button import Button
from UIobjects.constants import Colors
from UIobjects.constants import ScreenDimensions as sd


# defining the screen and the clock used in the game loop
pygame.init()
clock = pygame.time.Clock()

# put WIDTH and HEIGHT as constants
screen = pygame.display.set_mode((sd.WIDTH, sd.HEIGHT))    # please if you change the screen add a comment to tell us


#------- Example screen 1 -----------
# FOR EACH CLASS USE THIS STRUCTURE
class Screen1Structure:
    def __init__(self, manager):
        self.manager = manager     # ALWAYS ADD THE MANAGER
        self.button1 = Button(sd.CENTER_X, sd.CENTER_Y, 100, 50, "Red", Screen2Structure, self.manager)

    def handle_events(self, events):  # use this template for the key detection

        # passes each event to button1 homonym function

        for event in events:
            self.button1.handle_event(event)

    def update(self): # add any other object here like the car class as well as its physics
        # example:
        # car.y += 5
        pass

    def draw(self, surface): # use this function to draw anything onto the screen
        
        # fill surface + call draw for all the objects inside

        pygame.display.set_caption("Kar Kart")

        surface.fill((0, 0, 175))

        self.button1.draw(surface)

        




#------- Example screen 2 ---------
class Screen2Structure:

    # follorw documentation in Screen1Structure

    def __init__(self, manager):
        self.manager = manager
        self.button1 = Button(sd.CENTER_X, sd.CENTER_Y, 100, 50, "Blue", Screen1Structure, self.manager)

    def handle_events(self, events):
        for event in events:
            self.button1.handle_event(event) # to change to another screen do take this line

    def update(self):
        pass

    def draw(self, surface):
        pygame.display.set_caption("Kar Kart")

        surface.fill((175, 0, 0))

        self.button1.draw(surface)


#-------- screen switcher class -----------

class ScreenManager:
    def __init__(self):
        self.running= True
        self.state = None

    def change_state(self, new_state):
        self.state = new_state



#------- main function ---------
def main():
    #sets up the screen switcher
    manager = ScreenManager()
    manager.change_state(Screen1Structure(manager)) #start screen should be initialised here

    # game loop
    while manager.running:
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                manager.running = False

        #updates the event input
        manager.state.handle_events(events)

        #updates the screen
        manager.state.update()

        #draws the screen
        manager.state.draw(screen)

        pygame.display.update()

        clock.tick(60)

    pygame.quit()
    sys.exit()



if __name__ == "__main__":
    main()