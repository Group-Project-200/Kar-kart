import pygame



def _convert_for_display(surface: pygame.Surface) -> pygame.Surface:
    if pygame.display.get_surface() is None:
        return surface
    return surface.convert_alpha()


class Stacker:
    def __init__(self, image_stack: list[pygame.Surface], directions):
        self.images = image_stack #the original images
        self.scaled_img = []  #the scaled images
        self.dirs = directions   # the directions
        self.scale = None
        self.rotated_cache = None

    def scale_update(self, scale):
        self.scale = scale
        self.update()


    def scale_images(self):
        if self.scale == 1.0:
            return [_convert_for_display(img) for img in self. images]

        for img in self.images:
            width = max(1, int(img.get_width() * self.scale))
            height = max(1, int(img.get_height() * self.scale))
            scaled = pygame.transform.scale(img, (width, height))
            self.scaled_img.append(_convert_for_display(scaled))


    def build_rotated_cache(self):
        step_deg = 360 / self.dirs
        self.rotated_cache = [
            [_convert_for_display(pygame.transform.rotate(img, d * step_deg)) for img in self.scaled_img]
            for d in range(self.dirs)
        ]

    def update(self):
        self.scale_images()
        self.build_rotated_cache()



    def render_stack(self, display, dir_idx,  pos, spread: float):
        x, y = pos
        for i, img in enumerate(self.rotated_cache[dir_idx]):
            display.blit(
                img,
                (x - img.get_width() // 2, y - img.get_height() // 2 + i * spread),
            )
