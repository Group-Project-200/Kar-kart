from __future__ import annotations

import dataclasses
import random

from karkart.physics.car import CarHandling


CAR_HANDLING_PROFILES: dict[str, CarHandling] = {
    "car_01": CarHandling(),
    "car_02": CarHandling(
        max_speed=2.75,
        throttle_acceleration=0.045,
        max_turn_rate=2.1,
        default_slide_factor=0.45,
    ),
    "car_03": CarHandling(
        max_speed=2.3,
        throttle_acceleration=0.065,
        reverse_acceleration=0.05,
        max_turn_rate=2.25,
    ),
    "car_04": CarHandling(
        max_speed=3.0,
        throttle_acceleration=0.04,
        max_turn_rate=2.0,
        plateau_turn_rate=1.6,
        default_slide_factor=0.5,
    ),
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
