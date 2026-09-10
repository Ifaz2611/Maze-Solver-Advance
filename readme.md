# Maze Solver Advance

Robust pathfinding lab for comparing **BFS / Dijkstra / A*** on weighted terrain with benchmarking, heuristics, and procedural stress-testing.

## Overview

Maze Solver Laboratory is a Python-based algorithmic benchmarking tool designed to evaluate and visualize classic graph traversal and pathfinding strategies. It supports unweighted maps, multi-tier weighted terrain types (dirt, mud, water), and procedural maze generation to analyze performance metrics such as execution time, nodes expanded, memory footprint, and final path cost.

## Features

* **Pathfinding Algorithms:** Breadth-First Search (BFS), Dijkstra's Algorithm, and A* Search.
* **Heuristic Engine:** Supports Manhattan, Euclidean, Chebyshev, Octile, and Zero heuristics.
* **Weighted Terrain Modeling:** Factor in traversal penalties with terrain glyphs (grass, dirt, mud, water, walls).
* **Comparative Benchmarking:** Generate cross-algorithm comparison tables, performance metrics, and visual heatmaps.
* **Procedural Stress-Testing:** Automatically generate randomized unweighted or weighted maps on demand.
* **Standard-Library Only:** Built entirely on Python >= 3.10 standard libraries with no mandatory external dependencies.

## Project Structure

```text
maze-solver/
├── mazes/
│   ├── standard/       # unweighted (#, S, G, space)
│   ├── weighted/       # terrain: '.' dirt=2, 'm' mud=5, 'w' water=10
│   └── procedural/     # auto-generated stress mazes
├── src/maze_solver/
│   ├── graphs/algorithms/  # Strategy Pattern: base.py, bfs.py, dijkstra.py, astar.py
│   ├── graphs/heuristics.py# manhattan, euclidean, chebyshev, octile, zero
│   ├── graphs/graph.py     # explicit weighted adjacency list
│   ├── models/terrain.py   # TerrainType costs
│   ├── analytics/          # metrics.py + profiler.py
│   ├── view/               # renderer, animator, heatmap
│   ├── generator.py        # procedural maze generator
│   └── __main__.py         # CLI
├── pyproject.toml
└── GETSTART.md

```

## Requirements

* Python >= 3.10 (stdlib only)
* Operating System: Windows, macOS, or Linux

Verify your environment:

```bash
python --version  # Must be >= 3.10

```

## Installation

```bash
# Clone the repository
git clone https://github.com/Ifaz2611/Maze-Solver-Advance
cd Maze-Solver-Advance

# Editable install (exposes `maze-solver` CLI command)
pip install -e .

# Alternative without install — use PYTHONPATH
# Linux/macOS: PYTHONPATH=src python -m maze_solver ...
# Windows PowerShell: $env:PYTHONPATH="src"; python -m maze_solver ...

```

## Quick Start

### Solve a Single Maze

```bash
maze-solver mazes/standard/labyrinth.maze

```

### Choose an Algorithm or Heuristic

```bash
maze-solver mazes/standard/miniature.maze --algorithm bfs
maze-solver mazes/standard/miniature.maze --algorithm dijkstra
maze-solver mazes/standard/miniature.maze --algorithm astar --heuristic euclidean

```

*Available heuristics:* `manhattan`, `euclidean`, `chebyshev`, `octile`, `zero`.

### Run Benchmarks

```bash
maze-solver mazes/standard/labyrinth.maze --benchmark
maze-solver mazes/weighted/terrain_demo.maze --benchmark --heatmap --show-weights

```

### Generate Procedural Mazes

```bash
maze-solver --generate 31x21 --seed 7 --output mazes/procedural/my.maze
maze-solver --generate 25x15 --weighted --seed 42 --benchmark --show-weights

```

## Terrain & Legend

Maze character representations used in map files:

* `#`: Wall (`inf` cost)
* `S`: Start node
* `G`: Goal node
* ` ` / `g`: Grass (cost = 1)
* `.` / `d`: Dirt (cost = 2)
* `m`: Mud (cost = 5)
* `w`: Water (cost = 10)

## Python API Usage

```python
from maze_solver.persistence.serializer import load_maze
from maze_solver.graphs.algorithms import BFS, Dijkstra, AStar
from maze_solver.analytics.profiler import run_benchmark_suite, format_table
from maze_solver.view.renderer import render

maze = load_maze("mazes/weighted/terrain_demo.maze")

results = run_benchmark_suite(
    [BFS(), Dijkstra(), AStar("manhattan"), AStar("euclidean")],
    maze
)
print(format_table(results))

# Solve with a single algorithm
solution, metrics = AStar("manhattan").solve(maze.start, maze.goal, maze=maze)
print(metrics)
print(render(maze, solution))

```

## License

Distributed under the MIT License. See `LICENSE` for more information.