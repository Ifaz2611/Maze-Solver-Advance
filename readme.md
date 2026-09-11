# Maze Solver Laboratory — Advanced Edition

**Weighted pathfinding lab** comparing **BFS / DFS / Dijkstra / A* / Greedy / Bidirectional BFS** on terrain with live benchmarking, interactive Web UI, desktop GUI, heatmaps, and procedural stress-testing.

> **New in v1.0:** Web UI, Tkinter GUI, 3 new algorithms, diagonal mode, JSON/PNG export, expanded benchmark suite.

---

## 1. Requirements

* **Python >= 3.10** (stdlib only for core; optional Pillow for PNG export)
* Windows / macOS / Linux
* No mandatory external dependencies

Verify:
```bash
python --version  # >= 3.10
```

---

## 2. Install & Start

### Option A — Editable install (recommended, exposes `maze-solver` CLI)

```bash
# from project root (where pyproject.toml lives)
pip install -e .

# verify
maze-solver --help
```

### Option B — Without install (use PYTHONPATH)

```bash
# Linux / macOS
PYTHONPATH=src python -m maze_solver --help

# Windows PowerShell
$env:PYTHONPATH="src"; python -m maze_solver --help

# Windows CMD
set PYTHONPATH=src && python -m maze_solver --help
```

### Quick sanity check

```bash
maze-solver mazes/standard/labyrinth.maze --benchmark
```

---

## 3. Project Layout

```
MAZE SOLVER/
├── mazes/
│   ├── standard/       # unweighted (#, S, G, space)
│   ├── weighted/       # terrain: '.' dirt=2, 'm' mud=5, 'w' water=10
│   └── procedural/     # auto-generated stress mazes
├── src/maze_solver/
│   ├── graphs/algorithms/  # BFS, DFS, Dijkstra, AStar, Greedy, Bi-BFS (Strategy Pattern)
│   ├── graphs/heuristics.py# manhattan, euclidean, chebyshev, octile, zero
│   ├── graphs/graph.py     # explicit weighted adjacency list
│   ├── models/terrain.py   # TerrainType costs
│   ├── analytics/          # metrics.py + profiler.py
│   ├── persistence/        # serializer + exporter (JSON/PNG)
│   ├── view/               # renderer, animator, heatmap
│   ├── web/app.py          # interactive Web UI (stdlib HTTP server)
│   ├── gui.py              # Tkinter desktop visualizer
│   ├── generator.py        # procedural maze generator
│   └── __main__.py         # CLI
├── pyproject.toml
└── readme.md
```

Maze characters:
- `#` wall (`inf`), `S` start, `G` goal
- ` ` / `g` grass=1, `.` / `d` dirt=2, `m` mud=5, `w` water=10

---

## 4. How to Start — All Modes

### 4.1 CLI — Single solve (A* manhattan default)

```bash
maze-solver mazes/standard/labyrinth.maze
# or without install
python -m maze_solver mazes/standard/labyrinth.maze
```

### 4.2 Choose algorithm

```bash
maze-solver mazes/standard/miniature.maze --algorithm bfs
maze-solver mazes/standard/miniature.maze --algorithm dfs
maze-solver mazes/standard/miniature.maze --algorithm dijkstra
maze-solver mazes/standard/miniature.maze --algorithm astar --heuristic euclidean
maze-solver mazes/standard/miniature.maze --algorithm greedy --heuristic manhattan
maze-solver mazes/standard/miniature.maze --algorithm bi-bfs
# heuristics: manhattan, euclidean, chebyshev, octile, zero
```

### 4.3 Benchmark (comparative table — now 7 algorithms)

