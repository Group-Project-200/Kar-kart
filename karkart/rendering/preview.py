from __future__ import annotations

from dataclasses import dataclass

import pygame

from karkart.helpers import clamp_scale, clamp_zoom


DEFAULT_DIRS = 36
PREVIEW_BG_COLOR = (0, 0, 0, 0)


@dataclass(frozen=True, slots=True)
class MapCache:
    surface: pygame.Surface
    zoom: float
    center_x: int
    center_y: int


@dataclass(frozen=True, slots=True)
class RenderSetup:
    map_zoom: float = 3.0
    car_zoom: float = 3.0
    pixelation_scale: float = 0.35


@dataclass(slots=True)
class RenderPipeline:
    frame_surface: pygame.Surface
    screen_size: tuple[int, int]
    render_size: tuple[int, int]
    center: tuple[int, int]
    needs_present_scale: bool
    map_cache: MapCache | None
    scaled_car_stack: list[pygame.Surface]
    rotated_cache: list[list[pygame.Surface]]
    camera_buffer: pygame.Surface
    camera_buffer_center: tuple[int, int]
    dirs: int


def _convert_for_display(surface: pygame.Surface) -> pygame.Surface:
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert_alpha()


def _convert_opaque_for_display(surface: pygame.Surface) -> pygame.Surface:
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert()


def _scale_images(images: list[pygame.Surface], scale: float) -> list[pygame.Surface]:
    if scale == 1.0:
        return [_convert_for_display(img) for img in images]
    scaled: list[pygame.Surface] = []
    for img in images:
        w = max(1, int(img.get_width() * scale))
        h = max(1, int(img.get_height() * scale))
        scaled.append(_convert_for_display(pygame.transform.scale(img, (w, h))))
    return scaled


def _build_rotated_cache(
    images: list[pygame.Surface],
    dirs: int = DEFAULT_DIRS,
) -> list[list[pygame.Surface]]:
    step_deg = 360 / dirs
    return [
        [
            _convert_for_display(pygame.transform.rotate(img, d * step_deg))
            for img in images
        ]
        for d in range(dirs)
    ]


def _build_pixel_surface_size(
    screen_size: tuple[int, int],
    pixelation_scale: float,
) -> tuple[int, int]:
    scale = clamp_scale(pixelation_scale)
    w, h = screen_size
    return max(1, int(w * scale)), max(1, int(h * scale))


def _build_map_cache(
    map_surface: pygame.Surface | None, zoom: float
) -> MapCache | None:
    if map_surface is None:
        return None
    map_w, map_h = map_surface.get_size()
    zoomed_size = (max(1, int(map_w * zoom)), max(1, int(map_h * zoom)))
    zoomed_map = _convert_opaque_for_display(
        pygame.transform.scale(map_surface, zoomed_size)
    )
    return MapCache(
        surface=zoomed_map,
        zoom=zoom,
        center_x=zoomed_size[0] // 2,
        center_y=zoomed_size[1] // 2,
    )


def _build_camera_buffer(
    view_size: tuple[int, int],
) -> tuple[pygame.Surface, tuple[int, int]]:
    import math

    w, h = view_size
    side = max(1, int(math.ceil(math.hypot(w, h))) + 2)
    return pygame.Surface((side, side)).convert(), (side // 2, side // 2)


def build_render_pipeline(
    *,
    screen_size: tuple[int, int],
    map_surface: pygame.Surface | None,
    image_stack: list[pygame.Surface],
    setup: RenderSetup,
    dirs: int = DEFAULT_DIRS,
) -> RenderPipeline:

    render_size = _build_pixel_surface_size(screen_size, setup.pixelation_scale)
    render_scale = render_size[1] / screen_size[1]
    needs_present_scale = render_size != screen_size
    center = (render_size[0] // 2, render_size[1] // 2)

    draw_map_zoom = clamp_zoom(setup.map_zoom) * render_scale
    draw_car_scale = clamp_zoom(setup.car_zoom) * render_scale

    frame_surface = pygame.Surface(render_size, pygame.SRCALPHA).convert_alpha()
    map_cache = _build_map_cache(map_surface, draw_map_zoom)
    scaled_car_stack = _scale_images(image_stack, draw_car_scale)
    rotated_cache = _build_rotated_cache(scaled_car_stack, dirs=dirs)
    camera_buffer, camera_buffer_center = _build_camera_buffer(render_size)

    return RenderPipeline(
        frame_surface=frame_surface,
        screen_size=screen_size,
        render_size=render_size,
        center=center,
        needs_present_scale=needs_present_scale,
        map_cache=map_cache,
        scaled_car_stack=scaled_car_stack,
        rotated_cache=rotated_cache,
        camera_buffer=camera_buffer,
        camera_buffer_center=camera_buffer_center,
        dirs=dirs,
    )


def _render_stack_smooth(
    display: pygame.Surface,
    source_slices: list[pygame.Surface],
    pos: tuple[int, int],
    spread: int,
    rotation_degrees: float,
) -> None:

    x, y = pos
    for i, img in enumerate(source_slices):
        rotated = pygame.transform.rotate(img, rotation_degrees)
        display.blit(
            rotated,
            (x - rotated.get_width() // 2, y - rotated.get_height() // 2 + i * spread),
        )


def _present_frame(
    screen: pygame.Surface,
    frame_surface: pygame.Surface,
    screen_size: tuple[int, int],
    needs_scale: bool,
) -> None:
    if not needs_scale:
        screen.blit(frame_surface, (0, 0))
        return
    pygame.transform.scale(frame_surface, screen_size, screen)


def render_preview_debug_frame(
    screen: pygame.Surface,
    pipeline: RenderPipeline,
    *,
    car_rotation: float,
    stack_spread: int,
) -> None:

    frame_surface = pipeline.frame_surface
    frame_surface.fill(PREVIEW_BG_COLOR)
    _render_stack_smooth(
        frame_surface,
        pipeline.scaled_car_stack,
        pipeline.center,
        stack_spread,
        car_rotation,
    )
    _present_frame(
        screen, frame_surface, pipeline.screen_size, pipeline.needs_present_scale
    )
