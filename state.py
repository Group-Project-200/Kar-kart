print('''\nMOVED EVERYTHING TO:
         - main.py, 
         - start_screen.py,
         - car_selection_screen.py,
         - map_selection_screen.py\n''')


# import pygame
# import sys

# from UIobjects.button import Button
# from UIobjects.constants import Colors
# from UIobjects.constants import ScreenDimensions as sd

# # defining the screen and the clock used in the game loop
# pygame.init()
# clock = pygame.time.Clock()

# # put WIDTH and HEIGHT as constants
# screen = pygame.display.set_mode((sd.WIDTH, sd.HEIGHT))    # please if you change the screen add a comment to tell us




# #------- main function ---------
# def main():
#     #sets up the screen switcher
#     manager = ScreenManager()
#     manager.change_state(Screen1Structure(manager)) #start screen should be initialised here

#     # game loop
#     while manager.running:
#         events = pygame.event.get()

#         for event in events:
#             if event.type == pygame.QUIT:
#                 manager.running = False

#         #updates the event input
#         manager.state.handle_events(events)

#         #updates the screen
#         manager.state.update()

#         #draws the screen
#         manager.state.draw(screen)

#         pygame.display.update()

#         clock.tick(60)

#     pygame.quit()
#     sys.exit()



# if __name__ == "__main__":
#     main()