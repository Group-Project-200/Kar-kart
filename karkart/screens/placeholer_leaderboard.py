import pygame
class Placeholder:
    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return


        if event.key == pygame.K_RETURN:
            self.manager.change_screen("start")



    def update(self):
        return


    def draw(self, surface: pygame.Surface):
        surface.fill((50, 100, 200))

        return