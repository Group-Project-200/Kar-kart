"""when creating the maps we needed a way to place checkpoints, items, start and finish and other stuff so we decided
to create a map editor that has different modes and a click and drag feature to add different items as well as math to
calculate specific stuff such as the start positions based on the start area. the information for each map is saved
into a json file and is also updated based on changes made like deleting checkpoints or adding new items. """


import json
import pygame

from karkart.paths import MAPS_DIR, MAP_DATA_FILE


DEFAULT_MAP_NAME = "map_2"
WINDOW_SIZE = (1280, 720)


_SIDEBAR_W = 200
_MAP_VIEW_W = WINDOW_SIZE[0] - _SIDEBAR_W
_SB_X = _MAP_VIEW_W
_SB_PAD = 8
_SB_ROW_H = 34
_SB_TOP = 44
_BTN_W = 24
_BTN_H = 20


_MS_H = 26
_MS_PAD = 6
_MS_GAP = 4
_MS_BTN_W = 110


def _rect_from_corners(
    a: tuple[int, int], b: tuple[int, int]
) -> tuple[int, int, int, int]:
    x = min(a[0], b[0])
    y = min(a[1], b[1])
    return x, y, abs(b[0] - a[0]), abs(b[1] - a[1])

def find_coordinate(a, b, t):
    return a + (b - a) * t

def _start_pos(cp):
    coordinates = []

    x_near = find_coordinate(cp[0][0], cp[1][0], 3 / 4)
    y_near = find_coordinate(cp[0][1], cp[1][1], 3 / 4)
    x_far = find_coordinate(cp[3][0], cp[2][0], 3 / 4)
    y_far = find_coordinate(cp[3][1], cp[2][1], 3 / 4)


    x_first = find_coordinate(cp[0][0], cp[1][0], 0.25)
    y_first = find_coordinate(cp[0][1], cp[1][1], 0.25)
    x_second = find_coordinate(x_near, x_far, 2 / 5)
    y_second = find_coordinate(y_near, y_far, 2 / 5)
    x_fifth = find_coordinate(cp[3][0], cp[2][0], 0.25)
    y_fifth = find_coordinate(cp[3][1], cp[2][1], 0.25)
    x_third = find_coordinate(x_first, x_fifth, 3 / 5)
    y_third = find_coordinate(y_first, y_fifth, 3 / 5)
    x_fourth = find_coordinate(x_near, x_far, 4 / 5)
    y_fourth = find_coordinate(y_near, y_far, 4 / 5)

    coordinates.append((x_first, y_first))
    coordinates.append((x_second, y_second))
    coordinates.append((x_third, y_third))
    coordinates.append((x_fourth, y_fourth))
    coordinates.append((x_fifth, y_fifth))


    return coordinates


def _load_data() -> dict:
    try:
        with MAP_DATA_FILE.open() as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _point_in_rect(px: int, py: int, rx: int, ry: int, rw: int, rh: int) -> bool:
    return rx <= px <= rx + rw and ry <= py <= ry + rh


