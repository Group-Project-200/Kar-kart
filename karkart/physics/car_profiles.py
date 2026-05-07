from __future__ import annotations

import dataclasses
import random

from karkart.physics.car import CarHandling


CAR_HANDLING_PROFILES: dict[str, CarHandling] = {
    "car_01": CarHandling(
        max_speed=3.0,
        throttle_acceleration=0.05,
        plateau_acceleration=0.35,
        turn_slip_weight=0.2,
        coast_velocity_decay=0.01,
        default_slide_factor=0.4,
    ),
    "car_02": CarHandling(
        max_speed=3.0,
        throttle_acceleration=0.05,
        plateau_acceleration=0.35,
        turn_slip_weight=0.5,
        coast_velocity_decay=0.01,
        default_slide_factor=0.15,
    ),
    "car_03": CarHandling(),
    "car_04": CarHandling(
        max_speed=3.5,
        throttle_acceleration=0.08,
        plateau_acceleration=0.45,
        turn_slip_weight=0.5,
        coast_velocity_decay=0.05,
        default_slide_factor=0.15,
        max_slip=0.5,
        turn_top_speed_falloff=0.5,
    ),
    "car_05": CarHandling(),
}


_AI_JITTER: dict[str, float] = {
    "max_speed": 0.04,
    "throttle_acceleration": 0.06,
    "max_turn_rate": 0.04,
    "default_slide_factor": 0.05,
    "plateau_turn_rate": 0.04,
}


def get_handling_for(car_name: str) -> CarHandling:
    return CAR_HANDLING_PROFILES.get(car_name, CarHandling())


def randomize_for_ai(
    handling: CarHandling, rng: random.Random | None = None
) -> CarHandling:
    r = rng if rng is not None else random.Random()
    overrides = {
        field: getattr(handling, field) * (1.0 + r.uniform(-amp, amp))
        for field, amp in _AI_JITTER.items()
    }
    return dataclasses.replace(handling, **overrides)
