# constants.py - contains all the constants used throughout the videogame

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


class ScreenDimensions:

    # contains constants in screen dimensions

    WIDTH = 800
    HEIGHT = 600

    CENTER_X = WIDTH/2
    CENTER_Y = HEIGHT/2