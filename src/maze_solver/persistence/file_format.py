"""Rules for the plain-text .maze format."""

WALL = "#"
START = "S"
GOAL = "G"
# Extended weighted terrains: '.' dirt(2), 'm' mud(5), 'w' water(10), 'g' grass(1)
ALLOWED = frozenset({"#", " ", "S", "G", ".", "m", "M", "w", "W", "g", "d"})
ALLOWED_WEIGHTED = ALLOWED
