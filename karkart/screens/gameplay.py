"""The in-game screen: physics, rendering and collision for a single race."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass

import pygame

from karkart.ai.ai_controller import AIController
from karkart.ai.pathfinder import AStarPathfinder
from karkart.paths import MAP_DATA_FILE
from karkart.physics.camera import Camera
from karkart.physics.car import Car, get_handling_for
from karkart.physics.checkpoint import Checkpoint, RacerState
from karkart.physics.collision import CollisionDetector
from karkart.rendering.map import Map, MapData
from karkart.rendering.renderer import Renderer
from karkart.rendering.sparks import SparkManager
from karkart.rendering.stacker import Stacker
from karkart.runtime.pathfinder_worker import PathfinderWorker
from karkart.runtime.scheduler import (
    AIScheduler, CollisionScheduler, PhysicsScheduler,
)
from karkart.runtime.snapshot import SnapshotBuffer, WorldSnapshot
from karkart.runtime.world import World
from karkart.settings import Keys as K
from karkart.screens.start_sequence import StartSequence
from karkart.screens.leaderboard import GAME_LEADERBOARD, LeaderboardScreen, RaceResult

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


def _build_collision_masks(
    layer_masks: list[pygame.mask.Mask],
) -> tuple[pygame.mask.Mask, pygame.mask.Mask | None]:
    """Pick the (wall_mask, road_mask) pair to use for a given map.

    Old-style maps ship three mask layers: ``layer_masks[0]`` is solid walls
    and ``layer_masks[1]`` is the road surface — those can be used as-is.
    New-style maps ship only a single layer which is the road; for those the
    collision test has to fire *off* the road, so we invert the road mask
    into an "off-road" mask and use that as the wall layer.
    """
    if len(layer_masks) >= 2:
        return layer_masks[0], layer_masks[1]

    road = layer_masks[0]
    w, h = road.get_size()
    off_road = pygame.mask.Mask((w, h), fill=True)
    off_road.erase(road, (0, 0))
    return off_road, road


def _duplicate_checkpoints(source: list[Checkpoint]) -> list[Checkpoint]:
    """Clone the checkpoint geometry so every car owns its own list.

    Checkpoint instances carry mutable state (``passed``) and the game
    advances each racer independently — sharing the same list between cars
    risks one racer's progression leaking into another's.
    """
    return [
        Checkpoint(cp.rect.x, cp.rect.y, cp.rect.width, cp.rect.height)
        for cp in source
    ]


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

    # How many AI opponents spawn in Race Mode. Time Trial always has zero.
    _AI_COUNT_RACE: int = 4

    def __init__(self, manager) -> None:
        self.manager = manager
        self.mode = self.manager.app_data.modes[self.manager.app_data.current_mode]
        self.ai_active = self.mode["Ai"]
        self.config = GameConfig()

        self._race_finished: bool = False

        # HUD + debug overlay.
        self._debug_checkpoints: bool = False
        if not pygame.font.get_init():
            pygame.font.init()
        self._hud_font: pygame.font.Font = pygame.font.SysFont("monospace", 16)

        # Per-racer checkpoint progression (lap, cursor, cumulative total).
        # AI states are only populated when AI cars are spawned below.
        self.player_state = RacerState()
        self.ai_states: list[RacerState] = []

        # Per-car checkpoint geometry. The map's checkpoints_list is the
        # shared source of truth; each car gets its own independent clone so
        # their per-racer state can't interfere with each other.
        self.player_checkpoints: list[Checkpoint] = []
        self.ai_checkpoints: list[list[Checkpoint]] = []

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
        # Player car uses the handling profile tied to whichever sprite stack
        # was selected in the car picker.
        self.current_car = Car(
            handling=get_handling_for(self.manager.app_data.current_car_name),
        )
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
        # The renderer calls Map.zoom_fixing, which populates the map's
        # checkpoints_list. Clone it for the player now that it exists.
        self.player_checkpoints = _duplicate_checkpoints(
            self.current_map.checkpoints_list,
        )
        # Resolve which mask represents "blocked" for this map (walls for old
        # maps, inverted road for new maps) and which represents the driveable
        # surface (used by A* to stay on-track).
        wall_mask, road_mask = _build_collision_masks(self.current_map.masks)
        self.collision_detector = CollisionDetector(
            [wall_mask], self.car_stacker.mask_cache,
        )

        # Compute start pose: centre of the start-grid box in world coords,
        # heading pointing at the first checkpoint so every car faces the
        # correct way down the track regardless of how the grid was drawn.
        sg = map_record["start_grid"]   # [x, y, w, h]
        grid_cx = sg[0] + sg[2] / 2
        grid_cy = sg[1] + sg[3] / 2
        start_world_x, start_world_y = _car_pos_scaling(
            grid_cx, grid_cy, self.current_map.dimensions,
        )

        start_rotation, forward, right = self._compute_start_pose(
            start_world_x, start_world_y,
        )
        ai_count = self._AI_COUNT_RACE if self.ai_active else 0
        player_pos, ai_positions = self._grid_positions(
            start_world_x, start_world_y, forward, right, ai_count,
        )

        self.current_car.physics.car_x, self.current_car.physics.car_y = player_pos
        self.current_car.physics.rotation = start_rotation

        # Match the camera heading to the car's heading so the very first
        # rendered frame (during the countdown, before update_camera_angle
        # runs) shows the world oriented correctly — without this the cars
        # render rotated against a north-up map during the 3-2-1 sequence.
        self.current_camera.angle = start_rotation

        # ------------------------------------------------------------------ #
        # AI opponents                                                       #
        # ------------------------------------------------------------------ #

        self.ai_cars: list[Car] = []
        self.ai_stackers: list[Stacker] = []
        self.ai_collisions: list[CollisionDetector] = []
        self.ai_controllers: list[AIController] = []

        if self.ai_active:
            # Padding 3 keeps tight corridors
            self.pathfinder = AStarPathfinder(
                mask=wall_mask,
                map_dims=self.current_map.dimensions,
                cell_size=8,
                padding=4,
                road_mask=road_mask,
            )

            ai_stacks = self._pick_ai_car_stacks(ai_count)
            for i in range(ai_count):
                ai_name, ai_stack = ai_stacks[i]
                # Every AI uses the handling profile bound to its own car
                # model, so opponents actually drive like their respective
                # karts instead of all sharing the player's tuning.
                ai_car = Car(handling=get_handling_for(ai_name))
                ai_car.physics.car_x, ai_car.physics.car_y = ai_positions[i]
                ai_car.physics.rotation = start_rotation

                stacker = Stacker(ai_stack, self.config.dirs)
                stacker.scale_update(self.car_stacker.scale)

                collision = CollisionDetector([wall_mask], stacker.mask_cache)

                state = RacerState()
                ai_cp_list = _duplicate_checkpoints(
                    self.current_map.checkpoints_list,
                )
                controller = AIController(
                    car=ai_car,
                    pathfinder=self.pathfinder,
                    checkpoints=ai_cp_list,
                    racer_state=state,
                    ai_index=i,
                    planner=None,
                )

                self.ai_cars.append(ai_car)
                self.ai_stackers.append(stacker)
                self.ai_collisions.append(collision)
                self.ai_states.append(state)
                self.ai_controllers.append(controller)
                self.ai_checkpoints.append(ai_cp_list)
        else:
            self.pathfinder = None

        self.snapshot_buffer = SnapshotBuffer()
        self.world = World(
            player_car=self.current_car,
            ai_cars=self.ai_cars,
            camera=self.current_camera,
            sparks=self.sparks,
            player_state=self.player_state,
            ai_states=self.ai_states,
            player_checkpoints=self.player_checkpoints,
            ai_checkpoints=self.ai_checkpoints,
            ai_controllers=self.ai_controllers,
            powerups_manager=self.power_ups_manager,
            world_box=self.world_box,
            current_map=self.current_map,
            car_stacker=self.car_stacker,
            ai_stackers=self.ai_stackers,
            collision_detector=self.collision_detector,
            ai_collisions=self.ai_collisions,
            car_collision_radius=self._CAR_COLLISION_RADIUS,
            snap_step_degrees=self.config.rotation_snap_degrees,
        )
        self._pathfinder_worker: PathfinderWorker | None = None
        self._physics_thread: PhysicsScheduler | None = None
        self._collision_thread: CollisionScheduler | None = None
        self._ai_thread: AIScheduler | None = None
        self._threads_started: bool = False

        self._publish_initial_snapshot()

    # Grid stagger offsets: each row is one car-length behind the previous,
    # and cars alternate right/left so the line-up spreads across the track.
    _GRID_ROW_GAP: float = 26.0     # Forward spacing between rows (world units).
    _GRID_SIDE: float = 20.0        # Lateral offset per lane (world units).
    _POLE_FORWARD_OFFSET: float = 12.0  # Player slightly ahead of grid centre.

    def _compute_start_pose(
        self, start_world_x: float, start_world_y: float,
    ) -> tuple[float, tuple[float, float], tuple[float, float]]:
        """Return (rotation_degrees, forward_unit, right_unit) for the grid.

        Heading is derived from the direction to the first checkpoint so cars
        always face down the racing line regardless of how the start box was
        drawn. Falls back to facing up the map if no checkpoint is available.
        """
        checkpoints = self.current_map.checkpoints_list
        if checkpoints:
            target = checkpoints[0].rect
            dx = target.centerx - start_world_x
            dy = target.centery - start_world_y
        else:
            dx, dy = 0.0, -1.0
        length = math.hypot(dx, dy) or 1.0
        fx, fy = dx / length, dy / length

        # Screen-right perpendicular (Y grows downward): rotate forward 90° CW.
        rx, ry = -fy, fx

        # forward_vector(r) returns (-sin r, -cos r), so solve for r.
        rotation = math.degrees(math.atan2(-fx, -fy))
        return rotation, (fx, fy), (rx, ry)

    def _grid_positions(
        self,
        start_world_x: float, start_world_y: float,
        forward: tuple[float, float], right: tuple[float, float],
        ai_count: int,
    ) -> tuple[tuple[float, float], list[tuple[float, float]]]:
        """Staggered F1-style grid: player on pole, AI cars fanned out behind."""
        fx, fy = forward
        rx, ry = right

        # Player on pole: slightly forward, left of grid centre.
        player = (
            start_world_x + fx * self._POLE_FORWARD_OFFSET - rx * self._GRID_SIDE,
            start_world_y + fy * self._POLE_FORWARD_OFFSET - ry * self._GRID_SIDE,
        )

        # AI cars fill rows behind the player, alternating right/left.
        # Index 0 -> row 0 right; 1 -> row 1 left; 2 -> row 1 right; ...
        ai_positions: list[tuple[float, float]] = []
        for i in range(ai_count):
            row = (i + 1) // 2
            side = 1 if (i % 2 == 0) else -1
            fwd = -self._GRID_ROW_GAP * row - self._POLE_FORWARD_OFFSET
            lat = side * self._GRID_SIDE
            ai_positions.append((
                start_world_x + fx * fwd + rx * lat,
                start_world_y + fy * fwd + ry * lat,
            ))
        return player, ai_positions

    def _pick_ai_car_stacks(self, count: int) -> list[tuple[str, list[pygame.Surface]]]:
        """Pick *count* (name, sprite_stack) pairs, avoiding the player's car.

        The name is returned alongside the stack so each AI can look up the
        handling profile bound to its own car model.
        """
        cars = self.manager.app_data.cars
        player_name = self.manager.app_data.current_car_name
        others = [(name, cars[name]) for name in sorted(cars.keys()) if name != player_name]
        if not others:
            others = [(player_name, cars[player_name])]
        # Cycle through the available non-player stacks to fill the grid even
        # if there are fewer unique cars than AI slots.
        return [others[i % len(others)] for i in range(count)]

    def handle_event(self, event) -> None:
        controls = self.current_car.controls

        if event.type == pygame.KEYDOWN:
            match event.key:
                case K.LEFT:
                    with self.world.lock:
                        controls.left_pressed = True
                        controls.steer_input = 1
                case K.RIGHT:
                    with self.world.lock:
                        controls.right_pressed = True
                        controls.steer_input = -1
                case K.UP:
                    with self.world.lock:
                        controls.up_input = True
                case K.DOWN:
                    with self.world.lock:
                        controls.down_input = True
                case pygame.K_SPACE:
                    with self.world.lock:
                        controls.drift_input = True

                case pygame.K_ESCAPE:
                    # Capture frozen game frame, then open pause menu. Works
                    # during the countdown too — the backdrop is just
                    # whatever was last drawn (map + cars + countdown digit).
                    self.manager.change_screen("pause")
                    self.manager.get_screen().backdrop = self.manager.screen_display.copy()

                case pygame.K_F1:
                    self._debug_checkpoints = not self._debug_checkpoints
        elif event.type == pygame.KEYUP:
            match event.key:
                case K.LEFT:
                    with self.world.lock:
                        controls.left_pressed = False
                        if controls.steer_input == 1:
                            controls.steer_input = -1 if controls.right_pressed else 0
                case K.RIGHT:
                    with self.world.lock:
                        controls.right_pressed = False
                        if controls.steer_input == -1:
                            controls.steer_input = 1 if controls.left_pressed else 0
                case K.UP:
                    with self.world.lock:
                        controls.up_input = False
                case K.DOWN:
                    with self.world.lock:
                        controls.down_input = False
                case pygame.K_SPACE:
                    with self.world.lock:
                        controls.drift_input = False

    def _start_threads(self) -> None:
        if self._threads_started:
            return

        if self.ai_active and self.pathfinder is not None:
            worker = PathfinderWorker(self.pathfinder)
            worker.start()
            self._pathfinder_worker = worker
            for controller in self.ai_controllers:
                controller.planner = worker

        self._physics_thread = PhysicsScheduler(
            world=self.world, snapshot_buffer=self.snapshot_buffer,
        )
        self._collision_thread = CollisionScheduler(
            world=self.world, snapshot_buffer=self.snapshot_buffer,
        )
        self._physics_thread.start()
        self._collision_thread.start()

        if self.ai_active and self._pathfinder_worker is not None:
            self._ai_thread = AIScheduler(
                world=self.world,
                snapshot_buffer=self.snapshot_buffer,
                pathfinder_worker=self._pathfinder_worker,
            )
            self._ai_thread.start()

        self._threads_started = True

    def _stop_threads(self) -> None:
        self.world.stop_event.set()
        self.world.pause_event.clear()
        for thread in (self._ai_thread, self._collision_thread, self._physics_thread):
            if thread is not None and thread.is_alive():
                thread.join(timeout=1.0)
        if self._pathfinder_worker is not None:
            self._pathfinder_worker.stop(timeout=1.0)
        self._ai_thread = None
        self._collision_thread = None
        self._physics_thread = None
        self._pathfinder_worker = None
        self._threads_started = False

    def on_deactivate(self) -> None:
        self.world.pause_event.set()

    def on_destroy(self) -> None:
        self._stop_threads()

    def _publish_initial_snapshot(self) -> None:
        from karkart.runtime.scheduler import _car_snapshot
        from karkart.runtime.snapshot import RacerSnapshot, WorldSnapshot

        self.snapshot_buffer.publish(WorldSnapshot(
            tick=0,
            player=_car_snapshot(self.current_car.physics),
            ai=[_car_snapshot(c.physics) for c in self.ai_cars],
            camera_angle=self.current_camera.angle,
            sparks=[],
            player_racer=RacerSnapshot(
                list_counter=self.player_state.list_counter,
                current_lap=self.player_state.current_lap,
                total_checkpoints=self.player_state.total_checkpoints,
            ),
            ai_racers=[
                RacerSnapshot(
                    list_counter=s.list_counter,
                    current_lap=s.current_lap,
                    total_checkpoints=s.total_checkpoints,
                )
                for s in self.ai_states
            ],
            item_active=[box.active for box in self.world_box],
            position_label=self.world.cached_position_label,
            race_finished=False,
        ))

    def update_resources(self) -> None:
        self.car_stacker.set_images(self.manager.app_data.current_car)
        self.mode = self.manager.app_data.modes[self.manager.app_data.current_mode]
        self.ai_active = self.mode["Ai"] and bool(self.ai_cars)
        for items_box in self.world_box:
            items_box.active = self.mode["Items"]
        self.current_map.active = self.mode["Items"]

        from karkart.runtime.scheduler import _compute_position_label
        with self.world.lock:
            self.world.cached_position_label = _compute_position_label(
                self.player_state, self.ai_states, ai_active=self.ai_active,
            )

        if not self.countdown.complete:
            self.countdown.resume()

        self.world.pause_event.clear()

    def update(self) -> None:
        if not self.countdown.complete:
            self.countdown.update()
            if self.countdown.complete:
                now = time.perf_counter()
                with self.world.lock:
                    self.world.begin_race(now)
                self._start_threads()
            return

        if self._race_finished:
            return

        if self.world.race_finished_event.is_set():
            self.complete_race()

    # ------------------------------------------------------------------ #
    # HUD + debug overlay                                                #
    # ------------------------------------------------------------------ #

    def _world_to_screen_real(
        self, wx: float, wy: float,
        *, player_x: float, player_y: float, camera_angle: float,
    ) -> tuple[int, int]:
        """Project a world-space point onto the real (unscaled) screen surface."""
        renderer = self.current_renderer
        dx = (wx - player_x) * renderer.map_zoom
        dy = (wy - player_y) * renderer.map_zoom
        angle_rad = math.radians(camera_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        fx = renderer.center[0] + rx
        fy = renderer.center[1] + ry
        screen_w, screen_h = self.manager.screen_display.get_size()
        frame_w, frame_h = renderer.render_size
        return int(fx * screen_w / frame_w), int(fy * screen_h / frame_h)

    def draw_hud(self, screen: pygame.Surface, snapshot: WorldSnapshot) -> None:
        total_cps = len(self.current_map.checkpoints_list) or 1
        cp_in_lap = snapshot.player_racer.list_counter
        lap = snapshot.player_racer.current_lap
        speed = snapshot.player.speed

        lines = [
            f"Lap  {lap}",
            f"CP   {cp_in_lap} / {total_cps}",
            f"Spd  {speed:+.2f}",
            f"Pos  {snapshot.position_label}",
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

        self._draw_minimap(screen, snapshot)

        if self._debug_checkpoints:
            self._draw_checkpoint_debug(screen, snapshot)

    # ------------------------------------------------------------------ #
    # Minimap                                                            #
    # ------------------------------------------------------------------ #

    _MINIMAP_SIZE: int = 180
    _MINIMAP_MARGIN: int = 12

    def _draw_minimap(self, screen: pygame.Surface, snapshot: WorldSnapshot) -> None:
        """Top-right corner minimap: shrunk track + dots for every car."""
        map_surf = self.current_map.map_surface
        map_w, map_h = map_surf.get_size()
        if map_w <= 0 or map_h <= 0:
            return

        size = self._MINIMAP_SIZE
        scale = min(size / map_w, size / map_h)
        mini_w = max(1, int(map_w * scale))
        mini_h = max(1, int(map_h * scale))

        screen_w = screen.get_size()[0]
        ox = screen_w - mini_w - self._MINIMAP_MARGIN
        oy = self._MINIMAP_MARGIN

        # Backdrop panel (semi-transparent so the track still reads clearly).
        panel = pygame.Surface((mini_w + 4, mini_h + 4), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 160))
        screen.blit(panel, (ox - 2, oy - 2))

        mini_map = pygame.transform.smoothscale(map_surf, (mini_w, mini_h))
        screen.blit(mini_map, (ox, oy))

        def world_to_mini(wx: float, wy: float) -> tuple[int, int]:
            # World is centred at origin — shift into [0, map_w) then scale.
            mx = (wx + map_w / 2) * scale
            my = (wy + map_h / 2) * scale
            return ox + int(mx), oy + int(my)

        # AI dots (red) first so the player stays on top when cars overlap.
        for ai_snap in snapshot.ai:
            ax, ay = world_to_mini(ai_snap.car_x, ai_snap.car_y)
            pygame.draw.circle(screen, (0, 0, 0), (ax, ay), 5)
            pygame.draw.circle(screen, (230, 70, 70), (ax, ay), 4)

        # Player dot (yellow).
        px, py = world_to_mini(snapshot.player.car_x, snapshot.player.car_y)
        pygame.draw.circle(screen, (0, 0, 0), (px, py), 5)
        pygame.draw.circle(screen, (250, 220, 60), (px, py), 4)

    def _draw_checkpoint_debug(self, screen: pygame.Surface, snapshot: WorldSnapshot) -> None:
        target_idx = snapshot.player_racer.list_counter
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
            corners_screen = [
                self._world_to_screen_real(
                    x, y,
                    player_x=snapshot.player.car_x,
                    player_y=snapshot.player.car_y,
                    camera_angle=snapshot.camera_angle,
                )
                for x, y in corners_world
            ]
            pygame.draw.polygon(screen, colour, corners_screen, width=2)

    def complete_race(self) -> None:
        if self._race_finished:
            return

        self._race_finished = True
        self._stop_threads()

        total_time = time.perf_counter() - self.world.race_start_time

        try:
            result = RaceResult(
                player_name="Player 1",
                car_name=self.manager.app_data.current_car_name,
                map_name=self.manager.app_data.current_map.name,
                total_time=total_time,
                lap_times=self.world.player_lap_times.copy(),
                total_laps=self.player_state.current_lap - 1,
            )
            GAME_LEADERBOARD.add(result)
        except Exception as error:
            print(f"Could not save race result: {error}")

        self.manager.add_screen("placeholder", LeaderboardScreen(self.manager))
        self.manager.change_screen("placeholder")

    def draw(self, _surface: pygame.Surface) -> None:
        screen = self.manager.screen_display

        snapshot = self.snapshot_buffer.read()
        if snapshot is None:
            return

        extra_cars = (
            list(zip(snapshot.ai, self.ai_stackers))
            if self.ai_active and snapshot.ai
            else []
        )

        for box, active in zip(self.world_box, snapshot.item_active):
            box.active = active

        self.current_renderer.render_frame(
            self.config.gameplay_stack_spread,
            player=snapshot.player,
            camera_angle=snapshot.camera_angle,
            sparks=snapshot.sparks,
            extra_cars=extra_cars,
        )

        if not self.countdown.complete:
            self.countdown.write()

        # HUD draws on the full-resolution display, on top of the pixelated map.
        self.draw_hud(screen, snapshot)

        pygame.display.flip()
