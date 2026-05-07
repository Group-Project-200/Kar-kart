""" end.py - symbolic game over screen"""

from karkart.screens.screen_object import Screen

class EndScreen(Screen):
    
    def __init__(self, manager, label):
        super().__init__(manager, label)