from __future__ import annotations

import pygame


def _convert_for_display(surface: pygame.Surface) -> pygame.Surface:

    if pygame.display.get_surface() is None:
        return surface
    return surface.convert_alpha()

"""this is the car renderer which stacks the images to give the "3D" effect """
class Stacker:

    _COLLISION_SCALE: float = 0.70

    def __init__(self, image_stack: list[pygame.Surface], directions: int) -> None:
        self.images = image_stack
        self.scaled_img: list[pygame.Surface] = []
        self.dirs = directions
        self.scale: float | None = None
        self.rotated_cache: list[list[pygame.Surface]] | None = None
        self.mask_cache: list[pygame.mask.Mask] | None = None

    def scale_update(self, scale: float) -> None:

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
    """it creates the car with the given directions and saves the result in the cache so the car's rotation positions 
    are already saved"""
    def _build_rotated_cache(self) -> None:
        step_deg = 360 / self.dirs
        self.rotated_cache = [
            [
                _convert_for_display(pygame.transform.rotate(img, d * step_deg))
                for img in self.scaled_img
            ]
            for d in range(self.dirs)
        ]

        self.mask_cache = []
        base = self.scaled_img[0]
        coll_w = max(1, int(base.get_width() * self._COLLISION_SCALE))
        coll_h = max(1, int(base.get_height() * self._COLLISION_SCALE))
        small_base = pygame.transform.scale(base, (coll_w, coll_h))
        for d in range(self.dirs):
            rotated_small = pygame.transform.rotate(small_base, d * step_deg)
            self.mask_cache.append(pygame.mask.from_surface(rotated_small))

    def set_images(self, image_stack: list[pygame.Surface]) -> None:
        self.images = image_stack
        if self.scale is not None:
            self._scale_images()
            self._build_rotated_cache()

    """this here draws it to the screen where it has the direction given by the renderer and draws the car by 
    each layer at a time. the spread is the space between the image slices that are being put on top of each other. """
    def render_stack(
        self,
        display: pygame.Surface,
        dir_idx: int,
        pos: tuple[int, int],
        spread: float,
        hop_offset_y: int = 0,
    ) -> None:

        assert self.rotated_cache is not None, "Call scale_update() first"
        x, y = pos
        y -= hop_offset_y
        for i, img in enumerate(self.rotated_cache[dir_idx]):
            display.blit(
                img,
                (x - img.get_width() // 2, y - img.get_height() // 2 + i * spread),
            )
