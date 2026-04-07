import math

# Small math helpers used heavily in the physics hot path.

def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))

def clamp_scale(scale: float) -> float:
    return max(0.1, min(scale, 1.0))

def _clamp_zoom(zoom: float) -> float:
    return max(0.01, zoom)


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


def snap_degrees(deg: float, dirs: int ) -> int:
    step = 360.0 / dirs
    return int((deg % 360.0) / step + 0.5) % dirs


def _snap_angle(rotation: float, snap_step_degrees: float) -> float:
    if snap_step_degrees <= 0:
        return rotation
    return round(rotation / snap_step_degrees) * snap_step_degrees

def _shortest_angle_delta(current: float, target: float) -> float:
    # Wrap to [-180, 180] so interpolation rotates the shortest way.
    return ((target - current + 180.0) % 360.0) - 180.0


