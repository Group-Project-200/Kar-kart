"""The in-game renderer that composes map + car into the final frame."""

from __future__ import annotations

import math

import pygame

from karkart.helpers import clamp_scale, clamp_zoom, snap_degrees
from karkart.rendering.map import Map
from karkart.rendering.sparks import SparkManager
from karkart.rendering.stacker import Stacker


class Renderer:
    """It draws once frame and is responsible for collecting the elements of the current frame and drawing it correctly
    by calling their update and draw functions"""

    _MAP_ZOOM: float = 3.0
    _CAR_ZOOM: float = 3.0
    _PIXELATION_SCALE: float = 0.35
    _DRIFT_VISUAL_SKEW: float = 30.0
    _HOP_PIXEL_SCALE: float = 12.0

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
        if not self.needs_present_scale:
            self.screen.blit(self.frame_surface, (0, 0))
            return
        pygame.transform.scale(self.frame_surface, self.screen.get_size(), self.screen)

    def _world_to_screen(
        self,
        wx: float,
        wy: float,
        *,
        player_x: float,
        player_y: float,
        camera_angle: float,
    ) -> tuple[int, int]:
        dx = (wx - player_x) * self.map_zoom
        dy = (wy - player_y) * self.map_zoom

        angle_rad = math.radians(camera_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a

        return int(self.center[0] + rx), int(self.center[1] + ry)

    def _draw_extra_car(
        self,
        car,
        stacker: Stacker,
        stack_spread: float,
        *,
        player_x: float,
        player_y: float,
        camera_angle: float,
    ) -> None:
        sx, sy = self._world_to_screen(
            car.car_x,
            car.car_y,
            player_x=player_x,
            player_y=player_y,
            camera_angle=camera_angle,
        )

        width, height = self.render_size
        margin = 64

        if sx < -margin or sx > width + margin or sy < -margin or sy > height + margin:
            return

        dir_idx = snap_degrees(car.rotation - camera_angle, dirs=stacker.dirs)
        hop_px = int(car.car_z * self._HOP_PIXEL_SCALE)
        stacker.render_stack(self.frame_surface, dir_idx, (sx, sy), stack_spread, hop_px)

    def _draw_sparks(self, sparks, player, camera_angle: float) -> None:
        if not sparks:
            return

        for spark in sparks:
            sx, sy = self._world_to_screen(
                spark.x,
                spark.y,
                player_x=player.car_x,
                player_y=player.car_y,
                camera_angle=camera_angle,
            )

            t = spark.life / spark.max_life
            alpha = int(200 * t)
            radius = max(1, int(3.5 * t))

            spark_surface = pygame.Surface((radius * 2 + 1, radius * 2 + 1), pygame.SRCALPHA)
            pygame.draw.circle(
                spark_surface,
                (spark.r, spark.g, spark.b, alpha),
                (radius, radius),
                radius,
            )
            self.frame_surface.blit(spark_surface, (sx - radius, sy - radius))
    """here is where the rendering happens where it takes the player, the camera, the ai cars, and draws the scene"""
    def render_frame(
        self,
        stack_spread: float,
        *,
        player=None,
        camera_angle: float | None = None,
        sparks=None,
        extra_cars: list | None = None,
    ) -> None:
        frame_surface = self.frame_surface
        frame_surface.fill((0, 0, 0))

        if player is None:
            player = self.map.camera.car.physics

        if camera_angle is None:
            camera_angle = self.map.camera.angle

        self.map.draw_map_camera(
            display=frame_surface,
            center=self.center,
            render_size=self.render_size,
            car_x=player.car_x,
            car_y=player.car_y,
            camera_angle=camera_angle,
        )

        for obj in self.map.world_objects:
            obj.draw(
                frame_surface,
                self.center,
                player.car_x,
                player.car_y,
                self.map_zoom,
                camera_angle,
            )

        car_relative_rotation = player.rotation - camera_angle

        if player.drift_active:
            visual_rotation = car_relative_rotation + player.drift_direction * self._DRIFT_VISUAL_SKEW
        else:
            visual_rotation = car_relative_rotation

        dir_idx = snap_degrees(visual_rotation, dirs=self.stacker.dirs)

        if sparks is None:
            self.sparks.draw(
                frame_surface,
                player.car_x,
                player.car_y,
                camera_angle,
                self.map_zoom,
                self.center,
            )
        else:
            self._draw_sparks(sparks, player, camera_angle)

        if extra_cars:
            for other_car, other_stacker in extra_cars:
                self._draw_extra_car(
                    other_car,
                    other_stacker,
                    stack_spread,
                    player_x=player.car_x,
                    player_y=player.car_y,
                    camera_angle=camera_angle,
                )

        hop_px = int(player.car_z * self._HOP_PIXEL_SCALE)
        self.stacker.render_stack(self.frame_surface, dir_idx, self.center, stack_spread, hop_px)

        self._present_frame()