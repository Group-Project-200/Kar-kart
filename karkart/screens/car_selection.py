"""Kar-Kart car selection screen.

This file implements the screen where the player chooses which car to drive.

In the game flow:
- Start -> choose mode -> this screen (choose car) -> choose track -> gameplay.

What the player does here:
- LEFT / RIGHT: switch between the available cars.
- ENTER: confirm the highlighted car.
- DOWN: go to the back button (to return to mode selection).

What the program does:
- Shows a rotating preview of the car (so you can see it from different angles).
- Shows a pre-made stats image for the currently highlighted car.
- Saves the chosen car in shared state (`app_data`) so the next screens can use it.
"""

from __future__ import annotations

import pygame

from karkart.constants import Colors, ScreenPositions as sp
from karkart.ui.help_icon import HelpIcon
from karkart.settings import Keys as K
from karkart.paths import CAR_RENDER_DIR, PICTURES_DIR, PIXEL_FONT
from karkart.rendering.preview import (
    RenderSetup,
    build_render_pipeline,
    render_preview_debug_frame,
)
from karkart.screens.screen_object import Screen
from karkart.ui import BackButton, SettingsIcon


class CarScreen(Screen):
    """Screen where the player selects the car they want to race with."""

    PREVIEW_SIZE = (600, 450)
    STATBOX_SIZE = (600, 400)

    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)
        self.back_button = BackButton(self.manager, "race_selector")
        self.back_selected = False

        # self.x = 0
        # self.y = 0

        # self.width = sp.WIDTH
        # self.height = sp.HEIGHT

        self.background = pygame.transform.scale(
            pygame.image.load(str(PICTURES_DIR / "cust1.png")).convert(),
            (self.width, self.height),
        )

        # We sort the car names so the order is always the same for the player.
        self.car_names = sorted(self.manager.app_data.cars.keys())

        # Each car has a pre-made PNG "stats card". We load and scale them once,
        # then simply blit the correct one during draw().
        self.loaded_statboxes = [
            pygame.transform.scale(
                pygame.image.load(
                    str(
                        PICTURES_DIR
                        / "statsboxes"
                        / f"{car_name.replace('_', '')}_stats.png"
                    )
                ).convert_alpha(),
                self.STATBOX_SIZE,
            )
            for car_name in self.car_names
        ]

        # The preview renderer uses a stack of PNG slices for each car.
        self.car_slices = [self._load_car_slices(car_name) for car_name in self.car_names]

        # We build the render pipeline once per car in __init__ because it is
        # expensive. During the game loop, draw() can reuse it every frame.
        self.pipelines = [
            build_render_pipeline(
                screen_size=self.PREVIEW_SIZE,
                map_surface=None,
                image_stack=slices,
                setup=RenderSetup(map_zoom=1.0, car_zoom=9.0, pixelation_scale=1.0),
                dirs=36,
            )
            for slices in self.car_slices
        ]

        self.preview_angle: int = 0
        self.selected: int = 0

        self.settings_icon = SettingsIcon(self.manager, "car")
        self.help_icon = HelpIcon(self.manager, "car")

    @staticmethod
    def _load_car_slices(folder_name: str) -> list[pygame.Surface]:
        """Load the PNG slices for one car preview.

        Each car is stored in its own folder inside `CAR_RENDER_DIR`.
        We load all `.png` files, sort them, and return them as a list.
        """
        folder = CAR_RENDER_DIR / folder_name
        return [
            pygame.image.load(str(p)).convert_alpha()
            for p in sorted(folder.iterdir())
            if p.suffix.lower() == ".png"
        ]

    def handle_event(self, event) -> None:
        """Handle keyboard controls on the car selection screen."""

        if event.type != pygame.KEYDOWN:
            return

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)

        # When the back button is selected, we do not want LEFT/RIGHT to change cars.
        # Instead, ENTER activates the back button and UP returns focus to the cars.
        if self.back_selected:
            if event.key == pygame.K_RETURN:

                self.back_selected = False
                self.back_button.unselect()
                self.back_button.handle_event(event)

            elif event.key == K.UP:
                self.back_selected = False
                self.back_button.unselect()

        else:
            if event.key == K.RIGHT:
                self.selected = (self.selected + 1) % len(self.car_slices)
            elif event.key == K.LEFT:
                self.selected = (self.selected - 1) % len(self.car_slices)
            elif event.key == K.DOWN:
                # Move focus from car browsing to the back button.
                self.back_selected = True
                self.back_button.select()
            elif event.key == pygame.K_RETURN:
                # Save the chosen car in shared app data so the next screens can use it.
                car_name = self.car_names[self.selected]
                self.manager.app_data.set_current_car(car_name)
                self.manager.change_screen("map")

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the full car selection screen (background + preview + UI)."""
        pygame.display.set_caption("Car Selection")

        surface.blit(self.background, (self.x, self.y))
        surface.blit(self.loaded_statboxes[self.selected], (770, 400))
        pipeline = self.pipelines[self.selected]

        # We increase the angle a little bit each frame to animate rotation.
        self.preview_angle = (self.preview_angle + 1) % 360

        preview_surface = pygame.Surface(self.PREVIEW_SIZE, pygame.SRCALPHA)
        render_preview_debug_frame(
            preview_surface,
            pipeline,
            car_rotation=self.preview_angle,
            stack_spread=-8,
        )
        preview_rect = preview_surface.get_rect(center=(sp.WIDTH // 2, sp.HEIGHT // 2))
        surface.blit(preview_surface, preview_rect)

        # Instruction banner: simple text inside a rectangle.
        font_size = 15
        instr_font = pygame.font.Font(str(PIXEL_FONT), font_size)
        instr_text = instr_font.render(
            "Select your car", True, Colors.WHITE
        )
        instr_center = instr_text.get_rect(center=(sp.CENTER_X, 100))

        instr_width = 400
        instr_height = instr_text.get_height() + font_size * 1.5
        instr_x = instr_center.x - (instr_width - instr_text.get_width()) / 2
        instr_y = instr_center.y - (instr_height - instr_text.get_height()) / 2
        instr_rect = pygame.Rect(instr_x, instr_y, instr_width, instr_height)

        pygame.draw.rect(surface, Colors.DARK_BLUE, instr_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.LIGHT_BLUE, instr_rect, 4, border_radius=8)
        pygame.draw.rect(surface, Colors.BLACK, instr_rect, 2, border_radius=8)
        surface.blit(instr_text, instr_center)

        self.help_icon.draw(surface)
        self.back_button.draw(surface)
        self.settings_icon.draw(surface)

    def get_label(self) -> str:
        return self.label