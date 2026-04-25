"""Drift smoke/spark puffs from both rear wheels.

Particles are emitted at the left and right rear wheels once the hop has
landed.  They float away slowly and fade out quickly so they read as puffs
of smoke rather than flying debris.  Colour transitions blue -> orange in
step with the drift-charge boost tiers.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from karkart.helpers import forward_vector


# Sprite-measured geometry (resources/render/car_*/img_0.png — 12×18 px).
# At current zoom, 1 sprite pixel ≈ 1 world unit.
_REAR_OFFSET: float = 4.0    # World units behind car centre to rear-wheel axis.
_WHEEL_SIDE: float = 4.5     # World units left/right from centre to each wheel.
_MAX_SPARKS: int = 2000      # Safety cap on active puffs.


@dataclass(slots=True)
class Spark:
    x: float
    y: float
    vx: float        # World units per frame (very slow drift).
    vy: float
    life: int        # Remaining frames.
    max_life: int
    r: int
    g: int
    b: int


def _lerp_color(
    a: tuple[int, int, int], b: tuple[int, int, int], t: float,
) -> tuple[int, int, int]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


class SparkManager:
    """Animated smoke-puff emitter for both rear wheels during drift."""

    _BLUE: tuple[int, int, int] = (60, 200, 255)    # Bright cyan.
    _ORANGE: tuple[int, int, int] = (255, 140, 20)  # Saturated orange.

    _MAX_LIFE: int = 8         # Frames before a puff disappears (fast decay).
    _EMIT_COUNT: int = 1       # Puffs per wheel per frame.
    _DRIFT_SPEED: float = 0.015  # Max world-unit speed of each puff (very slow).
    _MAX_RADIUS: float = 3.5   # Pixel radius at birth (at render resolution).

    def __init__(self) -> None:
        self.sparks: list[Spark] = []

    def _spark_color(self, charge_frames: int) -> tuple[int, int, int]:
        if charge_frames >= 70:
            return self._ORANGE
        if charge_frames >= 40:
            return _lerp_color(self._BLUE, self._ORANGE, (charge_frames - 40) / 30.0)
        return self._BLUE

    def emit(
        self,
        car_x: float,
        car_y: float,
        rotation: float,
        charge_frames: int,
    ) -> None:
        """Spawn smoke puffs at both rear wheels."""
        color = self._spark_color(charge_frames)
        fx, fy = forward_vector(rotation)
        px, py = -fy, fx  # Perpendicular (rightward from heading).

        rear_x = car_x - fx * _REAR_OFFSET
        rear_y = car_y - fy * _REAR_OFFSET

        for sign in (-1, 1):  # Left wheel (-1) and right wheel (+1).
            wx = rear_x + px * _WHEEL_SIDE * sign
            wy = rear_y + py * _WHEEL_SIDE * sign

            for _ in range(self._EMIT_COUNT):
                # Slow random drift: mostly perpendicular to heading, small random component.
                angle = random.uniform(0, math.tau)
                speed = random.uniform(0.005, self._DRIFT_SPEED)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed

                self.sparks.append(Spark(
                    x=wx, y=wy, vx=vx, vy=vy,
                    life=self._MAX_LIFE, max_life=self._MAX_LIFE,
                    r=color[0], g=color[1], b=color[2],
                ))

        if len(self.sparks) > _MAX_SPARKS:
            del self.sparks[: len(self.sparks) - _MAX_SPARKS]

    def update(self) -> None:
        """Advance all puffs one frame; discard expired ones."""
        alive: list[Spark] = []
        for s in self.sparks:
            s.x += s.vx
            s.y += s.vy
            s.life -= 1
            if s.life > 0:
                alive.append(s)
        self.sparks = alive

    def draw(
        self,
        display: pygame.Surface,
        car_x: float,
        car_y: float,
        camera_angle: float,
        map_zoom: float,
        center: tuple[int, int],
    ) -> None:
        """Render this manager's live puffs (single-thread fallback)."""
        self.draw_from_list(
            display, self.sparks,
            car_x, car_y, camera_angle, map_zoom, center,
        )

    def draw_from_list(
        self,
        display: pygame.Surface,
        sparks: list,
        car_x: float,
        car_y: float,
        camera_angle: float,
        map_zoom: float,
        center: tuple[int, int],
    ) -> None:
        """Render an externally-supplied list of puff records.

        Accepts any object with the same fields as :class:`Spark`
        (``x``, ``y``, ``life``, ``max_life``, ``r``, ``g``, ``b``) so the
        renderer can draw a frozen :class:`SparkSnapshot` list without
        racing the physics thread that owns ``self.sparks``.
        """
        if not sparks:
            return

        cam_rad = math.radians(camera_angle)
        cos_a = math.cos(cam_rad)
        sin_a = math.sin(cam_rad)
        cx, cy = center
        surf_w, surf_h = display.get_size()

        for s in sparks:
            dx = (s.x - car_x) * map_zoom
            dy = (s.y - car_y) * map_zoom
            sx = dx * cos_a - dy * sin_a
            sy = dx * sin_a + dy * cos_a
            screen_x = int(cx + sx)
            screen_y = int(cy + sy)

            if screen_x < -8 or screen_x >= surf_w + 8 or screen_y < -8 or screen_y >= surf_h + 8:
                continue

            t = s.life / s.max_life          # 1.0 at birth → 0.0 at death.
            alpha = int(200 * t)
            radius = max(1, int(self._MAX_RADIUS * t))

            surf = pygame.Surface((radius * 2 + 1, radius * 2 + 1), pygame.SRCALPHA)
            pygame.draw.circle(surf, (s.r, s.g, s.b, alpha), (radius, radius), radius)
            display.blit(surf, (screen_x - radius, screen_y - radius))
