from __future__ import annotations

import threading
import time
import traceback
from typing import TYPE_CHECKING

from karkart.helpers import forward_vector, snap_degrees
from karkart.physics.checkpoint import advance_checkpoints
from karkart.runtime.snapshot import (
    CarSnapshot,
    RacerSnapshot,
    SparkSnapshot,
    WorldSnapshot,
)

if TYPE_CHECKING:
    from karkart.physics.car import Car, PhysicsState
    from karkart.runtime.snapshot import SnapshotBuffer
    from karkart.runtime.world import World


class FixedRateThread(threading.Thread):
    def __init__(self, *, world: "World", target_hz: float, name: str) -> None:
        super().__init__(name=name, daemon=True)
        self.world = world
        self._period = 1.0 / target_hz

    def run(self) -> None:
        period = self._period
        next_tick = time.perf_counter()
        while not self.world.stop_event.is_set():
            if self.world.pause_event.is_set():
                time.sleep(0.05)
                next_tick = time.perf_counter()
                continue
            try:
                self._tick()
            except Exception:
                traceback.print_exc()
            next_tick += period
            sleep_for = next_tick - time.perf_counter()
            if sleep_for > 0.0:
                if self.world.stop_event.wait(sleep_for):
                    return
            elif sleep_for < -period * 5.0:
                next_tick = time.perf_counter()

    def _tick(self) -> None:
        raise NotImplementedError


class PhysicsScheduler(FixedRateThread):
    _LAP_TARGET: int = 3

    def __init__(self, *, world: "World", snapshot_buffer: "SnapshotBuffer") -> None:
        super().__init__(world=world, target_hz=60.0, name="kk-physics")
        self.snapshot_buffer = snapshot_buffer

    def _tick(self) -> None:
        with self.world.lock:
            world = self.world
            player = world.player_car
            player.physics = player.step_physics_with_controls(
                snap_step_degrees=world.snap_step_degrees,
            )
            _apply_min_speed(player)

            ph = player.physics
            if ph.drift_active and ph.car_z <= 0.0:
                anchor_x = (
                    player.last_safe_x if player.last_safe_x is not None else ph.car_x
                )
                anchor_y = (
                    player.last_safe_y if player.last_safe_y is not None else ph.car_y
                )
                world.sparks.emit(
                    anchor_x, anchor_y, ph.rotation, ph.drift_charge_frames
                )

            pm = world.powerups_manager
            if pm.current is not None:
                if pm.current.tick(world):
                    pm.current = None

            for items_box in world.world_box:
                if items_box.check(ph.car_x, ph.car_y) and pm.current is None:
                    pm.current = pm.choose_random_powerup()
                    print(pm.current.name)
                    pm.current.activate(world)
                    break

            world.sparks.update()
            world.camera.update_camera_angle()

            for ai_car in world.ai_cars:
                ai_car.physics = ai_car.step_physics_with_controls(
                    snap_step_degrees=world.snap_step_degrees,
                )
                _apply_min_speed(ai_car)

            self._resolve_car_to_car()
            world.player_car.sync_hitbox()
            for ai_car in world.ai_cars:
                ai_car.sync_hitbox()
            self._advance_player_checkpoints()
            self._advance_ai_checkpoints()

            if (
                not world.race_finished_event.is_set()
                and world.player_state.current_lap > self._LAP_TARGET
            ):
                world.race_finished_event.set()

            snap = self._build_snapshot()
            world.tick += 1

        self.snapshot_buffer.publish(snap)

    def _resolve_car_to_car(self) -> None:
        world = self.world
        radius = world.car_collision_radius
        radius_sq = radius * radius
        player = world.player_car
        player_cp = world.player_state.list_counter
        for ai_car, ai_state in zip(world.ai_cars, world.ai_states):
            _resolve_pair(
                player,
                ai_car,
                player_cp,
                ai_state.list_counter,
                radius=radius,
                radius_sq=radius_sq,
                world=world,
            )
        n = len(world.ai_cars)
        for i in range(n):
            for j in range(i + 1, n):
                _resolve_pair(
                    world.ai_cars[i],
                    world.ai_cars[j],
                    world.ai_states[i].list_counter,
                    world.ai_states[j].list_counter,
                    radius=radius,
                    radius_sq=radius_sq,
                    world=world,
                )

    def _advance_player_checkpoints(self) -> None:
        world = self.world
        old_lap = world.player_state.current_lap
        advance_checkpoints(
            world.player_state,
            world.current_map.checkpoints_list,
            world.player_car.hitbox,
            items_active=world.current_map.active,
            world_objects=world.world_box,
        )
        if world.player_state.current_lap > old_lap and world.last_lap_start_time > 0.0:
            now = time.perf_counter()
            world.player_lap_times.append(now - world.last_lap_start_time)
            world.last_lap_start_time = now
            world.last_recorded_lap = world.player_state.current_lap

    def _advance_ai_checkpoints(self) -> None:
        world = self.world
        for ai_car, state, controller, checkpoints in zip(
            world.ai_cars,
            world.ai_states,
            world.ai_controllers,
            world.ai_checkpoints,
        ):
            if controller.is_in_recovery():
                continue
            prev_total = state.total_checkpoints
            advance_checkpoints(
                state,
                checkpoints,
                ai_car.hitbox,
            )
            if state.total_checkpoints != prev_total:
                world.cp_pass_counter += 1
                state.last_pass_order = world.cp_pass_counter
                world.cached_position_label = _compute_position_label(
                    world.player_state,
                    world.ai_states,
                    ai_active=True,
                )

    def _build_snapshot(self) -> WorldSnapshot:
        world = self.world
        return WorldSnapshot(
            tick=world.tick + 1,
            player=_car_snapshot(world.player_car.physics),
            ai=[_car_snapshot(c.physics) for c in world.ai_cars],
            camera_angle=world.camera.angle,
            sparks=[
                SparkSnapshot(
                    x=s.x,
                    y=s.y,
                    life=s.life,
                    max_life=s.max_life,
                    r=s.r,
                    g=s.g,
                    b=s.b,
                )
                for s in world.sparks.sparks
            ],
            player_racer=RacerSnapshot(
                list_counter=world.player_state.list_counter,
                current_lap=world.player_state.current_lap,
                total_checkpoints=world.player_state.total_checkpoints,
            ),
            ai_racers=[
                RacerSnapshot(
                    list_counter=s.list_counter,
                    current_lap=s.current_lap,
                    total_checkpoints=s.total_checkpoints,
                )
                for s in world.ai_states
            ],
            item_active=[box.active for box in world.world_box],
            position_label=world.cached_position_label,
            race_finished=world.race_finished_event.is_set(),
        )


