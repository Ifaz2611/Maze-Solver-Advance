"""Interactive Web UI - stdlib HTTP server + REST API (no extra deps)."""

from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from ..analytics.profiler import run_benchmark_suite
from ..generator import generate_maze
from ..graphs.algorithms.astar import AStar
from ..graphs.algorithms.bfs import BFS
from ..graphs.algorithms.bidirectional import BidirectionalBFS
from ..graphs.algorithms.dfs import DFS
from ..graphs.algorithms.dijkstra import Dijkstra
from ..graphs.algorithms.greedy import GreedyBFS
from ..models.maze import Maze
from ..models.solution import Solution
from ..view.renderer import render

ROOT = Path(__file__).parent

def _get_algo(name: str):
    name = name.lower()
    if name == "bfs":
        return BFS()
    if name == "dfs":
        return DFS()
    if name == "dijkstra":
        return Dijkstra()
    if name == "bi-bfs":
        return BidirectionalBFS()
    if name.startswith("greedy"):
        parts = name.split("-", 1)
        heu = parts[1] if len(parts) == 2 else "manhattan"
        return GreedyBFS(heu)
    if name.startswith("astar"):
        parts = name.split("-", 1)
        heu = parts[1] if len(parts) == 2 else "manhattan"
        return AStar(heu)
    raise ValueError(f"Unknown algorithm {name}")

