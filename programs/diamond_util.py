from enum import Enum
class DiamondColour(Enum):
    RED = 0
    BLUE = 1
    YELLOW = 2

Price = int
Catalogue = dict[DiamondColour, Price]
