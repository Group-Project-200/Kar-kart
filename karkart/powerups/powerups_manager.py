import math
import random
from collections import deque

import pygame

from karkart.paths import PICTURES_DIR
from karkart.powerups.powerup import EMPJammer, Shield, SpeedBoost


class PowerupsManager:
    def __init__(self, game):
        self.powerup_classes = [
            SpeedBoost,
            Shield,
            EMPJammer,
        ]

        self.current = None
        self.game = game
        self.active = True

    def choose_random_powerup(self):
        powerup_class = random.choice(self.powerup_classes)
        self.current = powerup_class()
        return self.current

    def get_current_name(self) -> str:
        if self.current is None:
            return "None"

        if hasattr(self.current, "remaining"):
            seconds_left = max(0, self.current.remaining // 60)
            return f"{self.current.name} {seconds_left}s"

        return self.current.name


class PowerupRendering:
    _frames_cache = None

    def __init__(self, dimensions, powerups_manager: PowerupsManager):
        self.x, self.y, self.w, self.h = dimensions
        self.active = True
        self.area = pygame.Rect(self.x, self.y, self.w, self.h)
        self.manager = powerups_manager

        if PowerupRendering._frames_cache is None:
            PowerupRendering._frames_cache = self._load_frames()

        self.frames = PowerupRendering._frames_cache

    def _is_background_pixel(self, color: pygame.Color) -> bool:
        r, g, b, a = color.r, color.g, color.b, color.a

        if a < 20:
            return True

        is_light = r > 185 and g > 185 and b > 185
        is_grayish = max(r, g, b) - min(r, g, b) < 45

        return is_light and is_grayish

    def _remove_fake_background(self, image: pygame.Surface) -> pygame.Surface:
        image = image.convert_alpha()
        width, height = image.get_size()

        visited = set()
        queue = deque()

        for x in range(width):
            queue.append((x, 0))
            queue.append((x, height - 1))

        for y in range(height):
            queue.append((0, y))
            queue.append((width - 1, y))

        while queue:
            x, y = queue.popleft()

            if (x, y) in visited:
                continue

            if x < 0 or x >= width or y < 0 or y >= height:
                continue

            visited.add((x, y))

            color = image.get_at((x, y))

            if not self._is_background_pixel(color):
                continue

            image.set_at((x, y), (255, 255, 255, 0))

            queue.append((x + 1, y))
            queue.append((x - 1, y))
            queue.append((x, y + 1))
            queue.append((x, y - 1))

        crop_rect = image.get_bounding_rect(min_alpha=10)

        if crop_rect.width <= 0 or crop_rect.height <= 0:
            return image

        cropped = pygame.Surface((crop_rect.width, crop_rect.height), pygame.SRCALPHA)
        cropped.blit(image, (0, 0), crop_rect)

        return cropped

    def _load_frames(self) -> list[pygame.Surface]:
        frame_names = [
            "box_1.png",
            "box_2.png",
            "box_3.png",
            "box_4.png",
        ]

        frames = []

        for frame_name in frame_names:
            image_path = PICTURES_DIR / frame_name

            try:
                image = pygame.image.load(str(image_path)).convert_alpha()
                image = self._remove_fake_background(image)
                frames.append(image)
            except (FileNotFoundError, pygame.error):
                print(f"Could not load powerup sprite: {image_path}")

        return frames

    def _draw_backup_box(
        self,
        surface: pygame.Surface,
        sx: int,
        sy: int,
        box_size: int,
    ) -> None:
        rect = pygame.Rect(0, 0, box_size, box_size)
        rect.center = (sx, sy)

        pygame.draw.rect(surface, (55, 35, 20), rect.move(2, 2), border_radius=3)
        pygame.draw.rect(surface, (255, 205, 45), rect, border_radius=3)
        pygame.draw.rect(surface, (120, 70, 20), rect, 2, border_radius=3)

        inner = rect.inflate(-8, -8)
        if inner.width > 2 and inner.height > 2:
            pygame.draw.rect(surface, (255, 235, 120), inner, border_radius=2)

        if not pygame.font.get_init():
            pygame.font.init()

        font = pygame.font.SysFont("arial", max(12, box_size // 2), bold=True)
        question = font.render("?", False, (80, 45, 15))
        question_rect = question.get_rect(center=rect.center)
        surface.blit(question, question_rect)

    def draw(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        car_x: float,
        car_y: float,
        zoom: float,
    ):
        if not self.active:
            return

        ticks = pygame.time.get_ticks()

        world_center_x = self.x + self.w / 2
        world_center_y = self.y + self.h / 2

        bob = math.sin(ticks * 0.01 + self.x * 0.05) * 3

        sx = center[0] + int((world_center_x - car_x) * zoom)
        sy = center[1] + int((world_center_y - car_y) * zoom + bob)

        box_size = 42

        shadow = pygame.Surface((box_size, max(6, box_size // 4)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        shadow_rect = shadow.get_rect(center=(sx, sy + box_size // 2))
        surface.blit(shadow, shadow_rect)

        if not self.frames:
            self._draw_backup_box(surface, sx, sy, box_size)
            return

        frame_index = (ticks // 120) % len(self.frames)
        frame = self.frames[frame_index]

        scaled_frame = pygame.transform.scale(frame, (box_size, box_size))
        frame_rect = scaled_frame.get_rect(center=(sx, sy))

        surface.blit(scaled_frame, frame_rect)

    def check(self, car_x: float, car_y: float):
        if not self.active:
            return False

        if self.manager.current is not None:
            return False

        collision = self.area.collidepoint(car_x, car_y)

        if collision:
            self.active = False
            return True

        return False