from __future__ import annotations

import math

def clamp(value: float, min_value: float, max_value: float) -> float:

    return max(min_value, min(value, max_value))

def clamp_scale(scale: float) -> float:

    return max(0.1, min(scale, 1.0))

def clamp_zoom(zoom: float) -> float:

    return max(0.01, zoom)

def move_toward(value: float, target: float, step: float) -> float:

    if value < target:
        return min(value + step, target)
    if value > target:
        return max(value - step, target)
    return value

def blend_toward(current: float, target: float, fraction: float) -> float:

    return current + (target - current) * fraction

def forward_vector(rotation_degrees: float) -> tuple[float, float]:
\
\
\

    radians = math.radians(rotation_degrees)
    return -math.sin(radians), -math.cos(radians)

def snap_degrees(deg: float, dirs: int) -> int:

    step = 360.0 / dirs
    return int((deg % 360.0) / step + 0.5) % dirs

def snap_angle(rotation: float, snap_step_degrees: float) -> float:

    if snap_step_degrees <= 0:
        return rotation
    return round(rotation / snap_step_degrees) * snap_step_degrees

def shortest_angle_delta(current: float, target: float) -> float:

    return ((target - current + 180.0) % 360.0) - 180.0
