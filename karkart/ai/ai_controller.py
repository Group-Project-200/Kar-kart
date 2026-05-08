from __future__ import annotations

import math

from karkart.helpers import shortest_angle_delta
from karkart.physics.car import Car

"""basically this is what controls the ai's movements because they dont move in a straight line. it creates waypoints 
that are created at each tick and are tracked from each checkpoint to the other using a star algorithm """
class AIController:

    LOOKAHEAD: int = 12
    STEER_DEADZONE: float = 4.0
    THROTTLE_OFF_ANGLE: float = 55.0
    WAYPOINT_RADIUS: float = 55.0

    # Frames of barely-no-movement before triggering recovery (~0.67s at 30 hz)
    STILL_FRAME_LIMIT: int = 20
    # Frames spent reversing during recovery (~0.67s at 30 hz)
    RECOVER_FRAMES: int = 20
    # How many waypoints to skip forward after recovery completes
    RECOVER_WP_SKIP: int = 8

    def __init__(
        self,
        car: Car,
        circuit_waypoints: list[tuple[float, float]],
    ) -> None:
        self.car = car
        self.circuit_waypoints = circuit_waypoints
        self._wp_idx: int = 0
        self._last_pos: tuple[float, float] = (car.physics.car_x, car.physics.car_y)
        self._still_frames: int = 0
        self._recover_frames: int = 0

    def is_in_recovery(self) -> bool:
        return self._recover_frames > 0

    def update(self) -> None:
        self.car.controls.min_speed_request = 0.0
        if not self.circuit_waypoints:
            return

        if self._recover_frames > 0:
            self._do_recover()
            self._recover_frames -= 1
            if self._recover_frames == 0:
                # Skip ahead so the car doesn't loop back into the same obstacle.
                n = len(self.circuit_waypoints)
                self._wp_idx = (self._wp_idx + self.RECOVER_WP_SKIP) % n
                self._still_frames = 0
            return

        # Only check for stuck when not already recovering.
        self._check_stuck()
        self._advance_waypoints()
        n = len(self.circuit_waypoints)
        aim_idx = (self._wp_idx + self.LOOKAHEAD) % n
        self._steer_toward(self.circuit_waypoints[aim_idx])
        self.car.controls.drift_input = False

    """ there is also a check for if the ai is stuck in the wall so it reverses and tries again to find the path"""
    def _check_stuck(self) -> None:
        # Don't count wall-stun frames as being stuck.
        if self.car.physics.wall_stun_frames > 0:
            self._last_pos = (self.car.physics.car_x, self.car.physics.car_y)
            self._still_frames = 0
            return
        pos = (self.car.physics.car_x, self.car.physics.car_y)
        moved = math.hypot(pos[0] - self._last_pos[0], pos[1] - self._last_pos[1])
        self._last_pos = pos
        if moved < 2.0:
            self._still_frames += 1
        else:
            self._still_frames = 0
        if self._still_frames >= self.STILL_FRAME_LIMIT:
            self._still_frames = 0
            self._recover_frames = self.RECOVER_FRAMES

    def _do_recover(self) -> None:
        # Reverse while steering the front toward the post-recovery aim point so
        # the car is naturally reoriented by the time it drives forward again.
        n = len(self.circuit_waypoints)
        aim = self.circuit_waypoints[(self._wp_idx + self.RECOVER_WP_SKIP) % n]
        dx = aim[0] - self.car.physics.car_x
        dy = aim[1] - self.car.physics.car_y
        desired = math.degrees(math.atan2(-dx, -dy))
        diff = shortest_angle_delta(self.car.physics.rotation, desired)
        if abs(diff) < self.STEER_DEADZONE:
            self.car.controls.steer_input = 0
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = False
        elif diff > 0:
            self.car.controls.steer_input = 1
            self.car.controls.left_pressed = True
            self.car.controls.right_pressed = False
        else:
            self.car.controls.steer_input = -1
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = True
        self.car.controls.up_input = False
        self.car.controls.down_input = True
        self.car.controls.drift_input = False

    def _advance_waypoints(self) -> None:
        car_x, car_y = self.car.physics.car_x, self.car.physics.car_y
        n = len(self.circuit_waypoints)
        # Scan ahead up to LOOKAHEAD*3 waypoints so a fast car never falls behind.
        for _ in range(self.LOOKAHEAD * 3):
            wx, wy = self.circuit_waypoints[self._wp_idx]
            if math.hypot(wx - car_x, wy - car_y) <= self.WAYPOINT_RADIUS:
                self._wp_idx = (self._wp_idx + 1) % n
            else:
                break

    def _steer_toward(self, target: tuple[float, float]) -> None:
        dx = target[0] - self.car.physics.car_x
        dy = target[1] - self.car.physics.car_y
        desired_angle = math.degrees(math.atan2(-dx, -dy))
        diff = shortest_angle_delta(self.car.physics.rotation, desired_angle)
        if abs(diff) < self.STEER_DEADZONE:
            self.car.controls.steer_input = 0
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = False
        elif diff > 0:
            self.car.controls.steer_input = 1
            self.car.controls.left_pressed = True
            self.car.controls.right_pressed = False
        else:
            self.car.controls.steer_input = -1
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = True
        if abs(diff) >= self.THROTTLE_OFF_ANGLE:
            self.car.controls.up_input = False
            self.car.controls.down_input = False
        else:
            self.car.controls.up_input = True
            self.car.controls.down_input = False
