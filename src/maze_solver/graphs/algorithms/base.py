"""Strategy pattern base for pathfinding."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ...analytics.metrics import SearchMetrics
from ...models.maze import Maze
from ...models.square import Square


class PathfindingAlgorithm(ABC):
    """Abstract strategy - all solvers must implement solve()."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def solve(
        self,
        start: Square,
        goal: Square,
        *,
        maze: Maze | None = None,
        graph=None,
    ) -> tuple[Optional[list[Square]], SearchMetrics]:
        """Return (path or None, metrics). Maze/graph optional for neighbor lookup."""
        ...
