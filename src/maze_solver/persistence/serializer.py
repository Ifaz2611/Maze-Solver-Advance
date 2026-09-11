from pathlib import Path

from ..models.maze import Maze
from .file_format import ALLOWED


def load_maze(path: str | Path) -> Maze:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    # Allow old weighted chars (., m, w...) and normalize to space for loading
    compat = {"#", " ", "S", "G", ".", "m", "M", "w", "W", "g", "d"}
    if any(char not in compat and char not in "\r\n" for char in text):
        raise ValueError(f"Unsupported character in maze file: {source}")
    # Normalize old terrain chars to open space before parsing
    for ch in (".", "m", "M", "w", "W", "g", "d"):
        text = text.replace(ch, " ")
    return Maze.from_text(text)


def save_maze(maze: Maze, path: str | Path) -> None:
    def _char(square):
        return square.role.value
    output = "\n".join("".join(_char(square) for square in row) for row in maze.rows)
    Path(path).write_text(output + "\n", encoding="utf-8")
