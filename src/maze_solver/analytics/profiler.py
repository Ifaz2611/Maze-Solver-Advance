"""Profiler for benchmarking algorithms."""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass

from ..graphs.algorithms.base import PathfindingAlgorithm
from ..models.maze import Maze
from ..models.square import Square
from .metrics import SearchMetrics


@dataclass
class BenchmarkResult:
    algorithm_name: str
    path: list[Square] | None
    metrics: SearchMetrics
    peak_memory_kb: float = 0.0


def run_benchmark(
    algorithm: PathfindingAlgorithm,
    maze: Maze,
    *,
    track_memory: bool = False,
) -> BenchmarkResult:
    """Run single algorithm on maze and collect metrics."""
    if track_memory:
        tracemalloc.start()
    metrics: SearchMetrics
    path, metrics = algorithm.solve(maze.start, maze.goal, maze=maze)
    peak = 0.0
    if track_memory:
        _, peak_bytes = tracemalloc.get_traced_memory()
        peak = peak_bytes / 1024
        tracemalloc.stop()
    return BenchmarkResult(algorithm_name=algorithm.name, path=path, metrics=metrics, peak_memory_kb=peak)


def run_benchmark_suite(
    algorithms: list[PathfindingAlgorithm],
    maze: Maze,
    *,
    track_memory: bool = False,
) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []
    for algo in algorithms:
        results.append(run_benchmark(algo, maze, track_memory=track_memory))
    return results


def format_table(results: list[BenchmarkResult]) -> str:
    """ASCII table comparing results."""
    headers = ["Algorithm", "Time(ms)", "Expanded", "Frontier", "Steps", "Cost", "Mem(KB)"]
    rows = []
    for r in results:
        m = r.metrics
        rows.append(
            [
                r.algorithm_name,
                f"{m.execution_time_ms:.2f}",
                str(m.nodes_expanded),
                str(m.max_frontier_size),
                str(m.path_length),
                f"{m.path_cost:.1f}" if m.path_cost != float("inf") else "inf",
                f"{r.peak_memory_kb:.1f}",
            ]
        )
    # compute widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    def fmt_row(cells):
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    lines = [sep, fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))
    lines.append(sep)
    # winner highlight
    if results:
        best_time = min(results, key=lambda r: r.metrics.execution_time_ms)
        best_exp = min(results, key=lambda r: r.metrics.nodes_expanded)
        lines.append(f"Fastest: {best_time.algorithm_name} | Fewest expansions: {best_exp.algorithm_name}")
    return "\n".join(lines)
