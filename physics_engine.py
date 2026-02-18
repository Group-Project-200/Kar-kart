import math


PLATEAU_ACCELERATION = 0.4
TURN_DAMPING = 0.15
MAX_TURN_RATE = 4.0
TURN_STOP_EPSILON = 0.05
INITIAL_TURN_ACCELERATION = 0.55
LATE_TURN_ACCELERATION = 0.2
INITIAL_PHASE_FRAMES = 4
PLATEAU_PHASE_FRAMES = 7
PLATEAU_TURN_RATE = 2.0
TURN_DIRECTION_CHANGE_DAMPING = 0.35
PLATEAU_END_FRAME = INITIAL_PHASE_FRAMES + PLATEAU_PHASE_FRAMES


THROTTLE_ACCELERATION = 0.05
COAST_DECELERATION = 0.03
BRAKE_DECELERATION = 0.14
REVERSE_ACCELERATION = 0.04
MAX_SPEED = 1.5
MAX_REVERSE_SPEED = 1.0
TURN_SPEED_PENALTY = 0.015
MAX_SLIP = 0.95
SPEED_SLIP_WEIGHT = 0.35
TURN_SLIP_WEIGHT = 0.35
HANDBRAKE_SLIP_BOOST = 0.6
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
    # Move current toward target by a fraction:
    # 0.0 keeps current, 1.0 jumps directly to target.
    return current + (target - current) * fraction


def _forward_vector(rotation: float) -> tuple[float, float]:
    radians = math.radians(rotation)
    return -math.sin(radians), -math.cos(radians)


def update_rotation(rotation, turn_rate, steer_input, steer_hold_frames, snap_step_degrees=None):
    # Steering uses 3 phases:
    # 1) fast initial turn, 2) short plateau, 3) slower continued acceleration.
    steer = int(steer_input)

    if steer != 0:
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

    if steer == 0 and abs(turn_rate) <= TURN_STOP_EPSILON:
        turn_rate = 0.0
        if snap_step_degrees is not None:
            rotation = _snap_angle(rotation, snap_step_degrees)

    return rotation, turn_rate


def update_speed(speed, up_input, down_input, turn_rate):
    # Up accelerates forward, down brakes first then enters reverse.
    # If no throttle/brake input, speed coasts toward zero.
    if up_input and not down_input:
        if speed < 0.0:
            speed = min(speed + BRAKE_DECELERATION, 0.0)
        speed = min(speed + THROTTLE_ACCELERATION, MAX_SPEED)
    elif down_input and not up_input:
        if speed > 0.0:
            speed = max(speed - BRAKE_DECELERATION, 0.0)
        else:
            speed = max(speed - REVERSE_ACCELERATION, -MAX_REVERSE_SPEED)
    else:
        speed = _move_toward(speed, 0.0, COAST_DECELERATION)

    turn_drag = abs(turn_rate) * TURN_SPEED_PENALTY
    speed = _move_toward(speed, 0.0, turn_drag)
    return speed


def update_velocity(
    velocity_x,
    velocity_y,
    rotation,
    speed,
    turn_rate,
    slide_factor=0.2,
    handbrake_input=False,
):
    # Build the velocity we "want" from heading + speed.
    # Then blend current velocity toward it based on grip.
    # More speed/turn -> more slip -> less grip -> more slide.
    forward_x, forward_y = _forward_vector(rotation)
    target_vx = forward_x * speed
    target_vy = forward_y * speed

    speed_ratio = abs(speed) / MAX_REFERENCE_SPEED if MAX_REFERENCE_SPEED > 0 else 0.0
    turn_ratio = abs(turn_rate) / MAX_TURN_RATE if MAX_TURN_RATE > 0 else 0.0
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


def update_position(car_x, car_y, velocity_x, velocity_y):
    car_x += velocity_x
    car_y += velocity_y
    return car_x, car_y
