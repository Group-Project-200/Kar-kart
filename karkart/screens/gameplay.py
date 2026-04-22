"""The in-game screen: physics, rendering and collision for a single race."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass

import pygame

from karkart.ai.ai_controller import AIController
from karkart.ai.pathfinder import AStarPathfinder
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

from karkart.powerups.powerups_manager import PowerupRendering, PowerupsManager

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


def _position_mapping(current_info, map_size):
    map_w,map_h =map_size
    raw_x, raw_y, item_w, item_h= current_info
    shifted_x = raw_x - map_w / 2
    shifted_y = raw_y - map_h / 2

    info = shifted_x,shifted_y,item_w, item_h
    return  info


class GamePlay:
    """Wires physics, map, camera, stacker and renderer together for one race."""

    # Distance-based car-to-car collision radius, in world (map-pixel) units.
    _CAR_COLLISION_RADIUS: float = 18.0

    def __init__(self, manager) -> None:
        self.ai_active = None
        self.manager = manager
        self.mode = self.manager.app_data.modes[self.manager.app_data.current_mode]
        self.config = GameConfig()


        # Alternating-frame scheduler: cheap per-frame work runs every tick;
        # expensive checks split across even/odd frames (see update()).
        self._frame_parity: int = 0

        # HUD + debug overlay.
        self._debug_checkpoints: bool = False
        if not pygame.font.get_init():
            pygame.font.init()
        self._hud_font: pygame.font.Font = pygame.font.SysFont("monospace", 16)

        # Cumulative checkpoint counters used to rank positions (lap-aware).
        self._player_total_cp: int = 0
        self._ai_total_cp: int = 0
        self._prev_player_counter: int = 0
        self._prev_ai_goal_idx: int = 0

        map_name = self.manager.app_data.current_map.name
        map_record = _MAP_DATA[map_name]

        self.current_map_data = MapData()
        self.current_map_data.checkpoints = map_record["checkpoints"]
        self.current_map_data.finish_line = map_record["finish_line"]
        self.current_map_data.layers = self.manager.app_data.return_map_layers()

        self.countdown = StartSequence(self.manager.screen_display)
        proper_coordinates =[]
        for item in map_record["items"]:
            proper_coordinates.append( _position_mapping(item, self.current_map_data.layers[0].get_size()))
        self.current_car = Car()
        self.power_ups_manager = PowerupsManager(self.current_car)

        self.world_box = []
        for box in proper_coordinates:
            self.world_box.append(PowerupRendering(box, self.power_ups_manager))
        self.current_camera = Camera(self.current_car)
        self.current_map = Map(self.current_map_data, self.current_camera, self.world_box)
        self.car_stacker = Stacker(self.manager.app_data.current_car, self.config.dirs)
        self.sparks = SparkManager()
        self.current_renderer = Renderer(
            self.current_map, self.car_stacker, self.manager.screen_display, self.sparks,
        )
        self.collision_detector = CollisionDetector(
            self.current_map.masks, self.car_stacker.mask_cache,
        )

        sg = map_record["start_grid"]   # [x, y, w, h]
        start_x = sg[0] + sg[2] / 2
        start_y = sg[1] + sg[3] / 2
        self.current_car.physics.car_x, self.current_car.physics.car_y = _car_pos_scaling(
            start_x, start_y, self.current_map.dimensions,
        )




        # ------------------------------------------------------------------ #
        # AI opponent                                                        #
        # ------------------------------------------------------------------ #

        if self.ai_active:
            self.ai_car = Car()
            ai_stack = self._pick_ai_car_stack()
            self.ai_stacker = Stacker(ai_stack, self.config.dirs)
            self.ai_stacker.scale_update(self.car_stacker.scale)
            self.ai_collision = CollisionDetector(
                self.current_map.masks, self.ai_stacker.mask_cache,
            )
            # Spawn the AI beside the player (offset within the start grid).
            self.ai_car.physics.car_x, self.ai_car.physics.car_y = _car_pos_scaling(
                start_x + 30, start_y, self.current_map.dimensions,
            )

            self.pathfinder = AStarPathfinder(
                mask=self.current_map.masks[0],
                map_dims=self.current_map.dimensions,
                cell_size=8,
                padding=4,
            )
            self.ai_controller = AIController(
                car=self.ai_car,
                pathfinder=self.pathfinder,
                checkpoints=self.current_map.checkpoints_list,
            )



    def _pick_ai_car_stack(self) -> list[pygame.Surface]:
        """Pick a sprite stack that's different from the player's car if possible."""
        cars = self.manager.app_data.cars
        player_name = self.manager.app_data.current_car_name
        for name in sorted(cars.keys()):
            if name != player_name:
                return cars[name]
        return cars[player_name]

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

                case pygame.K_ESCAPE:
                    # Open pause menu.
                    self.manager.change_screen("pause")
                    self.manager.get_screen().add_black_layer = True

                case pygame.K_F1:
                    self._debug_checkpoints = not self._debug_checkpoints
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
        self.current_car.collision_results = self.collision_detector.border_check(dir_idx, offset)


        for items_box in self.world_box:
            powered_up = items_box.check(self.current_car.physics.car_x, self.current_car.physics.car_y)
            if powered_up and self.power_ups_manager.current is None:
                self.power_ups_manager.current = self.power_ups_manager.choose_random_powerup()
                self.power_ups_manager.current.activate(self.current_car.physics)

    def _ai_collision_check(self) -> None:
        """Test the AI car against the same map masks the player uses."""
        cache = self.current_map.cache
        assert cache is not None and cache.zoom is not None
        ai_map_x = cache.center_x + int(self.ai_car.physics.car_x * cache.zoom)
        ai_map_y = cache.center_y + int(self.ai_car.physics.car_y * cache.zoom)
        dir_idx = snap_degrees(self.ai_car.physics.rotation, dirs=self.ai_stacker.dirs)
        self.ai_car.collision_results = self.ai_collision.border_check(dir_idx, (ai_map_x, ai_map_y))

    def update_resources(self):
        self.car_stacker.set_images(self.manager.app_data.current_car)
        self.mode = self.manager.app_data.modes[self.manager.app_data.current_mode]
        self.ai_active = self.mode["Ai"]
        for items_box in self.world_box:
            items_box.active = self.mode["Items"]
        self.current_map.active = self.mode["Items"]



    def _check_car_to_car_collision(self) -> None:
        """Push player and AI apart if they overlap, and bleed some momentum."""
        p = self.current_car.physics
        a = self.ai_car.physics
        dx = p.car_x - a.car_x
        dy = p.car_y - a.car_y
        dist_sq = dx * dx + dy * dy
        if dist_sq >= self._CAR_COLLISION_RADIUS ** 2:
            return
        dist = math.sqrt(dist_sq) or 0.001
        nx, ny = dx / dist, dy / dist
        p.velocity_x += nx * 0.4
        p.velocity_y += ny * 0.4
        a.velocity_x -= nx * 0.4
        a.velocity_y -= ny * 0.4
        p.speed *= 0.6
        a.speed *= 0.6

    def _update_checkpoints_player(self) -> None:
        self.current_map.update_checkpoints()
        cur = self.current_map.list_counter
        if cur != self._prev_player_counter:
            self._player_total_cp += 1
            self._prev_player_counter = cur

    def _update_checkpoints_ai(self) -> None:
        cur = self.ai_controller._goal_idx
        if cur != self._prev_ai_goal_idx:
            self._ai_total_cp += 1
            self._prev_ai_goal_idx = cur

    def ai_update(self):
        if not self.ai_active:
            return

        if self._frame_parity == 0:
            self._ai_collision_check()
            self._check_car_to_car_collision()
        else:
            self.ai_controller.update()
            self._update_checkpoints_ai()

        self.ai_car.physics = self.ai_car.step_physics_with_controls(
            snap_step_degrees=self.config.rotation_snap_degrees,
        )

    def update(self) -> None:
        if not self.countdown.complete:
            return

        self._frame_parity ^= 1

        # Even frames: mask-based collision checks and car-to-car overlap.
        # Odd frames: checkpoint bookkeeping and AI planning.
        # Cached collision_results and control state carry into the alternate
        # frame, so the one-frame latency is invisible at 60 FPS.
        if self._frame_parity == 0:
            self._collision_check()

        else:
            self._update_checkpoints_player()


        # Physics integrates every frame for both cars so motion stays smooth.
        self.current_car.physics = self.current_car.step_physics_with_controls(
            snap_step_degrees=self.config.rotation_snap_degrees,
        )
        physics = self.current_car.physics
        # Only emit sparks once the hop has landed — MK drift trails start after
        # the hop finishes, not during the airborne frames.
        if physics.drift_active and physics.car_z <= 0.0:
            anchor_x = self.current_car.last_safe_x if self.current_car.last_safe_x is not None else physics.car_x
            anchor_y = self.current_car.last_safe_y if self.current_car.last_safe_y is not None else physics.car_y
            self.sparks.emit(
                anchor_x, anchor_y,
                physics.rotation,
                physics.drift_charge_frames,
            )

        if self.power_ups_manager.current is not None:
            if self.power_ups_manager.current.tick(self.current_car.physics):
                self.power_ups_manager.current = None


        self.sparks.update()
        self.current_camera.update_camera_angle()

        self.ai_update()


        self.complete_race()

    # ------------------------------------------------------------------ #
    # HUD + debug overlay                                                #
    # ------------------------------------------------------------------ #

    def _world_to_screen_real(self, wx: float, wy: float) -> tuple[int, int]:
        """Project a world-space point onto the real (unscaled) screen surface."""
        renderer = self.current_renderer
        player = self.current_car.physics
        dx = (wx - player.car_x) * renderer.map_zoom
        dy = (wy - player.car_y) * renderer.map_zoom
        angle_rad = math.radians(self.current_camera.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        fx = renderer.center[0] + rx
        fy = renderer.center[1] + ry
        screen_w, screen_h = self.manager.screen_display.get_size()
        frame_w, frame_h = renderer.render_size
        return int(fx * screen_w / frame_w), int(fy * screen_h / frame_h)

    def _position_label(self) -> str:
        return "1st" if self._player_total_cp >= self._ai_total_cp else "2nd"

    def draw_hud(self, screen: pygame.Surface) -> None:
        total_cps = len(self.current_map.checkpoints_list) or 1
        cp_in_lap = self.current_map.list_counter
        lap = self.current_map.current_lap
        speed = self.current_car.physics.speed

        lines = [
            f"Lap  {lap}",
            f"CP   {cp_in_lap} / {total_cps}",
            f"Spd  {speed:+.2f}",
            f"Pos  {self._position_label()}",
        ]

        padding = 6
        rendered = [self._hud_font.render(text, True, (255, 255, 255)) for text in lines]
        width = max(s.get_width() for s in rendered) + padding * 2
        height = sum(s.get_height() for s in rendered) + padding * 2

        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        screen.blit(panel, (8, 8))

        y = 8 + padding
        for surf in rendered:
            screen.blit(surf, (8 + padding, y))
            y += surf.get_height()

        if self._debug_checkpoints:
            self._draw_checkpoint_debug(screen)

    def _draw_checkpoint_debug(self, screen: pygame.Surface) -> None:
        target_idx = self.current_map.list_counter
        finish_idx = len(self.current_map.checkpoints_list) - 1
        for idx, cp in enumerate(self.current_map.checkpoints_list):
            if idx == finish_idx:
                colour = (0, 220, 255) if idx != target_idx else (255, 255, 255)
            elif idx < target_idx:
                colour = (80, 220, 80)
            elif idx == target_idx:
                colour = (250, 220, 60)
            else:
                colour = (140, 140, 140)

            rect = cp.rect
            corners_world = [
                (rect.left, rect.top),
                (rect.right, rect.top),
                (rect.right, rect.bottom),
                (rect.left, rect.bottom),
            ]
            corners_screen = [self._world_to_screen_real(x, y) for x, y in corners_world]
            pygame.draw.polygon(screen, colour, corners_screen, width=2)

    def complete_race(self):
        if self.current_map.current_lap > 3:
            self.manager.change_screen("placeholder")

    def draw(self, _surface: pygame.Surface) -> None:
        screen = self.manager.screen_display

        extra_cars = [(self.ai_car, self.ai_stacker)] if self.ai_active else []

        self.current_renderer.render_frame(
            self.config.gameplay_stack_spread, extra_cars=extra_cars,
        )

        # TODO: DECOMMENT
        # One-shot blocking countdown at race start.
        # while self.countdown.seconds > 0:
        #     self.current_renderer.render_frame(
        #         self.config.gameplay_stack_spread, extra_cars=extra_cars,
        #     )
        #     self.countdown.write()
        #     pygame.display.flip()
        #     time.sleep(1)
        #     self.countdown.seconds -= 1

        self.countdown.complete = True

        # HUD draws on the full-resolution display, on top of the pixelated map.
        self.draw_hud(screen)

        pygame.display.flip()
