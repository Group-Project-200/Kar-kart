"""Offline map editor.

Run this script to place checkpoints, a finish line, a starting grid and an
item region on a map image, and to save the result back into ``map_data.json``.

Controls
--------
* Left-click + drag         -- pan the camera (map area only).
* Right-click + drag        -- draw a rectangle of the current kind.
* ``C`` / ``F`` / ``G`` / ``I`` -- switch between:
    - ``C``: checkpoints (appended to the list)
    - ``F``: finish line (the last checkpoint; crossing it after all CPs counts a lap)
    - ``G``: starting grid (spawn box; not a checkpoint)
* Left-click + drag  -- pan the camera.
* Right-click + drag -- draw a rectangle of the current kind.
* ``C`` / ``S`` / ``E`` / ``I`` -- switch between:
    - ``C``: checkpoints (append to list)
    - ``S``: start placement (sets ``start_box`` and ``start``)
    - ``E``: start checkpoint
    - ``I``: item placement
* ``ESC``                   -- cancel the current rectangle.
* Sidebar [▲] / [▼] buttons -- move a checkpoint up or down in race order.
* Close window              -- save ``map_data.json`` and exit.

Checkpoints are labelled CP_01 … CP_NN on the map and listed in the right-hand
sidebar in their current race order. Use the arrow buttons to correct the order
before closing; the final array order is what the game uses.
"""

from __future__ import annotations

import json

import pygame

from karkart.paths import MAPS_DIR, MAP_DATA_FILE


MAP_NAME = "map_2"
WINDOW_SIZE = (1280, 720)

# Sidebar geometry
_SIDEBAR_W = 200
_MAP_VIEW_W = WINDOW_SIZE[0] - _SIDEBAR_W   # map lives in [0, _MAP_VIEW_W)
_SB_X = _MAP_VIEW_W                          # sidebar left edge
_SB_PAD = 8
_SB_ROW_H = 34
_SB_TOP = 44                                 # first row y (below sidebar title)
_BTN_W = 24
_BTN_H = 20


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

def _row_button_rects(row: int) -> tuple[pygame.Rect, pygame.Rect]:
    """Return (up_rect, down_rect) for a sidebar row."""
    ry = _SB_TOP + row * _SB_ROW_H
    by = ry + (_SB_ROW_H - _BTN_H) // 2
    up_rect = pygame.Rect(_SB_X + _SIDEBAR_W - 2 * _BTN_W - 2 * _SB_PAD, by, _BTN_W, _BTN_H)
    down_rect = pygame.Rect(_SB_X + _SIDEBAR_W - _BTN_W - _SB_PAD, by, _BTN_W, _BTN_H)
    return up_rect, down_rect


