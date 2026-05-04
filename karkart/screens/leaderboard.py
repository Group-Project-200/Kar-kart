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

        self.selected_button = 0

        self.background = self._load_background()

        self.buttons = []

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
        self.counter = 0
        self.play_again_rect = pygame.Rect(323, 676, 309, 33)
        self.main_menu_rect = pygame.Rect(648, 676, 309, 33)
        self.next_race = pygame.Rect(323, 676, 309, 33)

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

    def _get_game_screen(self):
        return self.manager.screens.get("game")

    def _build_current_race_rows(self) -> list[dict]:
        game = self._get_game_screen()
        if game is None or not hasattr(game, "player_state"):
            return []

        rows = []

        player_time = None

        if getattr(game, "_race_finished", False) and GAME_LEADERBOARD.results:
            latest_result = GAME_LEADERBOARD.results[-1]
            player_time = latest_result.total_time

        elif hasattr(game, "_lap_times") and game._lap_times:
            player_time = sum(game._lap_times)

        elif hasattr(game, "_race_start_time") and game._race_start_time > 0.0:
            player_time = time.perf_counter() - game._race_start_time

        player_state = game.player_state

        if player_time is not None:
            player_score = self._format_time(player_time)
        else:
            player_score = "FINISHED"

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
            if state.current_lap > 1:
                score_text = "FINISHED"
            else:
                if total_checkpoints > 0:
                    score_text = f"L{state.current_lap} CP {state.list_counter}/{total_checkpoints}"
                else:
                    score_text = f"L{state.current_lap} CP {state.list_counter}"

            rows.append(
                {
                    "name": ai_cars[i].name,
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

    def _draw_slot_highlight(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int, int],
    ) -> None:
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill(color)
        surface.blit(overlay, rect.topleft)

    def _draw_row(self, surface: pygame.Surface, row: dict, row_index: int) -> None:
        boxes = self.row_boxes[row_index]

        if row_index == 0:
            self._draw_slot_highlight(surface, boxes["rank"], (255, 220, 100, 55))
            self._draw_slot_highlight(surface, boxes["name"], (255, 220, 100, 40))
            self._draw_slot_highlight(surface, boxes["score"], (255, 220, 100, 40))
        elif row["is_player"]:
            self._draw_slot_highlight(surface, boxes["rank"], (120, 180, 255, 55))
            self._draw_slot_highlight(surface, boxes["name"], (120, 180, 255, 35))
            self._draw_slot_highlight(surface, boxes["score"], (120, 180, 255, 35))

        rank_text = self.rank_font.render(str(row_index + 1), False, (40, 28, 18))

        name_text_value = self._fit_text(
            row["name"], self.name_font, boxes["name"].width - 18
        )
        name_text = self.name_font.render(name_text_value, False, (40, 28, 18))

        score_text_value = self._fit_text(
            row["score"], self.score_font, boxes["score"].width - 16
        )
        score_text = self.score_font.render(score_text_value, False, (40, 28, 18))

        rank_rect = rank_text.get_rect(center=boxes["rank"].center)
        name_rect = name_text.get_rect(
            midleft=(boxes["name"].x + 12, boxes["name"].centery)
        )
        score_rect = score_text.get_rect(center=boxes["score"].center)

        surface.blit(rank_text, rank_rect)
        surface.blit(name_text, name_rect)
        surface.blit(score_text, score_rect)

    def _draw_button(
        self, surface: pygame.Surface, rect: pygame.Rect, text: str, selected: bool
    ) -> None:
        mouse_over = rect.collidepoint(pygame.mouse.get_pos())

        if selected:
            fill = (255, 220, 100, 110)
        elif mouse_over:
            fill = (255, 235, 170, 80)
        else:
            fill = (255, 255, 255, 0)

        if fill[3] > 0:
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            overlay.fill(fill)
            surface.blit(overlay, rect.topleft)

        label = self.button_font.render(text, False, (40, 28, 18))
        label_rect = label.get_rect(center=rect.center)
        surface.blit(label, label_rect)

    def _go_to_screen(self, target: str) -> None:
        self.manager.change_screen(target)

    def handle_event(self, event) -> None:
        is_championships = self.manager.app_data.modes[self.manager.app_data.current_mode]["loop"]
        if is_championships:
            if self.counter >= 2:  # this leaderboard is after race 3
                self.buttons = [("PLAY AGAIN", "race_selector"), ("MAIN MENU", "start")]
            else:
                self.buttons = [("NEXT RACE", "map"), ("MAIN MENU", "start")]
        else:
            self.buttons = [("PLAY AGAIN", "race_selector"), ("MAIN MENU", "start")]

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_button = (self.selected_button - 1) % len(self.buttons)

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_button = (self.selected_button + 1) % len(self.buttons)

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                name, target = self.buttons[self.selected_button]
                if name == "NEXT RACE":
                    self._next_check()
                elif name == "PLAY AGAIN":
                    self.restart_championship()
                self._go_to_screen(target)

            elif event.key == pygame.K_ESCAPE:
                self._go_to_screen("start")

        elif event.type == pygame.MOUSEMOTION:
            left_rect = self.next_race if is_championships else self.play_again_rect
            if left_rect.collidepoint(event.pos):
                self.selected_button = 0
            elif self.main_menu_rect.collidepoint(event.pos):
                self.selected_button = 1

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if is_championships and self.next_race.collidepoint(event.pos):
                self.selected_button = 0
                self._next_check()
                self._go_to_screen("map")

            elif not is_championships and self.play_again_rect.collidepoint(event.pos):
                self.selected_button = 0
                self.restart_championship()
                self._go_to_screen("race_selector")

            elif self.main_menu_rect.collidepoint(event.pos):
                self.selected_button = 1
                self._go_to_screen("start")

    def _next_check(self) -> None:
        self.counter += 1
        if self.counter >= 3:
            self.counter = 0
            self.manager.app_data.modes[self.manager.app_data.current_mode]["loop"] = False

    def restart_championship(self):
        x=1
        counter = 0
        for player in self.manager.app_data.championship_results.values():
            player[0] = 0
            player[1] = x+counter
            counter += 1

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))

        rows = self._get_rows_to_draw()

        for i, row in enumerate(rows[:5]):
            self._draw_row(surface, row, i)

        if self.manager.app_data.modes[self.manager.app_data.current_mode]["loop"]:
            self._draw_button(
                surface, self.next_race, "NEXT RACE", self.selected_button == 0
            )

            if self.counter >= 3:
                self.counter = 0
                self.manager.app_data.modes[self.manager.app_data.current_mode]["loop"]= False




        else:
            self._draw_button(
            surface, self.play_again_rect, "PLAY AGAIN", self.selected_button == 0
            )

        self._draw_button(
            surface, self.main_menu_rect, "MAIN MENU", self.selected_button == 1
        )

        pygame.display.set_caption("Kar Kart - Leaderboard")

    def get_label(self):
        return self.label