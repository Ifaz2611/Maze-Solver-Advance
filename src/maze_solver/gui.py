"""Tkinter GUI visualizer - interactive desktop app (stdlib only)."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .analytics.profiler import run_benchmark_suite
from .generator import generate_maze
from .graphs.algorithms.astar import AStar
from .graphs.algorithms.bfs import BFS
from .graphs.algorithms.bidirectional import BidirectionalBFS
from .graphs.algorithms.dfs import DFS
from .graphs.algorithms.dijkstra import Dijkstra
from .graphs.algorithms.greedy import GreedyBFS
from .models.maze import Maze
from .persistence.serializer import load_maze

ALGO_MAP = {
    "BFS": BFS(),
    "DFS": DFS(),
    "Dijkstra": Dijkstra(),
    "Bi-BFS": BidirectionalBFS(),
    "A* Manhattan": AStar("manhattan"),
    "A* Euclidean": AStar("euclidean"),
    "Greedy": GreedyBFS("manhattan"),
}

COLORS = {
    "#": "#0f172a",
    " ": "#ffffff",
    ".": "#d6b98a",
    "m": "#8b5a2b",
    "w": "#60a5fa",
    "S": "#22c55e",
    "G": "#ef4444",
    "path": "#facc15",
    "visited": "#c084fc",
}

CELL = 22


def launch_gui(initial_maze: Maze | None = None):
    root = tk.Tk()
    root.title("Maze Solver Lab - GUI")
    root.configure(bg="#0f172a")

    maze_ref: list[Maze | None] = [initial_maze]
    path_ref: list[list | None] = [None]

    # Top controls
    ctrl = tk.Frame(root, bg="#1e293b", padx=10, pady=8)
    ctrl.pack(fill="x")

    tk.Label(ctrl, text="Algorithm:", bg="#1e293b", fg="white").pack(side="left")
    algo_var = tk.StringVar(value="A* Manhattan")
    ttk.Combobox(ctrl, textvariable=algo_var, values=list(ALGO_MAP.keys()), width=16, state="readonly").pack(side="left", padx=6)

    def load_file():
        p = filedialog.askopenfilename(filetypes=[("Maze", "*.maze"), ("All", "*.*")])
        if not p:
            return
        try:
            maze_ref[0] = load_maze(p)
            path_ref[0] = None
            draw()
            status.config(text=f"Loaded {Path(p).name} {maze_ref[0].width}x{maze_ref[0].height}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_generate():
        maze_ref[0] = generate_maze(25, 15, weighted=False)
        path_ref[0] = None
        draw()

    def on_generate_w():
        maze_ref[0] = generate_maze(25, 15, weighted=True)
        path_ref[0] = None
        draw()

    def solve():
        if not maze_ref[0]:
            messagebox.showwarning("No maze", "Load or generate a maze first")
            return
        algo = ALGO_MAP[algo_var.get()]
        # recreate fresh algo instance to avoid stale state
        from copy import deepcopy
        # instead create new instance by class
        name = algo_var.get()
        if name == "BFS":
            algo = BFS()
        elif name == "DFS":
            algo = DFS()
        elif name == "Dijkstra":
            algo = Dijkstra()
        elif name == "Bi-BFS":
            algo = BidirectionalBFS()
        elif "A*" in name:
            heu = "manhattan" if "Manhattan" in name else "euclidean"
            algo = AStar(heu)
        elif name == "Greedy":
            algo = GreedyBFS("manhattan")
        path, metrics = algo.solve(maze_ref[0].start, maze_ref[0].goal, maze=maze_ref[0])
        path_ref[0] = path
        draw(visited=metrics.explored_order)
        status.config(text=str(metrics))
        if not path:
            messagebox.showinfo("No path", "No path found!")

    def benchmark():
        if not maze_ref[0]:
            return
        algos = [BFS(), DFS(), Dijkstra(), BidirectionalBFS(), AStar("manhattan"), AStar("euclidean"), GreedyBFS("manhattan")]
        results = run_benchmark_suite(algos, maze_ref[0])
        win = tk.Toplevel(root)
        win.title("Benchmark")
        text = tk.Text(win, width=90, height=16, bg="#0f172a", fg="#e2e8f0", font=("Consolas", 9))
        text.pack()
        from .analytics.profiler import format_table
        text.insert("1.0", format_table(results))

    tk.Button(ctrl, text="Open .maze", command=load_file, bg="#38bdf8", fg="#0f172a", relief="flat", padx=10).pack(side="left", padx=4)
    tk.Button(ctrl, text="Generate", command=on_generate, bg="#334155", fg="white", relief="flat", padx=10).pack(side="left", padx=2)
    tk.Button(ctrl, text="Weighted", command=on_generate_w, bg="#334155", fg="white", relief="flat", padx=10).pack(side="left", padx=2)
    tk.Button(ctrl, text="▶ Solve", command=solve, bg="#22c55e", fg="white", relief="flat", padx=14, font=("Segoe UI", 9, "bold")).pack(side="left", padx=8)
    tk.Button(ctrl, text="📊 Benchmark", command=benchmark, bg="#a78bfa", fg="white", relief="flat", padx=10).pack(side="left", padx=2)

    canvas_frame = tk.Frame(root, bg="#0f172a")
    canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
    canvas = tk.Canvas(canvas_frame, bg="#0f172a", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    status = tk.Label(root, text="Ready - load a maze or generate one", bg="#0f172a", fg="#94a3b8", anchor="w", padx=10, pady=4)
    status.pack(fill="x")

    def draw(visited=None):
        canvas.delete("all")
        maze = maze_ref[0]
        if not maze:
            canvas.create_text(200, 100, text="No maze loaded\nClick Generate or Open .maze", fill="#94a3b8", font=("Segoe UI", 12), justify="center")
            return
        path_set = {(s.row, s.column) for s in path_ref[0]} if path_ref[0] else set()
        visited_set = {(s.row, s.column) for s in (visited or [])}
        # auto size canvas
        canvas.config(width=maze.width * CELL + 2, height=maze.height * CELL + 2)
        for r in range(maze.height):
            for c in range(maze.width):
                sq = maze.rows[r][c]
                x0, y0 = c * CELL, r * CELL
                x1, y1 = x0 + CELL, y0 + CELL
                if sq.role.value == "S":
                    col = COLORS["S"]
                elif sq.role.value == "G":
                    col = COLORS["G"]
                elif (r, c) in path_set and sq.role.value not in ("S", "G"):
                    col = COLORS["path"]
                elif (r, c) in visited_set and sq.role.value not in ("S", "G", "#"):
                    col = COLORS["visited"]
                elif sq.role.value == "#":
                    col = COLORS["#"]
                else:
                    ch = sq.terrain.char
                    if ch == "w":
                        col = COLORS["w"]
                    elif ch == "m":
                        col = COLORS["m"]
                    elif ch == ".":
                        col = COLORS["."]
                    else:
                        col = COLORS[" "]
                canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline="#1e293b")

        # animate visited in order if provided
        if visited and len(visited) > 1:
            def animate(i=0):
                if i >= len(visited):
                    return
                sq = visited[i]
                if (sq.row, sq.column) not in path_set:
                    x0, y0 = sq.column * CELL, sq.row * CELL
                    canvas.create_rectangle(x0, y0, x0 + CELL, y0 + CELL, fill=COLORS["visited"], outline="#1e293b")
                root.after(10, lambda: animate(i + 1))
            # Uncomment to animate: animate()

    # initial demo maze if none
    if not maze_ref[0]:
        try:
            maze_ref[0] = load_maze(Path(__file__).parents[2] / "mazes" / "standard" / "labyrinth.maze")
        except Exception:
            maze_ref[0] = generate_maze(25, 15)

    draw()
    root.mainloop()
