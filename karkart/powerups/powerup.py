from karkart.helpers import forward_vector


class SpeedBoost:
    name = "Boost"
    duration_frames = 180

    def __init__(self):
        self.remaining = self.duration_frames
        self.active = False

    def activate(self, game) -> None:
        self.active = True

        # Give an instant push so the player feels it straight away.
        player = game.current_car.physics
        player.speed = max(player.speed, 3.0)

    def tick(self, game) -> bool:
        if not self.active:
            return True

        player = game.current_car.physics

        # Push the car forward every frame while the boost is active.
        forward_x, forward_y = forward_vector(player.rotation)

        player.speed = min(player.speed + 0.08, 7.0)
        player.velocity_x += forward_x * 0.12
        player.velocity_y += forward_y * 0.12

        self.remaining -= 1

        if self.remaining <= 0:
            self.deactivate(game)
            return True

        return False

    def deactivate(self, game) -> None:
        self.active = False


class Shield:
    name = "Shield"
    duration_frames = 240

    def __init__(self):
        self.remaining = self.duration_frames
        self.active = False

    def activate(self, game) -> None:
        self.active = True
        game.player_invincible = True

    def tick(self, game) -> bool:
        if not self.active:
            return True

        self.remaining -= 1

        if self.remaining <= 0:
            self.deactivate(game)
            return True

        return False

    def deactivate(self, game) -> None:
        self.active = False
        game.player_invincible = False


class EMPJammer:
    name = "Jammer"
    duration_frames = 150

    def __init__(self):
        self.remaining = self.duration_frames
        self.active = False

    def activate(self, game) -> None:
        self.active = True

        if not game.ai_active:
            return

        # Big instant slowdown so it is obvious.
        for ai_car in game.ai_cars:
            ai_car.physics.speed *= 0.35
            ai_car.physics.velocity_x *= 0.35
            ai_car.physics.velocity_y *= 0.35

    def tick(self, game) -> bool:
        if not self.active:
            return True

        # Keep dragging the AI cars down while the EMP is active.
        if game.ai_active:
            for ai_car in game.ai_cars:
                ai_car.physics.speed *= 0.96
                ai_car.physics.velocity_x *= 0.96
                ai_car.physics.velocity_y *= 0.96

        self.remaining -= 1

        if self.remaining <= 0:
            self.deactivate(game)
            return True

        return False

    def deactivate(self, game) -> None:
        self.active = False