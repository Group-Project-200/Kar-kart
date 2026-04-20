"""Offline map editor.

Run this script to place checkpoints, a start box, a start checkpoint and an
item region on a map image, and to save the result back into ``map_data.json``.

Controls
--------
* Left-click + drag  -- pan the camera.
* Right-click + drag -- draw a rectangle of the current kind.
* ``C`` / ``S`` / ``E`` / ``I`` -- switch between:
    - ``C``: checkpoints (append to list)
    - ``S``: start placement (sets ``start_box`` and ``start``)
    - ``E``: start checkpoint
    - ``I``: item placement
* ``ESC`` -- cancel the current rectangle.
* Close window -- save ``map_data.json`` and exit.
"""

from __future__ import annotations

import json

import pygame

from karkart.paths import MAPS_DIR, MAP_DATA_FILE


MAP_NAME = "map_2"
WINDOW_SIZE = (1280, 720)


def _rect_from_corners(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int, int, int]:
    x = min(a[0], b[0])
    y = min(a[1], b[1])
    return x, y, abs(b[0] - a[0]), abs(b[1] - a[1])


def _start_pos(x: int, y: int, w: int, h: int) -> tuple[float, int]:
    """Centre the spawn 3/4 of the way across the start box, at the bottom edge."""
    return x + (3 / 4 * w), y + h


def _load_data() -> dict:
    try:
        with MAP_DATA_FILE.open() as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def _point_in_rect(px: int, py: int, rx: int, ry: int, rw: int, rh: int) -> bool:
    return rx <= px <= rx + rw and ry <= py <= ry + rh

def _try_delete_at(data: dict, wx: int, wy: int) -> bool:

    entry = data[MAP_NAME]

    # Single-placement rects first
    for key in ("start_box", "start_checkpoint", "items"):
        if key in entry:
            x, y, w, h = entry[key]
            if _point_in_rect(wx, wy, x, y, w, h):
                del entry[key]
                # If we removed the start box, the spawn point is meaningless.
                if key == "start_box" and "start" in entry:
                    del entry["start"]
                return True

    # Checkpoints: delete the top-most one clicked (iterate reversed)
    checkpoints = entry.get("checkpoints", [])
    for i in range(len(checkpoints) - 1, -1, -1):
        cp = checkpoints[i]
        if _point_in_rect(wx, wy, cp["x"], cp["y"], cp["w"], cp["h"]):
            checkpoints.pop(i)
            return True


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Map Editor")

    data = _load_data()
    data.setdefault(MAP_NAME, {"checkpoints": []})

    map_image = pygame.image.load(str(MAPS_DIR / MAP_NAME / "0.png"))
    screen = pygame.display.set_mode(WINDOW_SIZE)
    font = pygame.font.Font(None, 24)

    camera_x = camera_y = 0
    dragging = False
    last_mouse_x = last_mouse_y = 0
    placing = False
    place_start = (0, 0)
    mode = ""

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging = True
                last_mouse_x, last_mouse_y = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    mode, placing = "checkpoints", False
                elif event.key == pygame.K_s:
                    mode, placing = "start placement", False
                elif event.key == pygame.K_e:
                    mode, placing = "start_checkpoint", False
                elif event.key == pygame.K_i:
                    mode, placing = "item placements", False
                elif event.key == pygame.K_ESCAPE:
                    placing = False
                elif event.key == pygame.K_d:
                    mode, placing = "delete", False

            elif event.type == pygame.MOUSEMOTION and dragging:
                dx = event.pos[0] - last_mouse_x
                dy = event.pos[1] - last_mouse_y
                camera_x -= dx
                camera_y -= dy
                last_mouse_x, last_mouse_y = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                mx, my = event.pos
                wx, wy = mx + camera_x, my + camera_y
                if mode == "delete":
                    _try_delete_at(data, wx, wy)
                else:
                    place_start = (mx + camera_x, my + camera_y)
                    placing = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3 and placing:
                mx, my = event.pos
                end = (mx + camera_x, my + camera_y)
                x, y, w, h = _rect_from_corners(place_start, end)
                if w > 5 and h > 5:
                    if mode == "checkpoints":
                        data[MAP_NAME]["checkpoints"].append({"x": x, "y": y, "w": w, "h": h})
                    elif mode == "start placement":
                        data[MAP_NAME]["start_box"] = (x, y, w, h)
                        data[MAP_NAME]["start"] = _start_pos(x, y, w, h)
                    elif mode == "start_checkpoint":
                        data[MAP_NAME]["start_checkpoint"] = (x, y, w, h)
                    elif mode == "item placements":
                        data[MAP_NAME]["items"] = (x, y, w, h)
                placing = False

        camera_x = max(0, min(camera_x, max(0, map_image.get_width() - WINDOW_SIZE[0])))
        camera_y = max(0, min(camera_y, max(0, map_image.get_height() - WINDOW_SIZE[1])))

        screen.blit(map_image, (-camera_x, -camera_y))

        for cp in data[MAP_NAME]["checkpoints"]:
            pygame.draw.rect(
                screen, (255, 0, 0),
                (cp["x"] - camera_x, cp["y"] - camera_y, cp["w"], cp["h"]),
            )
        if "start_box" in data[MAP_NAME]:
            x, y, w, h = data[MAP_NAME]["start_box"]
            pygame.draw.rect(screen, (0, 0, 255), (x - camera_x, y - camera_y, w, h))
        if "start_checkpoint" in data[MAP_NAME]:
            x, y, w, h = data[MAP_NAME]["start_checkpoint"]
            pygame.draw.rect(screen, (0, 255, 0), (x - camera_x, y - camera_y, w, h))
        if "items" in data[MAP_NAME]:
            x, y, w, h = data[MAP_NAME]["items"]
            pygame.draw.rect(screen, (128, 0, 128), (x - camera_x, y - camera_y, w, h))

        if placing:
            mx, my = pygame.mouse.get_pos()
            end = (mx + camera_x, my + camera_y)
            x, y, w, h = _rect_from_corners(place_start, end)
            pygame.draw.rect(screen, (255, 255, 0), (x - camera_x, y - camera_y, w, h), 2)

        label = font.render(
            f"MODE: {mode if mode else '(press C or S or E or I)'}",
            True, (255, 255, 255),
        )
        screen.blit(label, (10, 10))
        pygame.display.flip()

    with MAP_DATA_FILE.open("w") as f:
        json.dump(data, f, indent=2)

    pygame.quit()


if __name__ == "__main__":
    main()
