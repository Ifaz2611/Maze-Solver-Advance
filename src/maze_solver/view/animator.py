"""Step-by-step animation of search frontier."""

from __future__ import annotations

import time

from ..analytics.metrics import SearchMetrics
from ..models.maze import Maze
from ..models.square import Square
from .renderer import render


def animate_search(
    maze: Maze,
    explored_order: list[Square],
    path: list[Square] | None = None,
    delay: float = 0.05,
    show_path: bool = True,
) -> None:
    """Print frames with increasing frontier to terminal."""
    path_set = set(path) if path else set()
    frontier: set[Square] = set()
    for i, sq in enumerate(explored_order):
        frontier.add(sq)
        print("\033[H\033[J", end="")
        print(f"Step {i+1}/{len(explored_order)} - visiting {sq.position}")
        frame = _render_with_frontier(maze, frontier, path_set if show_path and i == len(explored_order)-1 else set())
        print(frame)
        time.sleep(delay)


def _render_with_frontier(maze: Maze, visited: set[Square], path_set: set[Square]) -> str:
    from ..models.role import Role
    from .primitives import character

    def char_for(sq: Square) -> str:
        if sq in path_set and sq.role not in (Role.START, Role.GOAL, Role.WALL):
            return "."
        if sq in visited and sq.role == Role.OPEN:
            return "*"
        return sq.role.value

    lines = []
    for row in maze.rows:
        lines.append("".join(char_for(sq) for sq in row))
    return "\n".join(lines)