ALGO_LIST = ["bfs", "dfs", "dijkstra", "bi-bfs", "astar-manhattan", "astar-euclidean", "astar-octile", "greedy-manhattan"]

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maze Solver Lab - Interactive</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--accent:#38bdf8;--accent2:#a78bfa;--text:#e2e8f0;--muted:#94a3b8;--path:#facc15;--wall:#0f172a;--start:#22c55e;--goal:#ef4444}
*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text)}
header{padding:1.2rem 2rem;background:linear-gradient(135deg,#0ea5e9,#7c3aed);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem}
header h1{margin:0;font-size:1.6rem}header p{margin:0;opacity:.9}
.container{max-width:1200px;margin:0 auto;padding:1.5rem;display:grid;grid-template-columns:320px 1fr;gap:1.5rem}
@media(max-width:900px){.container{grid-template-columns:1fr}}
.card{background:var(--card);border-radius:14px;padding:1.2rem;box-shadow:0 4px 24px rgba(0,0,0,.4)}
label{display:block;margin:.6rem 0 .3rem;font-size:.85rem;color:var(--muted)}
select,textarea,input,button{width:100%;padding:.6rem .8rem;border-radius:8px;border:1px solid #334155;background:#0f172a;color:var(--text);font-size:.9rem}
textarea{font-family:monospace;min-height:180px;resize:vertical}
button{cursor:pointer;font-weight:600;border:none;margin-top:.6rem;transition:.2s}
.btn-primary{background:var(--accent);color:#0f172a}.btn-primary:hover{filter:brightness(1.1)}
.btn-secondary{background:#334155}.btn-secondary:hover{background:#475569}
.grid{display:grid;grid-template-columns:repeat(auto-fill,18px);gap:2px;justify-content:start}
.cell{width:18px;height:18px;border-radius:3px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700}
.cell.wall{background:#020617}.cell.grass{background:#f8fafc}.cell.dirt{background:#d6b98a}.cell.mud{background:#8b5a2b}.cell.water{background:#60a5fa}
.cell.start{background:var(--start);color:white}.cell.goal{background:var(--goal);color:white}.cell.path{background:var(--path);color:#422006;animation:pulse .8s infinite alternate}
@keyframes pulse{from{transform:scale(1)}to{transform:scale(1.08)}}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.8rem;margin-top:1rem}
.stat{background:#0f172a;padding:.8rem;border-radius:8px;text-align:center}
.stat b{display:block;font-size:1.3rem;color:var(--accent)}.bars{display:flex;gap:4px;align-items:end;height:60px;margin-top:.5rem}
.bar{flex:1;background:var(--accent);border-radius:4px 4px 0 0;min-width:8px}
.benchmark-table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:.85rem}
.benchmark-table th,.benchmark-table td{padding:.4rem .6rem;border:1px solid #334155;text-align:center}
.benchmark-table th{background:#0f172a;color:var(--accent)}
.mono{font-family:monospace;background:#0f172a;padding:1rem;border-radius:8px;white-space:pre;overflow:auto}
</style>
</head>
<body>
<header>
<div><h1>🧩 Maze Solver Laboratory</h1><p>Compare BFS • Dijkstra • A* • DFS • Greedy • Bi-BFS on weighted terrain</p></div>
<div style="display:flex;gap:.6rem"><button onclick="loadExample('labyrinth')" class="btn-secondary" style="width:auto;padding:.5rem 1rem">Labyrinth</button><button onclick="loadExample('terrain')" class="btn-secondary" style="width:auto;padding:.5rem 1rem">Terrain Demo</button></div>
</header>
<div class="container">
<div class="card">
<h3 style="margin-top:0">Controls</h3>
<label>Algorithm</label>
<select id="algo">
<option value="astar-manhattan">A* (Manhattan)</option>
<option value="astar-euclidean">A* (Euclidean)</option>
<option value="astar-octile">A* (Octile)</option>
<option value="astar-zero">A* (Zero → Dijkstra)</option>
<option value="bfs">BFS</option>
<option value="dijkstra">Dijkstra</option>
<option value="dfs">DFS</option>
<option value="greedy-manhattan">Greedy (Manhattan)</option>
<option value="bi-bfs">Bidirectional BFS</option>
</select>
<label><input type="checkbox" id="diagonal" style="width:auto"> Allow diagonal moves</label>
<label>Generate</label>
<div style="display:flex;gap:.5rem"><input id="genW" type="number" value="25" style="width:50%"><input id="genH" type="number" value="15" style="width:50%"></div>
<div style="display:flex;gap:.5rem"><button onclick="generate()" class="btn-secondary">Generate Random</button><button onclick="generateWeighted()" class="btn-secondary">Weighted +</button></div>
<label>Maze Editor (S=start, G=goal, #=wall, .=dirt m=mud w=water)</label>
<textarea id="mazeText" placeholder="Paste .maze text here..."></textarea>
<button onclick="solve()" class="btn-primary">▶ Solve</button>
<button onclick="benchmark()" class="btn-secondary">📊 Benchmark All</button>
<button onclick="clearPath()" class="btn-secondary">Clear Path</button>
<div id="metrics" class="stats"></div>
</div>
<div class="card">
<h3 style="margin-top:0">Visualization</h3>
<div id="grid"></div>
<div id="benchmarkArea"></div>
<div id="asciiArea" class="mono" style="margin-top:1rem;display:none"></div>
</div>
</div>
<script>
let lastPath = null;
const examples = {
 labyrinth: `###############\n#S#   #     # #\n# # # # ### # #\n# # # #   # # #\n# # ### ### # #\n#     #   #   #\n### # # # ### #\n#   # # # #   #\n# ### # # # ###\n#   #   #   #G#\n###############`,
 terrain: `###############\n#S..  www     #\n# ## ###m### # #\n#   w....   #G#\n###############`
};
function loadExample(k){document.getElementById('mazeText').value=examples[k];solve();}
function renderGrid(maze, path){
 const grid=document.getElementById('grid');grid.innerHTML='';
 const rows=maze.grid||maze.split('\n').filter(Boolean);
 const pathSet=new Set((path||[]).map(p=>p.join(',')));
 const cols=Math.max(...rows.map(r=>r.length));
 grid.style.gridTemplateColumns=`repeat(${cols},18px)`;
 rows.forEach((row,r)=>{
  [...row].forEach((ch,c)=>{
   const d=document.createElement('div');d.className='cell';
   const key=`${r},${c}`;
   if(ch==='S') d.classList.add('start'),d.textContent='S';
   else if(ch==='G') d.classList.add('goal'),d.textContent='G';
   else if(pathSet.has(key)) d.classList.add('path'),d.textContent='•';
   else if(ch==='#') d.classList.add('wall');
   else if(ch==='.') d.classList.add('dirt');
   else if(ch==='m'||ch==='M') d.classList.add('mud');
   else if(ch==='w'||ch==='W') d.classList.add('water');
   else d.classList.add('grass');
   grid.appendChild(d);
  });
 });
}
async function solve(){
 const text=document.getElementById('mazeText').value.trim();
 if(!text){alert('Paste a maze first');return;}
 const algo=document.getElementById('algo').value;
 const diagonal=document.getElementById('diagonal').checked;
 const res=await fetch('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({grid:text,algorithm:algo,diagonal})}).then(r=>r.json());
 if(res.error){alert(res.error);return;}
 lastPath=res.path;
 renderGrid(res.maze,res.path);
 document.getElementById('asciiArea').style.display='block';
 document.getElementById('asciiArea').textContent=res.rendered;
 const m=res.metrics;
 document.getElementById('metrics').innerHTML=`<div class="stat"><b>${m.time_ms}ms</b>Time</div><div class="stat"><b>${m.nodes_expanded}</b>Expanded</div><div class="stat"><b>${m.path_length}</b>Steps</div><div class="stat"><b>${m.path_cost.toFixed(1)}</b>Cost</div>`;
 document.getElementById('benchmarkArea').innerHTML=`<p style="color:var(--muted);font-size:.85rem">${res.algorithm} | Frontier max ${m.max_frontier}</p>`;
}
async function benchmark(){
 const text=document.getElementById('mazeText').value.trim();
 if(!text){alert('Paste a maze first');return;}
 const res=await fetch('/api/benchmark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({grid:text})}).then(r=>r.json());
 if(res.error){alert(res.error);return;}
 let html='<table class="benchmark-table"><tr><th>Algorithm</th><th>Time(ms)</th><th>Expanded</th><th>Frontier</th><th>Steps</th><th>Cost</th></tr>';
 res.results.forEach(r=>{const m=r.metrics;html+=`<tr><td>${r.algorithm}</td><td>${m.time_ms}</td><td>${m.nodes_expanded}</td><td>${m.max_frontier}</td><td>${m.path_length}</td><td>${m.path_cost.toFixed?m.path_cost.toFixed(1):m.path_cost}</td></tr>`});
 html+='</table>';
 // bar chart for expanded
 const maxE=Math.max(...res.results.map(r=>r.metrics.nodes_expanded));
 html+='<div class="bars">'+res.results.map(r=>`<div class="bar" style="height:${Math.max(8, (r.metrics.nodes_expanded/maxE)*60)}px" title="${r.algorithm}: ${r.metrics.nodes_expanded}"></div>`).join('')+'</div>';
 html+=`<p style="color:var(--muted);font-size:.8rem;margin-top:.4rem">Fastest: ${res.results.reduce((a,b)=>a.metrics.time_ms<b.metrics.time_ms?a:b).algorithm} | Fewest expansions: ${res.results.reduce((a,b)=>a.metrics.nodes_expanded<b.metrics.nodes_expanded?a:b).algorithm}</p>`;
 document.getElementById('benchmarkArea').innerHTML=html;
 if(res.best_path) renderGrid(res.maze,res.best_path);
 document.getElementById('metrics').innerHTML='';
}
async function generate(){
 const w=parseInt(document.getElementById('genW').value)||25;
 const h=parseInt(document.getElementById('genH').value)||15;
 const res=await fetch(`/api/generate?w=${w}&h=${h}`).then(r=>r.json());
 document.getElementById('mazeText').value=res.grid.join('\n');
 renderGrid(res,res.path||null);
}
async function generateWeighted(){
 const w=parseInt(document.getElementById('genW').value)||25;
 const h=parseInt(document.getElementById('genH').value)||15;
 const res=await fetch(`/api/generate?w=${w}&h=${h}&weighted=1`).then(r=>r.json());
 document.getElementById('mazeText').value=res.grid.join('\n');
 renderGrid(res,res.path||null);
}
function clearPath(){lastPath=null;const t=document.getElementById('mazeText').value;if(t) renderGrid({grid:t.split('\n')},null);}
// init
document.getElementById('mazeText').value=examples.labyrinth;
solve();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # quiet
        pass

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/" or parsed.path == "/index.html":
            self._html(HTML_PAGE)
            return
        if parsed.path == "/api/generate":
            w = int(qs.get("w", ["25"])[0])
            h = int(qs.get("h", ["15"])[0])
            weighted = qs.get("weighted", ["0"])[0] == "1"
            seed = qs.get("seed", [None])[0]
            seed = int(seed) if seed else None
            maze = generate_maze(w, h, weighted=weighted, seed=seed)
            self._json({"grid": maze.to_dict()["grid"], "width": maze.width, "height": maze.height})
            return
        if parsed.path == "/api/algorithms":
            self._json({"algorithms": ALGO_LIST})
            return
        self.send_error(404, "Not found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body.decode() or "{}")
        except Exception as e:
            self._json({"error": f"Invalid JSON: {e}"}, 400)
            return

        if self.path == "/api/solve":
            grid = data.get("grid", "")
            algo_name = data.get("algorithm", "astar-manhattan")
            diagonal = bool(data.get("diagonal", False))
            try:
                maze = Maze.from_text(grid)
                if diagonal:
                    maze = Maze(maze.rows, maze.start, maze.goal, allow_diagonal=True)
                algo = _get_algo(algo_name)
                path, metrics = algo.solve(maze.start, maze.goal, maze=maze)
                sol = Solution(tuple(path), cost=metrics.path_cost) if path else None
                rendered = render(maze, sol)
                self._json({
                    "algorithm": algo.name,
                    "path": [[s.row, s.column] for s in path] if path else None,
                    "metrics": metrics.as_dict(),
                    "rendered": rendered,
                    "maze": maze.to_dict(),
                })
            except Exception as e:
                self._json({"error": str(e)}, 400)
            return

        if self.path == "/api/benchmark":
            grid = data.get("grid", "")
            try:
                maze = Maze.from_text(grid)
                algos = [_get_algo(n) for n in ALGO_LIST]
                results = run_benchmark_suite(algos, maze)
                # find best by cost
                best = min(results, key=lambda r: r.metrics.path_cost if r.path else float("inf"))
                self._json({
                    "results": [
                        {"algorithm": r.algorithm_name, "path": [[s.row, s.column] for s in r.path] if r.path else None, "metrics": r.metrics.as_dict()}
                        for r in results
                    ],
                    "best_path": [[s.row, s.column] for s in best.path] if best.path else None,
                    "maze": maze.to_dict(),
                })
            except Exception as e:
                self._json({"error": str(e)}, 400)
            return

        if self.path == "/api/generate":
            w = int(data.get("width", 25))
            h = int(data.get("height", 15))
            weighted = bool(data.get("weighted", False))
            maze = generate_maze(w, h, weighted=weighted)
            self._json({"grid": maze.to_dict()["grid"]})
            return

        self.send_error(404, "Not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(host: str = "127.0.0.1", port: int = 8000):
    server = HTTPServer((host, port), Handler)
    print(f"🚀 Maze Solver Lab running at http://{host}:{port}")
    print("   Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run_server(args.host, args.port)
