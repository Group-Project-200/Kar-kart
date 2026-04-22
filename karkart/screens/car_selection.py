"""Car picker with a spinning sprite-stack preview."""

from __future__ import annotations

import pygame

from karkart.constants import ScreenPositions as sp
from karkart.constants import Keys as K
from karkart.paths import CAR_RENDER_DIR, PICTURES_DIR
from karkart.rendering.preview import (
    RenderSetup,
    build_render_pipeline,
    render_preview_debug_frame,
)
from karkart.ui.button import PaddingButton


class CarScreen:
    """Press LEFT/RIGHT to cycle cars, RETURN to confirm, DOWN + RETURN for back button."""

    PREVIEW_SIZE = (600, 450)
    STATBOX_SIZE = (600, 400)

    def __init__(self, manager) -> None:
        self.manager = manager
        self.back_btn = PaddingButton("Back", "race_selector", self.manager)
        self.back_selected = False

        self.background = pygame.transform.scale(
            pygame.image.load(str(PICTURES_DIR / "cust1.png")).convert(),
            (sp.WIDTH, sp.HEIGHT),
        )

        self.loaded_statboxes = [
            pygame.transform.scale(
                pygame.image.load(str(PICTURES_DIR / "statsboxes" / name)).convert_alpha(),
                self.STATBOX_SIZE,
            )
            for name in (
                "car01_stats.png", "car02_stats.png", "car03_stats.png", "car04_stats.png",
            )
        ]

        self.car_slices = [self._load_car_slices(f"car_{i:02d}") for i in range(1, 5)]

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

        # Back button selected -> RETURN brings to map & UP brings back to selection.
        if self.back_selected:
            if event.key == pygame.K_RETURN:
                # Enter on Back returns to the previous screen via the button itself.
                self.back_selected = False
                self.back_btn.unselect()
                self.back_btn.handle_event(event)

            elif event.key == K.UP:
                self.back_selected = False
                self.back_btn.unselect()

        # Not selected -> selection is on & DOWN brings to BACK button
        else:
            if event.key == K.RIGHT:
                self.selected = min(len(self.car_slices) - 1, self.selected + 1)
            elif event.key == K.LEFT:
                self.selected = max(0, self.selected - 1)
            elif event.key == K.DOWN:
                self.back_selected = True
                self.back_btn.select()
            elif event.key == pygame.K_RETURN:
                car_name = f"car_{self.selected + 1:02d}"
                self.manager.app_data.set_current_car(car_name)
                self.manager.change_screen("map")

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Car Selection")

        surface.blit(self.background, (0, 0))
        surface.blit(self.loaded_statboxes[self.selected], (770, 400))
        pipeline = self.pipelines[self.selected]

        # Slowly rotate the preview.
        self.preview_angle = (self.preview_angle + 1) % 360

        # Render onto a transparent surface sized to the pipeline, then centre it.
        preview_surface = pygame.Surface(self.PREVIEW_SIZE, pygame.SRCALPHA)
        render_preview_debug_frame(
            preview_surface, pipeline,
            car_rotation=self.preview_angle,
            stack_spread=-8,  # Controls the apparent "thickness" of the stack.
        )
        preview_rect = preview_surface.get_rect(center=(sp.WIDTH // 2, sp.HEIGHT // 2))
        surface.blit(preview_surface, preview_rect)

        self.back_btn.draw(surface)
