import pygame
import sys

from UIobjects.button import Button


#defining the screen and the clock used in the game loop
pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((800,600))    #please if you change the screen add a comment to tell us


#------- Example screen 1 -----------
#FOR EACH CLASS USE THIS STRUCTURE
class Screen1Structure:
    def __init__(self, manager):
        self.manager = manager     #ALWAYS ADD THE MANAGER

    def handle_events(self, events):  #use this template for the key detection
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.manager.change_state(Screen2Structure(self.manager))

    def update(self): #add any other object here like the car class as well as its physics
        #example:
        #car.y += 5
        pass

    def draw(self, screens): # use this function to draw anything onto the screen
        pygame.display.set_caption("Kar Kart")
        
        button = Button(50, 50, 100, 50, "Red", None)

        button.draw(screens)

        screens.fill((30, 30, 30))
        pass




#------- Example screen 2 ---------
class Screen2Structure:
    def __init__(self, manager):
        self.manager = manager
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.manager.change_state(Screen1Structure(self.manager)) #to change to another screen do take this line

    def update(self):
        pass


    def draw(self, screens):
        pygame.display.set_caption("Kar Kart")
        screens.fill((255, 0, 0))
        pass


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

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    sys.exit()



if __name__ == "__main__":
    main()