import os
import pygame


DEFAULT_BASE_PATH = "resources"
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


def load_map(map_folder_name: str, base_path: str = DEFAULT_BASE_PATH):
    maps_dir = os.path.join(base_path, "maps")
    requested_path = os.path.join(base_path, map_folder_name)

    # Support loading a specific map by name or filename (for example: "map_02" or "map_02.png").
    file_candidates = []
    if map_folder_name.lower().endswith(PNG_EXT):
        file_candidates.append(requested_path)
        file_candidates.append(os.path.join(maps_dir, map_folder_name))
    else:
        file_candidates.append(f"{requested_path}{PNG_EXT}")
        file_candidates.append(os.path.join(maps_dir, f"{map_folder_name}{PNG_EXT}"))
        file_candidates.append(os.path.join(maps_dir, map_folder_name))

    for file_path in file_candidates:
        if os.path.isfile(file_path):
            return pygame.image.load(file_path).convert()

    # Backward-compatible folder mode (for example: "maps").
    folder_path = requested_path
    if not os.path.isdir(folder_path):
        return None

    image_files = _list_png_files(folder_path)
    if not image_files:
        return None

    # Map is rendered as a full background layer; opaque format is faster to blit.
    return pygame.image.load(os.path.join(folder_path, image_files[0])).convert()