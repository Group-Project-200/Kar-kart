import pygame

class CollisionResults:
    collided : bool = False
    collision_type : str = None


class CollisionDetector:
    def __init__(self, map_masks: list, car_mask):
        self.car_masks = car_mask
        self.layers = {"borders" : map_masks[0]}
        self.collision_checking = CollisionResults()
        self.current_car_mask = None

    def offset_calc(self, car_map_positions):
        offset =  (
        car_map_positions[0] - self.current_car_mask.get_size()[0] // 2,
        car_map_positions[1] - self.current_car_mask.get_size()[1] // 2
    )
        return offset

    def check(self, direction, car_map_pos):
        self.collision_checking.collided = False
        self.current_car_mask = self.car_masks[direction]
        offset = self.offset_calc(car_map_pos)
        for name, mask in self.layers.items():
            if mask.overlap(self.current_car_mask, offset):
                self.collision_checking.collided = True
                self.collision_checking.collision_type = name



        return self.collision_checking.collided



                #def check collision()
    #this function check if two masks collide or not and if yes it makes collided true

