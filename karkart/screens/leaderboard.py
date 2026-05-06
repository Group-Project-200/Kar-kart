from __future__ import annotations

import time
from dataclasses import dataclass, field

import pygame

from karkart.constants import ScreenPositions as sp
from karkart.paths import PICTURES_DIR, PIXEL_FONT


@dataclass
class RaceResult:
    player_name: str
    car_name: str
    map_name: str
    total_time: float
    lap_times: list
    total_laps: int


@dataclass
class Leaderboard:
    results: list[RaceResult] = field(default_factory=list)

    def add(self, result: RaceResult) -> None:
        self.results.append(result)
        self.results.sort(key=lambda x: x.total_time)


GAME_LEADERBOARD = Leaderboard()


class LeaderboardScreen:
    def __init__(self, manager, label) -> None:
        self.manager = manager
        self.label = label

        if not pygame.font.get_init():
            pygame.font.init()

        self.rank_font = self._load_font(18)
        self.name_font = self._load_font(18)
        self.score_font = self._load_font(16)
        self.button_font = self._load_font(18)
        self.small_font = self._load_font(12)

        self.selected_button = 0
        self.counter = 0

        self.background = self._load_background()

        self.play_again_rect = pygame.Rect(323, 676, 309, 33)
        self.main_menu_rect = pygame.Rect(648, 676, 309, 33)
        self.next_race_rect = pygame.Rect(323, 676, 309, 33)

        self.row_boxes = [
            {
                "rank": pygame.Rect(318, 357, 36, 36),
                "name": pygame.Rect(381, 357, 392, 36),
                "score": pygame.Rect(785, 357, 182, 36),
            },
            {
                "rank": pygame.Rect(318, 410, 36, 36),
                "name": pygame.Rect(381, 410, 392, 36),
                "score": pygame.Rect(785, 410, 182, 36),
            },
            {
                "rank": pygame.Rect(318, 463, 36, 36),
                "name": pygame.Rect(381, 463, 392, 36),
                "score": pygame.Rect(785, 463, 182, 36),
            },
            {
                "rank": pygame.Rect(318, 516, 36, 36),
                "name": pygame.Rect(381, 516, 392, 36),
                "score": pygame.Rect(785, 516, 182, 36),
            },
            {
                "rank": pygame.Rect(318, 569, 36, 36),
                "name": pygame.Rect(381, 569, 392, 36),
                "score": pygame.Rect(785, 569, 182, 36),
            },
        ]

    def _load_font(self, size: int) -> pygame.font.Font:
        try:
            return pygame.font.Font(str(PIXEL_FONT), size)
        except (FileNotFoundError, OSError, pygame.error):
            return pygame.font.SysFont("arial", size, bold=True)

    def _load_background(self) -> pygame.Surface:
        image_path = PICTURES_DIR / "leaderboard.png"
        image = pygame.image.load(str(image_path)).convert()
        return pygame.transform.smoothscale(image, (sp.WIDTH, sp.HEIGHT))

    def _format_time(self, seconds: float) -> str:
        total_ms = int(round(seconds * 1000))
        minutes = total_ms // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{minutes:02d}:{secs:02d}.{ms:03d}"

    def _fit_text(self, text: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text

        trimmed = text
        while trimmed and font.size(trimmed + "...")[0] > max_width:
            trimmed = trimmed[:-1]

        if not trimmed:
            return ""

        return trimmed + "..."

    def _is_championship(self) -> bool:
        mode = self.manager.app_data.current_mode
        return self.manager.app_data.modes[mode]["loop"]

    def _get_buttons(self) -> list[tuple[str, str, pygame.Rect]]:
        if self._is_championship() and self.counter < 2:
            return [
                ("NEXT RACE", "map", self.next_race_rect),
                ("MAIN MENU", "start", self.main_menu_rect),
            ]

        return [
            ("PLAY AGAIN", "race_selector", self.play_again_rect),
            ("MAIN MENU", "start", self.main_menu_rect),
        ]

    def _get_game_screen(self):
        return self.manager.screens.get("game")

    def _build_current_race_rows(self) -> list[dict]:
        game = self._get_game_screen()
        if game is None or not hasattr(game, "player_state"):
            return []

        rows = []

        player_time = None
        if getattr(game, "_race_finished", False) and GAME_LEADERBOARD.results:
            player_time = GAME_LEADERBOARD.results[-1].total_time
        elif hasattr(game, "_lap_times") and game._lap_times:
            player_time = sum(game._lap_times)
        elif hasattr(game, "_race_start_time") and game._race_start_time > 0.0:
            player_time = time.perf_counter() - game._race_start_time
        elif hasattr(game, "world") and game.world.race_start_time > 0.0:
            player_time = time.perf_counter() - game.world.race_start_time

        player_state = game.player_state
        player_score = self._format_time(player_time) if player_time is not None else "FINISHED"

        rows.append(
            {
                "name": "Player 1",
                "score": player_score,
                "metric": (
                    player_state.total_checkpoints,
                    -getattr(player_state, "last_pass_order", 0),
                ),
                "is_player": True,
            }
        )

        total_checkpoints = (
            len(game.current_map.checkpoints_list)
            if hasattr(game, "current_map")
            else 0
        )

        ai_cars = getattr(game, "ai_cars", [])

        for i, state in enumerate(getattr(game, "ai_states", [])):
            if state.current_lap > 3:
                score_text = "FINISHED"
            elif total_checkpoints > 0:
                score_text = f"L{state.current_lap} CP {state.list_counter}/{total_checkpoints}"
            else:
                score_text = f"L{state.current_lap} CP {state.list_counter}"

            if i < len(ai_cars) and hasattr(ai_cars[i], "name"):
                ai_name = ai_cars[i].name
            else:
                ai_name = f"AI {i + 1}"

            rows.append(
                {
                    "name": ai_name,
                    "score": score_text,
                    "metric": (
                        state.total_checkpoints,
                        -getattr(state, "last_pass_order", 0),
                    ),
                    "is_player": False,
                }
            )

        rows.sort(key=lambda row: row["metric"], reverse=True)
        return rows[:5]

    def _build_history_rows(self) -> list[dict]:
        rows = []

        for result in GAME_LEADERBOARD.results[:5]:
            rows.append(
                {
                    "name": result.player_name,
                    "score": self._format_time(result.total_time),
                    "metric": (0, 0),
                    "is_player": False,
                }
            )

        return rows

    def _get_rows_to_draw(self) -> list[dict]:
        current_race_rows = self._build_current_race_rows()
        if current_race_rows:
            return current_race_rows
        return self._build_history_rows()

    def _draw_alpha_rect(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int, int],
        border_radius: int = 0,
    ) -> None:
        temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(temp, color, temp.get_rect(), border_radius=border_radius)
        surface.blit(temp, rect.topleft)

    def _draw_text_shadow(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        pos: tuple[int, int],
        color: tuple[int, int, int],
        *,
        center: bool = False,
        midleft: bool = False,
    ) -> None:
        shadow = font.render(text, False, (0, 0, 0))
        main = font.render(text, False, color)

        if center:
            rect = main.get_rect(center=pos)
        elif midleft:
            rect = main.get_rect(midleft=pos)
        else:
            rect = main.get_rect(topleft=pos)

        surface.blit(shadow, rect.move(2, 2))
        surface.blit(main, rect)

    def _draw_row(self, surface: pygame.Surface, row: dict, row_index: int) -> None:
        boxes = self.row_boxes[row_index]

        full_rect = pygame.Rect(
            boxes["rank"].left - 8,
            boxes["rank"].top - 4,
            boxes["score"].right - boxes["rank"].left + 16,
            boxes["rank"].height + 8,
        )

        if row_index == 0:
            self._draw_alpha_rect(surface, full_rect, (255, 220, 80, 95), 8)
            border_color = (255, 245, 170)
            text_color = (45, 28, 10)
        elif row["is_player"]:
            self._draw_alpha_rect(surface, full_rect, (90, 170, 255, 80), 8)
            border_color = (190, 225, 255)
            text_color = (35, 25, 18)
        else:
            self._draw_alpha_rect(surface, full_rect, (255, 255, 255, 28), 8)
            border_color = (110, 80, 45)
            text_color = (40, 28, 18)

        pygame.draw.rect(surface, border_color, full_rect, 2, border_radius=8)

        if row_index == 0:
            rank = "1st"
        elif row_index == 1:
            rank = "2nd"
        elif row_index == 2:
            rank = "3rd"
        else:
            rank = str(row_index + 1)

        name_text = self._fit_text(row["name"], self.name_font, boxes["name"].width - 18)
        score_text = self._fit_text(row["score"], self.score_font, boxes["score"].width - 16)

        self._draw_text_shadow(
            surface,
            self.rank_font,
            rank,
            boxes["rank"].center,
            text_color,
            center=True,
        )
        self._draw_text_shadow(
            surface,
            self.name_font,
            name_text,
            (boxes["name"].x + 12, boxes["name"].centery),
            text_color,
            midleft=True,
        )
        self._draw_text_shadow(
            surface,
            self.score_font,
            score_text,
            boxes["score"].center,
            text_color,
            center=True,
        )

    def _draw_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        text: str,
        selected: bool,
    ) -> None:
        mouse_over = rect.collidepoint(pygame.mouse.get_pos())
        active = selected or mouse_over

        if active:
            fill = (255, 218, 75, 145)
            border = (255, 255, 220)
            text_color = (45, 28, 10)
            y_offset = -2
        else:
            fill = (35, 22, 12, 80)
            border = (120, 85, 45)
            text_color = (255, 238, 190)
            y_offset = 0

        button_rect = rect.move(0, y_offset)
        shadow_rect = button_rect.move(0, 4)

        self._draw_alpha_rect(surface, shadow_rect, (0, 0, 0, 90), 8)
        self._draw_alpha_rect(surface, button_rect, fill, 8)
        pygame.draw.rect(surface, border, button_rect, 3, border_radius=8)

        if active:
            glow_rect = button_rect.inflate(10, 10)
            self._draw_alpha_rect(surface, glow_rect, (255, 230, 100, 45), 12)

        self._draw_text_shadow(
            surface,
            self.button_font,
            text,
            button_rect.center,
            text_color,
            center=True,
        )

    def _go_to_screen(self, target: str) -> None:
        self.manager.change_screen(target)

    def _next_check(self) -> None:
        self.counter += 1

        if self.counter >= 3:
            self.counter = 0
            self.manager.app_data.modes[self.manager.app_data.current_mode]["loop"] = False

    def restart_championship(self) -> None:
        start_pos = 1

        for i, player in enumerate(self.manager.app_data.championship_results.values()):
            player[0] = 0
            player[1] = start_pos + i

        self.counter = 0

    def handle_event(self, event) -> None:
        buttons = self._get_buttons()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_button = (self.selected_button - 1) % len(buttons)

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_button = (self.selected_button + 1) % len(buttons)

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                name, target, _ = buttons[self.selected_button]

                if name == "NEXT RACE":
                    self._next_check()
                elif name == "PLAY AGAIN":
                    self.restart_championship()

                self._go_to_screen(target)

            elif event.key == pygame.K_ESCAPE:
                self._go_to_screen("start")

        elif event.type == pygame.MOUSEMOTION:
            for i, (_, _, rect) in enumerate(buttons):
                if rect.collidepoint(event.pos):
                    self.selected_button = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (name, target, rect) in enumerate(buttons):
                if rect.collidepoint(event.pos):
                    self.selected_button = i

                    if name == "NEXT RACE":
                        self._next_check()
                    elif name == "PLAY AGAIN":
                        self.restart_championship()

                    self._go_to_screen(target)
                    break

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Kar Kart - Leaderboard")

        surface.blit(self.background, (0, 0))

        rows = self._get_rows_to_draw()
        for i, row in enumerate(rows[:5]):
            self._draw_row(surface, row, i)

        buttons = self._get_buttons()
        self.selected_button %= len(buttons)

        for i, (label, _, rect) in enumerate(buttons):
            self._draw_button(surface, rect, label, self.selected_button == i)

    def get_label(self):
        return self.label