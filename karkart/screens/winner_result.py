import math

import pygame
from karkart.constants import ScreenPositions as sp
from karkart.paths import PICTURES_DIR, PIXEL_FONT
from karkart.screens.screen_object import Screen

"""this file contains the screen for the winner of the championship mode. It is gets the data from the accumulation of the 
races, and places the final score on the screen"""
def _load_font( size: int) -> pygame.font.Font:
    try:
        return pygame.font.Font(str(PIXEL_FONT), size)
    except (FileNotFoundError, OSError, pygame.error):
        return pygame.font.SysFont("arial", size, bold=True)


def _load_background() -> pygame.Surface:
    image_path = PICTURES_DIR / "final_result_championship.png"
    image = pygame.image.load(str(image_path)).convert()
    return pygame.transform.smoothscale(image, (sp.WIDTH, sp.HEIGHT))

def _draw_alpha_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int, int],
    border_radius: int = 0,
) -> None:
    temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(temp, color, temp.get_rect(), border_radius=border_radius)
    surface.blit(temp, rect.topleft)


class WinnerScreen(Screen):
    def __init__(self, manager, label):
        super().__init__(manager, label)

        if not pygame.font.get_init():
            pygame.font.init()

        self.text_font = _load_font(40)
        self.score_font = _load_font(80)
        self.button_font = _load_font(15)

        self.selected_button = 0
        self.background = _load_background()
        self.main_menu_rect = pygame.Rect(263, 634, 750, 33)

        self.final_score = None

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.restart_championship()
                self.manager.change_screen("start")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.main_menu_rect.collidepoint(event.pos):
                self.restart_championship()
                self.manager.change_screen("start")

    def get_score(self):
        self.final_score = str(self.manager.app_data.championship_results["Player 1"][0])

    def restart_championship(self) -> None:
        start_pos = 1
        for i, player in enumerate(self.manager.app_data.championship_results.values()):
            player[0] = 0
            player[1] = start_pos + i

    def update(self) -> None:
        pass

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



    def draw(self, surface: pygame.Surface) -> None:
        pygame.display.set_caption("Kar Kart - Leaderboard")
        self.get_score()

        surface.blit(self.background, (0, 0))
        text_surface = self.text_font.render("Your Final Score is", False, (35, 24, 12))
        surface.blit(text_surface, (263, sp.HEIGHT // 2 - 50 ))
        text_surface = self.score_font.render(self.final_score, False, (35, 24, 12))
        surface.blit(text_surface, (sp.WIDTH // 2 - 27, sp.HEIGHT // 2 + 50))

        self._draw_button(surface, self.main_menu_rect, "MAIN MENU", True)



    def get_label(self):
        return self.label
