# race_selection_screen.py - race selection screen
import pygame


class RaceSelector:
    def __init__(self, manager):
        self.manager = manager
        self.screen_width = 1280
        self.screen_height = 720

        self.races = ["Time Trial", "Race Mode", "Championship"]
        self.selected_index = 1

        # Background
        try:
            self.bg = pygame.image.load("Race_Seleciton_bg.png").convert()
            self.bg = pygame.transform.scale(self.bg, (self.screen_width, self.screen_height))
        except:
            self.bg = None

        # Card dimensions
        self.card_width = 280
        self.card_height = 220
        self.card_y = self.screen_height - self.card_height - 100
        total_cards_width = self.card_width * 3 + 40 * 2
        self.card_start_x = (self.screen_width - total_cards_width) // 2

        # Load mode images
        image_files = ["Trial_Mode.png", "race_mode.png", "Championship_mode.png"]
        self.mode_images = []
        for file in image_files:
            try:
                img = pygame.image.load(file).convert_alpha()
                img = pygame.transform.scale(img, (self.card_width, self.card_height))
                self.mode_images.append(img)
            except:
                self.mode_images.append(None)


    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected_index = (self.selected_index - 1) % len(self.races)
            elif event.key == pygame.K_RIGHT:
                self.selected_index = (self.selected_index + 1) % len(self.races)
            elif event.key == pygame.K_RETURN:
                self.manager.change_screen("car")
            elif event.key == pygame.K_ESCAPE:
                self.manager.change_screen("start")


    def update(self):
        pass


    def draw(self, surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((50, 100, 200))

        for i in range(len(self.races)):
            x = self.card_start_x + i * (self.card_width + 40)
            card_rect = pygame.Rect(x, self.card_y, self.card_width, self.card_height)

            if self.mode_images[i]:
                surface.blit(self.mode_images[i], (x, self.card_y))
            else:
                pygame.draw.rect(surface, (220, 200, 160), card_rect, border_radius=8)

            # Visible selection border — white outer glow + black inner
            if i == self.selected_index:
                glow_rect = card_rect.inflate(8, 8)
                pygame.draw.rect(surface, (255, 255, 255), glow_rect, 4, border_radius=10)
                pygame.draw.rect(surface, (0, 0, 0), card_rect, 4, border_radius=8)

        pygame.display.set_caption("Kar Kart - Race Selector")