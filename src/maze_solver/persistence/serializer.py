from pathlib import Path

from ..models.maze import Maze
from .file_format import ALLOWED


def load_maze(path: str | Path) -> Maze:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if any(char not in ALLOWED and char not in "\r\n" for char in text):
        raise ValueError(f"Unsupported character in maze file: {source} - char {char!r} not in {sorted(ALLOWED)}")
    return Maze.from_text(text)


def save_maze(maze: Maze, path: str | Path) -> None:
    def _char(square):
        if square.role in (square.role.START, square.role.GOAL, square.role.WALL):
            return square.role.value
        # preserve terrain
        return square.terrain.char
    output = "\n".join("".join(_char(square) for square in row) for row in maze.rows)
    Path(path).write_text(output + "\n", encoding="utf-8")