```bash
maze-solver mazes/standard/labyrinth.maze --benchmark
maze-solver mazes/weighted/terrain_demo.maze --benchmark --heatmap --show-weights
maze-solver mazes/procedural/generated_25x15.maze --benchmark

# custom subset:
maze-solver mazes/weighted/terrain_demo.maze --algorithms bfs dfs dijkstra astar-manhattan astar-euclidean greedy-manhattan
# export results
maze-solver mazes/weighted/terrain_demo.maze --benchmark --export-json results.json --export-image results.png
maze-solver mazes/standard/labyrinth.maze --benchmark --json  # JSON stdout
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

### 4.4 Generate mazes

```bash
maze-solver --generate 31x21 --seed 7 --output mazes/procedural/my.maze
maze-solver --generate 25x15 --weighted --seed 42 --benchmark --show-weights
maze-solver --generate 51x31 --weighted --seed 123 --benchmark --heatmap
```

### 4.5 Diagonal movement (8-way)

```bash
maze-solver mazes/standard/labyrinth.maze --diagonal --algorithm astar --heuristic octile
maze-solver mazes/standard/labyrinth.maze --diagonal --benchmark
```

### 4.6 Web UI — Interactive browser solver (NEW)

```bash
maze-solver --web
# custom host/port
maze-solver --web --host 127.0.0.1 --port 8000
# or without install
python -m maze_solver --web --port 8000
```

Then open **http://127.0.0.1:8000** in your browser:
- Visual grid with path animation (grass/dirt/mud/water colors)
- Dropdown for all 7 algorithms + heuristics
- Benchmark bar charts, metrics cards, ASCII render
- Live maze editor & procedural generator
- REST API: `POST /api/solve`, `POST /api/benchmark`, `GET /api/generate?w=25&h=15`

### 4.7 Desktop GUI — Tkinter (NEW)

```bash
maze-solver --gui
# with initial maze
maze-solver mazes/standard/labyrinth.maze --gui
```

Features: Open .maze files, generate weighted/unweighted, solve with any algorithm, animated visited overlay, benchmark popup.

### 4.8 Other CLI flags

```bash
maze-solver mazes/standard/labyrinth.maze --no-path           # without solution
maze-solver mazes/weighted/terrain_demo.maze --show-weights    # terrain glyphs
maze-solver mazes/standard/labyrinth.maze --animate            # step-by-step (single algo)
maze-solver mazes/standard/labyrinth.maze --diagonal --animate
```

### 4.9 Python API

```python
from maze_solver.persistence.serializer import load_maze
from maze_solver.graphs.algorithms import BFS, Dijkstra, AStar
from maze_solver.graphs.algorithms.dfs import DFS
from maze_solver.graphs.algorithms.greedy import GreedyBFS
from maze_solver.analytics.profiler import run_benchmark_suite, format_table
from maze_solver.view.renderer import render

maze = load_maze("mazes/weighted/terrain_demo.maze")

results = run_benchmark_suite(
    [BFS(), DFS(), Dijkstra(), AStar("manhattan"), GreedyBFS("manhattan")],
    maze
)
print(format_table(results))

# single algorithm + export
from maze_solver.persistence.exporter import export_solution_json, export_maze_image
path, metrics = AStar("manhattan").solve(maze.start, maze.goal, maze=maze)
print(metrics)
print(render(maze, solution))
export_solution_json(path, metrics, "out.json")
export_maze_image(maze, path, "out.png")  # Pillow for PNG, else PPM
```

---

## 5. Creating Custom Mazes

Plain text `.maze` file, all rows same width:

```
###############
#S#   www     #
# # ###m### # #
#   w....   #G#
###############
```

Save and run `maze-solver path/to/maze.maze --benchmark`.

---

## 6. Troubleshooting

* `No module named maze_solver` → `pip install -e .` or `PYTHONPATH=src python -m maze_solver ...`
* `Maze rows must all have the same width.` → pad rows with spaces/`#` to equal length
* `Unsupported character` → allowed: `# S G space . m w g d` (see `persistence/file_format.py:1`)
* PowerShell quoting: use `$env:PYTHONPATH="src"`
* PNG export fails → `pip install Pillow` or it falls back to PPM format
* Web port in use → `maze-solver --web --port 8001`

---

## 7. Advanced Features Summary

| Feature | Command |
|---------|---------|
| 7 algorithms | `--algorithms bfs dfs dijkstra bi-bfs astar-manhattan greedy-manhattan` |
| Diagonal 8-way | `--diagonal` |
| Heatmaps | `--heatmap` |
| Animate | `--animate` |
| JSON export | `--export-json out.json` / `--json` |
| PNG export | `--export-image out.png` |
| Web UI | `--web --port 8000` |
| Desktop GUI | `--gui` |
| Procedural | `--generate 31x21 --weighted --seed 42` |
