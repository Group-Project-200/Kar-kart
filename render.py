import math
from dataclasses import dataclass

import pygame


DEFAULT_DIRS = 36
PREVIEW_DEBUG_BG_COLOR = (96, 96, 96)


# Lightweight render-side state containers.
@dataclass(frozen=True, slots=True)
class MapCache:
    surface: pygame.Surface
    zoom: float
    center_x: int
    center_y: int


@dataclass(slots=True)
class CameraState:
    angle: float = 0.0


@dataclass(frozen=True, slots=True)
class RenderSetup:
    map_zoom: float = 3.0
    car_zoom: float = 3.0
    pixelation_scale: float = 0.35


@dataclass(frozen=True, slots=True)
class CameraFollowSettings:
    follow_alpha: float = 0.03
    drift_tilt_factor: float = 0.35
    max_drift_tilt: float = 10.0
    snap_delta: float = 180.0


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


# Surface conversion helpers keep blits fast once the display is initialized.
def _convert_for_display(surface: pygame.Surface) -> pygame.Surface:
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert_alpha()


def _convert_opaque_for_display(surface: pygame.Surface) -> pygame.Surface:
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert()


def clamp_scale(scale: float) -> float:
    return max(0.1, min(scale, 1.0))


def snap_degrees(deg: float, dirs: int = DEFAULT_DIRS) -> int:
    step = 360.0 / dirs
    return int((deg % 360.0) / step + 0.5) % dirs


def build_rotated_cache(images, dirs: int = DEFAULT_DIRS):
    # Pre-rotate all car slices once so frame rendering is only list indexing + blits.
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
    # Keep the map opaque to avoid per-pixel alpha blending on large blits.
    zoomed_map = _convert_opaque_for_display(pygame.transform.scale(map_surface, zoomed_size))
    return MapCache(
        surface=zoomed_map,
        zoom=zoom,
        center_x=zoomed_size[0] // 2,
        center_y=zoomed_size[1] // 2,
    )


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def _shortest_angle_delta(current: float, target: float) -> float:
    # Wrap to [-180, 180] so interpolation rotates the shortest way.
    return ((target - current + 180.0) % 360.0) - 180.0


def _clamp_zoom(zoom: float) -> float:
    return max(0.01, zoom)


