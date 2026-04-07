import pygame, sys

pygame.init()

SCREEN_W, SCREEN_H = 800, 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()

map_surf = pygame.image.load("base").convert_alpha()
track_surf = pygame.image.load("track borders").convert_alpha()
track_mask = pygame.mask.from_surface(track_surf)



MAP_W, MAP_H = map_surf.get_size()



player_rect = pygame.Rect(100, 200, 30, 30)
normal_speed, slow_speed = 300, 120

player_mask = pygame.mask.Mask((player_rect.w, player_rect.h), fill=True)

px, py = float(player_rect.x), float(player_rect.y)

running = True
while running:
    dt = clock.tick(60) / 1000.0

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    speed = normal_speed

    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * speed * dt
    dy = (keys[pygame.K_DOWN]  - keys[pygame.K_UP])   * speed * dt

    new_px = px + dx
    if 0 <= new_px <= MAP_W - player_rect.w:
        offset = (int(new_px), int(py))
        if track_mask.overlap(player_mask, offset) is None:
            px = new_px

    new_py = py + dy
    if 0 <= new_py <= MAP_H - player_rect.h:
        offset = (int(px), int(new_py))
        if track_mask.overlap(player_mask, offset) is None:
            py = new_py

    player_rect.x = int(px)
    player_rect.y = int(py)

    camera_x = player_rect.centerx - SCREEN_W // 2
    camera_y = player_rect.centery - SCREEN_H // 2
    camera_x = max(0, min(camera_x, MAP_W - SCREEN_W))
    camera_y = max(0, min(camera_y, MAP_H - SCREEN_H))

    screen.fill((30, 30, 30))
    screen.blit(map_surf, (-camera_x, -camera_y))
    pygame.draw.rect(screen, (0, 200, 255), player_rect.move(-camera_x, -camera_y))
    pygame.display.flip()

pygame.quit()
sys.exit()