import math
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BoostTier:
    duration_frames: int
    acceleration: float
    max_speed_delta: float


@dataclass(frozen=True, slots=True)
class CarHandling:
    # Rotation tuning.
    plateau_acceleration: float = 0.4
    turn_damping: float = 0.2
    max_turn_rate: float = 3.0
    turn_stop_epsilon: float = 0.05
    initial_turn_acceleration: float = 0.2
    late_turn_acceleration: float = 0.15
    initial_phase_frames: int = 4
    plateau_phase_frames: int = 7
    plateau_turn_rate: float = 2.0
    turn_direction_change_damping: float = 0.35

    # Speed and steering tuning.
    throttle_acceleration: float = 0.05
    coast_deceleration: float = 0.005
    brake_deceleration: float = 0.14
    reverse_acceleration: float = 0.04
    max_speed: float = 2.5
    max_reverse_speed: float = 1.0
    min_steer_speed: float = 0.03
    turn_speed_penalty: float = 0.01
    min_turn_drag: float = 0.03
    speed_hold_floor_value: float = 1.0
    speed_hold_activation_min_value: float = 0.9
    hold_cancel_turn_rate: float = 3.0

    # Overspeed tuning.
    overspeed_near_threshold: float = 0.75
    overspeed_mid_threshold: float = 1.25
    overspeed_deceleration_near: float = 0.008
    overspeed_deceleration_mid: float = 0.015
    overspeed_deceleration_far: float = 0.07

    # Velocity blending and stopping thresholds.
    max_slip: float = 0.95
    speed_slip_weight: float = 0.35
    turn_slip_weight: float = 0.2
    coast_velocity_decay: float = 0.01
    overspeed_coast_velocity_decay: float = 0.8
    stop_speed_epsilon: float = 1e-6
    stop_velocity_epsilon: float = 1e-3

    # Drift and release behavior.
    default_slide_factor: float = 0.3
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

    # Two-step boost tiers.
    short_boost: BoostTier = field(
        default_factory=lambda: BoostTier(
            duration_frames=3,
            acceleration=0.45,
            max_speed_delta=1.25,
        )
    )
    long_boost: BoostTier = field(
        default_factory=lambda: BoostTier(
            duration_frames=5,
            acceleration=0.9,
            max_speed_delta=2.5,
        )
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

    def overspeed_deceleration_step(self, speed: float, max_forward_speed: float) -> float:
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
        # Two-tier drift reward: short charge or full charge.
        if drift_charge_frames >= self.drift_charge_long_frames:
            return self.long_boost
        if drift_charge_frames >= self.drift_charge_short_frames:
            return self.short_boost
        return None


DEFAULT_CAR_HANDLING = CarHandling()


# Mutable runtime state advanced every frame.
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
    drift_direction: int = 0
    drift_skew_degrees: float = 0.0
    drift_charge_frames: int = 0
    boost_frames: int = 0
    boost_acceleration: float = 0.0
    boost_max_speed: float = 0.0
    drift_active: bool = False


@dataclass(slots=True)
class ControlState:
    steer_input: int = 0
    left_pressed: bool = False
    right_pressed: bool = False
    up_input: bool = False
    down_input: bool = False
    drift_input: bool = False


# Small math helpers used heavily in the physics hot path.
def _snap_angle(rotation: float, snap_step_degrees: float) -> float:
    if snap_step_degrees <= 0:
        return rotation
    return round(rotation / snap_step_degrees) * snap_step_degrees


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def _move_toward(value: float, target: float, step: float) -> float:
    if value < target:
        return min(value + step, target)
    if value > target:
        return max(value - step, target)
    return value


def _blend_toward(current: float, target: float, fraction: float) -> float:
    return current + (target - current) * fraction


def _forward_vector(rotation: float) -> tuple[float, float]:
    radians = math.radians(rotation)
    return -math.sin(radians), -math.cos(radians)


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


# Drift lifecycle helpers (start, tune, release).
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


def _drift_tuning(
    left_pressed: bool,
    right_pressed: bool,
    drift_direction: int,
    handling: CarHandling,
) -> tuple[float, float]:
    if drift_direction > 0:
        sharper = left_pressed and not right_pressed
        slower = right_pressed and not left_pressed
    else:
        sharper = right_pressed and not left_pressed
        slower = left_pressed and not right_pressed

    if sharper:
        return handling.drift_sharp_steer_strength, handling.drift_sharp_skew_degrees
    if slower:
        return handling.drift_slow_steer_strength, handling.drift_slow_skew_degrees
    return handling.drift_base_steer_strength, handling.drift_base_skew_degrees


def _try_start_drift(
    state: PhysicsState,
    *,
    steer_input: int,
    left_pressed: bool,
    right_pressed: bool,
    drift_input: bool,
    handling: CarHandling,
) -> None:
    if state.drift_active or not drift_input or abs(state.speed) < handling.drift_min_speed:
        return

    drift_direction = _resolve_drift_direction(steer_input, left_pressed, right_pressed)
    if not drift_direction:
        return

    state.drift_direction = drift_direction
    state.drift_active = True
    state.drift_charge_frames = 0


def _set_boost(state: PhysicsState, *, tier: BoostTier, handling: CarHandling) -> None:
    state.boost_frames = tier.duration_frames
    state.boost_acceleration = tier.acceleration
    state.boost_max_speed = handling.max_speed + tier.max_speed_delta


def _apply_drift_release_boost(state: PhysicsState, handling: CarHandling) -> None:
    tier = handling.boost_for_charge(state.drift_charge_frames)
    if tier is None:
        return
    _set_boost(state, tier=tier, handling=handling)


def _stop_drift(state: PhysicsState, *, released: bool, handling: CarHandling) -> None:
    if released:
        _apply_drift_release_boost(state, handling)
    if released and state.drift_direction:
        # Snap the car nose opposite the drift so it visibly counter-steers on release.
        state.rotation -= state.drift_direction * handling.drift_release_countersteer_degrees
        state.turn_rate = -state.drift_direction * handling.drift_release_countersteer_turn_rate

    state.drift_active = False
    state.drift_charge_frames = 0


def _resolve_steering_and_skew(
    state: PhysicsState,
    *,
    steer_input: int,
    left_pressed: bool,
    right_pressed: bool,
    handling: CarHandling,
) -> tuple[int, float]:
    if state.drift_active:
        state.drift_charge_frames += 1
        steer_strength, drift_skew = _drift_tuning(
            left_pressed,
            right_pressed,
            state.drift_direction,
            handling,
        )
        state.drift_skew_degrees = drift_skew
        return state.drift_direction, steer_strength

    state.drift_skew_degrees = _move_toward(
        state.drift_skew_degrees,
        0.0,
        handling.drift_unskew_step_degrees,
    )
    if state.drift_skew_degrees == 0.0:
        state.drift_direction = 0
    return filter_steer_input(steer_input, state.speed, handling=handling), 1.0


def filter_steer_input(
    steer_input: int,
    speed: float,
    *,
    handling: CarHandling = DEFAULT_CAR_HANDLING,
) -> int:
    # Ignore steering at very low speed to avoid spinning in place.
    if abs(speed) < handling.min_steer_speed:
        return 0
    steer = int(steer_input)
    if steer > 0:
        return 1
    if steer < 0:
        return -1
    return 0


def update_rotation(
    rotation: float,
    turn_rate: float,
    steer_input: int,
    steer_hold_frames: int,
    *,
    handling: CarHandling = DEFAULT_CAR_HANDLING,
    steer_strength: float = 1.0,
    snap_step_degrees: float | None = None,
) -> tuple[float, float]:
    # Three-phase turn response: initial bite, plateau, then gentle growth.
    steer = int(steer_input)
    steer_strength = _clamp(steer_strength, 0.0, 2.0)
    max_turn_rate = handling.max_turn_rate * _clamp(steer_strength, 0.35, 1.5)

    if steer:
        if turn_rate * steer < 0:
            turn_rate = _move_toward(turn_rate, 0.0, handling.turn_direction_change_damping)

        if steer_hold_frames <= handling.initial_phase_frames:
            turn_rate += steer * handling.initial_turn_acceleration * steer_strength
        elif steer_hold_frames <= handling.plateau_end_frame:
            target_turn_rate = steer * handling.plateau_turn_rate * steer_strength
            turn_rate = _move_toward(turn_rate, target_turn_rate, handling.plateau_acceleration * steer_strength)
        else:
            turn_rate += steer * handling.late_turn_acceleration * steer_strength

        turn_rate = _clamp(turn_rate, -max_turn_rate, max_turn_rate)
    else:
        turn_rate = _move_toward(turn_rate, 0.0, handling.turn_damping)

    rotation += turn_rate

    if not steer and abs(turn_rate) <= handling.turn_stop_epsilon:
        turn_rate = 0.0
        if snap_step_degrees is not None:
            rotation = _snap_angle(rotation, snap_step_degrees)

    return rotation, turn_rate


def update_speed(
    speed: float,
    up_input: bool,
    down_input: bool,
    turn_rate: float,
    *,
    handling: CarHandling = DEFAULT_CAR_HANDLING,
    max_forward_speed: float | None = None,
) -> float:
    # Resolve throttle/brake/coast first, then apply additional turn drag.
    if max_forward_speed is None:
        max_forward_speed = handling.max_speed

    throttle = up_input and not down_input
    brake = down_input and not up_input
    abs_turn = abs(turn_rate)
    sharp_turn = abs_turn >= handling.hold_cancel_turn_rate
    hold_enabled = (
        not brake
        and not sharp_turn
        and (speed >= handling.hold_floor or (throttle and speed >= handling.hold_activation_min))
    )

    if throttle:
        if speed < 0.0:
            speed = min(speed + handling.brake_deceleration, 0.0)
        if speed < max_forward_speed:
            speed = min(speed + handling.throttle_acceleration, max_forward_speed)
        elif speed > max_forward_speed:
            overspeed_step = handling.overspeed_deceleration_step(speed, max_forward_speed)
            speed = _move_toward(
                speed,
                max_forward_speed,
                max(handling.coast_deceleration, overspeed_step),
            )
    elif brake:
        if speed > 0.0:
            speed = max(speed - handling.brake_deceleration, 0.0)
        else:
            speed = max(speed - handling.reverse_acceleration, -handling.max_reverse_speed)
    else:
        coast_target = handling.hold_floor if hold_enabled else 0.0
        speed = _move_toward(speed, coast_target, handling.coast_deceleration)

    turn_drag = abs_turn * handling.turn_speed_penalty
    if turn_drag > handling.min_turn_drag:
        drag_target = handling.hold_floor if hold_enabled else 0.0
        speed = _move_toward(speed, drag_target, turn_drag)

    if throttle and not sharp_turn and speed >= handling.hold_activation_min:
        speed = max(speed, handling.hold_floor)

    return speed


def update_velocity(
    velocity_x: float,
    velocity_y: float,
    rotation: float,
    speed: float,
    turn_rate: float,
    *,
    handling: CarHandling = DEFAULT_CAR_HANDLING,
    slide_factor: float | None = None,
    drift_direction: int = 0,
    drift_skew_degrees: float = 0.0,
) -> tuple[float, float]:
    # Blend current velocity toward target heading with slip-based grip.
    if slide_factor is None:
        slide_factor = handling.default_slide_factor

    abs_speed = abs(speed)
    forward_x, forward_y = _forward_vector(rotation)
    target_vx = forward_x * speed
    target_vy = forward_y * speed

    if drift_direction:
        drift_dir = 1 if drift_direction > 0 else -1
        skew_degrees = _clamp(drift_skew_degrees, 0.0, 45.0)
        if skew_degrees:
            drift_x, drift_y = _forward_vector(rotation - (drift_dir * skew_degrees))
            target_vx = drift_x * speed
            target_vy = drift_y * speed

    speed_ratio = abs_speed / handling.max_reference_speed if handling.max_reference_speed else 0.0
    speed_ratio = _clamp(speed_ratio, 0.0, 1.0)
    turn_ratio = abs(turn_rate) / handling.max_turn_rate if handling.max_turn_rate else 0.0
    slip = slide_factor + (speed_ratio * handling.speed_slip_weight) + (turn_ratio * handling.turn_slip_weight)
    slip = _clamp(slip, 0.0, handling.max_slip)
    grip = 1.0 - slip

    velocity_x = _blend_toward(velocity_x, target_vx, grip)
    velocity_y = _blend_toward(velocity_y, target_vy, grip)

    coast_velocity_decay = handling.coast_velocity_decay_for_speed(abs_speed)
    if abs_speed > handling.max_speed:
        velocity_x = _blend_toward(velocity_x, target_vx, coast_velocity_decay)
        velocity_y = _blend_toward(velocity_y, target_vy, coast_velocity_decay)
    elif abs_speed <= handling.stop_speed_epsilon:
        velocity_x *= coast_velocity_decay
        velocity_y *= coast_velocity_decay

    if abs(velocity_x) < handling.stop_velocity_epsilon:
        velocity_x = 0.0
    if abs(velocity_y) < handling.stop_velocity_epsilon:
        velocity_y = 0.0

    return velocity_x, velocity_y


def update_position(car_x: float, car_y: float, velocity_x: float, velocity_y: float) -> tuple[float, float]:
    car_x += velocity_x
    car_y += velocity_y
    return car_x, car_y


def step_physics(
    state: PhysicsState,
    *,
    steer_input: int,
    left_pressed: bool,
    right_pressed: bool,
    up_input: bool,
    down_input: bool,
    drift_input: bool,
    handling: CarHandling = DEFAULT_CAR_HANDLING,
    snap_step_degrees: float | None = None,
    slide_factor: float | None = None,
) -> PhysicsState:
    # Frame order: drift state -> steering -> rotation -> speed -> velocity -> position.
    _try_start_drift(
        state,
        steer_input=steer_input,
        left_pressed=left_pressed,
        right_pressed=right_pressed,
        drift_input=drift_input,
        handling=handling,
    )

    drift_released = state.drift_active and not drift_input
    drift_canceled = state.drift_active and abs(state.speed) < handling.drift_min_speed
    if drift_released or drift_canceled:
        _stop_drift(state, released=drift_released, handling=handling)

    steer_for_physics, steer_strength = _resolve_steering_and_skew(
        state,
        steer_input=steer_input,
        left_pressed=left_pressed,
        right_pressed=right_pressed,
        handling=handling,
    )

    state.steer_hold_frames, state.previous_steer_input = _update_steer_hold(
        steer_for_physics,
        state.previous_steer_input,
        state.steer_hold_frames,
    )

    state.rotation, state.turn_rate = update_rotation(
        state.rotation,
        state.turn_rate,
        steer_for_physics,
        state.steer_hold_frames,
        handling=handling,
        steer_strength=steer_strength,
        snap_step_degrees=snap_step_degrees,
    )

    forward_speed_cap = state.boost_max_speed if state.boost_frames > 0 else handling.max_speed
    state.speed = update_speed(
        state.speed,
        up_input,
        down_input,
        state.turn_rate,
        handling=handling,
        max_forward_speed=forward_speed_cap,
    )

    if state.boost_frames > 0:
        state.speed = min(state.speed + state.boost_acceleration, state.boost_max_speed)
        state.boost_frames -= 1
        if state.boost_frames == 0:
            state.boost_acceleration = 0.0
            state.boost_max_speed = handling.max_speed

    active_drift_direction = state.drift_direction if state.drift_skew_degrees > 0.0 else 0
    state.velocity_x, state.velocity_y = update_velocity(
        state.velocity_x,
        state.velocity_y,
        state.rotation,
        state.speed,
        state.turn_rate,
        handling=handling,
        slide_factor=slide_factor,
        drift_direction=active_drift_direction,
        drift_skew_degrees=state.drift_skew_degrees,
    )
    state.car_x, state.car_y = update_position(
        state.car_x,
        state.car_y,
        state.velocity_x,
        state.velocity_y,
    )
    return state


def step_physics_with_controls(
    state: PhysicsState,
    controls: ControlState,
    *,
    handling: CarHandling = DEFAULT_CAR_HANDLING,
    snap_step_degrees: float | None = None,
    slide_factor: float | None = None,
) -> PhysicsState:
    return step_physics(
        state,
        steer_input=controls.steer_input,
        left_pressed=controls.left_pressed,
        right_pressed=controls.right_pressed,
        up_input=controls.up_input,
        down_input=controls.down_input,
        drift_input=controls.drift_input,
        handling=handling,
        snap_step_degrees=snap_step_degrees,
        slide_factor=slide_factor,
    )