def build_camera_buffer(view_size: tuple[int, int]) -> tuple[pygame.Surface, tuple[int, int]]:
    view_width, view_height = view_size
    # Use a diagonal-sized square so rotated corners never clip.
    side = max(1, int(math.ceil(math.hypot(view_width, view_height))) + 2)
    surface = pygame.Surface((side, side)).convert()
    return surface, (side // 2, side // 2)


def update_camera_angle(
    state: CameraState,
    *,
    car_rotation: float,
    drift_direction: int,
    drift_skew_degrees: float,
    follow_alpha: float,
    drift_tilt_factor: float,
    max_drift_tilt: float,
    snap_delta: float,
) -> None:
    # Camera targets car heading, then adds drift tilt and smooth interpolation.
    if drift_direction > 0:
        drift_sign = 1.0
    elif drift_direction < 0:
        drift_sign = -1.0
    else:
        drift_sign = 0.0

    max_tilt = abs(max_drift_tilt)
    drift_tilt = drift_sign * drift_skew_degrees * drift_tilt_factor
    drift_tilt = _clamp(drift_tilt, -max_tilt, max_tilt)
    target_angle = car_rotation + drift_tilt

    delta = _shortest_angle_delta(state.angle, target_angle)
    if abs(delta) >= max(0.0, snap_delta):
        state.angle = target_angle
    else:
        alpha = _clamp(follow_alpha, 0.0, 1.0)
        state.angle += delta * alpha

    state.angle = ((state.angle + 180.0) % 360.0) - 180.0


def update_camera_from_physics(
    state: CameraState,
    *,
    physics_rotation: float,
    physics_drift_direction: int,
    physics_drift_skew_degrees: float,
    settings: CameraFollowSettings,
) -> None:
    update_camera_angle(
        state,
        car_rotation=physics_rotation,
        drift_direction=physics_drift_direction,
        drift_skew_degrees=physics_drift_skew_degrees,
        follow_alpha=settings.follow_alpha,
        drift_tilt_factor=settings.drift_tilt_factor,
        max_drift_tilt=settings.max_drift_tilt,
        snap_delta=settings.snap_delta,
    )


def build_render_pipeline(
    *,
    screen_size: tuple[int, int],
    map_surface: pygame.Surface | None,
    image_stack: list[pygame.Surface],
    setup: RenderSetup,
    dirs: int = DEFAULT_DIRS,
) -> RenderPipeline:
    # Build and cache everything needed per-frame at startup/resolution change.
    render_size = build_pixel_surface_size(screen_size, setup.pixelation_scale)
    render_scale = render_size[1] / screen_size[1]
    needs_present_scale = render_size != screen_size
    center = (render_size[0] // 2, render_size[1] // 2)

    draw_map_zoom = _clamp_zoom(setup.map_zoom) * render_scale
    draw_car_scale = _clamp_zoom(setup.car_zoom) * render_scale

    frame_surface = pygame.Surface(render_size).convert()
    map_cache = build_map_cache(map_surface, draw_map_zoom)
    scaled_car_stack = scale_images(image_stack, draw_car_scale)
    rotated_cache = build_rotated_cache(scaled_car_stack, dirs=dirs)
    camera_buffer, camera_buffer_center = build_camera_buffer(render_size)

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


def draw_map(display, map_cache: MapCache | None, car_x, car_y, center, view_size):
    if map_cache is None:
        return

    car_map_x = map_cache.center_x + int(car_x * map_cache.zoom)
    car_map_y = map_cache.center_y + int(car_y * map_cache.zoom)

    view_x = car_map_x - center[0]
    view_y = car_map_y - center[1]
    view_width, view_height = view_size
    display.blit(map_cache.surface, (0, 0), area=(view_x, view_y, view_width, view_height))


def draw_map_camera(
    display: pygame.Surface,
    map_cache: MapCache | None,
    *,
    car_x: float,
    car_y: float,
    camera_angle: float,
    center: tuple[int, int],
    view_size: tuple[int, int],
    camera_buffer: pygame.Surface,
    camera_buffer_center: tuple[int, int],
) -> None:
    # Fast path when camera is effectively unrotated.
    if abs(camera_angle) < 1e-4:
        draw_map(display, map_cache, car_x, car_y, center, view_size)
        return

    camera_buffer.fill((0, 0, 0))
    draw_map(
        camera_buffer,
        map_cache,
        car_x,
        car_y,
        center=camera_buffer_center,
        view_size=camera_buffer.get_size(),
    )
    rotated_map = pygame.transform.rotate(camera_buffer, -camera_angle)
    rotated_rect = rotated_map.get_rect(center=center)
    display.blit(rotated_map, rotated_rect)


def render_stack(display, rotated_slices, pos, spread: int):
    x, y = pos
    for i, img in enumerate(rotated_slices):
        display.blit(
            img,
            (x - img.get_width() // 2, y - img.get_height() // 2 + i * spread),
        )


def render_stack_smooth(display, source_slices, pos, spread: int, rotation_degrees: float):
    # Debug preview path: rotate each slice every frame for smooth angle updates.
    x, y = pos
    for i, img in enumerate(source_slices):
        rotated = pygame.transform.rotate(img, rotation_degrees)
        display.blit(
            rotated,
            (x - rotated.get_width() // 2, y - rotated.get_height() // 2 + i * spread),
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


def render_frame(
    screen: pygame.Surface,
    pipeline: RenderPipeline,
    *,
    car_x: float,
    car_y: float,
    car_rotation: float,
    camera_angle: float,
    stack_spread: int,
) -> None:
    # Frame composition order: map in camera space, then car in screen center.
    frame_surface = pipeline.frame_surface
    frame_surface.fill((0, 0, 0))

    draw_map_camera(
        frame_surface,
        pipeline.map_cache,
        car_x=car_x,
        car_y=car_y,
        camera_angle=camera_angle,
        center=pipeline.center,
        view_size=pipeline.render_size,
        camera_buffer=pipeline.camera_buffer,
        camera_buffer_center=pipeline.camera_buffer_center,
    )

    car_relative_rotation = car_rotation - camera_angle
    dir_idx = snap_degrees(car_relative_rotation, dirs=pipeline.dirs)
    render_stack(frame_surface, pipeline.rotated_cache[dir_idx], pipeline.center, stack_spread)

    present_frame(screen, frame_surface, pipeline.screen_size, pipeline.needs_present_scale)


def render_preview_debug_frame(
    screen: pygame.Surface,
    pipeline: RenderPipeline,
    *,
    car_rotation: float,
    stack_spread: int,
) -> None:
    # Preview debugger intentionally skips stepped rotation cache and map rendering.
    frame_surface = pipeline.frame_surface
    frame_surface.fill(PREVIEW_DEBUG_BG_COLOR)
    render_stack_smooth(
        frame_surface,
        pipeline.scaled_car_stack,
        pipeline.center,
        stack_spread,
        car_rotation,
    )
    present_frame(screen, frame_surface, pipeline.screen_size, pipeline.needs_present_scale)
