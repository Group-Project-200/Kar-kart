""" end.py - symbolic game over screen"""

class EndScreen:
    
    def __init__(self, manager, label):
        self.manager = manager
        self.label = label

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass

    def get_label(self):
        return self.label