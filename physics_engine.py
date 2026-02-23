import math
from dataclasses import dataclass


# Rotation tuning.
PLATEAU_ACCELERATION = 0.4
TURN_DAMPING = 0.15
MAX_TURN_RATE = 4.0
TURN_STOP_EPSILON = 0.05
INITIAL_TURN_ACCELERATION = 0.6
LATE_TURN_ACCELERATION = 0.15
INITIAL_PHASE_FRAMES = 4
PLATEAU_PHASE_FRAMES = 7
PLATEAU_TURN_RATE = 2.0
TURN_DIRECTION_CHANGE_DAMPING = 0.35
PLATEAU_END_FRAME = INITIAL_PHASE_FRAMES + PLATEAU_PHASE_FRAMES


# Speed and steering tuning.
THROTTLE_ACCELERATION = 0.05
COAST_DECELERATION = 0.005
BRAKE_DECELERATION = 0.14
REVERSE_ACCELERATION = 0.04
MAX_SPEED = 1.5
MAX_REVERSE_SPEED = 1.0
MIN_STEER_SPEED = 0.03
TURN_SPEED_PENALTY = 0.01
MIN_TURN_DRAG = 0.03
SPEED_HOLD_FLOOR_VALUE = 1.0
SPEED_HOLD_ACTIVATION_MIN_VALUE = 0.9
HOLD_CANCEL_TURN_RATE = 3.0
HOLD_FLOOR = min(SPEED_HOLD_FLOOR_VALUE, MAX_SPEED)
HOLD_ACTIVATION_MIN = min(SPEED_HOLD_ACTIVATION_MIN_VALUE, HOLD_FLOOR)

# Velocity blending and stopping thresholds.
MAX_SLIP = 0.95
SPEED_SLIP_WEIGHT = 0.35
TURN_SLIP_WEIGHT = 0.35
COAST_VELOCITY_DECAY = 0.01
MAX_REFERENCE_SPEED = max(MAX_SPEED, MAX_REVERSE_SPEED)
STOP_SPEED_EPSILON = 1e-6
STOP_VELOCITY_EPSILON = 1e-3

# Drift / boost tuning.
DEFAULT_SLIDE_FACTOR = 0.3
DRIFT_CHARGE_FRAMES = 80
DRIFT_BASE_STEER_STRENGTH = 0.65
DRIFT_SHARP_STEER_STRENGTH = 0.9
DRIFT_SLOW_STEER_STRENGTH = 0.45
DRIFT_BASE_SKEW_DEGREES = 20.0
DRIFT_SHARP_SKEW_DEGREES = 14.0
DRIFT_SLOW_SKEW_DEGREES = 28.0
DRIFT_UNSKEW_STEP_DEGREES = 5.0
DRIFT_RELEASE_COUNTERSTEER_DEGREES = 10.0
DRIFT_RELEASE_COUNTERSTEER_TURN_RATE = 0.8
DRIFT_MIN_SPEED = MIN_STEER_SPEED
MINI_BOOST_DURATION_FRAMES = 48
MINI_BOOST_ACCELERATION = 0.05
MINI_BOOST_MAX_SPEED = MAX_SPEED + 0.5


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
    drift_active: bool = False


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


def _drift_tuning(left_pressed: bool, right_pressed: bool, drift_direction: int) -> tuple[float, float]:
    if drift_direction > 0:
        sharper = left_pressed and not right_pressed
        slower = right_pressed and not left_pressed
    else:
        sharper = right_pressed and not left_pressed
        slower = left_pressed and not right_pressed

    if sharper:
        return DRIFT_SHARP_STEER_STRENGTH, DRIFT_SHARP_SKEW_DEGREES
    if slower:
        return DRIFT_SLOW_STEER_STRENGTH, DRIFT_SLOW_SKEW_DEGREES
    return DRIFT_BASE_STEER_STRENGTH, DRIFT_BASE_SKEW_DEGREES


