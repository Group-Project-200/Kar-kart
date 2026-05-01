from __future__ import annotations

import pygame

from karkart.constants import ScreenPositions as sp
from karkart.ui.help_icon import HelpIcon
from karkart.settings import Keys as K
from karkart.paths import CAR_RENDER_DIR, PICTURES_DIR
from karkart.rendering.preview import (
    RenderSetup,
    build_render_pipeline,
    render_preview_debug_frame,
)
from karkart.ui import Button, SettingsIcon


class CarScreen:

    PREVIEW_SIZE = (600, 450)
    STATBOX_SIZE = (600, 400)

    def __init__(self, manager) -> None:
        self.manager = manager
        self.back_btn = Button("Back", "race_selector", self.manager)
        self.back_selected = False

        self.background = pygame.transform.scale(
            pygame.image.load(str(PICTURES_DIR / "cust1.png")).convert(),
            (sp.WIDTH, sp.HEIGHT),
        )

        self.car_names = sorted(self.manager.app_data.cars.keys())

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

        self.car_slices = [self._load_car_slices(car_name) for car_name in self.car_names]

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
        folder = CAR_RENDER_DIR / folder_name
        return [
            pygame.image.load(str(p)).convert_alpha()
            for p in sorted(folder.iterdir())
            if p.suffix.lower() == ".png"
        ]

    def handle_event(self, event) -> None:

        if event.type != pygame.KEYDOWN:
            return

        self.help_icon.handle_event(event)
        self.settings_icon.handle_event(event)

        if self.back_selected:
            if event.key == pygame.K_RETURN:

                self.back_selected = False
                self.back_btn.unselect()
                self.back_btn.handle_event(event)

            elif event.key == K.UP:
                self.back_selected = False
                self.back_btn.unselect()

        else:
            if event.key == K.RIGHT:
                self.selected = min(len(self.car_slices) - 1, self.selected + 1)
            elif event.key == K.LEFT:
                self.selected = max(0, self.selected - 1)
            elif event.key == K.DOWN:
                self.back_selected = True
                self.back_btn.select()
            elif event.key == pygame.K_RETURN:
                car_name = self.car_names[self.selected]
                self.manager.app_data.set_current_car(car_name)
                self.manager.change_screen("map")

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Car Selection")

        surface.blit(self.background, (0, 0))
        surface.blit(self.loaded_statboxes[self.selected], (770, 400))
        pipeline = self.pipelines[self.selected]

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

        self.help_icon.draw(surface)
        self.back_btn.draw(surface)
        self.settings_icon.draw(surface)
