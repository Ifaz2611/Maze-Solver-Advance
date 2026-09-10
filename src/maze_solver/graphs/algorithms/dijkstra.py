"""Dijkstra's algorithm for weighted graphs."""

from __future__ import annotations

import heapq
import itertools

from ...analytics.metrics import SearchMetrics
from ...models.maze import Maze
from ...models.square import Square
from .base import PathfindingAlgorithm


class Dijkstra(PathfindingAlgorithm):
    @property
    def name(self) -> str:
        return "Dijkstra"

    def solve(self, start, goal, *, maze=None, graph=None):
        metrics = SearchMetrics(algorithm_name=self.name)
        metrics.start_timer()

        if maze is None and graph is None:
            raise ValueError("Dijkstra requires maze or graph")

        # Build neighbor+weight lookup
        if maze is not None:
            def get_neighbors(sq: Square):
                return tuple((nb, float(nb.cost)) for nb in maze.neighbors(sq))
        else:
            def get_neighbors(sq: Square):
                return tuple((e.target, float(e.weight)) for e in graph.neighbors(sq))

        dist: dict[Square, float] = {start: 0.0}
        prev: dict[Square, Square | None] = {start: None}
        visited: set[Square] = set()
        counter = itertools.count()
        heap: list[tuple[float, int, Square]] = [(0.0, next(counter), start)]
        metrics.record_frontier(len(heap))

        while heap:
            d, _, current = heapq.heappop(heap)
            if current in visited:
                continue
            visited.add(current)
            metrics.record_expansion(current)

            if current == goal:
                break

            # stale entry
            if d > dist.get(current, float("inf")):
                continue

            for neighbor, weight in get_neighbors(current):
                nd = d + weight
                if nd < dist.get(neighbor, float("inf")):
                    dist[neighbor] = nd
                    prev[neighbor] = current
                    heapq.heappush(heap, (nd, next(counter), neighbor))
            metrics.record_frontier(len(heap))

        metrics.stop_timer()

        if goal not in prev:
            metrics.finalize(None)
            return None, metrics

        # reconstruct
        path: list[Square] = []
        cur: Square | None = goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        cost = dist[goal]
        metrics.finalize(path, cost=cost)
        return path, metrics
