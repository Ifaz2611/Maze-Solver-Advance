"""Legacy solver kept for backward compatibility - delegates to BFS strategy."""

from ..models.maze import Maze
from ..models.solution import Solution
from .algorithms.bfs import BFS


def solve(maze: Maze) -> Solution | None:
    """Find the shortest path from S to G using breadth-first search (legacy API)."""
    algo = BFS()
    path, _ = algo.solve(maze.start, maze.goal, maze=maze)
    if path is None:
        return None
    return Solution(tuple(path))
