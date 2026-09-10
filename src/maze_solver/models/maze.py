from dataclasses import dataclass

from .role import Role
from .square import Square
from .terrain import TerrainType


@dataclass(frozen=True)
class Maze:
    """Rectangular maze represented by rows of squares."""

    rows: tuple[tuple[Square, ...], ...]
    start: Square
    goal: Square

    @classmethod
    def from_text(cls, text: str) -> "Maze":
        lines = text.splitlines()
        if not lines or any(not line for line in lines):
            raise ValueError("Maze must contain non-empty rows.")
        width = len(lines[0])
        if any(len(line) != width for line in lines):
            raise ValueError("Maze rows must all have the same width.")

        def _make_square(row: int, column: int, char: str) -> Square:
            # S / G have special roles, terrain = GRASS
            if char in (Role.START.value, Role.GOAL.value, Role.WALL.value):
                return Square(row, column, Role(char), TerrainType.GRASS if char != "#" else TerrainType.WALL)
            # Terrain chars: ' ', '.', 'm', 'w', etc. map to OPEN role + terrain
            if char in (" ", ".", "m", "M", "w", "W", "g", "d"):
                try:
                    terrain = TerrainType.from_char(char)
                except ValueError:
                    terrain = TerrainType.GRASS
                # impassable terrain still rendered as wall? no - keep OPEN
                return Square(row, column, Role.OPEN, terrain)
            # Fallback: try Role, then terrain
            try:
                return Square(row, column, Role(char), TerrainType.GRASS)
            except ValueError:
                terrain = TerrainType.from_char(char)
                return Square(row, column, Role.OPEN, terrain)

        rows = tuple(
            tuple(_make_square(row, column, char) for column, char in enumerate(line))
            for row, line in enumerate(lines)
        )
        starts = [square for line in rows for square in line if square.role == Role.START]
        goals = [square for line in rows for square in line if square.role == Role.GOAL]
        if len(starts) != 1 or len(goals) != 1:
            raise ValueError("Maze must contain exactly one S and one G.")
        return cls(rows, starts[0], goals[0])

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.rows[0])

    def square_at(self, row: int, column: int) -> Square | None:
        if 0 <= row < self.height and 0 <= column < self.width:
            return self.rows[row][column]
        return None

    def neighbors(self, square: Square) -> tuple[Square, ...]:
        candidates = (
            self.square_at(square.row - 1, square.column),
            self.square_at(square.row, square.column + 1),
            self.square_at(square.row + 1, square.column),
            self.square_at(square.row, square.column - 1),
        )
        return tuple(candidate for candidate in candidates if candidate and candidate.walkable)
