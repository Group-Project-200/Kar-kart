import argparse
import os
import sys
import time
from dataclasses import dataclass, field
import pygame

from MAP import Map
from RENDERER import Renderer
from CAR import Car
from STACKER import Stacker
from CAMERA import Camera

from file_manager import load_image_stack, load_map


# Central gameplay/render knobs used by startup and the main loop.
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



#this section is for runtime resources:
DEFAULT_MAP_NAME = "map_02"
DEFAULT_CAR_NAME = "car_01"

@dataclass(frozen=True, slots=True)
class RuntimeResources:
    map_surface: pygame.Surface | None
    car_folders: tuple[str, ...]
    car_stacks: dict[str, list[pygame.Surface]]



def discover_car_folders(base_path: str = "resources") -> tuple[str, ...]:
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


def select_default_car_index(car_folders: tuple[str, ...]) -> int:
    if DEFAULT_CAR_NAME in car_folders:
        return car_folders.index(DEFAULT_CAR_NAME)
    return 0







#controls of the game
def _quit_game() -> None:
    pygame.quit()
    sys.exit()


def handle_events(controls) :
    # Keep key controls normalized so physics can consume a compact control snapshot.
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                _quit_game()
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        _quit_game()
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

def main() -> None:
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    config = GameConfig

    current_car = Car()


    
    while True:
        clock.tick(config.fps)
        handle_events(current_car.controls)



        current_car.physics = current_car.step_physics_with_controls(snap_step_degrees = config.rotation_snap_degrees)