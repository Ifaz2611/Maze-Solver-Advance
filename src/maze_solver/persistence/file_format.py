"""Rules for the plain-text .maze format - unweighted only."""

WALL = "#"
START = "S"
GOAL = "G"
# Only walls, open space, start and goal - no weighted terrain
ALLOWED = frozenset({"#", " ", "S", "G"})
ALLOWED_WEIGHTED = ALLOWED
