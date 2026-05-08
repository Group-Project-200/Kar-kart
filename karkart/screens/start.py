"""Kar-Kart start screen.

This file implements the very first screen of the game.

What the player sees/does:
- A background image (title screen).
- A message that tells them to press ENTER.

What happens in the program:
- When the player presses ENTER, we switch to the next 
screen (`race_selector`), where they choose the game mode.
"""

import pygame
import time

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR, PIXEL_FONT
from karkart.screens.screen_object import Screen
from karkart.ui import TextCard, TextButton
from karkart.ui import HelpIcon, SettingsIcon


class StartScreen(Screen):
    """First screen shown when the game launches."""

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        # We try to load the background image. If it is missing, the game still
        # runs and we just draw a black background instead (so it won't crash).
        self.bg = self._try_load_image(PICTURES_DIR / "bp2.png", convert_alpha=False)

        self.settings_icon = SettingsIcon(self.manager, "start")
        self.help_icon = HelpIcon(self.manager, "start")

        # TextCard is a reusable UI widget. Here it is used as an on-screen
        # instruction so the player knows how to continue.
        self.start_card = TextCard(
            "PRESS ENTER TO START",
            width=560,
            height=72,
            font_size=18,
        )
        self.start_card.set_position(
            sp.CENTER_X - self.start_card.get_width() / 2,
            sp.XBOTTOM - self.start_card.get_height() / 2,
        )

        self.start_card.bord_2_thick = 15
        self.start_card.bord_thick = 5
        self.start_card.border_radius = 30

        self.time = time.time()

        self.help_card = TextCard("PRESS H FOR HELP", width=280, font_size=12)
        self.help_card.set_position(
            sp.CENTER_X - self.help_card.get_width() / 2,
            (sp.XXXBOTTOM + sp.XXBOTTOM)/2 - self.help_card.get_height() / 2,
        )

        self.help_font = pygame.font.Font(str(PIXEL_FONT), 12)

    def handle_event(self, event) -> None:
        """React to key presses on the start screen.

        The important input here is ENTER, which starts 
        the game flow by moving to the next screen.
        """
        if event.type != pygame.KEYDOWN:
            return None

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)

        if event.key == pygame.K_RETURN:
            # Move from the start screen to the mode selection screen.
            self.manager.change_screen("race_selector")

    def update(self) -> None:
        new_time = time.time()
        if new_time - self.time > 0.5:
            self.time = new_time
            if self.start_card.is_selected():
                self.start_card.unselect()
            else:
                self.start_card.select()

    def _draw_help_text(self, surface: pygame.Surface) -> None:
        text = "PRESS H FOR HELP"

        shadow = self.help_font.render(text, False, (25, 25, 25))
        label = self.help_font.render(text, False, Colors.WHITE)

        text_rect = label.get_rect(
            center=(
                sp.CENTER_X,
                sp.HEIGHT - 35,
            )
        )

        surface.blit(shadow, text_rect.move(2, 2))
        surface.blit(label, text_rect)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw everything visible on the start screen (background + UI)."""
        pygame.display.set_caption("Kar Kart")

        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(Colors.BLACK)

        self.start_card.draw(surface)
        self.help_card.draw(surface)
        # self._draw_help_text(surface)

        self.help_icon.draw(surface)
        self.settings_icon.draw(surface)

    @staticmethod
    def _try_load_image(path, *, convert_alpha: bool) -> pygame.Surface | None:
        """Load an image safely.

        We return None if the file cannot be loaded so the rest of the game can
        continue running (useful during development or if an asset is missing).
        """
        try:
            image = pygame.image.load(str(path))
        except (FileNotFoundError, pygame.error):
            return None

        return image.convert_alpha() if convert_alpha else image.convert()

    def get_label(self):
        return self.label