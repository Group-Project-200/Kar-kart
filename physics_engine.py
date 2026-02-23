import math


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
HANDBRAKE_SLIP_BOOST = 1.0
COAST_VELOCITY_DECAY = 0.01
MAX_REFERENCE_SPEED = max(MAX_SPEED, MAX_REVERSE_SPEED)
STOP_SPEED_EPSILON = 1e-6
STOP_VELOCITY_EPSILON = 1e-3


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
    snap_step_degrees: float | None = None,
) -> tuple[float, float]:
    # Three steering phases: early acceleration, plateau, late acceleration.
    steer = int(steer_input)

    if steer:
        if turn_rate * steer < 0:
            turn_rate = _move_toward(turn_rate, 0.0, TURN_DIRECTION_CHANGE_DAMPING)

        if steer_hold_frames <= INITIAL_PHASE_FRAMES:
            turn_rate += steer * INITIAL_TURN_ACCELERATION
        elif steer_hold_frames <= PLATEAU_END_FRAME:
            turn_rate = _move_toward(turn_rate, steer * PLATEAU_TURN_RATE, PLATEAU_ACCELERATION)
        else:
            turn_rate += steer * LATE_TURN_ACCELERATION

        turn_rate = _clamp(turn_rate, -MAX_TURN_RATE, MAX_TURN_RATE)
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
        speed = min(speed + THROTTLE_ACCELERATION, MAX_SPEED)
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
    handbrake_input: bool = False,
) -> tuple[float, float]:
    forward_x, forward_y = _forward_vector(rotation)
    target_vx = forward_x * speed
    target_vy = forward_y * speed

    speed_ratio = abs(speed) / MAX_REFERENCE_SPEED if MAX_REFERENCE_SPEED else 0.0
    turn_ratio = abs(turn_rate) / MAX_TURN_RATE if MAX_TURN_RATE else 0.0
    slip = slide_factor + (speed_ratio * SPEED_SLIP_WEIGHT) + (turn_ratio * TURN_SLIP_WEIGHT)
    if handbrake_input:
        slip += HANDBRAKE_SLIP_BOOST
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
