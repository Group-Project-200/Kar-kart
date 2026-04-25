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
from karkart.physics.car import Car, get_handling_for
from karkart.physics.checkpoint import Checkpoint, RacerState, advance_checkpoints
from karkart.physics.collision import CollisionDetector
from karkart.rendering.map import Map, MapData
from karkart.rendering.renderer import Renderer
from karkart.rendering.sparks import SparkManager
from karkart.rendering.stacker import Stacker
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
        self._race_start_time: float = 0.0
        self._last_lap_start_time: float = 0.0
        self._lap_times: list[float] = []


        # Alternating-frame scheduler: cheap per-frame work runs every tick;
        # expensive checks split across even/odd frames (see update()).
        self._frame_parity: int = 0

        # HUD + debug overlay.
        self._debug_checkpoints: bool = False
        if not pygame.font.get_init():
            pygame.font.init()
        self._hud_font: pygame.font.Font = pygame.font.SysFont("monospace", 16)

        # Per-racer checkpoint progression (lap, cursor, cumulative total).
        # AI states are only populated when AI cars are spawned below.
        self.player_state = RacerState()
        self._last_recorded_lap: int = self.player_state.current_lap
        self.ai_states: list[RacerState] = []

        # Per-car checkpoint geometry. The map's checkpoints_list is the
        # shared source of truth; each car gets its own independent clone so
        # their per-racer state can't interfere with each other.
        self.player_checkpoints: list[Checkpoint] = []
        self.ai_checkpoints: list[list[Checkpoint]] = []

        # Event-driven position ranking: only recomputed when a racer actually
        # passes a checkpoint. Avoids a per-frame O(N) scan in draw_hud().
        self._cp_pass_counter: int = 0
        self._cached_position_label: str = "1st"

        self.current_map_data, map_record = self.update_map()

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
                )

                self.ai_cars.append(ai_car)
                self.ai_stackers.append(stacker)
                self.ai_collisions.append(collision)
                self.ai_states.append(state)
                self.ai_controllers.append(controller)
                self.ai_checkpoints.append(ai_cp_list)

    # Grid stagger offsets: each row is one car-length behind the previous,
    # and cars alternate right/left so the line-up spreads across the track.
    _GRID_ROW_GAP: float = 26.0     # Forward spacing between rows (world units).
    _GRID_SIDE: float = 20.0        # Lateral offset per lane (world units).
    _POLE_FORWARD_OFFSET: float = 12.0  # Player slightly ahead of grid centre.


    def update_map(self):
        map_name = self.manager.app_data.current_map.name
        map_record = _MAP_DATA[map_name]

        current_map_data = MapData()
        current_map_data.checkpoints = map_record["checkpoints"]
        current_map_data.finish_line = map_record["finish_line"]
        current_map_data.layers = self.manager.app_data.return_map_layers()

        return current_map_data, map_record


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
                    controls.left_pressed = True
                    controls.steer_input = 1
                case K.RIGHT:
                    controls.right_pressed = True
                    controls.steer_input = -1
                case K.UP:
                    controls.up_input = True
                case K.DOWN:
                    controls.down_input = True
                case pygame.K_SPACE:
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
                    controls.left_pressed = False
                    if controls.steer_input == 1:
                        controls.steer_input = -1 if controls.right_pressed else 0
                case K.RIGHT:
                    controls.right_pressed = False
                    if controls.steer_input == -1:
                        controls.steer_input = 1 if controls.left_pressed else 0
                case K.UP:
                    controls.up_input = False
                case K.DOWN:
                    controls.down_input = False
                case pygame.K_SPACE:
                    controls.drift_input = False

    def _collision_check(self) -> None:
        car_relative_rotation = self.current_car.physics.rotation - self.current_camera.angle
        self.current_map.get_coordinates()
        dir_idx = snap_degrees(car_relative_rotation, dirs=self.car_stacker.dirs)
        offset = (self.current_map.car_map_x, self.current_map.car_map_y)
        hit = self.collision_detector.border_check(dir_idx, offset)
        self.current_car.collision_results = hit
        # On a fresh wall hit, sample the mask around the car to get an
        # outward normal; car_physics then reflects against it instead of
        # just reversing velocity.
        if hit:
            self.current_car.collision_normal = self.collision_detector.estimate_normal(offset)
        else:
            self.current_car.collision_normal = None


        for items_box in self.world_box:
            powered_up = items_box.check(self.current_car.physics.car_x, self.current_car.physics.car_y)
            if powered_up and self.power_ups_manager.current is None:
                self.power_ups_manager.current = self.power_ups_manager.choose_random_powerup()
                self.power_ups_manager.current.activate(self.current_car.physics)

    def _ai_collision_check(self) -> None:
        """Test every AI car against the same map masks the player uses."""
        cache = self.current_map.cache
        assert cache is not None and cache.zoom is not None
        for ai_car, stacker, collision in zip(self.ai_cars, self.ai_stackers, self.ai_collisions):
            ai_map_x = cache.center_x + int(ai_car.physics.car_x * cache.zoom)
            ai_map_y = cache.center_y + int(ai_car.physics.car_y * cache.zoom)
            dir_idx = snap_degrees(ai_car.physics.rotation, dirs=stacker.dirs)
            hit = collision.border_check(dir_idx, (ai_map_x, ai_map_y))
            ai_car.collision_results = hit
            if hit:
                ai_car.collision_normal = collision.estimate_normal((ai_map_x, ai_map_y))
            else:
                ai_car.collision_normal = None



    def _separate_two(self, a: Car, b: Car) -> None:
        """Push two cars apart along their centre-to-centre axis until they no longer overlap."""
        p, q = a.physics, b.physics
        dx = p.car_x - q.car_x
        dy = p.car_y - q.car_y
        dist = math.hypot(dx, dy) or 0.001
        overlap = self._CAR_COLLISION_RADIUS - dist
        if overlap <= 0:
            return
        nx, ny = dx / dist, dy / dist
        p.car_x += nx * overlap / 2
        p.car_y += ny * overlap / 2
        q.car_x -= nx * overlap / 2
        q.car_y -= ny * overlap / 2

    def _resolve_pair_collision(self, a: Car, b: Car, a_cp: int, b_cp: int) -> None:
        """Resolve overlap between two cars with impulse bounce and speed penalty."""
        p, q = a.physics, b.physics
        dx = p.car_x - q.car_x
        dy = p.car_y - q.car_y
        dist_sq = dx * dx + dy * dy
        if dist_sq >= self._CAR_COLLISION_RADIUS ** 2:
            return
        dist = math.sqrt(dist_sq) or 0.001
        nx, ny = dx / dist, dy / dist

        self._separate_two(a, b)

        impulse = a.handling.car_restitution
        p.velocity_x += nx * impulse
        p.velocity_y += ny * impulse
        q.velocity_x -= nx * impulse
        q.velocity_y -= ny * impulse

        # Checkpoint-priority speed penalty: the car that's further along the
        # track keeps most of its momentum; the car behind loses a lot.
        if a_cp > b_cp:
            p.speed *= 0.85
            q.speed *= 0.45
        elif b_cp > a_cp:
            p.speed *= 0.45
            q.speed *= 0.85
        else:
            p.speed *= 0.6
            q.speed *= 0.6

    def _check_car_to_car_collision(self) -> None:
        """Resolve overlaps between player and every AI, plus AI↔AI pairs."""
        player_cp = self.player_state.list_counter
        for ai_car, ai_state in zip(self.ai_cars, self.ai_states):
            self._resolve_pair_collision(
                self.current_car, ai_car, player_cp, ai_state.list_counter,
            )
        # AI vs AI pairs. N is small (4 AIs -> 6 pairs).
        for i in range(len(self.ai_cars)):
            for j in range(i + 1, len(self.ai_cars)):
                self._resolve_pair_collision(
                    self.ai_cars[i], self.ai_cars[j],
                    self.ai_states[i].list_counter, self.ai_states[j].list_counter,
                )

    def _register_pass(self, state: RacerState) -> None:
        """Record that *state* just crossed a checkpoint and refresh the rank."""
        self._cp_pass_counter += 1
        state.last_pass_order = self._cp_pass_counter
        self._recompute_position_label()

    def _update_checkpoints_player(self) -> None:
        old_lap = self.player_state.current_lap

        advance_checkpoints(
            self.player_state,
            self.current_map.checkpoints_list,
            self.current_car.physics.car_x,
            self.current_car.physics.car_y,
            items_active=self.current_map.active,
            world_objects=self.world_box,
        )

        if self.player_state.current_lap > old_lap and self._last_lap_start_time > 0.0:
            now = time.perf_counter()
            lap_time = now - self._last_lap_start_time
            self._lap_times.append(lap_time)
            self._last_lap_start_time = now
            self._last_recorded_lap = self.player_state.current_lap

    def _update_checkpoints_ai(self) -> None:
        for ai_car, state, controller, checkpoints in zip(
            self.ai_cars, self.ai_states, self.ai_controllers, self.ai_checkpoints,
        ):
            # Don't advance checkpoints if AI is in recovery mode (reversing or reorienting)
            if controller.is_in_recovery():
                continue
            prev_total = state.total_checkpoints
            advance_checkpoints(
                state,
                checkpoints,
                ai_car.physics.car_x,
                ai_car.physics.car_y,
            )
            if state.total_checkpoints != prev_total:
                self._register_pass(state)

    def ai_update(self):
        if not self.ai_active:
            return

        if self._frame_parity == 0:
            self._ai_collision_check()
            self._check_car_to_car_collision()
        else:
            self._update_checkpoints_ai()
            for controller in self.ai_controllers:
                controller.update()

        for ai_car in self.ai_cars:
            ai_car.physics = ai_car.step_physics_with_controls(
                snap_step_degrees=self.config.rotation_snap_degrees,
            )

    def update(self) -> None:
        if not self.countdown.complete:
            self.countdown.update()
            return

        if self._race_start_time == 0.0:
            now = time.perf_counter()
            self._race_start_time = now
            self._last_lap_start_time = now

        if self._race_finished:
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

    def _recompute_position_label(self) -> None:
        """Rebuild the cached position string from pure checkpoint order.

        Called only when a racer actually crosses a checkpoint — there's no
        per-frame work. A racer ranks ahead if they have passed more
        checkpoints overall; ties are broken by who reached that total first
        (smaller ``last_pass_order``).
        """
        if not self.ai_active:
            self._cached_position_label = "1st"
            return
        # Higher total = ahead. On tie, earlier pass_order = ahead, so we
        # negate it to sort descending alongside total_checkpoints.
        me = (self.player_state.total_checkpoints, -self.player_state.last_pass_order)
        ahead = 0
        for s in self.ai_states:
            if (s.total_checkpoints, -s.last_pass_order) > me:
                ahead += 1
        rank = ahead + 1
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank, "th")
        self._cached_position_label = f"{rank}{suffix}"

    def _position_label(self) -> str:
        return self._cached_position_label

    def draw_hud(self, screen: pygame.Surface) -> None:
        total_cps = len(self.current_map.checkpoints_list) or 1
        cp_in_lap = self.player_state.list_counter
        lap = self.player_state.current_lap
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

        self._draw_minimap(screen)

        if self._debug_checkpoints:
            self._draw_checkpoint_debug(screen)

    # ------------------------------------------------------------------ #
    # Minimap                                                            #
    # ------------------------------------------------------------------ #

    _MINIMAP_SIZE: int = 180
    _MINIMAP_MARGIN: int = 12

    def _draw_minimap(self, screen: pygame.Surface) -> None:
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
        for ai_car in self.ai_cars:
            ax, ay = world_to_mini(ai_car.physics.car_x, ai_car.physics.car_y)
            pygame.draw.circle(screen, (0, 0, 0), (ax, ay), 5)
            pygame.draw.circle(screen, (230, 70, 70), (ax, ay), 4)

        # Player dot (yellow).
        px, py = world_to_mini(self.current_car.physics.car_x, self.current_car.physics.car_y)
        pygame.draw.circle(screen, (0, 0, 0), (px, py), 5)
        pygame.draw.circle(screen, (250, 220, 60), (px, py), 4)

    def _draw_checkpoint_debug(self, screen: pygame.Surface) -> None:
        target_idx = self.player_state.list_counter
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
        if self.player_state.current_lap <= 3 or self._race_finished:
            return

        self._race_finished = True
        total_time = time.perf_counter() - self._race_start_time

        try:
            result = RaceResult(
                player_name="Player 1",
                car_name=self.manager.app_data.current_car_name,
                map_name=self.manager.app_data.current_map.name,
                total_time=total_time,
                lap_times=self._lap_times.copy(),
                total_laps=self.player_state.current_lap - 1,
            )
            GAME_LEADERBOARD.add(result)
        except Exception as error:
            print(f"Could not save race result: {error}")

        self.manager.add_screen("placeholder", LeaderboardScreen(self.manager))
        self.manager.change_screen("placeholder")

    def draw(self, _surface: pygame.Surface) -> None:
        screen = self.manager.screen_display

        extra_cars = list(zip(self.ai_cars, self.ai_stackers)) if self.ai_active else []

        self.current_renderer.render_frame(
            self.config.gameplay_stack_spread, extra_cars=extra_cars,
        )

        if not self.countdown.complete:
            self.countdown.write()

        # HUD draws on the full-resolution display, on top of the pixelated map.
        self.draw_hud(screen)

        pygame.display.flip()
