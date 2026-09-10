"""Export utilities: JSON, image, stats."""

from __future__ import annotations

import json
from pathlib import Path

from ..analytics.profiler import BenchmarkResult
from ..models.maze import Maze
from ..models.square import Square


def export_solution_json(path: list[Square] | None, metrics, dest: str | Path) -> None:
    data = {
        "path": [[s.row, s.column] for s in path] if path else None,
        "metrics": metrics.as_dict() if metrics else None,
    }
    Path(dest).write_text(json.dumps(data, indent=2), encoding="utf-8")


def export_benchmark_json(results: list[BenchmarkResult], dest: str | Path) -> None:
    data = [
        {
            "algorithm": r.algorithm_name,
            "path": [[s.row, s.column] for s in r.path] if r.path else None,
            "metrics": r.metrics.as_dict(),
            "peak_memory_kb": r.peak_memory_kb,
        }
        for r in results
    ]
    Path(dest).write_text(json.dumps(data, indent=2), encoding="utf-8")


def export_maze_json(maze: Maze, dest: str | Path) -> None:
    Path(dest).write_text(json.dumps(maze.to_dict(), indent=2), encoding="utf-8")


def export_maze_image(maze: Maze, path: list[Square] | None, dest: str | Path, cell_size: int = 20) -> None:
    """Export maze as PNG using Pillow if available, else PPM fallback."""
    try:
        from PIL import Image, ImageDraw  # type: ignore
        has_pil = True
    except ImportError:
        has_pil = False

    w, h = maze.width, maze.height
    path_set = {(s.row, s.column) for s in path} if path else set()

    if has_pil:
        from PIL import Image as PILImage
        from PIL import ImageDraw as PILDraw

        img = PILImage.new("RGB", (w * cell_size, h * cell_size), "white")
        draw = PILDraw.Draw(img)
        colors = {
            "wall": (30, 30, 30),
            "grass": (255, 255, 255),
            "dirt": (210, 180, 140),
            "mud": (139, 90, 43),
            "water": (100, 149, 237),
            "start": (50, 205, 50),
            "goal": (220, 20, 60),
            "path": (255, 215, 0),
        }
        for r in range(h):
            for c in range(w):
                sq = maze.rows[r][c]
                x0, y0 = c * cell_size, r * cell_size
                x1, y1 = x0 + cell_size, y0 + cell_size
                if sq.role.value == "S":
                    col = colors["start"]
                elif sq.role.value == "G":
                    col = colors["goal"]
                elif sq.role.value == "#":
                    col = colors["wall"]
                elif (r, c) in path_set:
                    col = colors["path"]
                elif sq.terrain.char == "w":
                    col = colors["water"]
                elif sq.terrain.char == "m":
                    col = colors["mud"]
                elif sq.terrain.char == ".":
                    col = colors["dirt"]
                else:
                    col = colors["grass"]
                draw.rectangle([x0, y0, x1, y1], fill=col, outline=(200, 200, 200))
        img.save(dest)
    else:
        # PPM fallback - no dependencies
        header = f"P3\n{w * cell_size} {h * cell_size}\n255\n"
        pixels: list[str] = []
        for r in range(h):
            for _ in range(cell_size):
                for c in range(w):
                    sq = maze.rows[r][c]
                    if sq.role.value == "S":
                        col = "50 205 50"
                    elif sq.role.value == "G":
                        col = "220 20 60"
                    elif sq.role.value == "#":
                        col = "30 30 30"
                    elif (r, c) in path_set:
                        col = "255 215 0"
                    elif sq.terrain.char == "w":
                        col = "100 149 237"
                    elif sq.terrain.char == "m":
                        col = "139 90 43"
                    elif sq.terrain.char == ".":
                        col = "210 180 140"
                    else:
                        col = "255 255 255"
                    for _ in range(cell_size):
                        pixels.append(col)
                pixels.append("\n")
        Path(dest).write_text(header + " ".join(pixels), encoding="utf-8")
