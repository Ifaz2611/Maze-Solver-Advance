"""Upgraded CLI - pathfinding laboratory with benchmarking."""

from __future__ import annotations

import argparse
from pathlib import Path

from .analytics.profiler import format_table, run_benchmark_suite
from .graphs.algorithms.astar import AStar
from .graphs.algorithms.bfs import BFS
from .graphs.algorithms.dijkstra import Dijkstra
from .graphs.heuristics import HEURISTICS
from .models.solution import Solution
from .persistence.serializer import load_maze
from .view.heatmap import render_heatmap
from .view.renderer import render


def _build_algorithms(args):
    algos = []
    names = [a.lower() for a in args.algorithms] if args.algorithms else ["bfs", "dijkstra", "astar-manhattan"]
    for n in names:
        if n == "bfs":
            algos.append(BFS())
        elif n == "dijkstra":
            algos.append(Dijkstra())
        elif n.startswith("astar"):
            # astar, astar-manhattan, astar-euclidean, etc.
            parts = n.split("-", 1)
            heu = parts[1] if len(parts) == 2 else "manhattan"
            if heu not in HEURISTICS:
                raise SystemExit(f"Unknown heuristic {heu!r}. Choose from {', '.join(HEURISTICS)}")
            algos.append(AStar(heuristic=heu))
        else:
            raise SystemExit(f"Unknown algorithm {n!r}. Options: bfs, dijkstra, astar[-heu]")
    return algos


def main() -> int:
    parser = argparse.ArgumentParser(description="Maze Solver Laboratory - benchmark BFS/Dijkstra/A*")
    parser.add_argument("maze", type=Path, nargs="?", help="Path to a .maze file")
    parser.add_argument("--benchmark", action="store_true", help="Run comparative benchmark of all algorithms")
    parser.add_argument("--algorithms", nargs="+", help="Algorithms to run: bfs dijkstra astar-manhattan astar-euclidean astar-chebyshev astar-octile")
    parser.add_argument("--heuristic", choices=list(HEURISTICS.keys()), default="manhattan", help="Heuristic for single A* run")
    parser.add_argument("--algorithm", choices=["bfs", "dijkstra", "astar"], default="astar", help="Single algorithm to run (when not benchmarking)")
    parser.add_argument("--no-path", action="store_true", help="Render maze without solution")
    parser.add_argument("--show-weights", action="store_true", help="Render terrain costs")
    parser.add_argument("--heatmap", action="store_true", help="Show heatmap of visited nodes (benchmark mode)")
    parser.add_argument("--animate", action="store_true", help="Animate search frontier (single algorithm)")
    parser.add_argument("--generate", type=str, help="Generate procedural maze WxH e.g. 31x21")
    parser.add_argument("--weighted", action="store_true", help="When generating, add terrain costs")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for generation")
    parser.add_argument("--output", type=Path, help="Save generated maze to path")
    args = parser.parse_args()

    # Generation mode
    if args.generate:
        try:
            w_str, h_str = args.generate.lower().split("x")
            w, h = int(w_str), int(h_str)
        except Exception:
            parser.error("--generate expects WxH like 31x21")
        from .generator import generate_maze, save_generated
        maze = generate_maze(w, h, weighted=args.weighted, seed=args.seed)
        if args.output:
            save_generated(maze, args.output)
            print(f"Generated {w}x{h} maze -> {args.output}")
        print(render(maze, show_weights=args.show_weights))
        # also benchmark generated maze if requested
        if args.benchmark or args.heatmap:
            algos = _build_algorithms(args)
            results = run_benchmark_suite(algos, maze)
            print("\n" + format_table(results))
        return 0

    if not args.maze:
        parser.error("maze path required (or use --generate WxH)")

    maze = load_maze(args.maze)

    # Benchmark mode
    if args.benchmark or args.heatmap or args.algorithms:
        algos = _build_algorithms(args)
        results = run_benchmark_suite(algos, maze)
        print(f"--- Benchmark: {args.maze} ({maze.width}x{maze.height}) ---\n")
        print(format_table(results))

        # Render best path
        best = min(results, key=lambda r: r.metrics.path_cost if r.path else float("inf"))
        if best.path:
            sol = Solution(tuple(best.path), cost=best.metrics.path_cost)
            print(f"\nBest path by cost: {best.algorithm_name} (cost {best.metrics.path_cost:.1f}, steps {best.metrics.path_length})")
            print(render(maze, sol, show_weights=args.show_weights))
        else:
            print("\nNo path found by any algorithm.")

        if args.heatmap:
            print("\n--- Heatmaps (visited frequency) ---")
            for r in results:
                print(f"\n{r.algorithm_name} heatmap:")
                print(render_heatmap(maze, r.metrics.explored_order or list(r.metrics.visited)))
        return 0 if any(r.path for r in results) else 1

    # Single algorithm mode
    if args.algorithm == "bfs":
        algo = BFS()
    elif args.algorithm == "dijkstra":
        algo = Dijkstra()
    else:
        algo = AStar(heuristic=args.heuristic)

    path, metrics = algo.solve(maze.start, maze.goal, maze=maze)
    solution = Solution(tuple(path), cost=metrics.path_cost) if path else None

    if args.animate and path:
        from .view.animator import animate_search
        animate_search(maze, metrics.explored_order, path)
    else:
        print(render(maze, None if args.no_path else solution, show_weights=args.show_weights))

    print(metrics)
    if solution is None:
        print("No path found.")
        return 1
    print(f"Path length: {solution.length} | Cost: {metrics.path_cost:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
