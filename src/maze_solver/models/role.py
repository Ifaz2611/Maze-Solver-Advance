from enum import Enum


class Role(str, Enum):
    OPEN = " "
    WALL = "#"
    START = "S"
    GOAL = "G"
    PATH = "."
