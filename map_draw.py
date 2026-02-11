import pygame

def draw_map(display, map_surface, car_x, car_y, zoom=2.0, center=(50, 50)):
    if not map_surface:
        return
    map_w, map_h = map_surface.get_width(), map_surface.get_height()
    zoomed_w, zoomed_h = int(map_w * zoom), int(map_h * zoom)
    zoomed_map = pygame.transform.smoothscale(map_surface, (zoomed_w, zoomed_h))
    map_cx, map_cy = zoomed_w // 2, zoomed_h // 2
    car_map_x = map_cx + int(car_x * zoom)
    car_map_y = map_cy + int(car_y * zoom)
    map_blit_x = car_map_x - center[0]
    map_blit_y = car_map_y - center[1]
    display.blit(zoomed_map, (0, 0), area=pygame.Rect(map_blit_x, map_blit_y, 100, 100))
