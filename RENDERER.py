from MAP import Map
from STACKER import Stacker
from COLLISION_DETECTOR import CollisionDetector
from Helper_functions import _clamp_zoom,clamp_scale,snap_degrees
import pygame


class Renderer:
    def __init__(self, current_map : Map, stacker: Stacker, screen):
        self.screen = screen
        self.render_size = self.build_pixel_surface_size(0.35)
        render_scale = self.render_size[1] / self.screen.get_size()[1]
        #the current zoom are manually inputted but i will change it later to be adjustable
        draw_map_zoom = _clamp_zoom(3.0) * render_scale
        draw_car_scale = _clamp_zoom(3.0) * render_scale
        self.center = (self.render_size[0] // 2, self.render_size[1] // 2)
        self.frame_surface = pygame.Surface(self.render_size).convert()
        self.map = current_map
        self.stacker = stacker
        self.needs_present_scale = self.render_size != self.screen.get_size()
        self.map.zoom_fixing(draw_map_zoom,self.render_size)
        self.stacker.scale_update(draw_car_scale)
        self.collision_detector =CollisionDetector(self.map.masks, self.stacker.mask_cache)

    def build_pixel_surface_size(self, pixelation_scale: float)-> tuple[int, int]:
        scale = clamp_scale(pixelation_scale)
        screen_width, screen_height = self.screen.get_size()
        pixel_width = max(1, int(screen_width * scale))
        pixel_height = max(1, int(screen_height * scale))
        return pixel_width, pixel_height


    def present_frame(self):
        if not self.needs_present_scale:
            self.screen.blit(self.frame_surface, (0, 0))
            return

        pygame.transform.scale(self.frame_surface, self.screen.get_size(), self.screen)


    def render_frame(self,stack_spread) -> None:
        # Frame composition order: map in camera space, then car in screen center.
        frame_surface = self.frame_surface
        frame_surface.fill((0, 0, 0))

        self.map.draw_map_camera(display=frame_surface, center = self.center, render_size = self.render_size)
        car_relative_rotation = self.map.camera.car.physics.rotation - self.map.camera.angle


        #has to stay in game loop
        dir_idx = snap_degrees(car_relative_rotation, dirs=self.stacker.dirs)
        offset = (self.map.car_map_x, self.map.car_map_y)
        self.map.camera.car.collision_results= self.collision_detector.check(dir_idx, offset)


        self.stacker.render_stack(self.frame_surface, dir_idx, self.center, stack_spread)
        self.present_frame()
