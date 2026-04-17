# map_customization_screen.py - screen to choose the map

import pygame, sys

from ui.button import PaddingButton as Button
from ui.container import MapContainer
from constants import Colors
from constants import ScreenPositions as sp
from ui.track import Track
from ui.card import MapCard

class MapScreen:

    # follow documentation in car_selection_screen.py

    def __init__(self, manager):
        self.manager = manager
        self.container1 = MapContainer(sp.CENTER_X, sp.CCCBOTTOM, sp.WIDTH/2, sp.HEIGHT/16*9, 3, 4)

        self.button = Button("Back", "car", self.manager)

        # importing tracks from manager

        app_data = self.manager.get_app_data()

        for track in app_data.get_tracks():

            # set dimensions of the track in advance
            track.set_dimensions(100, 80)
            self.container1.add_object(MapCard(track, manager))

        self.container1.add_back_button(self.button)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.manager.change_screen("game")

            # get map to show when objects are pressed
            curr_map = self.container1.handle_event(event)

            if curr_map:
                self.manager.get_app_data().set_current_map(curr_map)
                self.manager.change_screen("game")
        # to change to another screen do take this line
        # self.button1.handle_event(event)
        pass

    def update(self):
        pass

    def draw(self, surface):

        # draw background and introductory line

        pygame.display.set_caption("Kar Kart")

        surface.fill(Colors.BLACK)
        background = pygame.transform.scale(pygame.image.load("resources/pictures/map_selection2.png").convert(), (sp.WIDTH, sp.HEIGHT))
        background.set_alpha(192)
        surface.blit(background, (0,0))

        font_size = 15
        instr_font = pygame.font.Font("resources/assets/pixel_font.ttf", font_size)
        instr_text = instr_font.render("Select the track you want to race on", True, Colors.WHITE)
        instr_center = instr_text.get_rect(center=(sp.CENTER_X, sp.XTOP))

        instr_width = self.container1.get_width()
        instr_height = instr_text.get_height() + font_size * 1.5

        instr_x = instr_center.x - (instr_width - instr_text.get_width()) / 2
        instr_y = instr_center.y - (instr_height - instr_text.get_height()) / 2
        instr_rect = pygame.Rect(instr_x, instr_y, instr_width, instr_height)

        pygame.draw.rect(surface, Colors.DARK_BLUE, instr_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.LIGHT_BLUE, instr_rect, 4, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, instr_rect, 2, border_radius=8)
        surface.blit(instr_text, instr_center)

        self.container1.draw(surface)

        self.button.draw(surface)

