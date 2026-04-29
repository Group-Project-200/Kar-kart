"""CPU driver: feeds a :class:`Car`'s :class:`ControlState` from an A* plan.

The controller walks the checkpoint list in order. For each checkpoint it
plans a path with :class:`AStarPathfinder`, pops waypoints as the car gets
near, and periodically replans to compensate for drift or wall collisions.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from karkart.ai.pathfinder import AStarPathfinder
from karkart.helpers import shortest_angle_delta
from karkart.physics.car import Car
from karkart.physics.checkpoint import Checkpoint, RacerState

if TYPE_CHECKING:
    from karkart.runtime.pathfinder_worker import PathfinderWorker


class AIController:
    """Drives one :class:`Car` by writing into its :class:`ControlState` each frame."""

    # Index on the current path that the car actively aims for. Higher values
    # feel smoother but cut corners harder.
    # Original: LOOKAHEAD = 8
    LOOKAHEAD: int = 4

    # Degrees of heading error that are ignored before steering kicks in.
    STEER_DEADZONE: float = 8.0

    # Beyond this heading error the AI releases the throttle so it can
    # actually turn at high speed without oversteering into walls.
    THROTTLE_OFF_ANGLE: float = 55.0

    # How close (world units) the car has to get to the next waypoint before
    # it is popped from the path.
    # Original: WAYPOINT_RADIUS = 25.0
    WAYPOINT_RADIUS: float = 30.0

    # Force a replan after this many consumed waypoints; absorbs steering
    # drift and keeps the plan fresh without running A* every frame.
    REPLAN_EVERY_N_WAYPOINTS: int = 4

    # Stuck detection / recovery.
    STILL_DISTANCE_EPSILON: float = 2.0
    STILL_FRAME_LIMIT: int = 12
    RECOVER_REVERSE_FRAMES: int = 10
    # Large enough to actually complete a ~180° turn at AI update rate (30Hz):
    # max_turn_rate ~2.3°/frame * 2 physics frames per AI update = ~4.6°/update,
    # so a 180° flip needs ~40 updates to finish.
    RECOVER_REORIENT_FRAMES: int = 40
    REORIENT_ANGLE_OK: float = 22.0

    # "Going in circles" detection: if the car can't get materially closer to
    # the current goal for this many AI updates, force a reverse/reorient.
    # Catches orbit patterns the stillness check misses because the car is
    # still moving — just not toward the checkpoint.
    NO_PROGRESS_FRAME_LIMIT: int = 90
    NO_PROGRESS_MIN_DELTA: float = 20.0

    def __init__(
        self,
        car: Car,
        pathfinder: AStarPathfinder,
        checkpoints: list[Checkpoint],
        racer_state: RacerState,
        *,
        ai_index: int = 0,
        planner: "PathfinderWorker | None" = None,
    ) -> None:
        self.car = car
        self.pathfinder = pathfinder
        self.checkpoints = checkpoints
        self.racer_state = racer_state

        self.ai_index = ai_index
        self.planner = planner
        self._replan_pending: bool = False

        self._path: list[tuple[float, float]] = []
        self._popped_since_replan: int = 0
        self._last_goal_idx: int = racer_state.list_counter

        self._last_pos: tuple[float, float] = (
            car.physics.car_x,
            car.physics.car_y,
        )
        self._still_frames: int = 0
        self._reverse_frames: int = 0
        self._reorient_frames: int = 0

        # Tracks the closest the car has ever been to the current goal. If
        # this stops improving for NO_PROGRESS_FRAME_LIMIT updates, the car is
        # probably orbiting the checkpoint and needs a recovery.
        self._best_dist_to_goal: float = float("inf")
        self._no_progress_frames: int = 0

    # ------------------------------------------------------------------ #
    # Per-frame update                                                   #
    # ------------------------------------------------------------------ #

    def update(self) -> None:
        """Refresh steering, throttle and drift inputs on ``self.car.controls``."""
        self.car.controls.min_speed_request = 0.0

        if not self.checkpoints:
            self._straight_throttle()
            return

        self._invalidate_path_if_goal_changed()
        self._update_stillness()
        self._update_no_progress()

        # Phase 1: reverse out of a stuck/wall situation.
        if self._reverse_frames > 0:
            self._recover_reverse()
            self._reverse_frames -= 1
            if self._reverse_frames == 0:
                # After reversing, spend a short window turning forward toward the goal.
                self._reorient_frames = self.RECOVER_REORIENT_FRAMES
                self._path = []
                self._popped_since_replan = 0
            return

        # Phase 2: turn the car back toward the goal and drive forward.
        if self._reorient_frames > 0:
            done = self._recover_reorient()
            self._reorient_frames -= 1
            if done or self._reorient_frames == 0:
                self._path = []
                self._popped_since_replan = 0
            return

        self._consume_waypoints()
        if not self._path:
            self._replan()

        if not self._path:
            # Fall back to steering straight at the checkpoint if A* failed.
            self._steer_toward(self._current_goal_point())
            self.car.controls.drift_input = False
            return

        aim_idx = min(self.LOOKAHEAD, len(self._path) - 1)
        self._steer_toward(self._path[aim_idx])
        self.car.controls.drift_input = False

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #

    def is_in_recovery(self) -> bool:
        """Return True if the AI is currently in reverse or reorientation recovery mode."""
        return self._reverse_frames > 0 or self._reorient_frames > 0

    def _current_checkpoint(self) -> Checkpoint:
        return self.checkpoints[self.racer_state.list_counter]

    def _checkpoint_direction(self, idx: int) -> tuple[float, float]:
        """Approximate track direction entering checkpoint *idx*.

        Uses the vector from the previous checkpoint centre to this one,
        wrapping around so index 0 treats the last checkpoint as previous.
        """
        n = len(self.checkpoints)
        if n <= 1:
            # Arbitrary but stable default: "up" the map.
            return 0.0, -1.0

        prev_idx = (idx - 1) % n
        prev_rect = self.checkpoints[prev_idx].rect
        cur_rect = self.checkpoints[idx].rect

        dx = float(cur_rect.centerx - prev_rect.centerx)
        dy = float(cur_rect.centery - prev_rect.centery)
        length = math.hypot(dx, dy) or 1.0
        return dx / length, dy / length

    def _current_goal_point(self) -> tuple[float, float]:
        """Pick the center of the active checkpoint.

        The AI should aim for the checkpoint center so it naturally passes
        through and advances to the next checkpoint when touched.
        """
        idx = self.racer_state.list_counter
        cp = self.checkpoints[idx]
        rect = cp.rect
        return float(rect.centerx), float(rect.centery)

    def _invalidate_path_if_goal_changed(self) -> None:
        goal_idx = self.racer_state.list_counter
        if goal_idx == self._last_goal_idx:
            return
        self._last_goal_idx = goal_idx
        self._path = []
        self._popped_since_replan = 0
        self._replan_pending = False
        self._still_frames = 0
        self._reverse_frames = 0
        self._reorient_frames = 0
        self._best_dist_to_goal = float("inf")
        self._no_progress_frames = 0

    def _update_stillness(self) -> None:
        """Detect when the car is effectively stuck."""
        pos = (self.car.physics.car_x, self.car.physics.car_y)
        moved = math.hypot(pos[0] - self._last_pos[0], pos[1] - self._last_pos[1])

        if moved <= self.STILL_DISTANCE_EPSILON and abs(self.car.physics.speed) < 0.2:
            self._still_frames += 1
        else:
            self._still_frames = 0

        self._last_pos = pos

        # Colliding + barely moving shortens the wait before recovery.
        if self.car.collision_results and abs(self.car.physics.speed) < 0.35:
            self._still_frames = max(self._still_frames, self.STILL_FRAME_LIMIT - 4)

        if self._still_frames >= self.STILL_FRAME_LIMIT:
            self._reverse_frames = self.RECOVER_REVERSE_FRAMES
            self._reorient_frames = 0
            self._still_frames = 0

    def _update_no_progress(self) -> None:
        """Detect the car orbiting the goal without getting meaningfully closer."""
        if self._reverse_frames > 0 or self._reorient_frames > 0:
            return

        goal = self._current_goal_point()
        dist = math.hypot(
            goal[0] - self.car.physics.car_x,
            goal[1] - self.car.physics.car_y,
        )
        if dist < self._best_dist_to_goal - self.NO_PROGRESS_MIN_DELTA:
            self._best_dist_to_goal = dist
            self._no_progress_frames = 0
        else:
            self._no_progress_frames += 1

        if self._no_progress_frames >= self.NO_PROGRESS_FRAME_LIMIT:
            # Stuck circling: force a reverse + reorient sequence.
            self._reverse_frames = self.RECOVER_REVERSE_FRAMES
            self._reorient_frames = 0
            self._path = []
            self._popped_since_replan = 0
            self._still_frames = 0
            self._no_progress_frames = 0
            self._best_dist_to_goal = float("inf")

    def _recover_reverse(self) -> None:
        """Reverse away from the wall / bad approach.

        Steering is inverted in reverse by Car.filter_steer_input, so we
        choose the forward-facing heading that would point toward the
        *escape* point, then flip the steering choice here.
        """
        car_x = self.car.physics.car_x
        car_y = self.car.physics.car_y

        # Prefer backing away from the wall normal if we have one.
        if self.car.collision_normal is not None:
            nx, ny = self.car.collision_normal
            # Slightly farther than original (48.0) to clear tight inside walls.
            target = (car_x + nx * 80.0, car_y + ny * 80.0)  # Increased from 64.0
        else:
            # Otherwise back away from the checkpoint direction.
            gx, gy = self._current_goal_point()
            dx = gx - car_x
            dy = gy - car_y
            target = (car_x - dx, car_y - dy)

        dx = target[0] - car_x
        dy = target[1] - car_y
        desired_angle = math.degrees(math.atan2(-dx, -dy))
        diff = shortest_angle_delta(self.car.physics.rotation, desired_angle)

        if abs(diff) < self.STEER_DEADZONE:
            self.car.controls.steer_input = 0
            self.car.controls.left_pressed = False
            self.car.controls.right_pressed = False
        elif diff > 0:
            # Invert the normal forward steering choice for reverse.
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
        """Turn the car back toward the goal and drive forward.

        Returns True when the heading is close enough to resume normal AI.
        """
        target = self._current_goal_point()

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
        goal = self._current_goal_point()
        start = (self.car.physics.car_x, self.car.physics.car_y)
        if self.planner is not None:
            if self._replan_pending:
                return
            self.planner.request(self.ai_index, start, goal)
            self._replan_pending = True
            return
        self._path = self.pathfinder.find_path(start, goal)
        self._popped_since_replan = 0

    def receive_path(self, path: list[tuple[float, float]]) -> None:
        self._path = path
        self._popped_since_replan = 0
        self._replan_pending = False

    def _steer_toward(self, target: tuple[float, float]) -> None:
        """Set steer_input / left_pressed / right_pressed to aim at *target*.

        Also releases the throttle (coast) for heading errors beyond
        :THROTTLE_OFF_ANGLE — without this the AI reaches max speed
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
