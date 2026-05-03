from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CarSnapshot:
    car_x: float
    car_y: float
    rotation: float
    car_z: float
    speed: float
    drift_active: bool
    drift_direction: int
    drift_skew_degrees: float
    drift_charge_frames: int


@dataclass(slots=True)
class SparkSnapshot:
    x: float
    y: float
    life: int
    max_life: int
    r: int
    g: int
    b: int


@dataclass(slots=True)
class RacerSnapshot:
    list_counter: int
    current_lap: int
    total_checkpoints: int


@dataclass(slots=True)
class WorldSnapshot:
    tick: int
    player: CarSnapshot
    ai: list[CarSnapshot]
    camera_angle: float
    sparks: list[SparkSnapshot]
    player_racer: RacerSnapshot
    ai_racers: list[RacerSnapshot]
    item_active: list[bool]
    position_label: str
    race_finished: bool


class SnapshotBuffer:
    def __init__(self) -> None:
        self._latest: WorldSnapshot | None = None

    def publish(self, snapshot: WorldSnapshot) -> None:
        self._latest = snapshot

    def read(self) -> WorldSnapshot | None:
        return self._latest
