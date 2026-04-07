import math
from dataclasses import dataclass
from CAMERA import Camera
import pygame

# Lightweight render-side state containers.
@dataclass(frozen=True, slots=True)
class MapCache:
    surface: pygame.Surface | None
    zoom: float | None
    center_x: int
    center_y: int


def _convert_opaque_for_display(surface: pygame.Surface) -> pygame.Surface:
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert()


class Map:
    def __init__(self, map_surface: pygame.Surface | None, view_size: tuple[int, int], camera: Camera):
        self.cache = None
        self.map_surface = map_surface
        self.view_size = view_size
        self.camera_buffer = None
        self.camera_buffer_center = None
        self.zoomed_map= None
        self.zoomed_size = None
        self.car = camera.car.physics
        self.camera = camera


    def zoom_fixing(self, zoom : float):
        map_width, map_height = self.map_surface.get_size()
        self.zoomed_size = (
            max(1, int(map_width * zoom)),
            max(1, int(map_height * zoom)),
        )
        self. zoomed_map = _convert_opaque_for_display(pygame.transform.scale(self.map_surface, self.zoomed_size))

        view_width, view_height = self.view_size
        # Use a diagonal-sized square so rotated corners never clip.
        side = max(1, int(math.ceil(math.hypot(view_width, view_height))) + 2)
        surface = pygame.Surface((side, side)).convert()
        self.camera_buffer = surface
        self.camera_buffer_center = (side // 2, side // 2)
        self.cache= MapCache(
            surface=self.zoomed_map,
            zoom= zoom,
            center_x=self.zoomed_size[0] // 2,
            center_y=self.zoomed_size[1] // 2, )

    # map class
    def draw_map(self, display):
  
        car_map_x = self.cache.center_x + int(self.car.car_x * self.cache.zoom)
        car_map_y = self.cache.center_y + int(self.car.car_y * self.cache.zoom)

        view_x = car_map_x - self.camera_buffer_center[0]
        view_y = car_map_y - self.camera_buffer_center[1]
        view_width, view_height = self.view_size
        display.blit(self.cache.surface, (0, 0), area=(view_x, view_y, view_width, view_height))

    def draw_map_camera(self, display: pygame.Surface,) -> None:
        # Fast path when camera is effectively unrotated.
        if abs(self.camera.angle) < 1e-4:
            self.draw_map(display)
            return

        self.camera_buffer.fill((0, 0, 0))
        self.draw_map( display = display)
        rotated_map = pygame.transform.rotate(self.camera_buffer, -self.camera.angle)
        rotated_rect = rotated_map.get_rect(center=self.camera_buffer_center)
        display.blit(rotated_map, rotated_rect)

