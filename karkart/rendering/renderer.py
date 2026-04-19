"""The in-game renderer that composes map + car into the final frame."""

from __future__ import annotations

import pygame

from karkart.helpers import clamp_scale, clamp_zoom, snap_degrees
from karkart.rendering.map import Map
from karkart.rendering.sparks import SparkManager
from karkart.rendering.stacker import Stacker


class Renderer:
    """Draws one frame per ``render_frame`` call: pixelated map + rotated car stack."""

    _MAP_ZOOM: float = 3.0
    _CAR_ZOOM: float = 3.0
    _PIXELATION_SCALE: float = 0.35
    _DRIFT_VISUAL_SKEW: float = 30.0  # Degrees the car sprite rotates sideways during drift.
    _HOP_PIXEL_SCALE: float = 12.0    # Screen pixels of lift per car_z unit at render res.

    def __init__(
        self, current_map: Map, stacker: Stacker, screen: pygame.Surface, sparks: SparkManager,
    ) -> None:
        self.screen = screen
        self.render_size = self._build_pixel_surface_size(self._PIXELATION_SCALE)
        render_scale = self.render_size[1] / self.screen.get_size()[1]

        draw_map_zoom = clamp_zoom(self._MAP_ZOOM) * render_scale
        draw_car_scale = clamp_zoom(self._CAR_ZOOM) * render_scale

        self.center = (self.render_size[0] // 2, self.render_size[1] // 2)
        self.frame_surface = pygame.Surface(self.render_size).convert()
        self.map = current_map
        self.stacker = stacker
        self.sparks = sparks
        self.map_zoom = draw_map_zoom
        self.needs_present_scale = self.render_size != self.screen.get_size()

        self.map.zoom_fixing(draw_map_zoom, self.render_size)
        self.stacker.scale_update(draw_car_scale)

    def _build_pixel_surface_size(self, pixelation_scale: float) -> tuple[int, int]:
        scale = clamp_scale(pixelation_scale)
        screen_width, screen_height = self.screen.get_size()
        pixel_width = max(1, int(screen_width * scale))
        pixel_height = max(1, int(screen_height * scale))
        return pixel_width, pixel_height

    def _present_frame(self) -> None:
        """Blit (or scale-blit) the composed frame to the real display surface."""
        if not self.needs_present_scale:
            self.screen.blit(self.frame_surface, (0, 0))
            return
        pygame.transform.scale(self.frame_surface, self.screen.get_size(), self.screen)

    def render_frame(self, stack_spread: float) -> None:
        """Compose one frame: map in camera space, then car at screen centre."""
        frame_surface = self.frame_surface
        frame_surface.fill((0, 0, 0))

        self.map.draw_map_camera(display=frame_surface, center=self.center, render_size=self.render_size)

        physics = self.map.camera.car.physics
        camera_angle = self.map.camera.angle
        car_relative_rotation = physics.rotation - camera_angle

        # Apply a visual sideways tilt while drifting (purely cosmetic, no physics change).
        if physics.drift_active:
            visual_rotation = car_relative_rotation + physics.drift_direction * self._DRIFT_VISUAL_SKEW
        else:
            visual_rotation = car_relative_rotation

        dir_idx = snap_degrees(visual_rotation, dirs=self.stacker.dirs)

        # Sparks drawn before the car so they appear behind it.
        self.sparks.draw(
            frame_surface,
            physics.car_x, physics.car_y,
            camera_angle,
            self.map_zoom,
            self.center,
        )

        hop_px = int(physics.car_z * self._HOP_PIXEL_SCALE)
        self.stacker.render_stack(self.frame_surface, dir_idx, self.center, stack_spread, hop_px)

        self._present_frame()
