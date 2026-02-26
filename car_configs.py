from physics_engine import CarHandling


class BaseCarConfig:
    # Baseline physics profile used by cars that don't override values.
    PHYSICS = CarHandling()


class Car01Config(BaseCarConfig):
    pass


class Car02Config(BaseCarConfig):
    pass


class Car03Config(BaseCarConfig):
    # Example grip-focused variant:
    # lower slip caps + lower slip blending + less base slide => more planted handling.
    PHYSICS = CarHandling(
        max_slip=0.80,
        speed_slip_weight=0.10,
        turn_slip_weight=0.08,
        default_slide_factor=0.2,
        throttle_acceleration=0.065,
        coast_deceleration=0.006,
        brake_deceleration=0.18,
        reverse_acceleration=0.06,
        max_speed=2.8,
    )


# Map sprite folder names to car physics profiles.
CAR_HANDLING_BY_CAR_NAME = {
    "car_01": Car01Config.PHYSICS,
    "car_02": Car02Config.PHYSICS,
    "car_03": Car03Config.PHYSICS,
}


DEFAULT_CAR_HANDLING = BaseCarConfig.PHYSICS
