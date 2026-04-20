"""The in-game screen: physics, rendering and collision for a single race."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

import pygame

from karkart.helpers import snap_degrees
from karkart.paths import MAP_DATA_FILE
from karkart.physics.camera import Camera
from karkart.physics.car import Car
from karkart.physics.collision import CollisionDetector
from karkart.rendering.map import Map, MapData
from karkart.rendering.renderer import Renderer
from karkart.rendering.sparks import SparkManager
from karkart.rendering.stacker import Stacker
from karkart.screens.start_sequence import StartSequence


with MAP_DATA_FILE.open() as f:
    _MAP_DATA = json.load(f)


@dataclass(frozen=True, slots=True)
class GameConfig:
    fps: int = 60
    dirs: int = 36
    gameplay_stack_spread: float = -1
    default_resolution: tuple[int, int] = (1280, 720)
    standard_resolutions: tuple[tuple[int, int], ...] = ((1280, 720), (1920, 1080))

    @property
    def rotation_snap_degrees(self) -> float:
        return 360.0 / self.dirs


def _car_pos_scaling(x: float, y: float, map_dimensions: tuple[int, int]) -> tuple[float, float]:
    """Map-data start coords are in map-pixel space; centre them around the origin."""
    return x - map_dimensions[0] / 2, y - map_dimensions[1] / 2


class GamePlay:
    """Wires physics, map, camera, stacker and renderer together for one race."""

    def __init__(self, manager) -> None:
        self.manager = manager
        self.config = GameConfig()

        map_name = self.manager.app_data.current_map.name
        map_record = _MAP_DATA[map_name]

        self.current_map_data = MapData()
        self.current_map_data.checkpoints = map_record["checkpoints"]
        self.current_map_data.start_checkpoint = map_record["start_checkpoint"]
        self.current_map_data.layers = self.manager.app_data.return_map_layers()

        self.countdown = StartSequence(self.manager.screen_display)

        self.current_car = Car()
        self.current_camera = Camera(self.current_car)
        self.current_map = Map(self.current_map_data, self.current_camera)
        self.car_stacker = Stacker(self.manager.app_data.current_car, self.config.dirs)
        self.sparks = SparkManager()
        self.current_renderer = Renderer(
            self.current_map, self.car_stacker, self.manager.screen_display, self.sparks,
        )
        self.collision_detector = CollisionDetector(
            self.current_map.masks, self.car_stacker.mask_cache,
        )

        start_x, start_y = map_record["start"]
        self.current_car.physics.car_x, self.current_car.physics.car_y = _car_pos_scaling(
            start_x, start_y, self.current_map.dimensions,
        )


    def handle_event(self, event) -> None:
        controls = self.current_car.controls

        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_a:
                    controls.left_pressed = True
                    controls.steer_input = 1
                case pygame.K_d:
                    controls.right_pressed = True
                    controls.steer_input = -1
                case pygame.K_w:
                    controls.up_input = True
                case pygame.K_s:
                    controls.down_input = True
                case pygame.K_SPACE:
                    controls.drift_input = True
        elif event.type == pygame.KEYUP:
            match event.key:
                case pygame.K_a:
                    controls.left_pressed = False
                    if controls.steer_input == 1:
                        controls.steer_input = -1 if controls.right_pressed else 0
                case pygame.K_d:
                    controls.right_pressed = False
                    if controls.steer_input == -1:
                        controls.steer_input = 1 if controls.left_pressed else 0
                case pygame.K_w:
                    controls.up_input = False
                case pygame.K_s:
                    controls.down_input = False
                case pygame.K_SPACE:
                    controls.drift_input = False

    def _collision_check(self) -> None:
        car_relative_rotation = self.current_car.physics.rotation - self.current_camera.angle
        self.current_map.get_coordinates()
        dir_idx = snap_degrees(car_relative_rotation, dirs=self.car_stacker.dirs)
        offset = (self.current_map.car_map_x, self.current_map.car_map_y)
        self.current_car.collision_results = self.collision_detector.check(dir_idx, offset)
    def update_resources(self):
        self.car_stacker.set_images(self.manager.app_data.current_car)


    def update(self) -> None:

        if not self.countdown.complete:
            return
        self._collision_check()
        self.current_car.physics = self.current_car.step_physics_with_controls(
            snap_step_degrees=self.config.rotation_snap_degrees,
        )
        physics = self.current_car.physics
        # Only emit sparks once the hop has landed — MK drift trails start after
        # the hop finishes, not during the airborne frames.
        if physics.drift_active and physics.car_z <= 0.0:
            # Anchor tire marks on the last safe position so a collision-rollback
            # can't leave sparks stranded where the car never actually was.
            anchor_x = self.current_car.last_safe_x if self.current_car.last_safe_x is not None else physics.car_x
            anchor_y = self.current_car.last_safe_y if self.current_car.last_safe_y is not None else physics.car_y
            self.sparks.emit(
                anchor_x, anchor_y,
                physics.rotation,
                physics.drift_charge_frames,
            )
        self.sparks.update()
        self.current_camera.update_camera_angle()
        self.current_map.update_checkpoints()
        print(self.current_map.lap_times)

    def draw(self, _surface: pygame.Surface) -> None:
        self.current_renderer.render_frame(self.config.gameplay_stack_spread)

        # One-shot blocking countdown at race start.
        while self.countdown.seconds > 0:
            self.current_renderer.render_frame(self.config.gameplay_stack_spread)
            self.countdown.write()
            pygame.display.flip()
            time.sleep(1)
            self.countdown.seconds -= 1

        self.countdown.complete = True
        pygame.display.flip()
