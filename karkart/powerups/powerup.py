class SpeedBoost:
    name = "Speed Boost"
    duration_frames = 360  # 3 seconds at 60 FPS
    _multiplier = 3

    def __init__(self):
        self.remaining = self.duration_frames
        self.active = False

    def activate(self, player) -> None:
        self.active = True
        player.speed *= self._multiplier  # apply ONCE

    def tick(self, player) -> bool:
        if not self.active:
            return True
        self.remaining -= 1
        if self.remaining <= 0:
            self.deactivate(player)
            return True
        return False

    def deactivate(self, player) -> None:
        self.active = False
        player.speed /= self._multiplier  # remove ONCE