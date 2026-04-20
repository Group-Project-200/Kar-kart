"""A* pathfinding on a padded occupancy grid built from the collision mask.

The grid is derived once from the map's wall mask by sampling one cell per
``cell_size`` map pixels. A multi-source BFS from every wall cell then marks
any free cell within ``padding`` cells as blocked, so the planner naturally
keeps the racing line away from edges.
"""

from __future__ import annotations

import heapq
import math
from collections import deque

import pygame


class AStarPathfinder:
    """A* over a downsampled, wall-padded occupancy grid."""

    def __init__(
        self,
        mask: pygame.mask.Mask,
        map_dims: tuple[int, int],
        cell_size: int = 8,
        padding: int = 6,
    ) -> None:
        self.cell_size = max(1, int(cell_size))
        self.padding = max(0, int(padding))
        self.map_width, self.map_height = map_dims

        mask_w, mask_h = mask.get_size()
        self.mask_scale_x = mask_w / self.map_width if self.map_width else 1.0
        self.mask_scale_y = mask_h / self.map_height if self.map_height else 1.0

        self.cols = max(1, self.map_width // self.cell_size)
        self.rows = max(1, self.map_height // self.cell_size)

        self._grid: list[list[int]] = self._build_grid(mask)
        self._pad_grid()

    # ------------------------------------------------------------------ #
    # Grid construction                                                  #
    # ------------------------------------------------------------------ #

    def _build_grid(self, mask: pygame.mask.Mask) -> list[list[int]]:
        """Sample *mask* at each cell's centre. 1 = wall, 0 = free."""
        mask_w, mask_h = mask.get_size()
        grid = [[0] * self.cols for _ in range(self.rows)]
        for row in range(self.rows):
            for col in range(self.cols):
                mx = int((col + 0.5) * self.cell_size * self.mask_scale_x)
                my = int((row + 0.5) * self.cell_size * self.mask_scale_y)
                if 0 <= mx < mask_w and 0 <= my < mask_h and mask.get_at((mx, my)):
                    grid[row][col] = 1
        return grid

    def _pad_grid(self) -> None:
        """Multi-source BFS from every wall; block cells within ``padding`` cells."""
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
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
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

    # ------------------------------------------------------------------ #
    # Coordinate helpers                                                 #
    # ------------------------------------------------------------------ #

    def _world_to_cell(self, wx: float, wy: float) -> tuple[int, int]:
        """Convert world-centred coords to (row, col) on the grid."""
        mx = wx + self.map_width / 2
        my = wy + self.map_height / 2
        col = int(mx // self.cell_size)
        row = int(my // self.cell_size)
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        return row, col

    def _cell_to_world(self, row: int, col: int) -> tuple[float, float]:
        """Convert a (row, col) cell centre back to world-centred coords."""
        mx = (col + 0.5) * self.cell_size
        my = (row + 0.5) * self.cell_size
        return mx - self.map_width / 2, my - self.map_height / 2

    def _is_free(self, row: int, col: int) -> bool:
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return False
        return self._grid[row][col] == 0

    def _nearest_free(self, row: int, col: int, max_radius: int = 30) -> tuple[int, int] | None:
        """If (row, col) is blocked (e.g. car clipping through padding), BFS to a free cell."""
        if self._is_free(row, col):
            return row, col
        seen: set[tuple[int, int]] = {(row, col)}
        queue: deque[tuple[int, int, int]] = deque([(row, col, 0)])
        neighbours = (
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        )
        while queue:
            r, c, d = queue.popleft()
            if d >= max_radius:
                continue
            for dr, dc in neighbours:
                nr, nc = r + dr, c + dc
                if (nr, nc) in seen:
                    continue
                seen.add((nr, nc))
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    continue
                if self._grid[nr][nc] == 0:
                    return nr, nc
                queue.append((nr, nc, d + 1))
        return None

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def find_path(
        self,
        start_world: tuple[float, float],
        goal_world: tuple[float, float],
    ) -> list[tuple[float, float]]:
        """Return a list of world-space waypoints from start to goal, or [] on failure."""
        start_cell = self._world_to_cell(*start_world)
        goal_cell = self._world_to_cell(*goal_world)
        start_free = self._nearest_free(*start_cell)
        goal_free = self._nearest_free(*goal_cell)
        if start_free is None or goal_free is None:
            return []
        cells = self._astar(start_free, goal_free)
        if not cells:
            return []
        return [self._cell_to_world(r, c) for r, c in cells]

    # ------------------------------------------------------------------ #
    # A*                                                                 #
    # ------------------------------------------------------------------ #

    def _astar(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """Standard A* with 8-directional movement and Euclidean heuristic."""
        neighbours = (
            (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
            (-1, -1, 1.41421356), (-1, 1, 1.41421356),
            (1, -1, 1.41421356), (1, 1, 1.41421356),
        )

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
            for dr, dc, cost in neighbours:
                nr, nc = current[0] + dr, current[1] + dc
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    continue
                if self._grid[nr][nc] == 1:
                    continue
                tentative = cur_g + cost
                neighbour = (nr, nc)
                if tentative < g_score.get(neighbour, float("inf")):
                    came_from[neighbour] = current
                    g_score[neighbour] = tentative
                    f = tentative + heuristic(neighbour, goal)
                    counter += 1
                    heapq.heappush(open_heap, (f, counter, neighbour))
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
