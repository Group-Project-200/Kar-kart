def load_map(map_folder_name, base_path="resources"):
    """
    Loads and returns the first PNG map image from the given map folder.
    Args:
        map_folder_name (str): The name of the map folder (e.g., 'map_01').
        base_path (str): The base directory where map folders are located.
    Returns:
        pygame.Surface: Loaded map image, or None if not found.
    """
    folder_path = os.path.join(base_path, map_folder_name)
    if not os.path.isdir(folder_path):
        return None
    image_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith('.png')
    ])
    if not image_files:
        return None
    return pygame.image.load(os.path.join(folder_path, image_files[0])).convert_alpha()
import os
import pygame

def load_image_stack(car_folder_name, base_path="resources"):
    """
    Loads and returns a list of pygame Surfaces for all PNG images in the given car folder.
    Args:
        car_folder_name (str): The name of the car folder (e.g., 'car_01').
        base_path (str): The base directory where car folders are located.
    Returns:
        List[pygame.Surface]: List of loaded images sorted by filename.
    """
    folder_path = os.path.join(base_path, car_folder_name)
    image_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith('.png')
    ])
    return [pygame.image.load(os.path.join(folder_path, f)).convert_alpha() for f in image_files]