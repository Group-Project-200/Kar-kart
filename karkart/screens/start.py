from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.paths import PICTURES_DIR
from karkart.screens.screen_object import Screen
from karkart.ui import TextCard
from karkart.ui.help_icon import HelpIcon
from karkart.ui.settings_icon import SettingsIcon


class StartScreen(Screen):

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        self.bg = self._try_load_image(PICTURES_DIR / "bp2.png", convert_alpha=False)

        self.settings_icon = SettingsIcon(self.manager, "start")
        self.help_icon = HelpIcon(self.manager, "start")

        self.start_card = TextCard(
            "PRESS ENTER TO START",
            width=560,
            height=72,
            font_size=18,
        )
        self.start_card.set_position(
            sp.CENTER_X - self.start_card.get_width() / 2,
            sp.HEIGHT - 120,
        )

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return None

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)

        if event.key == pygame.K_RETURN:
            self.manager.change_screen("race_selector")

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Kar Kart")

        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(Colors.BLACK)

        self.start_card.draw(surface)

        self.help_icon.draw(surface)
        self.settings_icon.draw(surface)

    @staticmethod
    def _try_load_image(path, *, convert_alpha: bool) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(path))
        except (FileNotFoundError, pygame.error):
            return None

        return image.convert_alpha() if convert_alpha else image.convert()

    def get_label(self):
        return self.label