class CollisionScheduler(FixedRateThread):
    def __init__(self, *, world: "World", snapshot_buffer: "SnapshotBuffer") -> None:
        super().__init__(world=world, target_hz=30.0, name="kk-collision")
        self.snapshot_buffer = snapshot_buffer

    def _tick(self) -> None:
        world = self.world
        with world.lock:
            cache = world.current_map.cache
            if cache is None or cache.zoom is None:
                return
            zoom = cache.zoom
            cx, cy = cache.center_x, cache.center_y
            player_ph = world.player_car.physics
            camera_angle = world.camera.angle
            player_dir_idx = snap_degrees(
                player_ph.rotation - camera_angle,
                dirs=world.car_stacker.dirs,
            )
            player_offset = (
                cx + int(player_ph.car_x * zoom),
                cy + int(player_ph.car_y * zoom),
            )
            ai_inputs: list[tuple[int, tuple[int, int]]] = []
            for ai_car, stacker in zip(world.ai_cars, world.ai_stackers):
                dir_idx = snap_degrees(ai_car.physics.rotation, dirs=stacker.dirs)
                offset = (
                    cx + int(ai_car.physics.car_x * zoom),
                    cy + int(ai_car.physics.car_y * zoom),
                )
                ai_inputs.append((dir_idx, offset))

        player_hit = world.collision_detector.border_check(
            player_dir_idx, player_offset
        )
        if world.player_invincible:
            player_hit = False
        player_normal = (
            world.collision_detector.estimate_normal(player_offset)
            if player_hit
            else None
        )
        ai_results: list[tuple[bool, tuple[float, float] | None]] = []
        for (dir_idx, offset), detector in zip(ai_inputs, world.ai_collisions):
            hit = detector.border_check(dir_idx, offset)
            normal = detector.estimate_normal(offset) if hit else None
            ai_results.append((hit, normal))

        with world.lock:
            world.player_car.collision_results = player_hit
            world.player_car.collision_normal = player_normal
            for ai_car, (hit, normal) in zip(world.ai_cars, ai_results):
                ai_car.collision_results = hit
                ai_car.collision_normal = normal


