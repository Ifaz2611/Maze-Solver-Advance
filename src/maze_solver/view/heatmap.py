"""Heatmap visualization of visit frequency."""

from __future__ import annotations

from collections import Counter

from ..models.maze import Maze
from ..models.square import Square


_GRADIENT = " .:;+#@"  # ascii-safe for Windows cp1252

def render_heatmap(maze: Maze, visited: list[Square] | set[Square]) -> str:
    """Render maze where each visited cell shaded by visit count."""
    counts: Counter[tuple[int,int]] = Counter(s.position for s in visited)
    if not counts:
        max_c = 1
    else:
        max_c = max(counts.values())

    def shade(sq: Square) -> str:
        from ..models.role import Role
        if sq.role == Role.WALL:
            return "#"
        if sq.role == Role.START:
            return "S"
        if sq.role == Role.GOAL:
            return "G"
        c = counts.get(sq.position, 0)
        if c == 0:
            return " "
        idx = min(len(_GRADIENT)-1, max(1, round(c / max_c * (len(_GRADIENT)-1))))
        return _GRADIENT[idx]

    lines = []
    for row in maze.rows:
        lines.append("".join(shade(sq) for sq in row))
    return "\n".join(lines)


def render_combined_heatmap(mazes_results: dict[str, list[Square]], maze: Maze) -> str:
    union: list[Square] = []
    for v in mazes_results.values():
        union.extend(v)
    return render_heatmap(maze, union)
