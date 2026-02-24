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
    FONT_TITLE = pygame.font.SysFont("arial", 64, bold=True)
    FONT_BTN = pygame.font.SysFont("arial",32)

    WHITE = (255, 255, 255)
    DARK = (20, 20, 30)
    BTN_COLOR = (70, 130, 180)
    BTN_HOVER = (100, 170, 220)

    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0] # if the left mouse click is pressed

    screen.fill(DARK)

    title_surf = FONT_TITLE.render("Kar Kart", True, WHITE)
    title_rect = title_surf.get_rect(center=(400, 180))
    screen.blit(title_surf, title_rect)

    play_btn_rect = pygame.Rect(0, 0, 220, 70)
    play_btn_rect.center = (400, 350)

    if play_btn_rect.collidepoint(mouse_pos):
        color = BTN_HOVER
    else:
        color = BTN_COLOR

    # Play Button - EVERYTHING STILL IN TESTS

    pygame.draw.rect(screen,color, play_btn_rect, border_radius= 12)

    play_surf = FONT_BTN.render("Play", True, WHITE)
    play_text_rect = play_surf.get_rect(center = play_btn_rect.center)
    screen.blit(play_surf, play_text_rect)

    if play_btn_rect.collidepoint(mouse_pos) and mouse_pressed:
        return "test"   # this will change the state to the test state, which is the example screen in example.py

    # Settings Button - EVERYTHING STILL IN TESTS

    settings_btn_rect = pygame.Rect(0, 0, 220, 70)
    settings_btn_rect.center = (400, 450) # under play button
    settings_color = BTN_HOVER if settings_btn_rect.collidepoint(mouse_pos) else BTN_COLOR
    
    pygame.draw.rect(screen, settings_color, settings_btn_rect, border_radius=12)

    settings_surf = FONT_BTN.render("Settings", True, WHITE)
    settings_text_rect = settings_surf.get_rect(center = settings_btn_rect.center)
    screen.blit(settings_surf, settings_text_rect)

    if settings_btn_rect.collidepoint(mouse_pos) and mouse_pressed:
        print("Settings!") # Temporary
        return "settings"   # this will change the state to the settings state

    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        return "test"
    
    return "start"


def main():


    game_state = "start"
    running= True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


        if game_state == "start":
            game_state =example_screen_function()
        elif game_state == "test":
            example.example_screen_function()

        pygame.display.flip()

        clock.tick(60)
    pygame.quit()
    sys.exit()



if __name__ == "__main__":
    main()