def _point_in_polygon(px: float, py: float, points: list) -> bool:
    """Ray-casting test: True if (px, py) is inside the polygon."""
    n = len(points)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = points[i]
        xj, yj = points[j]
        if ((yi > py) != (yj > py)) and \
           (px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _row_button_rects(row: int) -> tuple[pygame.Rect, pygame.Rect]:
    ry = _SB_TOP + row * _SB_ROW_H
    by = ry + (_SB_ROW_H - _BTN_H) // 2
    up_rect = pygame.Rect(
        _SB_X + _SIDEBAR_W - 2 * _BTN_W - 2 * _SB_PAD, by, _BTN_W, _BTN_H
    )
    down_rect = pygame.Rect(_SB_X + _SIDEBAR_W - _BTN_W - _SB_PAD, by, _BTN_W, _BTN_H)
    return up_rect, down_rect


def _is_valid_rect(rect: object) -> bool:
    return (
        isinstance(rect, (list, tuple))
        and len(rect) == 4
        and all(isinstance(v, int) for v in rect)
    )


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


def powerups_sizing(x, y, w, h):
    if w >= h:
        box1 = [x, y, 60, 60]
        box2 = [x + 80, y, 60, 60]
        box3 = [x + 160, y, 60, 60]
    else:
        box1 = [x, y, 60, 60]
        box2 = [x, y + 80, 60, 60]
        box3 = [x, y + 160, 60, 60]
    return box1, box2, box3


def _available_maps() -> list[str]:
    if not MAPS_DIR.is_dir():
        return []
    return sorted(
        p.name for p in MAPS_DIR.iterdir() if p.is_dir() and (p / "0.png").is_file()
    )


def _map_switch_rects(maps: list[str]) -> list[pygame.Rect]:
    rects: list[pygame.Rect] = []
    x = _MS_PAD
    y = WINDOW_SIZE[1] - _MS_H - _MS_PAD
    for _ in maps:
        rects.append(pygame.Rect(x, y, _MS_BTN_W, _MS_H))
        x += _MS_BTN_W + _MS_GAP
    return rects


def _draw_map_switcher(
    screen: pygame.Surface,
    font: pygame.font.Font,
    maps: list[str],
    current: str,
    rects: list[pygame.Rect],
) -> None:
    for name, rect in zip(maps, rects):
        col = (60, 120, 200) if name == current else (55, 55, 65)
        pygame.draw.rect(screen, col, rect, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1, border_radius=4)
        lbl = font.render(name, True, (230, 230, 230))
        screen.blit(lbl, lbl.get_rect(center=rect.center))


def _try_delete_at(data: dict, map_name: str, wx: int, wy: int) -> bool:
    entry = data[map_name]

    # finish_line is still a rect
    fl = entry.get("finish_line")
    if _is_valid_rect(fl):
        x, y, w, h = fl
        if _point_in_rect(wx, wy, x, y, w, h):
            del entry["finish_line"]
            return True

    # start_grid is now a polygon (4 points)
    sg = entry.get("start_grid")
    if sg and len(sg) >= 3:
        if _point_in_polygon(wx, wy, sg):
            del entry["start_grid"]
            return True

    if "items" in entry:
        items = entry["items"]
        for i in range(len(items) - 1, -1, -1):
            item = items[i]
            if _is_valid_rect(item):
                x, y, w, h = item
                if _point_in_rect(wx, wy, x, y, w, h):
                    items.pop(i)
                    return True

    checkpoints = entry.get("checkpoints", [])
    for i in range(len(checkpoints) - 1, -1, -1):
        cp = checkpoints[i]
        if _point_in_rect(wx, wy, cp["x"], cp["y"], cp["w"], cp["h"]):
            checkpoints.pop(i)
            return True
    return False


def _draw_map_overlays(
    screen: pygame.Surface,
    font: pygame.font.Font,
    data: dict,
    map_name: str,
    camera_x: int,
    camera_y: int,
) -> None:
    cps = data[map_name]["checkpoints"]
    for i, cp in enumerate(cps):
        rx = cp["x"] - camera_x
        ry = cp["y"] - camera_y
        pygame.draw.rect(screen, (255, 80, 80), (rx, ry, cp["w"], cp["h"]), 2)

        label_surf = font.render(f"CP_{i + 1:02d}", True, (255, 240, 80))
        cx = rx + cp["w"] // 2
        cy = ry + cp["h"] // 2
        backing = pygame.Surface(
            (label_surf.get_width() + 4, label_surf.get_height() + 2),
            pygame.SRCALPHA,
        )
        backing.fill((0, 0, 0, 140))
        screen.blit(backing, backing.get_rect(center=(cx, cy)))
        screen.blit(label_surf, label_surf.get_rect(center=(cx, cy)))

    start_grid = data[map_name].get("start_grid")
    if start_grid:
        points = [(p[0] - camera_x, p[1] - camera_y) for p in start_grid]
        pygame.draw.lines(screen, (0, 80, 255), True, points, 2)

        cx = sum(p[0] for p in points) // len(points)
        cy = sum(p[1] for p in points) // len(points)
        lbl = font.render("START GRID", True, (80, 160, 255))
        screen.blit(lbl, lbl.get_rect(center=(cx, cy)))

        if len(start_grid) == 4:  # ← inside the if start_grid: block
            spawn_points = _start_pos(start_grid)
            colors = [
                (255, 80, 80),
                (255, 200, 80),
                (80, 255, 80),
                (80, 200, 255),
                (220, 80, 255),
            ]
            for i, (px, py) in enumerate(spawn_points):
                sx = int(px - camera_x)
                sy = int(py - camera_y)
                color = colors[i % len(colors)]
                pygame.draw.circle(screen, color, (sx, sy), 6)
                label = font.render(str(i + 1), True, (255, 255, 255))
                screen.blit(label, (sx + 8, sy - 8))


    finish_line = data[map_name].get("finish_line")
    if _is_valid_rect(finish_line):
        x, y, w, h = finish_line
        pygame.draw.rect(screen, (0, 220, 80), (x - camera_x, y - camera_y, w, h), 2)
        lbl = font.render("FINISH", True, (0, 255, 120))
        screen.blit(
            lbl, lbl.get_rect(center=(x - camera_x + w // 2, y - camera_y + h // 2))
        )

    for item in data[map_name].get("items", []):
        if _is_valid_rect(item):
            x, y, w, h = item
            pygame.draw.rect(
                screen, (180, 0, 200), (x - camera_x, y - camera_y, w, h), 2
            )


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Map Editor")

    data = _load_data()

    available_maps = _available_maps()
    if not available_maps:
        raise RuntimeError(f"No maps with a 0.png layer found in {MAPS_DIR}")
    map_name = (
        DEFAULT_MAP_NAME if DEFAULT_MAP_NAME in available_maps else available_maps[0]
    )
    switch_rects = _map_switch_rects(available_maps)

    data.setdefault(map_name, {"checkpoints": []})
    map_image = pygame.image.load(str(MAPS_DIR / map_name / "0.png"))
    pygame.display.set_caption(f"Map Editor - {map_name}")

    screen = pygame.display.set_mode(WINDOW_SIZE)
    font = pygame.font.Font(None, 22)

    camera_x = camera_y = 0
    dragging = False
    last_mouse_x = last_mouse_y = 0
    placing = False
    place_start = (0, 0)
    mode = ""
    pending_points: list[list[int]] = []

    running = True
    while running:
        cps = data[map_name]["checkpoints"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    mode, placing = "checkpoints", False
                    pending_points = []
                elif event.key == pygame.K_f:
                    mode, placing = "finish_line", False
                    pending_points = []
                elif event.key == pygame.K_g:
                    mode, placing = "start_grid", False
                elif event.key == pygame.K_i:
                    mode, placing = "item placements", False
                    pending_points = []
                elif event.key == pygame.K_d:
                    mode, placing = "delete", False
                    pending_points = []
                elif event.key == pygame.K_ESCAPE:
                    placing = False
                    pending_points = []

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                switched = False
                for name, rect in zip(available_maps, switch_rects):
                    if rect.collidepoint(mx, my):
                        if name != map_name:
                            map_name = name
                            data.setdefault(map_name, {"checkpoints": []})
                            map_image = pygame.image.load(
                                str(MAPS_DIR / map_name / "0.png"),
                            )
                            pygame.display.set_caption(f"Map Editor - {map_name}")
                            camera_x = camera_y = 0
                            placing = False
                            pending_points = []
                        switched = True
                        break
                if switched:
                    continue

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

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                mx, my = event.pos
                wx, wy = mx + camera_x, my + camera_y
                if mode == "delete":
                    _try_delete_at(data, map_name, wx, wy)
                elif mode == "start_grid" and mx < _MAP_VIEW_W:
                    pending_points.append([wx, wy])
                    if len(pending_points) == 4:
                        data[map_name]["start_grid"] = pending_points
                        spawn_points = _start_pos(pending_points)
                        data[map_name]["spawn_points"] = [list(p) for p in spawn_points]
                        pending_points = []
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
                        data[map_name]["finish_line"] = (x, y, w, h)
                    elif mode == "item placements":
                        box1, box2, box3 = powerups_sizing(x, y, w, h)
                        items = data[map_name].setdefault("items", [])
                        items.append(box1)
                        items.append(box2)
                        items.append(box3)
                placing = False

        camera_x = max(0, min(camera_x, max(0, map_image.get_width() - _MAP_VIEW_W)))
        camera_y = max(
            0, min(camera_y, max(0, map_image.get_height() - WINDOW_SIZE[1]))
        )

        screen.blit(map_image, (-camera_x, -camera_y))
        _draw_map_overlays(screen, font, data, map_name, camera_x, camera_y)

        if placing:
            mx, my = pygame.mouse.get_pos()
            px, py, pw, ph = _rect_from_corners(
                place_start, (mx + camera_x, my + camera_y)
            )
            pygame.draw.rect(
                screen, (255, 255, 0), (px - camera_x, py - camera_y, pw, ph), 2
            )

        if pending_points:
            screen_pts = [(p[0] - camera_x, p[1] - camera_y) for p in pending_points]
            for pt in screen_pts:
                pygame.draw.circle(screen, (255, 255, 0), pt, 4)
            if len(screen_pts) >= 2:
                pygame.draw.lines(screen, (255, 255, 0), False, screen_pts, 1)

        if mode == "delete":
            mode_text = "DELETE (right-click to remove)"
        elif mode == "start_grid":
            mode_text = f"start_grid ({len(pending_points)}/4 corners placed)"
        else:
            mode_text = mode if mode else "(press C / F / G / I / D)"

        mode_lbl = font.render(
            f"MODE: {mode_text}",
            True,
            (255, 255, 255),
        )
        mode_lbl_y = WINDOW_SIZE[1] - _MS_H - _MS_PAD - mode_lbl.get_height() - 6
        screen.blit(mode_lbl, (10, mode_lbl_y))

        _draw_sidebar(screen, font, cps)
        _draw_map_switcher(screen, font, available_maps, map_name, switch_rects)
        pygame.display.flip()

    with MAP_DATA_FILE.open("w") as f:
        json.dump(data, f, indent=2)

    pygame.quit()


if __name__ == "__main__":
    main()