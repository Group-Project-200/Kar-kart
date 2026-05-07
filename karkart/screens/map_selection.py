from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR, PIXEL_FONT
from karkart.screens.gameplay import GamePlay
from karkart.ui import BackButton, MapCard, MapContainer, SettingsIcon
from karkart.ui.help_icon import HelpIcon


class MapScreen:

    def __init__(self, manager, label) -> None:
        self.manager = manager
        self.label = label

        self.container = MapContainer(
            sp.CENTER_X,
            sp.CENTER_Y,
            width=480,
            height=400,
            rows=2,
            columns=2,
        )
        self.back_button = BackButton(self.manager, "car")

        tracks = []
        for track in self.manager.get_app_data().get_tracks():
            track.set_dimensions(150, 150)
            tracks.append(MapCard(track, manager))
        self.container.add_objects(tracks)

        self.container.calculate_padding()
        self.container.add_back_button(self.back_button)

        self.background = pygame.transform.scale(
            pygame.image.load(str(PICTURES_DIR / "map_selection2.png")).convert(),
            (sp.WIDTH, sp.HEIGHT),
        )
        self.background.set_alpha(192)

        self.settings_icon = SettingsIcon(self.manager, "map")
        self.help_icon = HelpIcon(self.manager, "map")

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            print(x, y)

        if event.type != pygame.KEYDOWN:
            return None

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)
        selected_track = self.container.handle_event(event)
        if selected_track is not None:
            self.manager.get_app_data().set_current_map(selected_track)
            self.manager.add_screen(GamePlay(self.manager, "game"))
            self.manager.change_screen("game")

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Kar Kart")

        surface.fill(Colors.BLACK)
        surface.blit(self.background, (0, 0))

        font_size = 15
        instr_font = pygame.font.Font(str(PIXEL_FONT), font_size)
        instr_text = instr_font.render(
            "Select the track", True, Colors.WHITE
        )
        instr_center = instr_text.get_rect(center=(sp.CENTER_X, 100))

        instr_width = self.container.get_width() + 50
        instr_height = instr_text.get_height() + font_size * 1.5
        instr_x = instr_center.x - (instr_width - instr_text.get_width()) / 2
        instr_y = instr_center.y - (instr_height - instr_text.get_height()) / 2
        instr_rect = pygame.Rect(instr_x, instr_y, instr_width, instr_height)

        pygame.draw.rect(surface, Colors.DARK_BLUE, instr_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.LIGHT_BLUE, instr_rect, 4, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, instr_rect, 2, border_radius=8)
        surface.blit(instr_text, instr_center)

        self.help_icon.draw(surface)
        self.container.draw(surface)
        self.back_button.draw(surface)
        self.settings_icon.draw(surface)

    def get_label(self):
        return self.label