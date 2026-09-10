"""Breadth-First Search (unweighted shortest path)."""

from __future__ import annotations

from collections import deque

from ...analytics.metrics import SearchMetrics
from ...models.maze import Maze
from ...models.square import Square
from .base import PathfindingAlgorithm


class BFS(PathfindingAlgorithm):
    @property
    def name(self) -> str:
        return "BFS"

    def solve(self, start, goal, *, maze=None, graph=None):
        metrics = SearchMetrics(algorithm_name=self.name)
        metrics.start_timer()

        if maze is None and graph is None:
            raise ValueError("BFS requires maze or graph")

        # neighbor function
        def neighbors(sq: Square):
            if maze is not None:
                return maze.neighbors(sq)
            return tuple(e.target for e in graph.neighbors(sq))

        queue = deque([start])
        previous: dict[Square, Square | None] = {start: None}
        visited_order: list[Square] = []

        metrics.record_frontier(len(queue))

        while queue:
            current = queue.popleft()
            metrics.record_expansion(current)
            visited_order.append(current)

            if current == goal:
                break

            for nb in neighbors(current):
                if nb not in previous:
                    previous[nb] = current
                    queue.append(nb)
            metrics.record_frontier(len(queue))

        metrics.stop_timer()

        if goal not in previous:
            metrics.finalize(None)
            return None, metrics

        # reconstruct
        path: list[Square] = []
        cur: Square | None = goal
        while cur is not None:
            path.append(cur)
            cur = previous[cur]
        path.reverse()

        # cost = sum of terrain costs (for weighted comparison) - BFS ignores weights during search but we report true cost
        if maze is not None:
            cost = sum(float(sq.cost) for sq in path[1:])
        elif graph is not None:
            # sum edge weights
            cost = 0.0
            for a, b in zip(path, path[1:]):
                try:
                    cost += float(graph.weight(a, b))
                except Exception:
                    cost += float(b.cost)
        else:
            cost = float(len(path) - 1)
        metrics.finalize(path, cost=cost)
        metrics.explored_order = visited_order
        return path, metrics
