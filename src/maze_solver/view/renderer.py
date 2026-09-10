from ..models.maze import Maze
from ..models.solution import Solution
from ..models.terrain import TerrainType
from .decomposer import path_positions
from .primitives import character


def render(maze: Maze, solution: Solution | None = None, *, show_weights: bool = False) -> str:
    positions = path_positions(solution.path) if solution else frozenset()

    def cell(square):
        if square.position in positions and square.role not in ("S", "G"):
            # on path: show '.' regardless of terrain unless weight view
            if show_weights and square.terrain != TerrainType.GRASS:
                return square.terrain.char if square.terrain.char.strip() else "."
            return character(square.role, True)
        if show_weights and square.walkable and square.role not in ("S", "G"):
            # show terrain glyph
            ch = square.terrain.char
            # grass is space - keep space for readability; other terrains visible
            return ch
        return character(square.role, False)

    return "\n".join(
        "".join(cell(square) for square in row)
        for row in maze.rows
    )
