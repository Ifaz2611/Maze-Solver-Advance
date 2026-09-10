"""Procedural maze generation for stress testing."""

from __future__ import annotations

import random
from pathlib import Path

from .models.maze import Maze
from .models.role import Role
from .models.square import Square
from .models.terrain import TerrainType


def generate_maze(
    width: int,
    height: int,
    wall_prob: float = 0.22,
    weighted: bool = False,
    seed: int | None = None,
) -> Maze:
    """Generate random maze with guaranteed path via carving.

    Args:
        width, height: dimensions (odd recommended for perfect maze feel)
        wall_prob: random wall density
        weighted: if True, sprinkle dirt/mud/water terrains
        seed: RNG seed
    """
    if seed is not None:
        random.seed(seed)

    # Start with open grid
    grid: list[list[str]] = [[" " for _ in range(width)] for _ in range(height)]

    # border walls
    for r in range(height):
        grid[r][0] = "#"
        grid[r][width - 1] = "#"
    for c in range(width):
        grid[0][c] = "#"
        grid[height - 1][c] = "#"

    # random interior walls (avoid blocking start/goal neighborhood)
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if (r, c) in ((1, 1), (1, 2), (2, 1), (height - 2, width - 2), (height - 2, width - 3), (height - 3, width - 2)):
                continue
            if random.random() < wall_prob:
                grid[r][c] = "#"

    # add weighted terrain
    if weighted:
        for r in range(1, height - 1):
            for c in range(1, width - 1):
                if grid[r][c] == "#":
                    continue
                roll = random.random()
                if roll < 0.08:
                    grid[r][c] = "w"  # water 10
                elif roll < 0.15:
                    grid[r][c] = "m"  # mud 5
                elif roll < 0.30:
                    grid[r][c] = "."  # dirt 2

    # place start / goal
    grid[1][1] = "S"
    grid[height - 2][width - 2] = "G"

    # Ensure path exists via BFS check; if blocked, carve a corridor
    text = "\n".join("".join(row) for row in grid)
    maze = Maze.from_text(text)
    # quick BFS to test connectivity; if no path, retry with less walls
    from .graphs.algorithms.bfs import BFS
    algo = BFS()
    path, _ = algo.solve(maze.start, maze.goal, maze=maze)
    if path is None:
        # carve simple L-shaped corridor as fallback
        for c in range(1, width - 1):
            if grid[1][c] == "#":
                grid[1][c] = " "
        for r in range(1, height - 1):
            if grid[r][width - 2] == "#":
                grid[r][width - 2] = " "
        text = "\n".join("".join(row) for row in grid)
        maze = Maze.from_text(text)

    return maze


def save_generated(maze: Maze, path: str | Path) -> None:
    from .persistence.serializer import save_maze
    save_maze(maze, path)
