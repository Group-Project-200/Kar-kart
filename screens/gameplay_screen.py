import os
import json

from dataclasses import dataclass
import pygame

from MAP import Map, MapData
from RENDERER import Renderer
from CAR import Car
from STACKER import Stacker
from CAMERA import Camera
from COLLISION_DETECTOR import CollisionDetector
from file_manager import load_image_stack
from Helper_functions import snap_degrees

with open("map_data.json") as f:
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

@dataclass(frozen=True, slots=True)
class RuntimeResources:
    map_surface: list
    car_folders: tuple[str, ...]
    car_stacks: dict[str, list[pygame.Surface]]

DEFAULT_MAP_NAME = "map1"
DEFAULT_CAR_NAME = "car_01"
current_map_data= MapData()


def car_pos_scaling(x,y,map_dimensions):
    start_x = x - map_dimensions[0] / 2
    start_y = y - map_dimensions[1] / 2
    return start_x,start_y


class GamePlay:
    def __init__(self, manager, screen):
        self.manager = manager
        self.config = GameConfig()
        self.resources = self.load_runtime_resources()

        self.current_car = Car()
        self.current_camera = Camera(self.current_car)
        self.current_map = Map(current_map_data, self.current_camera)
        self.car_stacker = Stacker(self.resources.car_stacks[DEFAULT_CAR_NAME], self.config.dirs)
        self.current_renderer = Renderer(self.current_map, self.car_stacker, screen)
        self.collision_detector =CollisionDetector(self.current_map.masks, self.car_stacker.mask_cache)
        self.current_car.physics.car_x, self.current_car.physics.car_y = car_pos_scaling(data["start"][0], data["start"][1], self.current_map.dimensions)

    def discover_car_folders(self, base_path: str = "resources") -> tuple[str, ...]:
        if not os.path.isdir(base_path):
            return ()

        car_folders = []
        for entry in sorted(os.listdir(base_path)):
            if not entry.startswith("car_"):
                continue
            folder_path = os.path.join(base_path, entry)
            if not os.path.isdir(folder_path):
                continue
            if any(file_name.lower().endswith(".png") for file_name in os.listdir(folder_path)):
                car_folders.append(entry)
        return tuple(car_folders)

    def select_default_car_index(self, car_folders: tuple[str, ...]) -> int:
        if DEFAULT_CAR_NAME in car_folders:
            return car_folders.index(DEFAULT_CAR_NAME)
        return 0

    def load_runtime_resources(self) -> RuntimeResources:
        current_map_data.layers = [pygame.image.load(
            os.path.join(r"C:\Users\mohna\Desktop\Uni\25-26\updated_gameloop\resources\maps\map_2", f)).convert_alpha()
                                   for f in
                                   os.listdir(r"C:\Users\mohna\Desktop\Uni\25-26\updated_gameloop\resources\maps\map1")
                                   if f.endswith(".png")]
        car_folders = self.discover_car_folders()
        if not car_folders:
            raise RuntimeError("No car sprite folders found in resources (expected names like car_01).")

        car_stacks = {folder_name: load_image_stack(folder_name) for folder_name in car_folders}
        return RuntimeResources(
            map_surface=current_map_data.layers,
            car_folders=car_folders,
            car_stacks=car_stacks,
        )

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
        self.collision_check()
        self.current_car.physics = self.current_car.step_physics_with_controls(snap_step_degrees=self.config.rotation_snap_degrees)
        self.current_camera.update_camera_angle()


    def draw(self, nothing):
        self.current_renderer.render_frame(self.config.gameplay_stack_spread)
        pygame.display.flip()