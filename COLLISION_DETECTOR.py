
class CollisionDetector:
    def __init__(self, map_masks: list, car_mask):
        self.car_masks = car_mask
        self.layers = [map_masks[0]]
        self.current_car_mask = None

    def offset_calc(self, car_map_positions):
        offset = (
            car_map_positions[0] - self.current_car_mask.get_size()[0] // 2,
            car_map_positions[1] - self.current_car_mask.get_size()[1] // 2,
        )
        return offset

    def check(self, direction, car_map_pos):
        self.current_car_mask = self.car_masks[direction]
        offset = self.offset_calc(car_map_pos)

        for mask in self.layers:
            if mask.overlap(self.current_car_mask, offset):
                return True

        return False