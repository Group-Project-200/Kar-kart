import pygame
import os
import json


pygame.init()

class Checkpoint:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)


try:
    with open("map_data.json") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"checkpoints": [],
            "start": (),
            "start_box" : ()}




def rect_from_corners(a, b):
    x = min(a[0], b[0])
    y = min(a[1], b[1])
    w = abs(b[0] - a[0])
    h = abs(b[1] - a[1])
    return x, y, w, h

def start_pos(x,y,w,h):
    start_position = (x+(3/4 * w), y + h)
    return start_position

BASE_DIR = os.path.dirname(__file__)
map_image = pygame.image.load(os.path.join(BASE_DIR, "resources", "maps", "map_2", "0.png"))

screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Map Editor")

camera_x, camera_y = 0, 0
dragging = False
last_mouse_x, last_mouse_y = 0, 0

placing = False
place_start = (0, 0)

mode =""

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dragging = True
            last_mouse_x, last_mouse_y = event.pos

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging = False


        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            mode = "checkpoints"

        if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            mode = "start placement"


        if event.type == pygame.MOUSEMOTION and dragging:
            dx = event.pos[0] - last_mouse_x
            dy = event.pos[1] - last_mouse_y
            camera_x -= dx
            camera_y -= dy
            last_mouse_x, last_mouse_y = event.pos


        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mx, my = event.pos
            place_start = (mx + camera_x, my + camera_y)
            placing = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 3 and placing:
            if mode == "checkpoints":
                mx, my = event.pos
                end = (mx + camera_x, my + camera_y)
                x, y, w, h = rect_from_corners(place_start, end)
                if w > 5 and h > 5:
                    data["checkpoints"].append({"x": x, "y": y, "w": w, "h": h})
                placing = False
            if mode == "start placement":
                mx, my = event.pos
                end = (mx + camera_x, my + camera_y)
                x, y, w, h = rect_from_corners(place_start, end)
                if w > 5 and h > 5:
                    data["start_box"] = (x,y,w,h)
                    data["start"] = start_pos(x,y,w,h)
                placing = False

        # Escape to cancel an in-progress placement
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            placing = False


    camera_x = max(0, min(camera_x, max(0, map_image.get_width() - 1280)))
    camera_y = max(0, min(camera_y, max(0, map_image.get_height() - 720)))


    screen.blit(map_image, (-camera_x, -camera_y))


    for cp in data["checkpoints"]:
        pygame.draw.rect(screen, (255, 0, 0),
                         (cp["x"] - camera_x, cp["y"] - camera_y, cp["w"], cp["h"]))

    if "start_box" in data:
        x, y, w, h = data["start_box"]
        pygame.draw.rect(screen, (0, 0, 255), (x - camera_x, y - camera_y, w, h))


    if placing:
        mx, my = pygame.mouse.get_pos()
        end = (mx + camera_x, my + camera_y)
        x, y, w, h = rect_from_corners(place_start, end)
        pygame.draw.rect(screen, (255, 255, 0),
                         (x - camera_x, y - camera_y, w, h), 2)

    pygame.display.flip()


with open("map_data.json", "w") as f:
    json.dump(data, f, indent=2)

pygame.quit()