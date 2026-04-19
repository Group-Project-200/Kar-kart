import os
import json
import time

from dataclasses import dataclass
import pygame

from MAP import Map, MapData
from RENDERER import Renderer
from CAR import Car
from STACKER import Stacker
from CAMERA import Camera
from COLLISION_DETECTOR import CollisionDetector
from start_sequence import StartSequence
from Helper_functions import snap_degrees


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "map_data.json")) as f:
    data = json.load(f)



@dataclass(frozen=True, slots=True)
class GameConfig:
    fps: int = 60
    dirs: int = 36
    gameplay_stack_spread: float = -1
    default_resolution: tuple[int, int] = (1280, 720)
    standard_resolutions: tuple[tuple[int, int], ...] = (
        (1280, 720),
        (1920, 1080),
    )
    rotation_snap_degrees = 360.0 / dirs


def car_pos_scaling(x,y,map_dimensions):
    start_x = x - map_dimensions[0] / 2
    start_y = y - map_dimensions[1] / 2
    return start_x,start_y


class GamePlay:
    def __init__(self, manager):
        self.manager = manager
        self.config = GameConfig()
        self.current_map_data = MapData()
        self.current_map_data.checkpoints = data[self.manager.app_data.current_map.name]["checkpoints"]
        self.current_map_data.start_checkpoint = data[self.manager.app_data.current_map.name]["start_checkpoint"]
        self.current_map_data.layers = self.manager.app_data.return_map_layers()
        self.countdown = StartSequence(self.manager.screen_display)

        self.current_car = Car()
        self.current_camera = Camera(self.current_car)
        self.current_map = Map(self.current_map_data, self.current_camera)
        self.car_stacker = Stacker(self.manager.app_data.current_car, self.config.dirs)
        self.current_renderer = Renderer(self.current_map, self.car_stacker, self.manager.screen_display)
        self.collision_detector =CollisionDetector(self.current_map.masks, self.car_stacker.mask_cache)
        self.current_car.physics.car_x, self.current_car.physics.car_y = car_pos_scaling(data[self.manager.app_data.current_map.name]["start"][0], data[self.manager.app_data.current_map.name]["start"][1], self.current_map.dimensions)



    def handle_event(self, event):
        controls = self.current_car.controls
        match event.type:
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_a:
                        controls.left_pressed = True
                        controls.steer_input = 1
                    case pygame.K_d:
                        controls.right_pressed = True
                        controls.steer_input = -1
                    case pygame.K_w:
                        controls.up_input = True
                    case pygame.K_s:
                        controls.down_input = True
                    case pygame.K_SPACE:
                        controls.drift_input = True
            case pygame.KEYUP:
                match event.key:
                    case pygame.K_a:
                        controls.left_pressed = False
                        if controls.steer_input == 1:
                            controls.steer_input = -1 if controls.right_pressed else 0
                    case pygame.K_d:
                        controls.right_pressed = False
                        if controls.steer_input == -1:
                            controls.steer_input = 1 if controls.left_pressed else 0
                    case pygame.K_w:
                        controls.up_input = False
                    case pygame.K_s:
                        controls.down_input = False
                    case pygame.K_SPACE:
                        controls.drift_input = False

    def collision_check(self):
        car_relative_rotation = self.current_car.physics.rotation - self.current_camera.angle
        self.current_map.get_coordinates()
        dir_idx = snap_degrees(car_relative_rotation, dirs=self.car_stacker.dirs)
        offset = (self.current_map.car_map_x, self.current_map.car_map_y)
        self.current_car.collision_results = self.collision_detector.check(dir_idx, offset)



    def update(self):
        if not self.countdown.complete:
            return
        self.collision_check()
        self.current_car.physics = self.current_car.step_physics_with_controls(snap_step_degrees=self.config.rotation_snap_degrees)
        self.current_camera.update_camera_angle()
        self.current_map.update_checkpoints()


    def draw(self, _):
        self.current_renderer.render_frame(self.config.gameplay_stack_spread)
        #code for start_time countdown
        while self.countdown.seconds > 0:
            self.current_renderer.render_frame(self.config.gameplay_stack_spread)
            self.countdown.write()
            pygame.display.flip()
            time.sleep(1)
            self.countdown.seconds -= 1

        self.countdown.complete = True

        print(self.current_map.lap_times)

        pygame.display.flip()