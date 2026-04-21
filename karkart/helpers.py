"""Small math helpers used heavily in the physics hot path and renderer."""

from __future__ import annotations

import math


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp *value* to the closed interval [*min_value*, *max_value*]."""
    return max(min_value, min(value, max_value))


def clamp_scale(scale: float) -> float:
    """Clamp a render scale factor to (0.1, 1.0]."""
    return max(0.1, min(scale, 1.0))


def clamp_zoom(zoom: float) -> float:
    """Reject zero or negative zoom values."""
    return max(0.01, zoom)


def move_toward(value: float, target: float, step: float) -> float:
    """Move *value* toward *target* by at most *step* without overshooting."""
    if value < target:
        return min(value + step, target)
    if value > target:
        return max(value - step, target)
    return value


def blend_toward(current: float, target: float, fraction: float) -> float:
    """Linearly interpolate *current* toward *target* by *fraction* in [0, 1]."""
    return current + (target - current) * fraction


def forward_vector(rotation_degrees: float) -> tuple[float, float]:
    """Return a unit vector pointing along *rotation_degrees* in screen space.

    Screen Y increases downward, so the vector uses negative sine/cosine.
    """
    radians = math.radians(rotation_degrees)
    return -math.sin(radians), -math.cos(radians)


def snap_degrees(deg: float, dirs: int) -> int:
    """Quantise a continuous heading to one of *dirs* evenly spaced sprite indices."""
    step = 360.0 / dirs
    return int((deg % 360.0) / step + 0.5) % dirs


def snap_angle(rotation: float, snap_step_degrees: float) -> float:
    """Round *rotation* to the nearest multiple of *snap_step_degrees*."""
    if snap_step_degrees <= 0:
        return rotation
    return round(rotation / snap_step_degrees) * snap_step_degrees


def shortest_angle_delta(current: float, target: float) -> float:
    """Return the signed delta in (-180, 180] to rotate *current* toward *target*."""
    return ((target - current + 180.0) % 360.0) - 180.0
