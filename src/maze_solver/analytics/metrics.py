"""Search metrics for pathfinding comparison."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..models.square import Square


@dataclass
class SearchMetrics:
    algorithm_name: str
    nodes_expanded: int = 0
    nodes_in_frontier: int = 0
    max_frontier_size: int = 0
    path_length: int = 0
    path_cost: float = 0.0
    execution_time_ms: float = 0.0
    branching_factor: float = 0.0
    visited: set[Square] = field(default_factory=set, repr=False)
    frontier_history: list[int] = field(default_factory=list, repr=False)
    explored_order: list[Square] = field(default_factory=list, repr=False)

    _start_time: float = field(default=0.0, repr=False, compare=False)

    def start_timer(self) -> None:
        self._start_time = time.perf_counter()

    def stop_timer(self) -> None:
        self.execution_time_ms = (time.perf_counter() - self._start_time) * 1000

    def record_expansion(self, square: Square) -> None:
        self.nodes_expanded += 1
        self.visited.add(square)
        self.explored_order.append(square)

    def record_frontier(self, size: int) -> None:
        self.nodes_in_frontier = size
        self.max_frontier_size = max(self.max_frontier_size, size)
        self.frontier_history.append(size)

    def finalize(self, path: list[Square] | tuple[Square, ...] | None, cost: float | None = None) -> None:
        if path:
            self.path_length = max(0, len(path) - 1)
            if cost is not None:
                self.path_cost = cost
            # branching approx = expanded / path_length
            if self.path_length > 0:
                self.branching_factor = self.nodes_expanded / self.path_length
        else:
            self.path_length = 0
            self.path_cost = float("inf")

    def as_dict(self) -> dict:
        return {
            "algorithm": self.algorithm_name,
            "nodes_expanded": self.nodes_expanded,
            "max_frontier": self.max_frontier_size,
            "path_length": self.path_length,
            "path_cost": self.path_cost,
            "time_ms": round(self.execution_time_ms, 3),
            "branching": round(self.branching_factor, 2),
        }

    def __str__(self) -> str:
        return (
            f"[{self.algorithm_name}] Time: {self.execution_time_ms:.2f}ms | "
            f"Expanded: {self.nodes_expanded} | Frontier max: {self.max_frontier_size} | "
            f"Steps: {self.path_length} | Cost: {self.path_cost:.1f}"
        )
