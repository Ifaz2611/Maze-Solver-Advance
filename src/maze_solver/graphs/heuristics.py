"""Heuristic functions for A*."""

from __future__ import annotations

import math
from typing import Callable

from ..models.square import Square

Heuristic = Callable[[Square, Square], float]


def manhattan_distance(current: Square, goal: Square) -> float:
    """L1 - optimal for 4-way movement with uniform cost."""
    return abs(current.row - goal.row) + abs(current.column - goal.column)


def euclidean_distance(current: Square, goal: Square) -> float:
    """L2 - optimal for 8-way / continuous movement."""
    return math.hypot(current.row - goal.row, current.column - goal.column)


def chebyshev_distance(current: Square, goal: Square) -> float:
    """L-infinity - diagonal cost == orthogonal (king moves)."""
    return max(abs(current.row - goal.row), abs(current.column - goal.column))


def octile_distance(current: Square, goal: Square) -> float:
    """Octile - 8-way with diagonal cost sqrt(2)."""
    dx = abs(current.row - goal.row)
    dy = abs(current.column - goal.column)
    # D=1, D2=sqrt2
    return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)


def zero_heuristic(current: Square, goal: Square) -> float:
    """Degenerates A* into Dijkstra."""
    return 0.0


HEURISTICS: dict[str, Heuristic] = {
    "manhattan": manhattan_distance,
    "euclidean": euclidean_distance,
    "chebyshev": chebyshev_distance,
    "octile": octile_distance,
    "zero": zero_heuristic,
}


def get_heuristic(name: str) -> Heuristic:
    key = name.lower().strip()
    if key not in HEURISTICS:
        raise ValueError(f"Unknown heuristic {name!r}. Available: {', '.join(HEURISTICS)}")
    return HEURISTICS[key]
