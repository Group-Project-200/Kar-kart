from __future__ import annotations

import math
from dataclasses import dataclass, field

import pygame

from karkart.helpers import (
    blend_toward,
    clamp,
    forward_vector,
    move_toward,
    snap_angle,
)
from karkart.physics.collision import apply_wall_bounce, push_out_of_wall


def _update_steer_hold(
    steer_input: int,
    previous_steer_input: int,
    steer_hold_frames: int,
) -> tuple[int, int]:

    if steer_input == 0:
        return 0, steer_input
    if steer_input != previous_steer_input:
        return 1, steer_input
    return steer_hold_frames + 1, steer_input


def _resolve_drift_direction(
    steer_input: int,
    left_pressed: bool,
    right_pressed: bool,
) -> int:

    if left_pressed and not right_pressed:
        return 1
    if right_pressed and not left_pressed:
        return -1
    if steer_input > 0:
        return 1
    if steer_input < 0:
        return -1
    return 0


def _update_position(
    car_x: float,
    car_y: float,
    velocity_x: float,
    velocity_y: float,
) -> tuple[float, float]:
    return car_x + velocity_x, car_y + velocity_y


def _update_hop(physics: "PhysicsState", handling: "CarHandling") -> None:

    if physics.car_z <= 0.0 and physics.velocity_z <= 0.0:
        return
    physics.velocity_z += handling.hop_gravity
    physics.car_z = max(0.0, physics.car_z + physics.velocity_z)
    if physics.car_z == 0.0:
        physics.velocity_z = 0.0


@dataclass(frozen=True, slots=True)
class BoostTier:

    duration_frames: int
    acceleration: float
    max_speed_delta: float


@dataclass(frozen=True, slots=True)
class CarHandling:

    plateau_acceleration: float = 0.35
    turn_damping: float = 0.2
    max_turn_rate: float = 2.3
    turn_stop_epsilon: float = 0.05
    initial_turn_acceleration: float = 0.1
    late_turn_acceleration: float = 0.15
    initial_phase_frames: int = 4
    plateau_phase_frames: int = 7
    plateau_turn_rate: float = 1.6
    turn_direction_change_damping: float = 0.35

    throttle_acceleration: float = 0.05
    coast_deceleration: float = 0.004
    brake_deceleration: float = 0.09
    reverse_acceleration: float = 0.04
    max_speed: float = 3.0
    max_reverse_speed: float = 1.0
    min_steer_speed: float = 0.03
    turn_speed_penalty: float = 0.01
    min_turn_drag: float = 0.03

    speed_hold_floor_value: float = 1.5
    speed_hold_activation_min_value: float = 1.3
    hold_cancel_turn_rate: float = 1.6
    turn_top_speed_falloff: float = 0.35

    hop_velocity: float = 0.35
    hop_gravity: float = -0.045
    hop_pixel_scale: float = 12.0

    overspeed_near_threshold: float = 0.9
    overspeed_mid_threshold: float = 1.25
    overspeed_deceleration_near: float = 0.006
    overspeed_deceleration_mid: float = 0.011
    overspeed_deceleration_far: float = 0.05

    max_slip: float = 0.95
    speed_slip_weight: float = 0.35
    turn_slip_weight: float = 0.2
    coast_velocity_decay: float = 0.01
    overspeed_coast_velocity_decay: float = 0.8
    stop_speed_epsilon: float = 1e-6
    stop_velocity_epsilon: float = 1e-3

    default_slide_factor: float = 0.4
    drift_charge_short_frames: int = 40
    drift_charge_long_frames: int = 70
    drift_base_steer_strength: float = 0.65
    drift_sharp_steer_strength: float = 0.75
    drift_slow_steer_strength: float = 0.45
    drift_base_skew_degrees: float = 20.0
    drift_sharp_skew_degrees: float = 14.0
    drift_slow_skew_degrees: float = 28.0
    drift_unskew_step_degrees: float = 5.0
    drift_release_countersteer_degrees: float = 10.0
    drift_release_countersteer_turn_rate: float = 0.8

    wall_restitution: float = 1.5
    car_restitution: float = 0.65
    wall_stun_frames: int = 34
    wall_slide_decay: float = 0.97

    short_boost: BoostTier = field(
        default_factory=lambda: BoostTier(
            duration_frames=3, acceleration=0.45, max_speed_delta=1.25
        ),
    )
    long_boost: BoostTier = field(
        default_factory=lambda: BoostTier(
            duration_frames=5, acceleration=0.9, max_speed_delta=2.5
        ),
    )

    @property
    def plateau_end_frame(self) -> int:
        return self.initial_phase_frames + self.plateau_phase_frames

    @property
    def hold_floor(self) -> float:
        return min(self.speed_hold_floor_value, self.max_speed)

    @property
    def hold_activation_min(self) -> float:
        return min(self.speed_hold_activation_min_value, self.hold_floor)

    @property
    def max_reference_speed(self) -> float:
        return max(self.max_speed, self.max_reverse_speed)

    @property
    def drift_min_speed(self) -> float:
        return self.min_steer_speed

    def overspeed_deceleration_step(
        self, speed: float, max_forward_speed: float
    ) -> float:

        overspeed = speed - max_forward_speed
        if overspeed <= 0.0:
            return 0.0
        if overspeed >= self.overspeed_mid_threshold:
            return self.overspeed_deceleration_far
        if overspeed >= self.overspeed_near_threshold:
            return self.overspeed_deceleration_mid
        return self.overspeed_deceleration_near

    def coast_velocity_decay_for_speed(self, abs_speed: float) -> float:
        if abs_speed > self.max_speed:
            return self.overspeed_coast_velocity_decay
        return self.coast_velocity_decay

    def boost_for_charge(self, drift_charge_frames: int) -> BoostTier | None:

        if drift_charge_frames >= self.drift_charge_long_frames:
            return self.long_boost
        if drift_charge_frames >= self.drift_charge_short_frames:
            return self.short_boost
        return None