def _draw_sidebar(
    screen: pygame.Surface,
    font: pygame.font.Font,
    checkpoints: list,
) -> None:
    pygame.draw.rect(screen, (28, 28, 35), (_SB_X, 0, _SIDEBAR_W, WINDOW_SIZE[1]))
    pygame.draw.line(screen, (70, 70, 80), (_SB_X, 0), (_SB_X, WINDOW_SIZE[1]))

    title = font.render("CHECKPOINTS", True, (180, 180, 200))
    screen.blit(title, (_SB_X + _SB_PAD, 12))

    n = len(checkpoints)
    for i in range(n):
        ry = _SB_TOP + i * _SB_ROW_H

        lbl = font.render(f"CP_{i + 1:02d}", True, (230, 230, 230))
        screen.blit(lbl, (_SB_X + _SB_PAD, ry + (_SB_ROW_H - lbl.get_height()) // 2))

        up_rect, down_rect = _row_button_rects(i)

        up_col = (55, 55, 65) if i == 0 else (60, 120, 200)
        down_col = (55, 55, 65) if i == n - 1 else (60, 120, 200)

        pygame.draw.rect(screen, up_col, up_rect, border_radius=3)
        pygame.draw.rect(screen, down_col, down_rect, border_radius=3)

        for surf, rect in (
            (font.render("\u25b2", True, (220, 220, 220)), up_rect),
            (font.render("\u25bc", True, (220, 220, 220)), down_rect),
        ):
            screen.blit(surf, surf.get_rect(center=rect.center))

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

def _draw_map_overlays(
    screen: pygame.Surface,
    font: pygame.font.Font,
    data: dict,
    camera_x: int,
    camera_y: int,
) -> None:
    cps = data[MAP_NAME]["checkpoints"]
    for i, cp in enumerate(cps):
        rx = cp["x"] - camera_x
        ry = cp["y"] - camera_y
        pygame.draw.rect(screen, (255, 80, 80), (rx, ry, cp["w"], cp["h"]), 2)

        label_surf = font.render(f"CP_{i + 1:02d}", True, (255, 240, 80))
        cx = rx + cp["w"] // 2
        cy = ry + cp["h"] // 2
        backing = pygame.Surface(
            (label_surf.get_width() + 4, label_surf.get_height() + 2), pygame.SRCALPHA,
        )
        backing.fill((0, 0, 0, 140))
        screen.blit(backing, backing.get_rect(center=(cx, cy)))
        screen.blit(label_surf, label_surf.get_rect(center=(cx, cy)))

    if "start_grid" in data[MAP_NAME]:
        x, y, w, h = data[MAP_NAME]["start_grid"]
        pygame.draw.rect(screen, (0, 80, 255), (x - camera_x, y - camera_y, w, h), 2)
        lbl = font.render("START GRID", True, (80, 160, 255))
        screen.blit(lbl, lbl.get_rect(center=(x - camera_x + w // 2, y - camera_y + h // 2)))

    if "finish_line" in data[MAP_NAME]:
        x, y, w, h = data[MAP_NAME]["finish_line"]
        pygame.draw.rect(screen, (0, 220, 80), (x - camera_x, y - camera_y, w, h), 2)
        lbl = font.render("FINISH", True, (0, 255, 120))
        screen.blit(lbl, lbl.get_rect(center=(x - camera_x + w // 2, y - camera_y + h // 2)))

    if "items" in data[MAP_NAME]:
        x, y, w, h = data[MAP_NAME]["items"]
        pygame.draw.rect(screen, (180, 0, 200), (x - camera_x, y - camera_y, w, h), 2)

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Map Editor")

    data = _load_data()
    data.setdefault(MAP_NAME, {"checkpoints": []})

    map_image = pygame.image.load(str(MAPS_DIR / MAP_NAME / "0.png"))
    screen = pygame.display.set_mode(WINDOW_SIZE)
    font = pygame.font.Font(None, 22)

    camera_x = camera_y = 0
    dragging = False
    last_mouse_x = last_mouse_y = 0
    placing = False
    place_start = (0, 0)
    mode = ""

    running = True
    while running:
        cps = data[MAP_NAME]["checkpoints"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ---- keyboard ------------------------------------------------- #
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    mode, placing = "checkpoints", False
                elif event.key == pygame.K_f:
                    mode, placing = "finish_line", False
                elif event.key == pygame.K_g:
                    mode, placing = "start_grid", False
                elif event.key == pygame.K_i:
                    mode, placing = "item placements", False
                elif event.key == pygame.K_ESCAPE:
                    placing = False
                elif event.key == pygame.K_d:
                    mode, placing = "delete", False

            # ---- left-click: pan (map only) or sidebar buttons ------------ #
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if mx < _MAP_VIEW_W:
                    dragging = True
                    last_mouse_x, last_mouse_y = mx, my
                else:
                    for i in range(len(cps)):
                        up_rect, down_rect = _row_button_rects(i)
                        if up_rect.collidepoint(mx, my) and i > 0:
                            cps[i], cps[i - 1] = cps[i - 1], cps[i]
                        elif down_rect.collidepoint(mx, my) and i < len(cps) - 1:
                            cps[i], cps[i + 1] = cps[i + 1], cps[i]

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                dx = event.pos[0] - last_mouse_x
                dy = event.pos[1] - last_mouse_y
                camera_x -= dx
                camera_y -= dy
                last_mouse_x, last_mouse_y = event.pos

            # ---- right-click: draw rectangle ------------------------------ #
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                mx, my = event.pos
                wx, wy = mx + camera_x, my + camera_y
                if mode == "delete":
                    _try_delete_at(data, wx, wy)
                elif mx < _MAP_VIEW_W:
                    place_start = (mx + camera_x, my + camera_y)
                    placing = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3 and placing:
                mx, my = event.pos
                end = (mx + camera_x, my + camera_y)
                x, y, w, h = _rect_from_corners(place_start, end)
                if w > 5 and h > 5:
                    if mode == "checkpoints":
                        cps.append({"x": x, "y": y, "w": w, "h": h})
                    elif mode == "finish_line":
                        data[MAP_NAME]["finish_line"] = (x, y, w, h)
                    elif mode == "start_grid":
                        data[MAP_NAME]["start_grid"] = (x, y, w, h)
                    elif mode == "item placements":
                        data[MAP_NAME]["items"] = (x, y, w, h)
                placing = False

        # ---- clamp camera to map bounds ----------------------------------- #
        camera_x = max(0, min(camera_x, max(0, map_image.get_width() - _MAP_VIEW_W)))
        camera_y = max(0, min(camera_y, max(0, map_image.get_height() - WINDOW_SIZE[1])))

        # ---- draw --------------------------------------------------------- #
        screen.blit(map_image, (-camera_x, -camera_y))
        _draw_map_overlays(screen, font, data, camera_x, camera_y)

        if placing:
            mx, my = pygame.mouse.get_pos()
            px, py, pw, ph = _rect_from_corners(place_start, (mx + camera_x, my + camera_y))
            pygame.draw.rect(screen, (255, 255, 0), (px - camera_x, py - camera_y, pw, ph), 2)

        mode_lbl = font.render(
            f"MODE: {mode if mode else '(press C / F / G / I)'}",
            True, (255, 255, 255),
        )
        screen.blit(mode_lbl, (10, WINDOW_SIZE[1] - mode_lbl.get_height() - 10))

        _draw_sidebar(screen, font, cps)
        pygame.display.flip()

    with MAP_DATA_FILE.open("w") as f:
        json.dump(data, f, indent=2)

    pygame.quit()


if __name__ == "__main__":
    main()
