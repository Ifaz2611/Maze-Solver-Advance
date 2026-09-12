"""CLI - Maze Solver Laboratory - exploration only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analytics.profiler import format_table, run_benchmark_suite
from .graphs.algorithms.astar import AStar
from .graphs.algorithms.bfs import BFS
from .graphs.algorithms.bidirectional import BidirectionalBFS
from .graphs.algorithms.dfs import DFS
from .graphs.algorithms.dijkstra import Dijkstra
from .graphs.algorithms.greedy import GreedyBFS
from .graphs.heuristics import HEURISTICS
from .models.maze import Maze
from .models.solution import Solution
from .persistence.serializer import load_maze
from .view.renderer import render


def _build_algorithms(args):
    algos = []
    default = ["bfs", "dfs", "dijkstra", "bi-bfs", "astar-manhattan", "astar-euclidean", "greedy-manhattan"]
    names = [a.lower() for a in args.algorithms] if args.algorithms else default if args.benchmark else ["astar-manhattan"]
    if args.benchmark and not args.algorithms:
        names = default
    for n in names:
        if n == "bfs":
            algos.append(BFS())
        elif n == "dfs":
            algos.append(DFS())
        elif n == "dijkstra":
            algos.append(Dijkstra())
        elif n in ("bi-bfs", "bibfs", "bidirectional"):
            algos.append(BidirectionalBFS())
        elif n.startswith("astar"):
            parts = n.split("-", 1)
            heu = parts[1] if len(parts) == 2 else "manhattan"
            if heu not in HEURISTICS:
                raise SystemExit(f"Unknown heuristic {heu!r}. Choose from {', '.join(HEURISTICS)}")
            algos.append(AStar(heuristic=heu))
        elif n.startswith("greedy"):
            parts = n.split("-", 1)
            heu = parts[1] if len(parts) == 2 else "manhattan"
            if heu not in HEURISTICS:
                raise SystemExit(f"Unknown heuristic {heu!r}. Choose from {', '.join(HEURISTICS)}")
            algos.append(GreedyBFS(heuristic=heu))
        else:
            raise SystemExit(f"Unknown algorithm {n!r}. Options: bfs, dfs, dijkstra, bi-bfs, astar[-heu], greedy[-heu]")
    return algos


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Maze Solver Laboratory - benchmark BFS/DFS/Dijkstra/A*/Greedy/Bi-BFS | Web UI | Terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  maze-solver mazes/standard/labyrinth.maze
  maze-solver mazes/standard/labyrinth.maze --benchmark
  maze-solver mazes/standard/miniature.maze --algorithm astar --heuristic octile
  maze-solver --generate 31x21 --benchmark --output mazes/procedural/my.maze
  maze-solver --web --port 8000
  maze-solver maze.maze --algorithm bfs --export-json result.json --export-image result.png
        """,
    )
    parser.add_argument("maze", type=Path, nargs="?", help="Path to a .maze file")
    parser.add_argument("--benchmark", action="store_true", help="Run comparative benchmark")
    parser.add_argument("--algorithms", nargs="+", help="Algorithms: bfs dfs dijkstra bi-bfs astar-manhattan astar-euclidean astar-chebyshev astar-octile greedy-manhattan")
    parser.add_argument("--heuristic", choices=list(HEURISTICS.keys()), default="manhattan", help="Heuristic for single A*/Greedy run")
    parser.add_argument("--algorithm", choices=["bfs", "dfs", "dijkstra", "astar", "greedy", "bi-bfs"], default="astar", help="Single algorithm (non-benchmark)")
    parser.add_argument("--no-path", action="store_true", help="Render without solution")
    parser.add_argument("--generate", type=str, help="Generate maze WxH e.g. 31x21")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed")
    parser.add_argument("--output", type=Path, help="Save generated maze")
    parser.add_argument("--export-json", type=Path, help="Export solution/benchmark to JSON")
    parser.add_argument("--export-image", type=Path, help="Export maze+path to PNG (needs Pillow) or PPM")
    parser.add_argument("--json", action="store_true", help="Print metrics as JSON")
    parser.add_argument("--web", action="store_true", help="Launch interactive Web UI")
    parser.add_argument("--port", type=int, default=8000, help="Web UI port (default 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Web UI host")
    parser.add_argument("--diagonal", action="store_true", help="Allow diagonal movement (8-way)")
    args = parser.parse_args()

    if args.web:
        from .web.app import run_server
        run_server(args.host, args.port)
        return 0

    if args.generate:
        try:
            w_str, h_str = args.generate.lower().split("x")
            w, h = int(w_str), int(h_str)
        except Exception:
            parser.error("--generate expects WxH like 31x21")
        from .generator import generate_maze, save_generated
        maze = generate_maze(w, h, seed=args.seed)
        if args.output:
            save_generated(maze, args.output)
            print(f"Generated {w}x{h} maze -> {args.output}")
        print(render(maze))
        if args.benchmark:
            algos = _build_algorithms(args)
            results = run_benchmark_suite(algos, maze)
            print("\n" + format_table(results))
            if args.export_json:
                from .persistence.exporter import export_benchmark_json
                export_benchmark_json(results, args.export_json)
                print(f"Benchmark exported -> {args.export_json}")
        return 0

    if not args.maze:
        parser.error("maze path required (or use --generate WxH, --web)")

    maze = load_maze(args.maze)
    if args.diagonal:
        maze = Maze(maze.rows, maze.start, maze.goal, allow_diagonal=True)

    if args.benchmark or args.algorithms:
        algos = _build_algorithms(args)
        results = run_benchmark_suite(algos, maze)
        print(f"--- Benchmark: {args.maze} ({maze.width}x{maze.height}) ---\n")
        if args.json:
            print(json.dumps([{"algorithm": r.algorithm_name, "metrics": r.metrics.as_dict()} for r in results], indent=2))
        else:
            print(format_table(results))

        best = min(results, key=lambda r: r.metrics.path_cost if r.path else float("inf"))
        if best.path:
            sol = Solution(tuple(best.path), cost=best.metrics.path_cost)
            print(f"\nBest path: {best.algorithm_name} (cost {best.metrics.path_cost:.1f}, steps {best.metrics.path_length})")
            print(render(maze, sol))
            if args.export_image:
                from .persistence.exporter import export_maze_image
                export_maze_image(maze, best.path, args.export_image)
                print(f"Image exported -> {args.export_image}")
        else:
            print("\nNo path found by any algorithm.")

        if args.export_json:
            from .persistence.exporter import export_benchmark_json
            export_benchmark_json(results, args.export_json)
            print(f"Benchmark JSON -> {args.export_json}")

        return 0 if any(r.path for r in results) else 1

    if args.algorithm == "bfs":
        algo = BFS()
    elif args.algorithm == "dfs":
        algo = DFS()
    elif args.algorithm == "dijkstra":
        algo = Dijkstra()
    elif args.algorithm == "bi-bfs":
        algo = BidirectionalBFS()
    elif args.algorithm == "greedy":
        algo = GreedyBFS(heuristic=args.heuristic)
    else:
        algo = AStar(heuristic=args.heuristic)

    path, metrics = algo.solve(maze.start, maze.goal, maze=maze)
    solution = Solution(tuple(path), cost=metrics.path_cost) if path else None

    print(render(maze, None if args.no_path else solution))

    if args.json:
        print(json.dumps({"algorithm": algo.name, "metrics": metrics.as_dict(), "path": [[s.row, s.column] for s in path] if path else None}, indent=2))
    else:
        print(metrics)
        if solution is None:
            print("No path found.")
        else:
            print(f"Path length: {solution.length} | Cost: {metrics.path_cost:.1f}")

    if args.export_json and path is not None:
        from .persistence.exporter import export_solution_json
        export_solution_json(path, metrics, args.export_json)
        print(f"Solution JSON -> {args.export_json}")

    if args.export_image:
        from .persistence.exporter import export_maze_image
        export_maze_image(maze, path, args.export_image)
        print(f"Image exported -> {args.export_image}")

    return 0 if solution else 1


if __name__ == "__main__":
    raise SystemExit(main())
