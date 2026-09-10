"""Bidirectional BFS - searches from both start and goal simultaneously."""

from __future__ import annotations

from collections import deque

from ...analytics.metrics import SearchMetrics
from ...models.square import Square
from .base import PathfindingAlgorithm


class BidirectionalBFS(PathfindingAlgorithm):
    @property
    def name(self) -> str:
        return "Bi-BFS"

    def solve(self, start, goal, *, maze=None, graph=None):
        metrics = SearchMetrics(algorithm_name=self.name)
        metrics.start_timer()

        if maze is None and graph is None:
            raise ValueError("Bi-BFS requires maze or graph")

        if start == goal:
            metrics.stop_timer()
            metrics.finalize([start], cost=0)
            return [start], metrics

        def neighbors(sq: Square):
            if maze is not None:
                return maze.neighbors(sq)
            return tuple(e.target for e in graph.neighbors(sq))

        q_start: deque[Square] = deque([start])
        q_goal: deque[Square] = deque([goal])
        prev_start: dict[Square, Square | None] = {start: None}
        prev_goal: dict[Square, Square | None] = {goal: None}
        visited_start: set[Square] = {start}
        visited_goal: set[Square] = {goal}
        meeting: Square | None = None

        metrics.record_frontier(2)

        while q_start and q_goal:
            # Expand from start side
            for _ in range(len(q_start)):
                cur = q_start.popleft()
                metrics.record_expansion(cur)
                for nb in neighbors(cur):
                    if nb not in visited_start:
                        visited_start.add(nb)
                        prev_start[nb] = cur
                        q_start.append(nb)
                        if nb in visited_goal:
                            meeting = nb
                            break
                if meeting:
                    break
            if meeting:
                break

            # Expand from goal side
            for _ in range(len(q_goal)):
                cur = q_goal.popleft()
                metrics.record_expansion(cur)
                for nb in neighbors(cur):
                    if nb not in visited_goal:
                        visited_goal.add(nb)
                        prev_goal[nb] = cur
                        q_goal.append(nb)
                        if nb in visited_start:
                            meeting = nb
                            break
                if meeting:
                    break
            if meeting:
                break

            metrics.record_frontier(len(q_start) + len(q_goal))

        metrics.stop_timer()

        if meeting is None:
            metrics.finalize(None)
            return None, metrics

        # Reconstruct path start -> meeting -> goal
        path_start: list[Square] = []
        cur: Square | None = meeting
        while cur is not None:
            path_start.append(cur)
            cur = prev_start[cur]
        path_start.reverse()

        path_goal: list[Square] = []
        cur = prev_goal[meeting]
        while cur is not None:
            path_goal.append(cur)
            cur = prev_goal[cur]

        path = path_start + path_goal

        if maze is not None:
            cost = sum(float(sq.cost) for sq in path[1:])
        else:
            cost = float(len(path) - 1)
        metrics.finalize(path, cost=cost)
        return path, metrics
