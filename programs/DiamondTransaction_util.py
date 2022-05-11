from enum import Enum


class DiamondColor(Enum):
    RED = 0
    BLUE = 1
    YELLOW = 2


Price = int
Catalogue = dict[DiamondColor, Price]
