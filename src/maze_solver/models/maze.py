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
    allow_diagonal: bool = False

    @classmethod
    def from_text(cls, text: str) -> "Maze":
        lines = text.splitlines()
        if not lines or any(not line for line in lines):
            raise ValueError("Maze must contain non-empty rows.")
        width = len(lines[0])
        if any(len(line) != width for line in lines):
            raise ValueError("Maze rows must all have the same width.")

        def _make_square(row: int, column: int, char: str) -> Square:
            # Back-compat: old weighted chars (., m, w ...) are treated as open space
            if char in (".", "d", "m", "M", "w", "W", "g"):
                char = " "
            if char in (Role.START.value, Role.GOAL.value, Role.WALL.value):
                return Square(row, column, Role(char), TerrainType.GRASS if char != "#" else TerrainType.WALL)
            if char == " ":
                return Square(row, column, Role.OPEN, TerrainType.GRASS)
            try:
                return Square(row, column, Role(char), TerrainType.GRASS)
            except ValueError:
                raise ValueError(f"Unsupported character {char!r} at ({row},{column}). Allowed: '#', ' ', 'S', 'G'")

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

    def neighbors(self, square: Square, allow_diagonal: bool | None = None) -> tuple[Square, ...]:
        use_diag = self.allow_diagonal if allow_diagonal is None else allow_diagonal
        candidates = (
            self.square_at(square.row - 1, square.column),
            self.square_at(square.row, square.column + 1),
            self.square_at(square.row + 1, square.column),
            self.square_at(square.row, square.column - 1),
        )
        orthogonal = tuple(candidate for candidate in candidates if candidate and candidate.walkable)
        if not use_diag:
            return orthogonal
        diagonals = (
            self.square_at(square.row - 1, square.column - 1),
            self.square_at(square.row - 1, square.column + 1),
            self.square_at(square.row + 1, square.column + 1),
            self.square_at(square.row + 1, square.column - 1),
        )
        all_neighbors = orthogonal + tuple(c for c in diagonals if c and c.walkable)
        return all_neighbors

    def to_dict(self) -> dict:
        """Serialize maze to dict for JSON export."""
        return {
            "width": self.width,
            "height": self.height,
            "start": [self.start.row, self.start.column],
            "goal": [self.goal.row, self.goal.column],
            "grid": ["".join(s.role.value for s in row) for row in self.rows],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Maze":
        grid = "\n".join(data["grid"])
        return cls.from_text(grid)
