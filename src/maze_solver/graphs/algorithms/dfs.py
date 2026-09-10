"""Depth-First Search (stack-based, not optimal but fast)."""

from __future__ import annotations

from ...analytics.metrics import SearchMetrics
from ...models.square import Square
from .base import PathfindingAlgorithm


class DFS(PathfindingAlgorithm):
    """DFS using explicit stack - explores deep paths first."""

    @property
    def name(self) -> str:
        return "DFS"

    def solve(self, start, goal, *, maze=None, graph=None):
        metrics = SearchMetrics(algorithm_name=self.name)
        metrics.start_timer()

        if maze is None and graph is None:
            raise ValueError("DFS requires maze or graph")

        def neighbors(sq: Square):
            if maze is not None:
                return maze.neighbors(sq)
            return tuple(e.target for e in graph.neighbors(sq))

        stack: list[Square] = [start]
        prev: dict[Square, Square | None] = {start: None}
        visited: set[Square] = set()

        metrics.record_frontier(len(stack))

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            metrics.record_expansion(current)

            if current == goal:
                break

            for nb in neighbors(current):
                if nb not in prev and nb not in visited:
                    prev[nb] = current
                    stack.append(nb)
            metrics.record_frontier(len(stack))

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

        if maze is not None:
            cost = sum(float(sq.cost) for sq in path[1:])
        else:
            cost = 0.0
            for a, b in zip(path, path[1:]):
                try:
                    cost += float(graph.weight(a, b))
                except Exception:
                    cost += float(b.cost)
        metrics.finalize(path, cost=cost)
        return path, metrics
