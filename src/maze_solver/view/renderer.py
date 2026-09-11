from ..models.maze import Maze
from ..models.solution import Solution
from .decomposer import path_positions
from .primitives import character


def render(maze: Maze, solution: Solution | None = None, *, show_weights: bool = False) -> str:
    positions = path_positions(solution.path) if solution else frozenset()

    def cell(square):
        if square.position in positions and square.role not in ("S", "G"):
            return character(square.role, True)
        return character(square.role, False)

    return "\n".join(
        "".join(cell(square) for square in row)
        for row in maze.rows
    )
