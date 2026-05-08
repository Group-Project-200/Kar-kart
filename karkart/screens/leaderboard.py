import math
import time
from dataclasses import dataclass, field

import pygame

from karkart.constants import ScreenPositions as sp
from karkart.paths import PICTURES_DIR, PIXEL_FONT
from karkart.screens.screen_object import Screen


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


def _load_font(size: int) -> pygame.font.Font:
    try:
        return pygame.font.Font(str(PIXEL_FONT), size)
    except (FileNotFoundError, OSError, pygame.error):
        return pygame.font.SysFont("arial", size, bold=True)


def _load_background() -> pygame.Surface:
    image_path = PICTURES_DIR / "leaderboard.png"
    image = pygame.image.load(str(image_path)).convert()
    return pygame.transform.smoothscale(image, (sp.WIDTH, sp.HEIGHT))


def _format_time(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    minutes = total_ms // 60000
    secs = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{minutes:02d}:{secs:02d}.{ms:03d}"


def _fit_text(text: str, font: pygame.font.Font, max_width: int) -> str:
    if font.size(text)[0] <= max_width:
        return text

    trimmed = text
    while trimmed and font.size(trimmed + "...")[0] > max_width:
        trimmed = trimmed[:-1]

    if not trimmed:
        return ""

    return trimmed + "..."

def _draw_alpha_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int, int],
    border_radius: int = 0,
) -> None:
    temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(temp, color, temp.get_rect(), border_radius=border_radius)
    surface.blit(temp, rect.topleft)

def _draw_text_shadow(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    pos: tuple[int, int],
    color: tuple[int, int, int],
    *,
    center: bool = False,
    midleft: bool = False,
) -> None:
    shadow = font.render(text, False, (95, 65, 35))
    main = font.render(text, False, color)

    if center:
        rect = main.get_rect(center=pos)
    elif midleft:
        rect = main.get_rect(midleft=pos)
    else:
        rect = main.get_rect(topleft=pos)

    surface.blit(shadow, rect.move(1, 1))
    surface.blit(main, rect)

def _rank_label(row_index: int) -> str:
    if row_index == 0:
        return "1st"
    if row_index == 1:
        return "2nd"
    if row_index == 2:
        return "3rd"
    return str(row_index + 1)

def _draw_small_star( surface: pygame.Surface, x: int, y: int) -> None:
    points = [
        (x, y - 7),
        (x + 3, y - 2),
        (x + 8, y - 2),
        (x + 4, y + 2),
        (x + 6, y + 8),
        (x, y + 4),
        (x - 6, y + 8),
        (x - 4, y + 2),
        (x - 8, y - 2),
        (x - 3, y - 2),
    ]
    pygame.draw.polygon(surface, (90, 55, 15), points)
    pygame.draw.polygon(surface, (255, 225, 90), points[:-1])


def _build_history_rows() -> list[dict]:
    rows = []

    for result in GAME_LEADERBOARD.results[:5]:
        rows.append(
            {
                "name": result.player_name,
                "score": _format_time(result.total_time),
                "metric": (0, 0),
                "is_player": False,
            }
        )

    return rows


