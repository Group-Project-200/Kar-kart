from __future__ import annotations

from threading import Event, RLock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from karkart.ai.ai_controller import AIController
    from karkart.physics.camera import Camera
    from karkart.physics.car import Car
    from karkart.physics.checkpoint import Checkpoint, RacerState
    from karkart.physics.collision import CollisionDetector
    from karkart.powerups.powerups_manager import PowerupRendering, PowerupsManager
    from karkart.rendering.map import Map
    from karkart.rendering.sparks import SparkManager
    from karkart.rendering.stacker import Stacker


class World:
    def __init__(
        self,
        *,
        player_car: "Car",
        ai_cars: list["Car"],
        camera: "Camera",
        sparks: "SparkManager",
        player_state: "RacerState",
        ai_states: list["RacerState"],
        player_checkpoints: list["Checkpoint"],
        ai_checkpoints: list[list["Checkpoint"]],
        ai_controllers: list["AIController"],
        powerups_manager: "PowerupsManager",
        world_box: list["PowerupRendering"],
        current_map: "Map",
        car_stacker: "Stacker",
        ai_stackers: list["Stacker"],
        collision_detector: "CollisionDetector",
        ai_collisions: list["CollisionDetector"],
        car_collision_radius: float,
        snap_step_degrees: float,
    ) -> None:
        self.player_car = player_car
        self.current_car = player_car
        self.ai_active = bool(ai_cars)
        self.player_invincible: bool = False

        self.ai_cars = ai_cars
        self.camera = camera
        self.sparks = sparks
        self.player_state = player_state
        self.ai_states = ai_states
        self.player_checkpoints = player_checkpoints
        self.ai_checkpoints = ai_checkpoints
        self.ai_controllers = ai_controllers
        self.powerups_manager = powerups_manager
        self.world_box = world_box
        self.current_map = current_map
        self.car_stacker = car_stacker
        self.ai_stackers = ai_stackers
        self.collision_detector = collision_detector
        self.ai_collisions = ai_collisions
        self.car_collision_radius = car_collision_radius
        self.snap_step_degrees = snap_step_degrees

        self.lock = RLock()
        self.stop_event = Event()
        self.pause_event = Event()
        self.race_finished_event = Event()

        self.cached_position_label: str = "1st"
        self.cp_pass_counter: int = 0
        self.race_start_time: float = 0.0
        self.last_lap_start_time: float = 0.0
        self.player_lap_times: list[float] = []
        self.last_recorded_lap: int = player_state.current_lap
        self.tick: int = 0

    def begin_race(self, now: float) -> None:
        self.race_start_time = now
        self.last_lap_start_time = now

    def collect_powerup_if_needed(self) -> None:
        if self.powerups_manager.current is not None:
            return

        player = self.player_car.physics

        for item_box in self.world_box:
            picked_up = item_box.check(player.car_x, player.car_y)

            if picked_up:
                self.powerups_manager.current = self.powerups_manager.choose_random_powerup()
                self.powerups_manager.current.activate(self)
                break

    def update_powerup(self) -> None:
        if self.powerups_manager.current is None:
            return

        finished = self.powerups_manager.current.tick(self)

        if finished:
            self.powerups_manager.current = None