@dataclass(slots=True)
class PhysicsState:

    rotation: float = 0.0
    turn_rate: float = 0.0
    steer_hold_frames: int = 0
    previous_steer_input: int = 0

    speed: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    car_x: float = 0.0
    car_y: float = 0.0

    car_z: float = 0.0
    velocity_z: float = 0.0

    drift_direction: int = 0
    drift_skew_degrees: float = 0.0
    drift_charge_frames: int = 0
    boost_frames: int = 0
    boost_level: int = 0
    boost_acceleration: float = 0.0
    boost_max_speed: float = 0.0
    drift_active: bool = False
    wall_stun_frames: int = 0


@dataclass(slots=True)
class ControlState:

    steer_input: int = 0
    left_pressed: bool = False
    right_pressed: bool = False
    up_input: bool = False
    down_input: bool = False
    drift_input: bool = False
    min_speed_request: float = 0.0


class Car:

    def __init__(self, handling: "CarHandling | None" = None, name : str | None = None) -> None:
        self.name = name
        self.handling = handling if handling is not None else CarHandling()
        self.physics = PhysicsState()
        self.controls = ControlState()

        self.last_safe_x: float | None = None
        self.last_safe_y: float | None = None
        self.last_safe_x2: float | None = None
        self.last_safe_y2: float | None = None
        self.collision_results: bool = False

        self.collision_normal: tuple[float, float] | None = None

        self.hitbox: pygame.Rect = pygame.Rect(0, 0, 20, 20)

    def sync_hitbox(self) -> None:
        self.hitbox.center = (int(self.physics.car_x), int(self.physics.car_y))

    def _drift_tuning(
        self,
        left_pressed: bool,
        right_pressed: bool,
        drift_direction: int,
    ) -> tuple[float, float]:

        if drift_direction > 0:
            sharper = left_pressed and not right_pressed
            slower = right_pressed and not left_pressed
        else:
            sharper = right_pressed and not left_pressed
            slower = left_pressed and not right_pressed

        if sharper:
            return (
                self.handling.drift_sharp_steer_strength,
                self.handling.drift_sharp_skew_degrees,
            )
        if slower:
            return (
                self.handling.drift_slow_steer_strength,
                self.handling.drift_slow_skew_degrees,
            )
        return (
            self.handling.drift_base_steer_strength,
            self.handling.drift_base_skew_degrees,
        )

    def _try_start_drift(
        self,
        *,
        steer_input: int,
        left_pressed: bool,
        right_pressed: bool,
        drift_input: bool,
    ) -> None:
        if (
            self.physics.drift_active
            or not drift_input
            or self.physics.speed < self.handling.drift_min_speed
            or self.physics.car_z > 0.0
            or self.physics.velocity_z > 0.0
        ):
            return

        drift_direction = _resolve_drift_direction(
            steer_input, left_pressed, right_pressed
        )
        if not drift_direction:
            return

        self.physics.drift_direction = drift_direction
        self.physics.drift_active = True
        self.physics.drift_charge_frames = 0
        self.physics.velocity_z = self.handling.hop_velocity

    def _set_boost(self, *, tier: BoostTier) -> None:
        self.physics.boost_frames = tier.duration_frames
        self.physics.boost_level = 2 if tier is self.handling.long_boost else 1
        self.physics.boost_acceleration = tier.acceleration
        self.physics.boost_max_speed = self.handling.max_speed + tier.max_speed_delta

    def _apply_drift_release_boost(self) -> None:
        tier = self.handling.boost_for_charge(self.physics.drift_charge_frames)
        if tier is None:
            return
        self._set_boost(tier=tier)

    def _stop_drift(self, *, released: bool) -> None:
        if released:
            self._apply_drift_release_boost()
        if released and self.physics.drift_direction:

            self.physics.rotation -= (
                self.physics.drift_direction
                * self.handling.drift_release_countersteer_degrees
            )
            self.physics.turn_rate = (
                -self.physics.drift_direction
                * self.handling.drift_release_countersteer_turn_rate
            )

        self.physics.drift_active = False
        self.physics.drift_charge_frames = 0

    def _resolve_steering_and_skew(
        self,
        *,
        steer_input: int,
        left_pressed: bool,
        right_pressed: bool,
        handling: CarHandling,
    ) -> tuple[int, float]:

        if self.physics.drift_active:
            self.physics.drift_charge_frames += 1
            steer_strength, drift_skew = self._drift_tuning(
                left_pressed,
                right_pressed,
                self.physics.drift_direction,
            )
            self.physics.drift_skew_degrees = drift_skew
            return self.physics.drift_direction, steer_strength

        self.physics.drift_skew_degrees = move_toward(
            self.physics.drift_skew_degrees,
            0.0,
            self.handling.drift_unskew_step_degrees,
        )
        if self.physics.drift_skew_degrees == 0.0:
            self.physics.drift_direction = 0

        steer_for_physics = self.filter_steer_input(steer_input, self.physics.speed)

        if self.physics.speed < -handling.min_steer_speed:
            steer_for_physics *= -1
        return steer_for_physics, 1.0

    def filter_steer_input(self, steer_input: int, speed: float) -> int:

        if abs(speed) < self.handling.min_steer_speed:
            return 0
        steer = int(steer_input)
        if steer > 0:
            return 1
        if steer < 0:
            return -1
        return 0

    def update_rotation(
        self,
        rotation: float,
        turn_rate: float,
        steer_input: int,
        steer_hold_frames: int,
        *,
        steer_strength: float = 1.0,
        snap_step_degrees: float | None = None,
    ) -> tuple[float, float]:

        steer = int(steer_input)
        steer_strength = clamp(steer_strength, 0.0, 2.0)
        max_turn_rate = self.handling.max_turn_rate * clamp(steer_strength, 0.35, 1.5)

        if steer:

            if turn_rate * steer < 0:
                turn_rate = move_toward(
                    turn_rate, 0.0, self.handling.turn_direction_change_damping
                )

            if steer_hold_frames <= self.handling.initial_phase_frames:
                turn_rate += (
                    steer * self.handling.initial_turn_acceleration * steer_strength
                )
            elif steer_hold_frames <= self.handling.plateau_end_frame:
                target_turn_rate = (
                    steer * self.handling.plateau_turn_rate * steer_strength
                )
                turn_rate = move_toward(
                    turn_rate,
                    target_turn_rate,
                    self.handling.plateau_acceleration * steer_strength,
                )
            else:
                turn_rate += (
                    steer * self.handling.late_turn_acceleration * steer_strength
                )

            turn_rate = clamp(turn_rate, -max_turn_rate, max_turn_rate)
        else:
            turn_rate = move_toward(turn_rate, 0.0, self.handling.turn_damping)

        rotation += turn_rate

        if not steer and abs(turn_rate) <= self.handling.turn_stop_epsilon:
            turn_rate = 0.0
            if snap_step_degrees is not None:
                rotation = snap_angle(rotation, snap_step_degrees)

        return rotation, turn_rate

    def update_speed(
        self,
        speed: float,
        up_input: bool,
        down_input: bool,
        turn_rate: float,
        *,
        max_forward_speed: float | None = None,
    ) -> float:

        if max_forward_speed is None:
            max_forward_speed = self.handling.max_speed

        throttle = up_input and not down_input
        brake = down_input and not up_input
        abs_turn = abs(turn_rate)
        sharp_turn = abs_turn >= self.handling.hold_cancel_turn_rate

        turn_ratio = (
            min(1.0, abs_turn / self.handling.max_turn_rate)
            if self.handling.max_turn_rate
            else 0.0
        )
        effective_cap = max_forward_speed * (
            1.0 - self.handling.turn_top_speed_falloff * turn_ratio
        )
        effective_floor = min(self.handling.hold_floor, effective_cap)

        hold_enabled = (
            not brake
            and not sharp_turn
            and (
                speed >= effective_floor
                or (throttle and speed >= self.handling.hold_activation_min)
            )
        )

        if throttle:
            if speed < 0.0:
                speed = min(speed + self.handling.brake_deceleration, 0.0)
            if speed < effective_cap:
                speed = min(
                    speed + self.handling.throttle_acceleration, effective_cap
                )
            elif speed > effective_cap:
                overspeed_step = self.handling.overspeed_deceleration_step(
                    speed, effective_cap
                )
                speed = move_toward(
                    speed,
                    effective_cap,
                    max(self.handling.coast_deceleration, overspeed_step),
                )
        elif brake:
            if speed > 0.0:
                speed = max(speed - self.handling.brake_deceleration, 0.0)
            else:
                speed = max(
                    speed - self.handling.reverse_acceleration,
                    -self.handling.max_reverse_speed,
                )
        else:
            coast_target = effective_floor if hold_enabled else 0.0
            speed = move_toward(speed, coast_target, self.handling.coast_deceleration)

        turn_drag = abs_turn * self.handling.turn_speed_penalty
        if turn_drag > self.handling.min_turn_drag:
            drag_target = effective_floor if hold_enabled else 0.0
            speed = move_toward(speed, drag_target, turn_drag)

        if not throttle and speed > effective_cap:
            overspeed_step = self.handling.overspeed_deceleration_step(
                speed, effective_cap
            )
            speed = move_toward(
                speed,
                effective_cap,
                max(self.handling.coast_deceleration, overspeed_step),
            )

        if throttle and not sharp_turn and speed >= self.handling.hold_activation_min:
            speed = max(speed, effective_floor)

        return speed

    def update_velocity(
        self,
        velocity_x: float,
        velocity_y: float,
        rotation: float,
        speed: float,
        turn_rate: float,
        *,
        slide_factor: float | None = None,
        drift_direction: int = 0,
        drift_skew_degrees: float = 0.0,
    ) -> tuple[float, float]:

        if slide_factor is None:
            slide_factor = self.handling.default_slide_factor

        abs_speed = abs(speed)
        forward_x, forward_y = forward_vector(rotation)
        target_vx = forward_x * speed
        target_vy = forward_y * speed

        if drift_direction:
            slide_factor = max(slide_factor - 0.08, 0.0)
            drift_dir = 1 if drift_direction > 0 else -1
            skew_degrees = clamp(drift_skew_degrees, 0.0, 45.0)
            if skew_degrees:
                drift_x, drift_y = forward_vector(rotation - (drift_dir * skew_degrees))
                target_vx = drift_x * speed
                target_vy = drift_y * speed

        speed_ratio = (
            abs_speed / self.handling.max_reference_speed
            if self.handling.max_reference_speed
            else 0.0
        )
        speed_ratio = clamp(speed_ratio, 0.0, 1.0)
        turn_ratio = (
            abs(turn_rate) / self.handling.max_turn_rate
            if self.handling.max_turn_rate
            else 0.0
        )
        slip = (
            slide_factor
            + (speed_ratio * self.handling.speed_slip_weight)
            + (turn_ratio * self.handling.turn_slip_weight)
        )
        slip = clamp(slip, 0.0, self.handling.max_slip)
        grip = 1.0 - slip

        velocity_x = blend_toward(velocity_x, target_vx, grip)
        velocity_y = blend_toward(velocity_y, target_vy, grip)

        coast_velocity_decay = self.handling.coast_velocity_decay_for_speed(abs_speed)
        if abs_speed > self.handling.max_speed:
            velocity_x = blend_toward(velocity_x, target_vx, coast_velocity_decay)
            velocity_y = blend_toward(velocity_y, target_vy, coast_velocity_decay)
        elif abs_speed <= self.handling.stop_speed_epsilon:
            velocity_x *= coast_velocity_decay
            velocity_y *= coast_velocity_decay

        if abs(velocity_x) < self.handling.stop_velocity_epsilon:
            velocity_x = 0.0
        if abs(velocity_y) < self.handling.stop_velocity_epsilon:
            velocity_y = 0.0

        return velocity_x, velocity_y

    def step_physics(
        self,
        *,
        steer_input: int,
        left_pressed: bool,
        right_pressed: bool,
        up_input: bool,
        down_input: bool,
        drift_input: bool,
        snap_step_degrees: float | None = None,
        slide_factor: float | None = None,
    ) -> PhysicsState:

        if self.physics.wall_stun_frames > 0:
            if self.collision_results and self.collision_normal is not None:
                # hit another wall mid-slide — re-bounce instead of zeroing speed
                vx, vy = self.physics.velocity_x, self.physics.velocity_y
                self.physics.car_x, self.physics.car_y = push_out_of_wall(
                    self.physics.car_x,
                    self.physics.car_y,
                    self.collision_normal,
                )
                self.physics.velocity_x, self.physics.velocity_y = apply_wall_bounce(
                    vx,
                    vy,
                    self.collision_normal,
                    self.handling.wall_restitution,
                )
                fwd_x, fwd_y = forward_vector(self.physics.rotation)
                self.physics.speed = (
                    self.physics.velocity_x * fwd_x
                    + self.physics.velocity_y * fwd_y
                )
                self.physics.wall_stun_frames = self.handling.wall_stun_frames
                self.collision_normal = None
                return self.physics
            self.physics.wall_stun_frames -= 1
            self.last_safe_x2 = self.last_safe_x
            self.last_safe_y2 = self.last_safe_y
            self.last_safe_x = self.physics.car_x
            self.last_safe_y = self.physics.car_y
            self.physics.car_x += self.physics.velocity_x
            self.physics.car_y += self.physics.velocity_y
            decay = self.handling.wall_slide_decay
            self.physics.velocity_x *= decay
            self.physics.velocity_y *= decay
            self.physics.speed *= decay
            _update_hop(self.physics, self.handling)
            return self.physics

        if self.collision_results:
            vx, vy = self.physics.velocity_x, self.physics.velocity_y
            if self.collision_normal is not None:
                normal = self.collision_normal
            else:
                mag = math.hypot(vx, vy) or 1.0
                normal = (-vx / mag, -vy / mag)

            # push just clear of the wall surface, then slide away with reflected velocity
            self.physics.car_x, self.physics.car_y = push_out_of_wall(
                self.physics.car_x,
                self.physics.car_y,
                normal,
            )
            self.physics.velocity_x, self.physics.velocity_y = apply_wall_bounce(
                vx,
                vy,
                normal,
                self.handling.wall_restitution,
            )
            fwd_x, fwd_y = forward_vector(self.physics.rotation)
            self.physics.speed = (
                self.physics.velocity_x * fwd_x + self.physics.velocity_y * fwd_y
            )
            self.physics.wall_stun_frames = self.handling.wall_stun_frames
            self.collision_normal = None
            return self.physics

        self._try_start_drift(
            steer_input=steer_input,
            left_pressed=left_pressed,
            right_pressed=right_pressed,
            drift_input=drift_input,
        )

        drift_released = self.physics.drift_active and not drift_input
        drift_canceled = (
            self.physics.drift_active
            and self.physics.speed < self.handling.drift_min_speed
        )
        if drift_released or drift_canceled:
            self._stop_drift(released=drift_released)

        steer_for_physics, steer_strength = self._resolve_steering_and_skew(
            steer_input=steer_input,
            left_pressed=left_pressed,
            right_pressed=right_pressed,
            handling=self.handling,
        )

        self.physics.steer_hold_frames, self.physics.previous_steer_input = (
            _update_steer_hold(
                steer_for_physics,
                self.physics.previous_steer_input,
                self.physics.steer_hold_frames,
            )
        )

        self.physics.rotation, self.physics.turn_rate = self.update_rotation(
            self.physics.rotation,
            self.physics.turn_rate,
            steer_for_physics,
            self.physics.steer_hold_frames,
            steer_strength=steer_strength,
            snap_step_degrees=snap_step_degrees,
        )

        forward_speed_cap = (
            self.physics.boost_max_speed
            if self.physics.boost_frames > 0
            else self.handling.max_speed
        )
        self.physics.speed = self.update_speed(
            self.physics.speed,
            up_input,
            down_input,
            self.physics.turn_rate,
            max_forward_speed=forward_speed_cap,
        )

        if self.physics.boost_frames > 0:
            self.physics.speed = min(
                self.physics.speed + self.physics.boost_acceleration,
                self.physics.boost_max_speed,
            )
            self.physics.boost_frames -= 1
            if self.physics.boost_frames == 0:
                self.physics.boost_level = 0
                self.physics.boost_acceleration = 0.0
                self.physics.boost_max_speed = self.handling.max_speed

        active_drift_direction = (
            self.physics.drift_direction if self.physics.drift_skew_degrees > 0.0 else 0
        )
        self.physics.velocity_x, self.physics.velocity_y = self.update_velocity(
            self.physics.velocity_x,
            self.physics.velocity_y,
            self.physics.rotation,
            self.physics.speed,
            self.physics.turn_rate,
            slide_factor=slide_factor,
            drift_direction=active_drift_direction,
            drift_skew_degrees=self.physics.drift_skew_degrees,
        )

        self.last_safe_x2 = self.last_safe_x
        self.last_safe_y2 = self.last_safe_y
        self.last_safe_x = self.physics.car_x
        self.last_safe_y = self.physics.car_y

        self.physics.car_x, self.physics.car_y = _update_position(
            self.physics.car_x,
            self.physics.car_y,
            self.physics.velocity_x,
            self.physics.velocity_y,
        )

        _update_hop(self.physics, self.handling)

        return self.physics

    def step_physics_with_controls(
        self,
        snap_step_degrees: float | None = None,
        slide_factor: float | None = None,
    ) -> PhysicsState:

        return self.step_physics(
            steer_input=self.controls.steer_input,
            left_pressed=self.controls.left_pressed,
            right_pressed=self.controls.right_pressed,
            up_input=self.controls.up_input,
            down_input=self.controls.down_input,
            drift_input=self.controls.drift_input,
            snap_step_degrees=snap_step_degrees,
            slide_factor=slide_factor,
        )


from karkart.physics.car_profiles import (  # noqa: E402
    CAR_HANDLING_PROFILES,
    get_handling_for,
    randomize_for_ai,
)
