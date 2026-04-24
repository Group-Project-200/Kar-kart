"""Checkpoint geometry plus per-racer progression state.

A :class:`Checkpoint` is a static rectangle on the map. A :class:`RacerState`
owns the mutable per-racer progression (which checkpoint is next, current lap,
lap times, cumulative total). :func:`advance_checkpoints` moves one racer's
state forward by one slot if the car is currently touching the next checkpoint.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import pygame


class Checkpoint:
    """Axis-aligned rectangle that records whether the car has passed through."""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.passed: bool = False


    def check(self, car_x: float, car_y: float, half_size: float = 10.0) -> bool:
        """Return True if the car's footprint overlaps the checkpoint rect.

        Tests a small square around (*car_x*, *car_y*) rather than a single
        point so narrow checkpoints still trigger when the car's edge — not
        just its centre — crosses the rect.
        """
        car_rect = pygame.Rect(
            int(car_x - half_size), int(car_y - half_size),
            int(half_size * 2), int(half_size * 2),
        )
        return self.rect.colliderect(car_rect)


@dataclass
class RacerState:
    """Per-racer checkpoint progression state.

    ``list_counter`` is the index of the next checkpoint the racer must touch;
    it resets to 0 at the start of every lap. ``current_lap`` starts at 1 and
    increments when the finish line is crossed. ``lap_times`` records a
    ``(time.perf_counter(), lap)`` sample at each advance. ``total_checkpoints``
    is a monotonic count across the whole race — useful for position ranking
    since it never resets.
    """

    list_counter: int = 0
    current_lap: int = 1
    lap_times: list = field(default_factory=list)
    total_checkpoints: int = 0
    # Monotonic "race-wide" pass counter assigned each time this racer crosses
    # a checkpoint. Lets ranking break ties between two racers on the same
    # checkpoint count by comparing who got there first.
    last_pass_order: int = 0


def advance_checkpoints(
    state: RacerState,
    checkpoints_list: list,
    car_x: float,
    car_y: float,
    items_active: bool = False,
    world_objects: list | None = None,
) -> None:
    """Advance *state* by one slot if the car is touching its next checkpoint.

    *checkpoints_list* is the static geometry (regular CPs followed by the
    finish line). When the finish line is crossed, ``current_lap`` increments
    and — if ``items_active`` is True — every object in ``world_objects`` is
    reactivated so the racer can pick them up again on the next lap.
    """
    if not checkpoints_list:
        return

    current_checkpoint = checkpoints_list[state.list_counter]
    if not current_checkpoint.check(car_x, car_y):
        return

    state.list_counter += 1
    state.total_checkpoints += 1
    if state.list_counter >= len(checkpoints_list):
        # Full lap completed: reset cursor, bump lap, optionally respawn items.
        state.current_lap += 1
        if items_active and world_objects:
            for item in world_objects:
                item.active = True
        state.lap_times.append((time.perf_counter(), state.current_lap))
        state.list_counter = 0
    else:
        state.lap_times.append((time.perf_counter(), state.current_lap))
