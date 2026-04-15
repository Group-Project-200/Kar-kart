# constants.py - contains all the constants used throughout the videogame

import pygame

class Colors:

    # contains all colors
    # use "from UIobjects.constants import Colors" in your files

    # e.g. Colors.RED is mapped to (255, 0, 0)

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    LIGHT_BLUE = (173, 216, 230)
    YELLOW = (255, 255, 0)
    PURPLE = (128, 0, 128)
    PINK = (255, 192, 203)
    ORANGE = (255, 165, 0)
    GRAY = (128, 128, 128)

    LIGHT_GRAY = (192, 192, 192)


class ScreenPositions:

    # contains screen dimensions
    # contains screen positions split into 16x16

    WIDTH = 1280
    HEIGHT = 720

    W = WIDTH
    H = HEIGHT

    AREA = W * H

    XXXLEFT = W/16
    XXLEFT = W/8
    XLEFT = W/16*3
    LEFT = W/4
    CLEFT = W/16*5
    CCLEFT = W/8*3
    CCCLEFT = W/16*7

    CENTER_X = W/2

    CCCRIGHT = W/16*9
    CCRIGHT = W/8*5
    CRIGHT = W/16*11
    RIGHT = W/4*3
    XRIGHT = W/16*13
    XXRIGHT = W/8*7
    XXXRIGHT = W/16*15


    XXXTOP = H/16
    XXTOP = H/8
    XTOP = H/16*3
    TOP = H/4
    CTOP = H/16*5
    CCTOP = H/8*3
    CCCTOP = H/16*7

    CENTER_Y = H/2

    CCCBOTTOM = H/16*9
    CCBOTTOM = H/8*5
    CBOTTOM = H/16*11
    BOTTOM = H/4*3
    XBOTTOM = H/16*13
    XXBOTTOM = H/8*7
    XXXBOTTOM = H/16*15

class Keys:
    UP = pygame.K_w
    DOWN = pygame.K_s
    LEFT = pygame.K_a 
    RIGHT = pygame.K_d