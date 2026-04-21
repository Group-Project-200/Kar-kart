"""CPU driver: feeds a :class:`Car`'s :class:`ControlState` from an A* plan.

The controller walks the checkpoint list in order. For each checkpoint it
plans a path with :class:`AStarPathfinder`, pops waypoints as the car gets
near, and periodically replans to compensate for drift or wall collisions.
"""

from __future__ import annotations

import math

from karkart.ai.pathfinder import AStarPathfinder
from karkart.helpers import shortest_angle_delta
from karkart.physics.car import Car
from karkart.physics.checkpoint import Checkpoint


class AIController:
    """Drives one :class:`Car` by writing into its :class:`ControlState` each frame."""

    # Index on the current path that the car actively aims for. Higher values
    # feel smoother but cut corners harder.
    LOOKAHEAD: int = 8

    # Degrees of heading error that are ignored before steering kicks in.
    STEER_DEADZONE: float = 8.0

    # Beyond this heading error the AI releases the throttle so it can
    # actually turn at high speed without oversteering into walls.
    THROTTLE_OFF_ANGLE: float = 55.0

    # How close (world units) the car has to get to the next waypoint before
    # it is popped from the path.
    WAYPOINT_RADIUS: float = 25.0

    # Force a replan after this many consumed waypoints; absorbs steering
    # drift and keeps the plan fresh without running A* every frame.
    REPLAN_EVERY_N_WAYPOINTS: int = 4

    def __init__(
        self,
        car: Car,
        pathfinder: AStarPathfinder,
        checkpoints: list[Checkpoint],
    ) -> None:
        self.car = car
        self.pathfinder = pathfinder
        self.checkpoints = checkpoints
        self._goal_idx: int = 0
        self._path: list[tuple[float, float]] = []
        self._popped_since_replan: int = 0

    # ------------------------------------------------------------------ #
    # Per-frame update                                                   #
    # ------------------------------------------------------------------ #

    def update(self) -> None:
        """Refresh steering, throttle and drift inputs on ``self.car.controls``."""
        if not self.checkpoints:
            self._straight_throttle()
            return

        self._advance_checkpoint_if_reached()
        self._consume_waypoints()
        if not self._path:
            self._replan()

        if not self._path:
            self._straight_throttle()
            return

        aim_idx = min(self.LOOKAHEAD, len(self._path) - 1)
        self._steer_toward(self._path[aim_idx])
        self.car.controls.drift_input = False

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #

    def _straight_throttle(self) -> None:
        self.car.controls.steer_input = 0
        self.car.controls.left_pressed = False
        self.car.controls.right_pressed = False
        self.car.controls.up_input = True
        self.car.controls.down_input = False
        self.car.controls.drift_input = False

    def _current_checkpoint(self) -> Checkpoint:
        return self.checkpoints[self._goal_idx]

    def _advance_checkpoint_if_reached(self) -> None:
        cp = self._current_checkpoint()
        if cp.check(self.car.physics.car_x, self.car.physics.car_y):
            self._goal_idx = (self._goal_idx + 1) % len(self.checkpoints)
            self._path = []
            self._popped_since_replan = 0

    def _consume_waypoints(self) -> None:
        car_x = self.car.physics.car_x
        car_y = self.car.physics.car_y
        while self._path:
            wx, wy = self._path[0]
            if math.hypot(wx - car_x, wy - car_y) <= self.WAYPOINT_RADIUS:
                self._path.pop(0)
                self._popped_since_replan += 1
            else:
                break
        if self._popped_since_replan >= self.REPLAN_EVERY_N_WAYPOINTS:
            self._path = []
            self._popped_since_replan = 0

    def _replan(self) -> None:
        cp = self._current_checkpoint()
        goal = (float(cp.rect.centerx), float(cp.rect.centery))
        start = (self.car.physics.car_x, self.car.physics.car_y)
        self._path = self.pathfinder.find_path(start, goal)
        self._popped_since_replan = 0

    def _steer_toward(self, target: tuple[float, float]) -> None:
        """Set steer_input / left_pressed / right_pressed to aim at *target*.

        Also releases the throttle (coast) for heading errors beyond
        :data:`THROTTLE_OFF_ANGLE` — without this the AI reaches max speed
        and oversteers into walls on tight corners.
        """
        dx = target[0] - self.car.physics.car_x
        dy = target[1] - self.car.physics.car_y
        # forward_vector(rotation) = (-sin, -cos), so the heading that points
        # toward (dx, dy) is atan2(-dx, -dy).
        desired_angle = math.degrees(math.atan2(-dx, -dy))
        diff = shortest_angle_delta(self.car.physics.rotation, desired_angle)

        if abs(diff) < self.STEER_DEADZONE:
            self.car.controls.steer_input = 0
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = False
        elif diff > 0:
            # steer_input = 1 accumulates positive turn_rate (CCW / left).
            self.car.controls.steer_input = 1
            self.car.controls.left_pressed = True
            self.car.controls.right_pressed = False
        else:
            self.car.controls.steer_input = -1
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = True

        # Throttle modulation: ease off on sharp turns so the kart can
        # actually rotate instead of ploughing into walls. Coast rather
        # than brake — braking past zero reverses the car and strands it.
        if abs(diff) >= self.THROTTLE_OFF_ANGLE:
            self.car.controls.up_input = False
            self.car.controls.down_input = False
        else:
            self.car.controls.up_input = True
            self.car.controls.down_input = False
