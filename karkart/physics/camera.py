from __future__ import annotations

from dataclasses import dataclass

from karkart.helpers import clamp, shortest_angle_delta
from karkart.physics.car import Car


@dataclass(frozen=True, slots=True)
class CameraFollowSettings:

    follow_alpha: float = 0.03
    drift_tilt_factor: float = 0.35
    max_drift_tilt: float = 10.0
    snap_delta: float = 180.0


class Camera:

    def __init__(self, car: Car) -> None:
        self.angle: float = 0.0
        self.settings = CameraFollowSettings()
        self.car = car

    def update_camera_angle(self) -> None:

        drift_direction = self.car.physics.drift_direction
        if drift_direction > 0:
            drift_sign = 1.0
        elif drift_direction < 0:
            drift_sign = -1.0
        else:
            drift_sign = 0.0

        max_tilt = abs(self.settings.max_drift_tilt)
        drift_tilt = (
            drift_sign
            * self.car.physics.drift_skew_degrees
            * self.settings.drift_tilt_factor
        )
        drift_tilt = clamp(drift_tilt, -max_tilt, max_tilt)
        target_angle = self.car.physics.rotation + drift_tilt

        delta = shortest_angle_delta(self.angle, target_angle)
        if abs(delta) >= max(0.0, self.settings.snap_delta):

            self.angle = target_angle
        else:
            alpha = clamp(self.settings.follow_alpha, 0.0, 1.0)
            self.angle += delta * alpha

        self.angle = ((self.angle + 180.0) % 360.0) - 180.0
