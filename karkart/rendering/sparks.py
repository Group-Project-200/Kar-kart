\
\
\
\
\
\
   

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from karkart.helpers import forward_vector


                                                                         
                                                 
_REAR_OFFSET: float = 4.0                                                       
_WHEEL_SIDE: float = 4.5                                                        
_MAX_SPARKS: int = 2000                                   


@dataclass(slots=True)
class Spark:
    x: float
    y: float
    vx: float                                                  
    vy: float
    life: int                           
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
                                                                        

    _BLUE: tuple[int, int, int] = (60, 200, 255)                  
    _ORANGE: tuple[int, int, int] = (255, 140, 20)                     

    _MAX_LIFE: int = 8                                                        
    _EMIT_COUNT: int = 1                                   
    _DRIFT_SPEED: float = 0.015                                                  
    _MAX_RADIUS: float = 3.5                                                  

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
                                                    
        color = self._spark_color(charge_frames)
        fx, fy = forward_vector(rotation)
        px, py = -fy, fx                                           

        rear_x = car_x - fx * _REAR_OFFSET
        rear_y = car_y - fy * _REAR_OFFSET

        for sign in (-1, 1):                                         
            wx = rear_x + px * _WHEEL_SIDE * sign
            wy = rear_y + py * _WHEEL_SIDE * sign

            for _ in range(self._EMIT_COUNT):
                                                                                             
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

            t = s.life / s.max_life                                        
            alpha = int(200 * t)
            radius = max(1, int(self._MAX_RADIUS * t))

            surf = pygame.Surface((radius * 2 + 1, radius * 2 + 1), pygame.SRCALPHA)
            pygame.draw.circle(surf, (s.r, s.g, s.b, alpha), (radius, radius), radius)
            display.blit(surf, (screen_x - radius, screen_y - radius))
