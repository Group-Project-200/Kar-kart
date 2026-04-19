"""Stacker: pre-rotated, pre-scaled sprite stacks for a single car."""

from __future__ import annotations

import pygame


def _convert_for_display(surface: pygame.Surface) -> pygame.Surface:
    """Convert *surface* to the display's pixel format if one is available."""
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert_alpha()


class Stacker:
    """Caches rotated copies of a car sprite stack for cheap per-frame blits."""

    def __init__(self, image_stack: list[pygame.Surface], directions: int) -> None:
        self.images = image_stack              # Original unscaled images.
        self.scaled_img: list[pygame.Surface] = []
        self.dirs = directions
        self.scale: float | None = None
        self.rotated_cache: list[list[pygame.Surface]] | None = None
        self.mask_cache: list[pygame.mask.Mask] | None = None

    def scale_update(self, scale: float) -> None:
        """Re-scale and rebuild the rotated cache for the new *scale* factor."""
        self.scale = scale
        self._scale_images()
        self._build_rotated_cache()

    def _scale_images(self) -> None:
        self.scaled_img = []
        if self.scale == 1.0:
            self.scaled_img = [_convert_for_display(img) for img in self.images]
            return

        for img in self.images:
            width = max(1, int(img.get_width() * self.scale))
            height = max(1, int(img.get_height() * self.scale))
            scaled = pygame.transform.scale(img, (width, height))
            self.scaled_img.append(_convert_for_display(scaled))

    def _build_rotated_cache(self) -> None:
        step_deg = 360 / self.dirs
        self.rotated_cache = [
            [_convert_for_display(pygame.transform.rotate(img, d * step_deg)) for img in self.scaled_img]
            for d in range(self.dirs)
        ]
        # One mask per heading, taken from the bottom slice (the car's footprint).
        self.mask_cache = [
            pygame.mask.from_surface(frame_list[0]) for frame_list in self.rotated_cache
        ]

    def render_stack(
        self, display: pygame.Surface, dir_idx: int, pos: tuple[int, int], spread: float,
    ) -> None:
        """Blit the rotated stack centred at *pos* with a *spread*-pixel vertical offset."""
        assert self.rotated_cache is not None, "Call scale_update() first"
        x, y = pos
        for i, img in enumerate(self.rotated_cache[dir_idx]):
            display.blit(
                img, (x - img.get_width() // 2, y - img.get_height() // 2 + i * spread),
            )
