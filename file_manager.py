import os
import pygame


DEFAULT_BASE_PATH = "resources/render"
PNG_EXT = ".png"


# Filesystem helpers for loading sprite stacks and map textures.
def _list_png_files(folder_path: str):
    return sorted(
        file_name
        for file_name in os.listdir(folder_path)
        if file_name.lower().endswith(PNG_EXT)
    )


def load_image_stack(car_folder_name: str, base_path: str = DEFAULT_BASE_PATH):
    folder_path = os.path.join(base_path, car_folder_name)
    image_files = _list_png_files(folder_path)
    return [
        # Car is rendered as a stack of offset sprites; alpha format is needed for proper car shape.
        pygame.image.load(os.path.join(folder_path, file_name)).convert_alpha()
        for file_name in image_files
    ]

