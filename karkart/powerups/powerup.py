class Powerup:
    def __init__(self):
        self.name = None
        self.duration = None
        self.effect = None

    #applies the effect of the powerup
    def apply(self):
        return

    #applies the duration of hte powerup
    def count(self):
        return


class SpeedBoost(Powerup):
    name = "Speed Boost"
    duration = 3.0

    def apply(self, player) -> None:
        player.speed *= 1.5