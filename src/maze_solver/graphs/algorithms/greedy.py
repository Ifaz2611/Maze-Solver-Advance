"""Greedy Best-First Search - expands node closest to goal via heuristic."""

from __future__ import annotations

import heapq
import itertools

from ...analytics.metrics import SearchMetrics
from ...graphs.heuristics import Heuristic, manhattan_distance
from ...models.square import Square
from .base import PathfindingAlgorithm


class GreedyBFS(PathfindingAlgorithm):
    """Greedy Best-First Search: f(n) = h(n), ignores path cost."""

    def __init__(self, heuristic: Heuristic | str | None = None):
        if heuristic is None:
            self.heuristic: Heuristic = manhattan_distance
            self._heu_name = "manhattan"
        elif isinstance(heuristic, str):
            from ...graphs.heuristics import get_heuristic
            self.heuristic = get_heuristic(heuristic)
            self._heu_name = heuristic.lower()
        else:
            self.heuristic = heuristic
            self._heu_name = getattr(heuristic, "__name__", "custom")

    @property
    def name(self) -> str:
        return f"Greedy({self._heu_name})"

    def solve(self, start, goal, *, maze=None, graph=None):
        metrics = SearchMetrics(algorithm_name=self.name)
        metrics.start_timer()

        if maze is None and graph is None:
            raise ValueError("Greedy requires maze or graph")

        def get_neighbors(sq: Square):
            if maze is not None:
                return tuple((nb, float(nb.cost)) for nb in maze.neighbors(sq))
            return tuple((e.target, float(e.weight)) for e in graph.neighbors(sq))

        open_set: list[tuple[float, int, Square]] = []
        counter = itertools.count()
        heapq.heappush(open_set, (self.heuristic(start, goal), next(counter), start))
        prev: dict[Square, Square | None] = {start: None}
        visited: set[Square] = set()
        cost_so_far: dict[Square, float] = {start: 0}
        metrics.record_frontier(len(open_set))

        while open_set:
            _, _, current = heapq.heappop(open_set)
            if current in visited:
                continue
            visited.add(current)
            metrics.record_expansion(current)

            if current == goal:
                break

            for neighbor, weight in get_neighbors(current):
                if neighbor in visited:
                    continue
                if neighbor not in prev:
                    prev[neighbor] = current
                    cost_so_far[neighbor] = cost_so_far[current] + weight
                    priority = self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (priority, next(counter), neighbor))
            metrics.record_frontier(len(open_set))

        metrics.stop_timer()

        if goal not in prev:
            metrics.finalize(None)
            return None, metrics

        path: list[Square] = []
        cur: Square | None = goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        cost = cost_so_far.get(goal, sum(float(s.cost) for s in path[1:]))
        metrics.finalize(path, cost=cost)
        return path, metrics
