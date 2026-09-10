# Maze Solver Laboratory — Get Started

Robust pathfinding lab for comparing **BFS / Dijkstra / A*** on weighted terrain with benchmarking, heuristics, and procedural stress-testing.

## 1. Requirements

* Python >= 3.10 (stdlib only, no extra deps)
* Windows / macOS / Linux

Verify:

```bash
python --version  # >= 3.10
```

## 2. Install

```bash
# clone your repo
https://github.com/Ifaz2611/Maze-Solver-Advance
cd Maze-Solver-Advance

# editable install (exposes `maze-solver` CLI)
pip install -e .

# alternative without install — use PYTHONPATH
# Linux/macOS: PYTHONPATH=src python -m maze_solver ...
# Windows PowerShell: $env:PYTHONPATH="src"; python -m maze_solver ...
```

## 3. Project Layout

```
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

Maze characters:
- `#` wall (`inf`), `S` start, `G` goal
- ` ` / `g` grass=1, `.` / `d` dirt=2, `m` mud=5, `w` water=10

## 4. Quick Start

### Solve a single maze (A* manhattan default)

```bash
maze-solver mazes/standard/labyrinth.maze
# or without install:
python -m maze_solver mazes/standard/labyrinth.maze
```

### Choose algorithm

```bash
maze-solver mazes/standard/miniature.maze --algorithm bfs
maze-solver mazes/standard/miniature.maze --algorithm dijkstra
maze-solver mazes/standard/miniature.maze --algorithm astar --heuristic euclidean
# heuristics: manhattan, euclidean, chebyshev, octile, zero
```

### Benchmark (comparative table)

```bash
maze-solver mazes/standard/labyrinth.maze --benchmark
maze-solver mazes/weighted/terrain_demo.maze --benchmark --heatmap --show-weights
maze-solver mazes/procedural/generated_25x15.maze --benchmark

# custom set:
maze-solver mazes/weighted/terrain_demo.maze --algorithms bfs dijkstra astar-manhattan astar-euclidean
```

Example output:

```
+---------------+----------+----------+----------+-------+------+
| Algorithm     | Time(ms) | Expanded | Frontier | Steps | Cost |
+---------------+----------+----------+----------+-------+------+
| BFS           | 0.93     | 219      | 12       | 34    | 67.0 |
| Dijkstra      | 1.72     | 205      | 22       | 38    | 48.0 |
| A*(manhattan) | 1.02     | 105      | 25       | 38    | 48.0 |
+---------------+----------+----------+----------+-------+------+
Fastest: BFS | Fewest expansions: A*(manhattan)
```
> Weighted maze shows why it matters: BFS finds fewer steps (34) but higher cost (67), Dijkstra/A* find longer step path (38) with minimal cost (48) — A* halves expansions.

### Generate mazes

```bash
# unweighted
maze-solver --generate 31x21 --seed 7 --output mazes/procedural/my.maze

# weighted terrain + benchmark in one go
maze-solver --generate 25x15 --weighted --seed 42 --benchmark --show-weights

# procedural benchmark
maze-solver --generate 51x31 --weighted --seed 123 --benchmark --heatmap
```

### Other options

```bash
maze-solver mazes/standard/labyrinth.maze --no-path      # render without solution
maze-solver mazes/weighted/terrain_demo.maze --show-weights # show terrain glyphs
maze-solver mazes/standard/labyrinth.maze --animate       # step-by-step frontier (single algo)
maze-solver mazes/standard/labyrinth.maze --algorithm astar --heuristic chebyshev --animate
```

## 5. Python API

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

# single algorithm
path, metrics = AStar("manhattan").solve(maze.start, maze.goal, maze=maze)
print(metrics)  # [A*(manhattan)] Time: 0.46ms | Expanded: 56 | ...
print(render(maze, solution))  # with path
```

Weighted graph explicitly:

```python
from maze_solver.graphs.converter import to_weighted_graph
graph = to_weighted_graph(maze)
print(graph.edge_count(), len(graph))
```

## 6. Creating Custom Mazes

Plain text `.maze` file, all rows same width:

```
###############
#S#   www     #
# # ###m### # #
#   w....   #G#
###############
```

Save and run `maze-solver path/to/maze.maze --benchmark`.

## 7. Troubleshooting

* `No module named maze_solver` → `pip install -e .` or `PYTHONPATH=src python -m maze_solver ...`
* `Maze rows must all have the same width.` → pad rows with spaces/`#` to equal length
* `Unsupported character` → allowed: `# S G space . m w g d` (see `persistence/file_format.py:1`)
* PowerShell quoting: use `$env:PYTHONPATH="src"`

## 8. GitHub Push

```bash
git init
git add .
git commit -m "feat: pathfinding lab with weighted terrain, A*/Dijkstra/BFS benchmark"
git branch -M main
git remote add origin https://github.com/<you>/maze-solver.git
git push -u origin main
```

## 9. License

MIT — do as you wish, keep the header.
