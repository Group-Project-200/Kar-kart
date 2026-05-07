from __future__ import annotations

import heapq
import math
from collections import deque

import pygame

_Grid = list[list[int]]

_DIRS_8 = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
_DIRS_8_COST = (
    (-1, 0, 1.0),
    (1, 0, 1.0),
    (0, -1, 1.0),
    (0, 1, 1.0),
    (-1, -1, 1.41421356),
    (-1, 1, 1.41421356),
    (1, -1, 1.41421356),
    (1, 1, 1.41421356),
)


class AStarPathfinder:

    def __init__(
        self,
        mask: pygame.mask.Mask,
        map_dims: tuple[int, int],
        cell_size: int = 1,
        padding: int = 10,
        road_mask: pygame.mask.Mask | None = None,
    ) -> None:
        self.cell_size = max(1, int(cell_size))
        self.padding = max(0, int(padding))
        self.map_width, self.map_height = map_dims

        mask_w, mask_h = mask.get_size()
        self.mask_scale_x = mask_w / self.map_width if self.map_width else 1.0
        self.mask_scale_y = mask_h / self.map_height if self.map_height else 1.0

        self.road_mask = road_mask
        self.cols = max(1, self.map_width // self.cell_size)
        self.rows = max(1, self.map_height // self.cell_size)

        self._raw_grid: _Grid = self._build_grid(mask)
        self._grid: _Grid = [row[:] for row in self._raw_grid]
        self._pad_grid()

    def _build_grid(self, mask: pygame.mask.Mask) -> _Grid:
        mask_w, mask_h = mask.get_size()
        road_w = road_h = 0
        if self.road_mask is not None:
            road_w, road_h = self.road_mask.get_size()

        grid = [[0] * self.cols for _ in range(self.rows)]
        for row in range(self.rows):
            for col in range(self.cols):
                mx = int((col + 0.5) * self.cell_size * self.mask_scale_x)
                my = int((row + 0.5) * self.cell_size * self.mask_scale_y)
                if 0 <= mx < mask_w and 0 <= my < mask_h and mask.get_at((mx, my)):
                    grid[row][col] = 1
                    continue
                if self.road_mask is not None:
                    on_road = (
                        0 <= mx < road_w
                        and 0 <= my < road_h
                        and self.road_mask.get_at((mx, my))
                    )
                    if not on_road:
                        grid[row][col] = 1
        return grid

    def _pad_grid(self) -> None:
        if self.padding <= 0:
            return

        dist = [[-1] * self.cols for _ in range(self.rows)]
        queue: deque[tuple[int, int]] = deque()
        for row in range(self.rows):
            for col in range(self.cols):
                if self._grid[row][col] == 1:
                    dist[row][col] = 0
                    queue.append((row, col))

        while queue:
            row, col = queue.popleft()
            d = dist[row][col]
            if d >= self.padding:
                continue
            for dr, dc in _DIRS_8:
                nr, nc = row + dr, col + dc
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    continue
                if dist[nr][nc] != -1:
                    continue
                dist[nr][nc] = d + 1
                queue.append((nr, nc))

        for row in range(self.rows):
            for col in range(self.cols):
                if 0 <= dist[row][col] <= self.padding and self._grid[row][col] == 0:
                    self._grid[row][col] = 1

    def _world_to_cell(self, wx: float, wy: float) -> tuple[int, int]:
        col = max(
            0, min(self.cols - 1, int((wx + self.map_width / 2) // self.cell_size))
        )
        row = max(
            0, min(self.rows - 1, int((wy + self.map_height / 2) // self.cell_size))
        )
        return row, col

    def _cell_to_world(self, row: int, col: int) -> tuple[float, float]:
        return (col + 0.5) * self.cell_size - self.map_width / 2, (
            row + 0.5
        ) * self.cell_size - self.map_height / 2

    def _nearest_free(
        self,
        row: int,
        col: int,
        grid: _Grid | None = None,
        max_radius: int = 30,
    ) -> tuple[int, int] | None:
        if grid is None:
            grid = self._grid
        if 0 <= row < self.rows and 0 <= col < self.cols and grid[row][col] == 0:
            return row, col
        seen: set[tuple[int, int]] = {(row, col)}
        queue: deque[tuple[int, int, int]] = deque([(row, col, 0)])
        while queue:
            r, c, d = queue.popleft()
            if d >= max_radius:
                continue
            for dr, dc in _DIRS_8:
                nr, nc = r + dr, c + dc
                if (nr, nc) in seen:
                    continue
                seen.add((nr, nc))
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    continue
                if grid[nr][nc] == 0:
                    return nr, nc
                queue.append((nr, nc, d + 1))
        return None

    def find_path(
        self,
        start_world: tuple[float, float],
        goal_world: tuple[float, float],
    ) -> list[tuple[float, float]]:
        start_cell = self._world_to_cell(*start_world)
        goal_cell = self._world_to_cell(*goal_world)

        start_free = self._nearest_free(*start_cell)
        goal_free = self._nearest_free(*goal_cell)
        if start_free is not None and goal_free is not None:
            cells = self._astar(start_free, goal_free)
            if cells:
                return [self._cell_to_world(r, c) for r, c in cells]

        start_raw = self._nearest_free(*start_cell, grid=self._raw_grid)
        goal_raw = self._nearest_free(*goal_cell, grid=self._raw_grid)
        if start_raw is None or goal_raw is None:
            return []

        start_padded = self._nearest_free(*start_raw)
        goal_padded = self._nearest_free(*goal_raw)
        if start_padded is not None and goal_padded is not None:
            cells = self._astar(start_padded, goal_padded)
            if cells:
                return [self._cell_to_world(r, c) for r, c in cells]

        cells = self._astar(start_raw, goal_raw, grid=self._raw_grid)
        return [self._cell_to_world(r, c) for r, c in cells] if cells else []

    def _astar(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        grid: _Grid | None = None,
    ) -> list[tuple[int, int]]:
        if grid is None:
            grid = self._grid

        def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
            return math.hypot(a[0] - b[0], a[1] - b[1])

        open_heap: list[tuple[float, int, tuple[int, int]]] = []
        counter = 0
        heapq.heappush(open_heap, (heuristic(start, goal), counter, start))

        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start: 0.0}
        closed: set[tuple[int, int]] = set()

        while open_heap:
            _, _, current = heapq.heappop(open_heap)
            if current in closed:
                continue
            if current == goal:
                return self._reconstruct(came_from, current)
            closed.add(current)
            cur_g = g_score[current]
            for dr, dc, cost in _DIRS_8_COST:
                nr, nc = current[0] + dr, current[1] + dc
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    continue
                if grid[nr][nc] == 1:
                    continue
                tentative = cur_g + cost
                neighbour = (nr, nc)
                if tentative < g_score.get(neighbour, float("inf")):
                    came_from[neighbour] = current
                    g_score[neighbour] = tentative
                    counter += 1
                    heapq.heappush(
                        open_heap,
                        (tentative + heuristic(neighbour, goal), counter, neighbour),
                    )
        return []

    @staticmethod
    def _reconstruct(
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
    ) -> list[tuple[int, int]]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
