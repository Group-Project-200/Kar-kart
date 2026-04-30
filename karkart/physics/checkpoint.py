from __future__ import annotations

import time
from dataclasses import dataclass, field

import pygame


class Checkpoint:

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.passed: bool = False

    def check(self, car_hitbox: pygame.Rect) -> bool:
        return self.rect.colliderect(car_hitbox)


@dataclass
class RacerState:

    list_counter: int = 0
    current_lap: int = 1
    lap_times: list = field(default_factory=list)
    total_checkpoints: int = 0

    last_pass_order: int = 0


def advance_checkpoints(
    state: RacerState,
    checkpoints_list: list,
    car_hitbox: pygame.Rect,
    items_active: bool = False,
    world_objects: list | None = None,
) -> None:

    if not checkpoints_list:
        return

    current_checkpoint = checkpoints_list[state.list_counter]
    if not current_checkpoint.check(car_hitbox):
        return

    state.list_counter += 1
    state.total_checkpoints += 1
    if state.list_counter >= len(checkpoints_list):

        state.current_lap += 1
        if items_active and world_objects:
            for item in world_objects:
                item.active = True
        state.lap_times.append((time.perf_counter(), state.current_lap))
        state.list_counter = 0
    else:
        state.lap_times.append((time.perf_counter(), state.current_lap))
