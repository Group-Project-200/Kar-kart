from __future__ import annotations

import threading
import traceback
from queue import Empty, Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from karkart.ai.pathfinder import AStarPathfinder


_SHUTDOWN = object()


class PathfinderWorker:
    def __init__(self, pathfinder: "AStarPathfinder") -> None:
        self._pathfinder = pathfinder
        self._requests: Queue = Queue()
        self._results: Queue = Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="kk-pathfinder",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 1.0) -> None:
        self._stop.set()
        self._requests.put(_SHUTDOWN)
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def request(
        self,
        ai_index: int,
        start: tuple[float, float],
        goal: tuple[float, float],
    ) -> None:
        self._requests.put((ai_index, start, goal))

    def collect(self) -> dict[int, list[tuple[float, float]]]:
        out: dict[int, list[tuple[float, float]]] = {}
        while True:
            try:
                ai_index, path = self._results.get_nowait()
            except Empty:
                break
            out[ai_index] = path
        return out

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                item = self._requests.get(timeout=0.1)
            except Empty:
                continue
            if item is _SHUTDOWN:
                break
            ai_index, start, goal = item
            try:
                path = self._pathfinder.find_path(start, goal)
            except Exception:
                traceback.print_exc()
                path = []
            self._results.put((ai_index, path))