class AIScheduler(FixedRateThread):
    def __init__(self, *, world: "World", snapshot_buffer: "SnapshotBuffer") -> None:
        super().__init__(world=world, target_hz=30.0, name="kk-ai")
        self.snapshot_buffer = snapshot_buffer

    def _tick(self) -> None:
        with self.world.lock:
            for controller in self.world.ai_controllers:
                controller.update()


def _apply_min_speed(car: "Car") -> None:
    req = car.controls.min_speed_request
    if req <= 0.0:
        return
    if abs(car.physics.speed) < req:
        if car.physics.speed < 0.0:
            car.physics.speed = -req
        else:
            car.physics.speed = req


def _car_snapshot(physics: "PhysicsState") -> CarSnapshot:
    return CarSnapshot(
        car_x=physics.car_x,
        car_y=physics.car_y,
        rotation=physics.rotation,
        car_z=physics.car_z,
        speed=physics.speed,
        drift_active=physics.drift_active,
        drift_direction=physics.drift_direction,
        drift_skew_degrees=physics.drift_skew_degrees,
        drift_charge_frames=physics.drift_charge_frames,
    )


def _resolve_pair(
    a: "Car",
    b: "Car",
    a_cp: int,
    b_cp: int,
    *,
    radius: float,
    radius_sq: float,
    world: "World",
) -> None:
    p, q = a.physics, b.physics
    dx = p.car_x - q.car_x
    dy = p.car_y - q.car_y
    dist_sq = dx * dx + dy * dy
    if dist_sq >= radius_sq:
        return
    dist = dist_sq**0.5 or 0.001
    nx, ny = dx / dist, dy / dist
    overlap = radius - dist
    p.car_x += nx * overlap * 0.5
    p.car_y += ny * overlap * 0.5
    q.car_x -= nx * overlap * 0.5
    q.car_y -= ny * overlap * 0.5

    e = max(a.handling.car_restitution, b.handling.car_restitution)

    if world.player_invincible and a is world.player_car:
        q.velocity_x -= nx * e * 2.0
        q.velocity_y -= ny * e * 2.0
        q.speed *= 0.35
        return

    if world.player_invincible and b is world.player_car:
        p.velocity_x += nx * e * 2.0
        p.velocity_y += ny * e * 2.0
        p.speed *= 0.35
        return

    vrel_n = (p.velocity_x - q.velocity_x) * nx + (p.velocity_y - q.velocity_y) * ny
    if vrel_n >= 0.0:
        return
    j = -(1.0 + e) * vrel_n * 0.5
    p.velocity_x += j * nx
    p.velocity_y += j * ny
    q.velocity_x -= j * nx
    q.velocity_y -= j * ny

    # sync speed so physics doesn't fight the new velocity
    fwd_ax, fwd_ay = forward_vector(p.rotation)
    fwd_bx, fwd_by = forward_vector(q.rotation)
    p.speed = p.velocity_x * fwd_ax + p.velocity_y * fwd_ay
    q.speed = q.velocity_x * fwd_bx + q.velocity_y * fwd_by


def _compute_position_label(player_state, ai_states, *, ai_active: bool) -> str:
    if not ai_active:
        return "1st"
    me = (player_state.total_checkpoints, -player_state.last_pass_order)
    ahead = 0
    for s in ai_states:
        if (s.total_checkpoints, -s.last_pass_order) > me:
            ahead += 1
    rank = ahead + 1
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank, "th")
    return f"{rank}{suffix}"