import pygame
from dataclasses import dataclass


DEFAULT_DIRS = 36


@dataclass(frozen=True, slots=True)
class MapCache:
    surface: pygame.Surface
    zoom: float
    center_x: int
    center_y: int


def _convert_for_display(surface: pygame.Surface) -> pygame.Surface:
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert_alpha()


def clamp_scale(scale: float) -> float:
    return max(0.1, min(scale, 1.0))


def snap_degrees(deg: float, dirs: int = DEFAULT_DIRS) -> int:
    step = 360.0 / dirs
    return int((deg % 360.0) / step + 0.5) % dirs


def build_rotated_cache(images, dirs: int = DEFAULT_DIRS):
    step_deg = 360 / dirs
    return [
        [_convert_for_display(pygame.transform.rotate(img, d * step_deg)) for img in images]
        for d in range(dirs)
    ]


def scale_images(images, scale: float):
    if scale == 1.0:
        return [_convert_for_display(img) for img in images]

    scaled_images = []
    for img in images:
        width = max(1, int(img.get_width() * scale))
        height = max(1, int(img.get_height() * scale))
        scaled = pygame.transform.scale(img, (width, height))
        scaled_images.append(_convert_for_display(scaled))
    return scaled_images


def build_world_scales(
    screen_height: int,
    reference_height: int,
    base_map_zoom: float,
    base_car_scale: float,
) -> tuple[float, float]:
    height_scale = screen_height / reference_height
    map_zoom = base_map_zoom * height_scale
    car_scale = base_car_scale * height_scale
    return map_zoom, car_scale


def build_pixel_surface_size(screen_size: tuple[int, int], pixelation_scale: float) -> tuple[int, int]:
    scale = clamp_scale(pixelation_scale)
    screen_width, screen_height = screen_size
    pixel_width = max(1, int(screen_width * scale))
    pixel_height = max(1, int(screen_height * scale))
    return pixel_width, pixel_height


def build_map_cache(map_surface: pygame.Surface | None, zoom: float) -> MapCache | None:
    if map_surface is None:
        return None

    map_width, map_height = map_surface.get_size()
    zoomed_size = (
        max(1, int(map_width * zoom)),
        max(1, int(map_height * zoom)),
    )
    zoomed_map = _convert_for_display(pygame.transform.scale(map_surface, zoomed_size))
    return MapCache(
        surface=zoomed_map,
        zoom=zoom,
        center_x=zoomed_size[0] // 2,
        center_y=zoomed_size[1] // 2,
    )


def draw_map(display, map_cache: MapCache | None, car_x, car_y, center, view_size):
    if map_cache is None:
        return

    car_map_x = map_cache.center_x + int(car_x * map_cache.zoom)
    car_map_y = map_cache.center_y + int(car_y * map_cache.zoom)

    view_x = car_map_x - center[0]
    view_y = car_map_y - center[1]
    view_width, view_height = view_size
    display.blit(map_cache.surface, (0, 0), area=(view_x, view_y, view_width, view_height))


def render_stack(display, rotated_slices, pos, spread: int):
    x, y = pos
    for i, img in enumerate(rotated_slices):
        display.blit(
            img,
            (x - img.get_width() // 2, y - img.get_height() // 2 + i * spread),
        )


def present_frame(
    screen,
    frame_surface: pygame.Surface,
    screen_size: tuple[int, int],
    needs_scale: bool,
):
    if not needs_scale:
        screen.blit(frame_surface, (0, 0))
        return

    pygame.transform.scale(frame_surface, screen_size, screen)
