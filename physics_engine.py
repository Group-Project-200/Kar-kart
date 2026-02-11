import math

current_spin = 0.0

# Car physics update for rotation

def update_rotation(rotation, left_input, right_input):
    global current_spin
    spin_acceleration = 0.2
    spin_decay = 0.1
    max_spin = 3
    if left_input:
        current_spin = min(current_spin + spin_acceleration, max_spin)
    elif right_input:
        current_spin = max(current_spin - spin_acceleration, -max_spin)
    else:
        if current_spin > 0:
            current_spin = max(current_spin - spin_decay, 0)
        elif current_spin < 0:
            current_spin = min(current_spin + spin_decay, 0)
    rotation += current_spin
    return rotation

def update_position(car_x, car_y, rotation, car_speed):
    rad = math.radians(rotation)
    car_x -= math.sin(rad) * car_speed
    car_y -= math.cos(rad) * car_speed
    return car_x, car_y
