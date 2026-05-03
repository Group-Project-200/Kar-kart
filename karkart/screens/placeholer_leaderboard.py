import pygame
class Placeholder:
    def __init__(self, manager, label):
        self.manager = manager
        self.label = label

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

    def get_label(self):
        return self.label