def _try_start_drift(
    state: PhysicsState,
    *,
    steer_input: int,
    left_pressed: bool,
    right_pressed: bool,
    drift_input: bool,
) -> None:
    if state.drift_active or not drift_input or abs(state.speed) < DRIFT_MIN_SPEED:
        return

    drift_direction = _resolve_drift_direction(steer_input, left_pressed, right_pressed)
    if not drift_direction:
        return

    state.drift_direction = drift_direction
    state.drift_active = True
    state.drift_charge_frames = 0


def _stop_drift(state: PhysicsState, *, released: bool) -> None:
    if released and state.drift_charge_frames >= DRIFT_CHARGE_FRAMES:
        state.boost_frames = MINI_BOOST_DURATION_FRAMES
    if released and state.drift_direction:
        # Snap the car nose opposite the drift so it visibly counter-steers on release.
        state.rotation -= state.drift_direction * DRIFT_RELEASE_COUNTERSTEER_DEGREES
        state.turn_rate = -state.drift_direction * DRIFT_RELEASE_COUNTERSTEER_TURN_RATE

    state.drift_active = False
    state.drift_charge_frames = 0


def _resolve_steering_and_skew(
    state: PhysicsState,
    *,
    steer_input: int,
    left_pressed: bool,
    right_pressed: bool,
) -> tuple[int, float]:
    if state.drift_active:
        state.drift_charge_frames += 1
        steer_strength, drift_skew = _drift_tuning(left_pressed, right_pressed, state.drift_direction)
        state.drift_skew_degrees = drift_skew
        return state.drift_direction, steer_strength

    state.drift_skew_degrees = _move_toward(
        state.drift_skew_degrees,
        0.0,
        DRIFT_UNSKEW_STEP_DEGREES,
    )
    if state.drift_skew_degrees == 0.0:
        state.drift_direction = 0
    return filter_steer_input(steer_input, state.speed), 1.0


def filter_steer_input(steer_input: int, speed: float) -> int:
    # Ignore steering when the car is almost stopped.
    if abs(speed) < MIN_STEER_SPEED:
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
    steer_strength: float = 1.0,
    snap_step_degrees: float | None = None,
) -> tuple[float, float]:
    # Three steering phases: early acceleration, plateau, late acceleration.
    steer = int(steer_input)
    steer_strength = _clamp(steer_strength, 0.0, 2.0)
    max_turn_rate = MAX_TURN_RATE * _clamp(steer_strength, 0.35, 1.5)

    if steer:
        if turn_rate * steer < 0:
            turn_rate = _move_toward(turn_rate, 0.0, TURN_DIRECTION_CHANGE_DAMPING)

        if steer_hold_frames <= INITIAL_PHASE_FRAMES:
            turn_rate += steer * INITIAL_TURN_ACCELERATION * steer_strength
        elif steer_hold_frames <= PLATEAU_END_FRAME:
            target_turn_rate = steer * PLATEAU_TURN_RATE * steer_strength
            turn_rate = _move_toward(turn_rate, target_turn_rate, PLATEAU_ACCELERATION * steer_strength)
        else:
            turn_rate += steer * LATE_TURN_ACCELERATION * steer_strength

        turn_rate = _clamp(turn_rate, -max_turn_rate, max_turn_rate)
    else:
        turn_rate = _move_toward(turn_rate, 0.0, TURN_DAMPING)

    rotation += turn_rate

    if not steer and abs(turn_rate) <= TURN_STOP_EPSILON:
        turn_rate = 0.0
        if snap_step_degrees is not None:
            rotation = _snap_angle(rotation, snap_step_degrees)

    return rotation, turn_rate


