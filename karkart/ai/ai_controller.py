from __future__ import annotations

import math

from karkart.helpers import shortest_angle_delta
from karkart.physics.car import Car


class AIController:

    LOOKAHEAD: int = 5
    STEER_DEADZONE: float = 4.0
    THROTTLE_OFF_ANGLE: float = 55.0
    WAYPOINT_RADIUS: float = 50.0

    STILL_DISTANCE_EPSILON: float = 2.0
    STILL_FRAME_LIMIT: int = 12
    RECOVER_REVERSE_FRAMES: int = 10
    RECOVER_REORIENT_FRAMES: int = 40
    REORIENT_ANGLE_OK: float = 22.0

    NO_PROGRESS_FRAME_LIMIT: int = 50
    NO_PROGRESS_MIN_DELTA: float = 20.0
    SKIP_STUCK_FRAME_LIMIT: int = 150

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
        self._reverse_frames: int = 0
        self._reorient_frames: int = 0
        self._best_dist_to_goal: float = float("inf")
        self._no_progress_frames: int = 0
        self._skip_stuck_frames: int = 0

    def is_in_recovery(self) -> bool:

        return self._reverse_frames > 0 or self._reorient_frames > 0

    def update(self) -> None:

        self.car.controls.min_speed_request = 0.0
        if not self.circuit_waypoints:
            return

        self._update_stillness()
        self._update_no_progress()

        if self._reverse_frames > 0:
            self._recover_reverse()
            self._reverse_frames -= 1
            if self._reverse_frames == 0:
                self._reorient_frames = self.RECOVER_REORIENT_FRAMES
            return

        if self._reorient_frames > 0:
            done = self._recover_reorient()
            self._reorient_frames -= 1
            if done or self._reorient_frames == 0:
                self._reorient_frames = 0
            return

        self._advance_waypoints()
        n = len(self.circuit_waypoints)
        aim_idx = (self._wp_idx + self.LOOKAHEAD) % n
        self._steer_toward(self.circuit_waypoints[aim_idx])
        self.car.controls.drift_input = False

    def _current_target(self) -> tuple[float, float]:
        return self.circuit_waypoints[self._wp_idx]

    def _skip_current_target(self) -> None:
        n = len(self.circuit_waypoints)
        if n == 0:
            return
        self._wp_idx = (self._wp_idx + 1) % n
        self._best_dist_to_goal = float("inf")
        self._no_progress_frames = 0
        self._skip_stuck_frames = 0
        self._still_frames = 0

    def _advance_waypoints(self) -> None:
        car_x, car_y = self.car.physics.car_x, self.car.physics.car_y
        n = len(self.circuit_waypoints)
        for _ in range(self.LOOKAHEAD * 2):
            wx, wy = self.circuit_waypoints[self._wp_idx]
            if math.hypot(wx - car_x, wy - car_y) <= self.WAYPOINT_RADIUS:
                self._wp_idx = (self._wp_idx + 1) % n
                self._best_dist_to_goal = float("inf")
                self._no_progress_frames = 0
                self._skip_stuck_frames = 0
            else:
                break

    def _update_stillness(self) -> None:
        if self.car.physics.wall_stun_frames > 0:
            self._last_pos = (self.car.physics.car_x, self.car.physics.car_y)
            return
        pos = (self.car.physics.car_x, self.car.physics.car_y)
        moved = math.hypot(pos[0] - self._last_pos[0], pos[1] - self._last_pos[1])
        if moved <= self.STILL_DISTANCE_EPSILON and abs(self.car.physics.speed) < 0.2:
            self._still_frames += 1
        else:
            self._still_frames = 0
        self._last_pos = pos
        if self.car.collision_results and abs(self.car.physics.speed) < 0.35:
            self._still_frames = max(self._still_frames, self.STILL_FRAME_LIMIT - 4)
        if self._still_frames >= self.STILL_FRAME_LIMIT:
            self._reverse_frames = self.RECOVER_REVERSE_FRAMES
            self._reorient_frames = 0
            self._still_frames = 0

    def _update_no_progress(self) -> None:
        if (
            self._reverse_frames > 0
            or self._reorient_frames > 0
            or self.car.physics.wall_stun_frames > 0
        ):
            return
        target = self._current_target()
        dist = math.hypot(
            target[0] - self.car.physics.car_x,
            target[1] - self.car.physics.car_y,
        )
        if dist < self._best_dist_to_goal - self.NO_PROGRESS_MIN_DELTA:
            self._best_dist_to_goal = dist
            self._no_progress_frames = 0
            self._skip_stuck_frames = 0
        else:
            self._no_progress_frames += 1
            self._skip_stuck_frames += 1

        if self._skip_stuck_frames >= self.SKIP_STUCK_FRAME_LIMIT:
            self._skip_current_target()
            return

        if self._no_progress_frames >= self.NO_PROGRESS_FRAME_LIMIT:
            self._reverse_frames = self.RECOVER_REVERSE_FRAMES
            self._reorient_frames = 0
            self._still_frames = 0
            self._no_progress_frames = 0
            self._best_dist_to_goal = float("inf")

    def _recover_reverse(self) -> None:
        car_x, car_y = self.car.physics.car_x, self.car.physics.car_y
        if self.car.collision_normal is not None:
            nx, ny = self.car.collision_normal
            target = (car_x + nx * 80.0, car_y + ny * 80.0)
        else:
            gx, gy = self._current_target()
            dx, dy = gx - car_x, gy - car_y
            dist = math.hypot(dx, dy) or 1.0
            fx, fy = dx / dist, dy / dist
            # back away at a lateral angle so we don't re-ram the blocking car
            target = (car_x - fx * 50.0 + fy * 30.0, car_y - fy * 50.0 - fx * 30.0)
        dx, dy = target[0] - car_x, target[1] - car_y
        desired_angle = math.degrees(math.atan2(-dx, -dy))
        diff = shortest_angle_delta(self.car.physics.rotation, desired_angle)
        if abs(diff) < self.STEER_DEADZONE:
            self.car.controls.steer_input = 0
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = False
        elif diff > 0:
            self.car.controls.steer_input = -1
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = True
        else:
            self.car.controls.steer_input = 1
            self.car.controls.left_pressed = True
            self.car.controls.right_pressed = False
        self.car.controls.up_input = False
        self.car.controls.down_input = True
        self.car.controls.drift_input = False

    def _recover_reorient(self) -> bool:
        target = self._current_target()
        dx = target[0] - self.car.physics.car_x
        dy = target[1] - self.car.physics.car_y
        desired_angle = math.degrees(math.atan2(-dx, -dy))
        diff = shortest_angle_delta(self.car.physics.rotation, desired_angle)
        if abs(diff) <= self.REORIENT_ANGLE_OK and abs(self.car.physics.speed) < 0.6:
            self.car.controls.min_speed_request = 0.5
            self.car.controls.steer_input = 0
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = False
            self.car.controls.up_input = True
            self.car.controls.down_input = False
            self.car.controls.drift_input = False
            return True
        self.car.controls.min_speed_request = self.car.handling.min_steer_speed + 0.15
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
        self.car.controls.up_input = True
        self.car.controls.down_input = False
        self.car.controls.drift_input = False
        return False

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
