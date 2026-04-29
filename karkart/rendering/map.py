"""Zoomed world map, collision masks and checkpoint bookkeeping."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from karkart.physics.camera import Camera
from karkart.physics.checkpoint import Checkpoint


@dataclass(frozen=True, slots=True)
class MapCache:
    """Immutable snapshot of the zoomed map surface used as a blit source."""

    surface: pygame.Surface | None
    zoom: float | None
    center_x: int
    center_y: int


class MapData:
    """Static data about a single map (layers, checkpoints, finish line, start grid)."""

    checkpoints: list | None
    layers: list | None
    finish_line: list[int] | None


def _convert_opaque_for_display(surface: pygame.Surface) -> pygame.Surface:
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert()


def _simplify_surface(surface: pygame.Surface, factor: float = 1.5) -> pygame.Surface:
    """Downsample then upsample *surface* to build a coarser mask source."""
    w, h = surface.get_size()
    small = pygame.transform.scale(surface, (max(1, int(w // factor)), max(1, int(h // factor))))
    return pygame.transform.scale(small, (w, h))


class Map:
    """The playable world: zoomed terrain surface + collision masks + checkpoints."""

    def __init__(self, map_data: MapData, camera: Camera, world_objects: list | None = None) -> None:
        self.data = map_data
        self.camera = camera
        self.car = camera.car.physics

        self.map_surface: pygame.Surface = self.data.layers[0]

        self.world_objects = world_objects or []
        self.active = True

        # Everything below is populated by :meth:`zoom_fixing`.
        self.dimensions: tuple[int, int] | None = None
        self.cache: MapCache | None = None
        self.zoomed_map: pygame.Surface | None = None
        self.zoomed_size: tuple[int, int] | None = None
        self.zoomed_layers: list[pygame.Surface] | None = None
        self.masks: list[pygame.mask.Mask] | None = None
        self.camera_buffer: pygame.Surface | None = None
        self.camera_buffer_center: tuple[int, int] | None = None

        # Static checkpoint geometry (regular CPs followed by the finish line).
        # Per-racer progression state lives on :class:`RacerState` in
        # :mod:`karkart.physics.checkpoint`.
        self.checkpoints: list[Checkpoint] = []
        self.checkpoints_list: list[Checkpoint] = []
        self.finish_line: Checkpoint | None = None

        # Most recent world-space coordinates of the car, in map pixels.
        self.car_map_x: int | None = None
        self.car_map_y: int | None = None

    def zoom_fixing(self, zoom: float, view_size: tuple[int, int]) -> None:
        """Pre-bake every zoom-dependent surface, mask and checkpoint rect."""
        map_width, map_height = self.map_surface.get_size()
        self.dimensions = (map_width, map_height)
        self.zoomed_size = (max(1, int(map_width * zoom)), max(1, int(map_height * zoom)))

        self.zoomed_map = _convert_opaque_for_display(
            pygame.transform.scale(self.map_surface, self.zoomed_size),
        )

        self.zoomed_layers = [
            pygame.transform.scale(layer, self.zoomed_size) for layer in self.data.layers[1:]
        ]
        self.masks = [pygame.mask.from_surface(_simplify_surface(layer)) for layer in self.zoomed_layers]

        # Use a diagonal-sized square so rotated corners never clip.
        view_width, view_height = view_size
        side = max(1, int(math.ceil(math.hypot(view_width, view_height))) + 2)
        self.camera_buffer = pygame.Surface((side, side)).convert()
        self.camera_buffer_center = (side // 2, side // 2)

        self.cache = MapCache(
            surface=self.zoomed_map,
            zoom=zoom,
            center_x=self.zoomed_size[0] // 2,
            center_y=self.zoomed_size[1] // 2,
        )

        self.checkpoints = [
            Checkpoint(
                cp["x"] - self.dimensions[0] / 2,
                cp["y"] - self.dimensions[1] / 2,
                cp["w"], cp["h"],
            )
            for cp in self.data.checkpoints
        ]
        self.finish_line = Checkpoint(
            self.data.finish_line[0] - self.dimensions[0] / 2,
            self.data.finish_line[1] - self.dimensions[1] / 2,
            self.data.finish_line[2],
            self.data.finish_line[3],
        )
        # Finish line is last: all regular CPs must be hit in order first.
        self.checkpoints_list = [*self.checkpoints, self.finish_line]

    def get_coordinates(self) -> None:
        """Refresh :attr:`car_map_x`/``car_map_y`` from the car's world position."""
        assert self.cache is not None
        self.car_map_x = self.cache.center_x + int(self.car.car_x * self.cache.zoom)
        self.car_map_y = self.cache.center_y + int(self.car.car_y * self.cache.zoom)

    def draw_map(
        self,
        display: pygame.Surface,
        center: tuple[int, int],
        render_size: tuple[int, int],
        *,
        car_x: float,
        car_y: float,
    ) -> None:
        """Blit the zoomed map into *display* centred on (*car_x*, *car_y*)."""
        assert self.cache is not None
        car_map_x = self.cache.center_x + int(car_x * self.cache.zoom)
        car_map_y = self.cache.center_y + int(car_y * self.cache.zoom)
        self.car_map_x = car_map_x
        self.car_map_y = car_map_y

        view_x = car_map_x - center[0]
        view_y = car_map_y - center[1]
        view_width, view_height = render_size
        display.blit(self.cache.surface, (0, 0), area=(view_x, view_y, view_width, view_height))

    def draw_map_camera(
        self,
        display: pygame.Surface,
        center: tuple[int, int],
        render_size: tuple[int, int],
        *,
        car_x: float,
        car_y: float,
        camera_angle: float,
    ) -> None:
        """Draw the map with camera rotation applied (fast path when angle ~ 0)."""
        if abs(camera_angle) < 1e-4:
            self.draw_map(display, center, render_size, car_x=car_x, car_y=car_y)
            for obj in self.world_objects:
                obj.draw(display, center, car_x, car_y, self.cache.zoom)
            return

        assert self.camera_buffer is not None and self.camera_buffer_center is not None
        self.camera_buffer.fill((0, 0, 0))
        self.draw_map(
            self.camera_buffer, self.camera_buffer_center, self.camera_buffer.get_size(),
            car_x=car_x, car_y=car_y,
        )
        for obj in self.world_objects:
            obj.draw(self.camera_buffer, self.camera_buffer_center, car_x, car_y, self.cache.zoom)
        rotated_map = pygame.transform.rotate(self.camera_buffer, -camera_angle)
        rotated_rect = rotated_map.get_rect(center=center)
        display.blit(rotated_map, rotated_rect)