class LeaderboardScreen(Screen):
    def __init__(self, manager, label) -> None:
        super().__init__(manager, label)

        if not pygame.font.get_init():
            pygame.font.init()

        self.rank_font = _load_font(14)
        self.name_font = _load_font(15)
        self.score_font = _load_font(13)
        self.button_font =_load_font(15)

        self.selected_button = 0
        self.counter = 0

        self.background = _load_background()

        self.play_again_rect = pygame.Rect(323, 676, 309, 33)
        self.main_menu_rect = pygame.Rect(648, 676, 309, 33)
        self.next_race_rect = pygame.Rect(323, 676, 309, 33)
        self.results_rect = pygame.Rect(323, 676, 309, 33)
        self.buttons = None
        self.championship_over =False

        self.row_boxes = [
            {
                "rank": pygame.Rect(318, 357, 52, 36),
                "name": pygame.Rect(381, 357, 392, 36),
                "score": pygame.Rect(785, 357, 182, 36),
            },
            {
                "rank": pygame.Rect(318, 410, 52, 36),
                "name": pygame.Rect(381, 410, 392, 36),
                "score": pygame.Rect(785, 410, 182, 36),
            },
            {
                "rank": pygame.Rect(318, 463, 52, 36),
                "name": pygame.Rect(381, 463, 392, 36),
                "score": pygame.Rect(785, 463, 182, 36),
            },
            {
                "rank": pygame.Rect(318, 516, 52, 36),
                "name": pygame.Rect(381, 516, 392, 36),
                "score": pygame.Rect(785, 516, 182, 36),
            },
            {
                "rank": pygame.Rect(318, 569, 52, 36),
                "name": pygame.Rect(381, 569, 392, 36),
                "score": pygame.Rect(785, 569, 182, 36),
            },
        ]



    def _is_championship(self) -> bool:
        mode = self.manager.app_data.current_mode
        return self.manager.app_data.modes[mode]["loop"]

    def _get_buttons(self) -> list[tuple[str, str, pygame.Rect]]:
        if self._is_championship() and self.counter < 2:
            return [
                ("NEXT RACE", "game", self.next_race_rect),
                ("MAIN MENU", "start", self.main_menu_rect),
            ]

        if self._is_championship() and self.counter >= 2:
            return [
                ("SHOW RESULTS", "winner_screen", self.results_rect),
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
        player_score = _format_time(player_time) if player_time is not None else "FINISHED"

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



    def _get_rows_to_draw(self) -> list[dict]:
        current_race_rows = self._build_current_race_rows()
        if current_race_rows:
            return current_race_rows
        return _build_history_rows()


    def _draw_row_highlight(self, surface: pygame.Surface, row_index: int, row: dict) -> None:
        boxes = self.row_boxes[row_index]

        full_rect = pygame.Rect(
            boxes["rank"].left + 4,
            boxes["rank"].top + 4,
            boxes["score"].right - boxes["rank"].left - 8,
            boxes["rank"].height - 8,
        )

        if row_index == 0:
            ticks = pygame.time.get_ticks()
            shine = int(45 + 25 * math.sin(ticks * 0.006))
            _draw_alpha_rect(surface, full_rect, (255, 225, 95, 55 + shine), 5)
            _draw_small_star(surface, boxes["rank"].left - 12, boxes["rank"].centery)
        elif row["is_player"]:
            _draw_alpha_rect(surface, full_rect, (100, 180, 255, 35), 5)

    def _draw_row(self, surface: pygame.Surface, row: dict, row_index: int) -> None:
        boxes = self.row_boxes[row_index]

        self._draw_row_highlight(surface, row_index, row)

        rank_text = _rank_label(row_index)
        name_text = _fit_text(
            row["name"],
            self.name_font,
            boxes["name"].width - 28,
        )
        score_text = _fit_text(
            row["score"],
            self.score_font,
            boxes["score"].width - 20,
        )

        text_color = (35, 24, 12)

        _draw_text_shadow(
            surface,
            self.rank_font,
            rank_text,
            (boxes["rank"].centerx, boxes["rank"].centery + 1),
            text_color,
            center=True,
        )
        _draw_text_shadow(
            surface,
            self.name_font,
            name_text,
            (boxes["name"].x + 20, boxes["name"].centery + 1),
            text_color,
            midleft=True,
        )
        _draw_text_shadow(
            surface,
            self.score_font,
            score_text,
            (boxes["score"].centerx, boxes["score"].centery + 1),
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

        ticks = pygame.time.get_ticks()
        pulse = int(25 + 20 * math.sin(ticks * 0.008))

        draw_rect = rect.copy()
        if active:
            draw_rect.y -= 2

        if active:
            glow_rect = draw_rect.inflate(-6, -3)
            _draw_alpha_rect(surface, glow_rect, (255, 225, 85, 90 + pulse), 8)
            text_color = (35, 25, 12)
        else:
            text_color = (75, 50, 25)

        label = self.button_font.render(text, False, text_color)
        shadow = self.button_font.render(text, False, (130, 85, 35))

        label_rect = label.get_rect(center=(draw_rect.centerx, draw_rect.centery + 1))
        surface.blit(shadow, label_rect.move(1, 1))
        surface.blit(label, label_rect)

        if active:
            underline = pygame.Rect(label_rect.left, label_rect.bottom + 2, label_rect.width, 3)
            _draw_alpha_rect(surface, underline, (255, 240, 150, 150), 2)

    def _go_to_screen(self, target: str) -> None:
        self.manager.change_screen(target)

    def _next_check(self) -> None:
        self.counter += 1

        if self.counter >= 3:
            self.championship_over = True
            self.counter = 0
            self.manager.app_data.modes[self.manager.app_data.current_mode]["loop"] = False


    def handle_event(self, event) -> None:
        self.buttons = self._get_buttons()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_button = (self.selected_button - 1) % len(self.buttons)

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_button = (self.selected_button + 1) % len(self.buttons)

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                name, target, _ = self.buttons[self.selected_button]

                if name == "NEXT RACE":
                    from karkart.screens.gameplay import GamePlay
                    self._next_check()
                    self.manager.app_data.set_current_map(self.manager.app_data.randomised_maps_order[self.counter])
                    if "game" in self.manager.screens:
                        del self.manager.screens["game"]
                    new_game = GamePlay(self.manager, "game")
                    self.manager.add_screen(GamePlay(self.manager, "game"))
                    self.manager.change_screen("game")
                elif name == "PLAY AGAIN" or "MAIN MENU":
                    self.counter = 0

                self._go_to_screen(target)

            elif event.key == pygame.K_ESCAPE:
                self._go_to_screen("start")

        elif event.type == pygame.MOUSEMOTION:
            for i, (_, _, rect) in enumerate(self.buttons):
                if rect.collidepoint(event.pos):
                    self.selected_button = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (name, target, rect) in enumerate(self.buttons):
                if rect.collidepoint(event.pos):
                    self.selected_button = i

                    if name == "NEXT RACE":
                        from karkart.screens.gameplay import GamePlay
                        self._next_check()
                        self.manager.app_data.set_current_map(self.manager.app_data.randomised_maps_order[self.counter])
                        if "game" in self.manager.screens:
                            del self.manager.screens["game"]
                        new_game = GamePlay(self.manager, "game")
                        self.manager.add_screen(GamePlay(self.manager, "game"))
                        self.manager.change_screen("game")
                    elif name == "PLAY AGAIN" or "MAIN MENU":
                        self.counter = 0

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