def update_speed(
    speed: float,
    up_input: bool,
    down_input: bool,
    turn_rate: float,
    max_forward_speed: float = MAX_SPEED,
) -> float:
    throttle = up_input and not down_input
    brake = down_input and not up_input
    abs_turn = abs(turn_rate)
    sharp_turn = abs_turn >= HOLD_CANCEL_TURN_RATE
    hold_enabled = (
        not brake
        and not sharp_turn
        and (speed >= HOLD_FLOOR or (throttle and speed >= HOLD_ACTIVATION_MIN))
    )

    if throttle:
        if speed < 0.0:
            speed = min(speed + BRAKE_DECELERATION, 0.0)
        # Preserve temporary overspeed (e.g. boost) instead of hard-clamping it.
        if speed < max_forward_speed:
            speed = min(speed + THROTTLE_ACCELERATION, max_forward_speed)
        elif speed > max_forward_speed:
            speed = _move_toward(speed, max_forward_speed, COAST_DECELERATION)
    elif brake:
        if speed > 0.0:
            speed = max(speed - BRAKE_DECELERATION, 0.0)
        else:
            speed = max(speed - REVERSE_ACCELERATION, -MAX_REVERSE_SPEED)
    else:
        coast_target = HOLD_FLOOR if hold_enabled else 0.0
        speed = _move_toward(speed, coast_target, COAST_DECELERATION)

    turn_drag = abs_turn * TURN_SPEED_PENALTY
    if turn_drag > MIN_TURN_DRAG:
        drag_target = HOLD_FLOOR if hold_enabled else 0.0
        speed = _move_toward(speed, drag_target, turn_drag)

    if throttle and not sharp_turn and speed >= HOLD_ACTIVATION_MIN:
        speed = max(speed, HOLD_FLOOR)

    return speed


def update_velocity(
    velocity_x: float,
    velocity_y: float,
    rotation: float,
    speed: float,
    turn_rate: float,
    slide_factor: float = 0.2,
    drift_direction: int = 0,
    drift_skew_degrees: float = 0.0,
) -> tuple[float, float]:
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

    speed_ratio = abs(speed) / MAX_REFERENCE_SPEED if MAX_REFERENCE_SPEED else 0.0
    speed_ratio = _clamp(speed_ratio, 0.0, 1.0)
    turn_ratio = abs(turn_rate) / MAX_TURN_RATE if MAX_TURN_RATE else 0.0
    slip = slide_factor + (speed_ratio * SPEED_SLIP_WEIGHT) + (turn_ratio * TURN_SLIP_WEIGHT)
    slip = _clamp(slip, 0.0, MAX_SLIP)
    grip = 1.0 - slip

    velocity_x = _blend_toward(velocity_x, target_vx, grip)
    velocity_y = _blend_toward(velocity_y, target_vy, grip)

    if abs(speed) <= STOP_SPEED_EPSILON:
        velocity_x *= COAST_VELOCITY_DECAY
        velocity_y *= COAST_VELOCITY_DECAY

    if abs(velocity_x) < STOP_VELOCITY_EPSILON:
        velocity_x = 0.0
    if abs(velocity_y) < STOP_VELOCITY_EPSILON:
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
    snap_step_degrees: float | None = None,
    slide_factor: float = DEFAULT_SLIDE_FACTOR,
) -> PhysicsState:
    _try_start_drift(
        state,
        steer_input=steer_input,
        left_pressed=left_pressed,
        right_pressed=right_pressed,
        drift_input=drift_input,
    )

    drift_released = state.drift_active and not drift_input
    drift_canceled = state.drift_active and abs(state.speed) < DRIFT_MIN_SPEED
    if drift_released or drift_canceled:
        _stop_drift(state, released=drift_released)

    steer_for_physics, steer_strength = _resolve_steering_and_skew(
        state,
        steer_input=steer_input,
        left_pressed=left_pressed,
        right_pressed=right_pressed,
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
        steer_strength=steer_strength,
        snap_step_degrees=snap_step_degrees,
    )
    forward_speed_cap = MINI_BOOST_MAX_SPEED if state.boost_frames > 0 else MAX_SPEED
    state.speed = update_speed(
        state.speed,
        up_input,
        down_input,
        state.turn_rate,
        max_forward_speed=forward_speed_cap,
    )

    if state.boost_frames > 0:
        state.speed = min(state.speed + MINI_BOOST_ACCELERATION, MINI_BOOST_MAX_SPEED)
        state.boost_frames -= 1

    active_drift_direction = state.drift_direction if state.drift_skew_degrees > 0.0 else 0
    state.velocity_x, state.velocity_y = update_velocity(
        state.velocity_x,
        state.velocity_y,
        state.rotation,
        state.speed,
        state.turn_rate,
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
