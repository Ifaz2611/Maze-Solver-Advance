"""Maze Walk: a small, friendly web interface for exploring maze algorithms.

The module deliberately uses the Python standard library for the web server. The
algorithm implementations remain in the package, while this file owns the HTTP
boundary and the browser-facing presentation.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

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

logger = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 256 * 1024
MIN_MAZE_SIZE = 5
MAX_MAZE_SIZE = 81
ALGORITHM_NAMES = (
    "bfs", "dfs", "dijkstra", "bi-bfs", "astar-manhattan",
    "astar-euclidean", "astar-octile", "astar-zero", "greedy-manhattan",
)


def make_algorithm(name: str):
    """Build one of the algorithms exposed by the browser."""
    name = str(name or "").strip().lower()
    if name == "bfs":
        return BFS()
    if name == "dfs":
        return DFS()
    if name == "dijkstra":
        return Dijkstra()
    if name == "bi-bfs":
        return BidirectionalBFS()
    if name.startswith("greedy"):
        heuristic = name.split("-", 1)[1] if "-" in name else "manhattan"
        return GreedyBFS(heuristic)
    if name.startswith("astar"):
        heuristic = name.split("-", 1)[1] if "-" in name else "manhattan"
        return AStar(heuristic)
    raise ValueError(f"Unknown algorithm: {name}")


def odd_size(value: Any, fallback: int) -> int:
    """Keep generated mazes within the UI's supported odd dimensions."""
    try:
        size = int(value)
    except (TypeError, ValueError):
        size = fallback
    size = max(MIN_MAZE_SIZE, min(MAX_MAZE_SIZE, size))
    if size % 2 == 0:
        size += 1 if size < MAX_MAZE_SIZE else -1
    return size


def as_bool(value: Any) -> bool:
    return value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes", "on"}


def maze_json(maze: Maze) -> dict[str, Any]:
    return maze.to_dict()


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maze Walk | A friendly pathfinding playground</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--accent:#38bdf8;--accent2:#a78bfa;--text:#e2e8f0;--muted:#94a3b8;--path:#facc15;--wall:#020617;--start:#22c55e;--goal:#ef4444;--visited:#334155;--frontier:#38bdf8}
*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.5}
header{padding:1.2rem 2rem;background:linear-gradient(135deg,#0ea5e9,#7c3aed);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;position:sticky;top:0;z-index:10}
header h1{margin:0;font-size:1.6rem}header p{margin:0;opacity:.9;font-size:.9rem}
.container{max-width:1280px;margin:0 auto;padding:1.5rem;display:grid;grid-template-columns:340px 1fr;gap:1.5rem}
@media(max-width:960px){.container{grid-template-columns:1fr}}
.card{background:var(--card);border-radius:16px;padding:1.25rem;box-shadow:0 8px 32px rgba(0,0,0,.4);border:1px solid #263449}
label{display:block;margin:.7rem 0 .3rem;font-size:.82rem;color:var(--muted);font-weight:600;letter-spacing:.02em}
select,textarea,input,button{width:100%;padding:.62rem .8rem;border-radius:10px;border:1px solid #334155;background:#0f172a;color:var(--text);font-size:.9rem;transition:.2s}
select:focus,textarea:focus,input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(56,189,248,.2)}
textarea{font-family:ui-monospace,Consolas,monospace;min-height:170px;resize:vertical;line-height:1.4}
button{cursor:pointer;font-weight:700;border:none;margin-top:.6rem;transition:.18s;letter-spacing:.01em}
button:active{transform:scale(.98)}
.btn-primary{background:linear-gradient(135deg,var(--accent),#0ea5e9);color:#0f172a}.btn-primary:hover{filter:brightness(1.08);transform:translateY(-1px)}
.btn-secondary{background:#334155;color:var(--text)}.btn-secondary:hover{background:#475569}
.btn-ghost{background:transparent;border:1px solid #334155}.btn-ghost:hover{background:#1e293b}
.btn-row{display:flex;gap:.5rem}
.btn-row button{flex:1}
.range-row{display:flex;align-items:center;gap:.6rem;margin:.5rem 0}
.range-row input[type=range]{flex:1;accent-color:var(--accent)}
.range-row span{min-width:36px;text-align:center;background:#0f172a;padding:.2rem .4rem;border-radius:6px;font-size:.8rem;border:1px solid #334155}
.badge{display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;border-radius:999px;font-size:.72rem;font-weight:700;letter-spacing:.03em}
.badge-live{background:#22c55e;color:white;animation:blink 1.2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.6}}
.maze-wrap{background:#0b1222;border-radius:12px;padding:1rem;border:1px solid #1e3a5f;overflow:auto;max-height:70vh;position:relative}
.maze-wrap::-webkit-scrollbar{height:8px;width:8px}
.maze-wrap::-webkit-scrollbar-thumb{background:#334155;border-radius:999px}
.grid{display:grid;gap:2px;justify-content:start;position:relative;transition:.2s}
.cell{border-radius:4px;display:flex;align-items:center;justify-content:center;font-weight:800;position:relative;user-select:none;transition:background .18s, transform .18s, box-shadow .18s}
.cell.wall{background:#020617;border:1px solid #0f172a}
.cell.open{background:#f1f5f9;border:1px solid #e2e8f0}
.cell.start{background:var(--start);color:white;box-shadow:0 0 0 2px rgba(34,197,94,.5);z-index:2}
.cell.goal{background:var(--goal);color:white;box-shadow:0 0 0 2px rgba(239,68,68,.5);animation:goalPulse 1.4s infinite;z-index:2}
@keyframes goalPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
.cell.visited{background:#475569;color:#cbd5e1;animation:visitedIn .35s ease}
.cell.frontier{background:var(--frontier);color:white;animation:frontIn .25s ease}
.cell.path{background:var(--path);color:#422006;box-shadow:inset 0 0 0 1px #eab308, 0 2px 8px rgba(250,204,21,.4);animation:pathIn .4s cubic-bezier(.34,1.56,.64,1) forwards;transform:scale(0)}
.cell.path.revealed{transform:scale(1)}
.cell.agent{box-shadow:0 0 0 2px white, 0 0 12px rgba(56,189,248,.9);transform:scale(1.12);z-index:5}
.cell.trail{box-shadow:inset 0 0 0 2px rgba(250,204,21,.35)}
@keyframes visitedIn{from{background:#1e293b;transform:scale(.85)}to{background:#475569;transform:scale(1)}}
@keyframes frontIn{from{transform:scale(.7);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes pathIn{from{transform:scale(0) rotate(-8deg);opacity:0}to{transform:scale(1) rotate(0);opacity:1}}
@keyframes pulse{from{transform:scale(1)}to{transform:scale(1.06)}}
.legend{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.8rem}
.legend span{display:inline-flex;align-items:center;gap:.35rem;font-size:.72rem;color:var(--muted);background:#0f172a;padding:.25rem .5rem;border-radius:999px;border:1px solid #334155}
.legend i{width:12px;height:12px;border-radius:3px;display:inline-block}
.status-bar{display:flex;align-items:center;gap:.6rem;margin-top:.9rem;padding:.6rem .8rem;background:#0f172a;border-radius:10px;border:1px solid #334155;font-size:.82rem;min-height:40px}
.status-dot{width:10px;height:10px;border-radius:50%;background:#475569;transition:.3s}
.status-dot.running{background:var(--accent);box-shadow:0 0 8px var(--accent);animation:blink 1s infinite}
.status-dot.done{background:var(--start);box-shadow:0 0 8px var(--start)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:.6rem;margin-top:1rem}
@media(max-width:600px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:#0f172a;padding:.75rem .5rem;border-radius:10px;text-align:center;border:1px solid #263449}
.stat b{display:block;font-size:1.25rem;color:var(--accent);line-height:1}
.stat small{color:var(--muted);font-size:.7rem;letter-spacing:.04em;text-transform:uppercase}
.bars{display:flex;gap:3px;align-items:end;height:56px;margin-top:.6rem}
.bar{flex:1;background:linear-gradient(to top,#0ea5e9,var(--accent));border-radius:4px 4px 0 0;min-width:8px;transition:height .5s}
.benchmark-table{width:100%;border-collapse:collapse;margin-top:.9rem;font-size:.82rem;overflow:hidden;border-radius:10px;border:1px solid #334155}
.benchmark-table th,.benchmark-table td{padding:.45rem .5rem;border-bottom:1px solid #1e293b;text-align:center}
.benchmark-table th{background:#0f172a;color:var(--accent);font-size:.74rem;letter-spacing:.04em;text-transform:uppercase}
.benchmark-table tr:hover td{background:#1e293b}
.toast{position:fixed;bottom:1.2rem;right:1.2rem;background:#1e293b;color:var(--text);padding:.8rem 1rem;border-radius:10px;border:1px solid #334155;box-shadow:0 8px 24px rgba(0,0,0,.5);transform:translateY(80px);opacity:0;transition:.35s;z-index:99;max-width:380px;font-size:.85rem}
.toast.show{transform:translateY(0);opacity:1}
.toast.err{border-color:#ef4444;background:#1f0f12}
.mono{font-family:ui-monospace,Consolas,monospace;background:#0f172a;padding:.9rem;border-radius:10px;white-space:pre;overflow:auto;border:1px solid #334155;font-size:.78rem;line-height:1.4}
.controls-group{border:1px solid #263449;border-radius:12px;padding:.8rem;background:rgba(15,23,42,.6);margin-top:.8rem}
.controls-group h4{margin:0 0 .5rem;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}
</style>
</head>
<body>
<header>
<div><h1>Maze Walk</h1><p>Try a route, watch the search unfold, and see how each algorithm thinks.</p></div>
<div style="display:flex;gap:.5rem;flex-wrap:wrap"><button onclick="loadExample('labyrinth')" class="btn-secondary" style="width:auto;padding:.5rem .9rem">Load a labyrinth</button></div>
</header>
<div class="container">
<div class="card">
<h3 style="margin:0 0 .2rem">Choose a route</h3>
<p style="margin:0;color:var(--muted);font-size:.78rem">Pick a strategy, then let the explorer take its time.</p>
<label>Algorithm</label>
<select id="algo">
<option value="astar-manhattan">A* (Manhattan) — best for 4-dir</option>
<option value="astar-euclidean">A* (Euclidean)</option>
<option value="astar-octile">A* (Octile) — best for diagonal</option>
<option value="astar-zero">A* (Zero → Dijkstra)</option>
 <option value="bfs">BFS — shortest</option>
 <option value="dijkstra">Dijkstra — shortest</option>
<option value="dfs">DFS — deep explorer</option>
<option value="greedy-manhattan">Greedy (Manhattan)</option>
<option value="bi-bfs">Bidirectional BFS</option>
</select>
<label style="display:flex;align-items:center;gap:.5rem;margin-top:.7rem"><input type="checkbox" id="diagonal" style="width:16px;height:16px;accent-color:var(--accent)"> Allow diagonal moves (8-dir)</label>

<div class="controls-group">
<h4>Make a new maze</h4>
<div style="display:flex;gap:.5rem;align-items:end">
<div style="flex:1"><label style="margin-top:0">Width</label><input id="genW" type="number" value="25" min="5" max="81" step="2"></div>
<div style="flex:1"><label style="margin-top:0">Height</label><input id="genH" type="number" value="15" min="5" max="81" step="2"></div>
</div>
 <div class="btn-row"><button onclick="generate()" class="btn-secondary">New maze</button></div>
<p style="margin:.4rem 0 0;color:var(--muted);font-size:.7rem">Odd sizes give perfect mazes. Clamped 5–81.</p>
</div>

<label>Maze editor <span style="color:var(--muted);font-weight:400">(S=start, G=goal, #=wall, space=open)</span></label>
<textarea id="mazeText" placeholder="Paste .maze text here..."></textarea>

<div class="controls-group">
<h4>Walking pace</h4>
<div style="display:flex;align-items:center;gap:.6rem">
<label style="margin:0;display:flex;align-items:center;gap:.4rem"><input type="checkbox" id="animateToggle" checked style="width:16px;height:16px;accent-color:var(--accent)"> Animate</label>
<span id="liveBadge" class="badge badge-live" style="display:none">● LIVE</span>
<span id="stepInfo" style="margin-left:auto;font-size:.78rem;color:var(--muted)">—</span>
</div>
<div class="range-row"><span style="font-size:.72rem;color:var(--muted)">Slow</span><input id="speed" type="range" min="1" max="100" value="42"><span style="font-size:.72rem;color:var(--muted)">Fast</span><span id="speedVal">42ms</span></div>
<div class="btn-row">
<button onclick="solve()" class="btn-primary" id="solveBtn">Find a route</button>
<button onclick="togglePause()" class="btn-ghost" id="pauseBtn" style="flex:0 0 90px">Pause</button>
</div>
<div class="btn-row">
<button onclick="stepOnce()" class="btn-ghost">One step</button>
<button onclick="replay()" class="btn-ghost">Walk again</button>
<button onclick="clearPath()" class="btn-ghost">Clear route</button>
</div>
</div>

<button onclick="benchmark()" class="btn-secondary">Benchmark All algorithms</button>
<div id="metrics" class="stats"></div>
</div>

<div class="card">
<div style="display:flex;align-items:center;gap:.7rem;flex-wrap:wrap">
<h3 style="margin:0">The maze</h3>
<span id="sizeInfo" style="font-size:.75rem;color:var(--muted);background:#0f172a;padding:.2rem .5rem;border-radius:999px;border:1px solid #334155"></span>
<span id="costInfo" style="font-size:.75rem;color:var(--muted)"></span>
</div>
<div class="status-bar"><div id="statusDot" class="status-dot"></div><div id="statusText" style="flex:1">Ready when you are. Choose a maze and find a route.</div><div id="progressText" style="font-weight:700;color:var(--accent)"></div></div>
<div class="maze-wrap" id="mazeWrap"><div id="grid" class="grid"></div></div>
<div class="legend">
<span><i style="background:#020617"></i> Wall</span>
<span><i style="background:#f1f5f9;border:1px solid #cbd5e1"></i> Open</span>
<span><i style="background:#22c55e"></i> Start</span>
<span><i style="background:#ef4444"></i> Goal</span>
<span><i style="background:#facc15"></i> Path</span>
<span><i style="background:#475569"></i> Explored</span>
<span><i style="background:#38bdf8"></i> Frontier</span>
</div>
<div id="benchmarkArea"></div>
<div id="asciiArea" class="mono" style="margin-top:1rem;display:none"></div>
</div>
</div>
<div id="toast" class="toast"></div>
<script>
let lastPath=null, lastMaze=null, lastExplored=null, animTimer=null, animIndex=0, isPaused=false, currentPathSet=null;
const examples={
 labyrinth: `###############\n#S#   #     # #\n# # # # ### # #\n# # # #   # # #\n# # ### ### # #\n#     #   #   #\n### # # # ### #\n#   # # # #   #\n# ### # # # ###\n#   #   #   #G#\n###############`
};
function toast(msg, isErr=false){
 const t=document.getElementById('toast');t.textContent=msg;t.className='toast '+(isErr?'err show':'show');
 clearTimeout(t._hide);t._hide=setTimeout(()=>t.className='toast'+(isErr?' err':''), 2600);
}
function clampSize(v){ let n=parseInt(v); if(isNaN(n)) return 15; n=Math.max(5,Math.min(81,n)); if(n%2===0) n+=1; if(n>81) n=81; return n; }
function cellSizeFor(cols, rows){
 const available = document.getElementById('mazeWrap').clientWidth - 32;
 if(!available || available<=0) return 18;
 // aim to fit without scroll, but allow scroll for huge mazes
 let s = Math.floor((available - (cols-1)*2) / cols);
 s = Math.max(10, Math.min(22, s));
 if(cols>40 || rows>40) s = Math.max(10, Math.min(s, 14));
 if(cols>60) s = 10;
 return s;
}
function loadExample(k){document.getElementById('mazeText').value=examples[k];solve();}
function buildGridDOM(rows, cellSize){
 const grid=document.getElementById('grid'); grid.innerHTML='';
 const cols=Math.max(...rows.map(r=>r.length));
 const size=cellSizeFor(cols, rows.length);
 grid.style.gridTemplateColumns=`repeat(${cols}, ${size}px)`;
 document.getElementById('sizeInfo').textContent=`${cols} × ${rows.length}  •  cell ${size}px`;
 const cells=[];
 rows.forEach((row,r)=>{
   [...row].forEach((ch,c)=>{
    const d=document.createElement('div'); d.className='cell'; d.style.width=size+'px'; d.style.height=size+'px'; d.style.fontSize=Math.max(7, Math.floor(size*0.55))+'px';
    const key=`${r},${c}`;
    d.dataset.r=r; d.dataset.c=c; d.dataset.key=key; d.dataset.ch=ch;
    if(ch==='S'){ d.classList.add('start'); d.textContent='S'; d.title=`Start (${r},${c})`; }
    else if(ch==='G'){ d.classList.add('goal'); d.textContent='G'; d.title=`Goal (${r},${c})`; }
    else if(ch==='#'){ d.classList.add('wall'); d.title=`Wall (${r},${c})`; }
    else { d.classList.add('open'); d.title=`Open (${r},${c})`; }
   grid.appendChild(d); cells.push(d);
  });
 });
 return {grid, cells, cols, size};
}
function renderGrid(maze, path){
 const rows=maze.grid|| (typeof maze==='string'? maze.split('\n').filter(Boolean) : maze.split? maze.split('\n').filter(Boolean): []);
 if(!rows.length) return;
 lastMaze=rows;
 const {cells}=buildGridDOM(rows, 18);
 if(!path||!path.length) return;
 // instant draw (no animation) - used for generate preview
 const pathSet=new Set(path.map(p=>p.join(',')));
 cells.forEach(d=>{
  const key=d.dataset.key;
  if(pathSet.has(key) && !d.classList.contains('start') && !d.classList.contains('goal')){
   d.classList.add('path','revealed');
  }
 });
}
function applyPathProgress(path, upto){
 const grid=document.getElementById('grid');
 if(!grid.children.length) return;
 const pathSet=new Set(path.slice(0, upto).map(p=>p.join(',')));
 // clear old path
 [...grid.children].forEach(d=>{
  if(d.classList.contains('start')||d.classList.contains('goal')) return;
  d.classList.remove('path','revealed','trail');
  // restore terrain class is kept, just remove path
 });
 // add path up to index
 [...grid.children].forEach(d=>{
  const key=d.dataset.key;
  if(pathSet.has(key) && !d.classList.contains('start') && !d.classList.contains('goal')){
   d.classList.add('path');
   // stagger reveal
   setTimeout(()=>d.classList.add('revealed'), 10);
  }
 });
 // mark trail (past agent)
 for(let i=0;i<Math.min(upto, path.length-1);i++){
  const k=path[i].join(',');
  const el=grid.querySelector(`[data-key="${k}"]`);
  if(el) el.classList.add('trail');
 }
}
function applyExploredFrontier(path, explored, upto){
 const grid=document.getElementById('grid');
 if(!grid || !explored) return;
 const pathSet=new Set(path.map(p=>p.join(',')));
 // reset visited/frontier but keep walls/start/goal/path
 [...grid.children].forEach(d=>{
  if(d.classList.contains('start')||d.classList.contains('goal')||d.classList.contains('wall')) return;
  // keep path if already drawn - visited should stay under path
  d.classList.remove('visited','frontier','agent');
  // restore terrain visual: if not path, ensure base class remains (already)
 });
 // color explored up to current
 for(let i=0;i<Math.min(upto, explored.length);i++){
  const [r,c]=explored[i];
  const key=`${r},${c}`;
  if(pathSet.has(key)) continue;
  const el=grid.querySelector(`[data-key="${key}"]`);
  if(!el) continue;
  el.classList.add('visited');
 }
 // frontier = next ~8 nodes that will be explored (lookahead)
 const look=8;
 for(let i=upto;i<Math.min(upto+look, explored.length);i++){
  const [r,c]=explored[i];
  const key=`${r},${c}`;
  if(pathSet.has(key)) continue;
  const el=grid.querySelector(`[data-key="${key}"]`);
  if(el && !el.classList.contains('visited')) el.classList.add('frontier');
 }
 // agent position along path if path exists, otherwise at explored head
 let agentPos=null;
 if(path && path.length){
  // map explored progress to path progress (human walks only on final path after thinking)
  // during exploration phase agent stays at start, then walks path at the end - more human-like: first explore, then walk
  if(upto < explored.length){
   // explorer head
   agentPos=explored[Math.min(upto, explored.length-1)];
  } else {
   const pathIdx = upto - explored.length;
   if(pathIdx>=0 && pathIdx<path.length) agentPos=path[pathIdx];
  }
 } else if(explored.length){
  agentPos=explored[Math.min(upto, explored.length-1)];
 }
 if(agentPos){
  const akey=`${agentPos[0]},${agentPos[1]}`;
  const ael=grid.querySelector(`[data-key="${akey}"]`);
  if(ael) ael.classList.add('agent');
 }
}
function setStatus(state, text){
 const dot=document.getElementById('statusDot');
 const st=document.getElementById('statusText');
 dot.className='status-dot'+(state==='running'?' running': state==='done'?' done':'');
 st.textContent=text;
}
function stopAnimation(){
 if(animTimer){ clearTimeout(animTimer); animTimer=null; }
 document.getElementById('liveBadge').style.display='none';
 isPaused=false; document.getElementById('pauseBtn').textContent='Pause';
}
function animateHuman(path, explored){
 stopAnimation();
 if(!path && !explored) return;
 const speedEl=document.getElementById('speed');
 const doAnimate=document.getElementById('animateToggle').checked;
 const totalSteps = (explored?explored.length:0) + (path?path.length:0) + 6;
 animIndex=0; isPaused=false;
 if(!doAnimate){
  // instant
  if(explored) applyExploredFrontier(path||[], explored, explored.length);
  if(path) applyPathProgress(path, path.length);
  setStatus('done', `Finished — route ${path?path.length-1:0} steps, explored ${explored?explored.length:0} cells.`);
  document.getElementById('progressText').textContent='100%';
  return;
 }
 document.getElementById('liveBadge').style.display='inline-flex';
 setStatus('running','Looking around… checking nearby paths.');
 const gridRows=lastMaze||[];
 // ensure grid built
 if(!document.getElementById('grid').children.length && gridRows.length) buildGridDOM(gridRows, 18);
 function tick(){
  if(isPaused) return;
  const speed=parseInt(speedEl.value)||42;
  const delay = Math.max(8, 120 - speed); // 1->119ms, 100->20ms, human-like variable
  const jitter = (Math.random()*0.4+0.8); // human hesitation
  const actual = delay * jitter;
  const exploredLen=explored?explored.length:0;
  const pathLen=path?path.length:0;
  if(animIndex < exploredLen){
   applyExploredFrontier(path||[], explored, animIndex+1);
   document.getElementById('stepInfo').textContent=`Exploring ${animIndex+1}/${exploredLen}`;
   document.getElementById('progressText').textContent=Math.round((animIndex/totalSteps)*100)+'%';
   // occasional human pause at branches
   if(Math.random()<0.04) {
    setStatus('running','That way is blocked. I’ll try another turn.');
   } else if(animIndex%30===0) setStatus('running','Taking a careful look around.');
   animIndex++;
   animTimer=setTimeout(tick, animIndex < exploredLen-6 ? actual : actual*1.4);
  } else if(animIndex < exploredLen + pathLen){
   const pathIdx=animIndex - exploredLen;
   if(pathIdx===0) setStatus('running','I found a route. Now I’ll walk it.');
   applyExploredFrontier(path, explored, exploredLen);
   applyPathProgress(path, pathIdx+1);
   // agent moves along path
   const pos=path[pathIdx];
   // highlight agent
   const grid=document.getElementById('grid');
   grid.querySelectorAll('.agent').forEach(e=>e.classList.remove('agent'));
   const akey=`${pos[0]},${pos[1]}`;
   const ael=grid.querySelector(`[data-key="${akey}"]`);
   if(ael) ael.classList.add('agent');
   document.getElementById('stepInfo').textContent=`Walking ${pathIdx+1}/${pathLen}`;
   document.getElementById('progressText').textContent=Math.round((animIndex/totalSteps)*100)+'%';
   animIndex++;
   animTimer=setTimeout(tick, actual*1.1);
  } else {
   // done - final polish
   if(path) applyPathProgress(path, path.length);
   setStatus('done', `Made it! ${pathLen?pathLen-1:0} steps walked, ${exploredLen} cells considered like a human would.`);
   document.getElementById('stepInfo').textContent=`Done`;
   document.getElementById('progressText').textContent='100%';
   document.getElementById('liveBadge').style.display='none';
   // add finish sparkle to goal
   const goalEl=document.querySelector('.cell.goal');
   if(goalEl){ goalEl.animate([{transform:'scale(1)'},{transform:'scale(1.28)'},{transform:'scale(1)'}],{duration:520,easing:'ease-out'}); }
  }
 }
 tick();
}
function togglePause(){
 if(!animTimer && !isPaused) return;
 isPaused=!isPaused;
 document.getElementById('pauseBtn').textContent=isPaused?'▶ Resume':'Pause';
 if(!isPaused){
  // resume tick from current index - need to restart loop
  const path=lastPath; const explored=lastExplored;
  // continue from animIndex
  const speedEl=document.getElementById('speed');
  function resumeTick(){
   if(isPaused) return;
   const speed=parseInt(speedEl.value)||42;
   const delay=Math.max(8,120-speed);
   const totalSteps=(explored?explored.length:0)+(path?path.length:0)+6;
   const exploredLen=explored?explored.length:0;
   const pathLen=path?path.length:0;
   if(animIndex < exploredLen){
    applyExploredFrontier(path||[], explored, animIndex+1);
    animIndex++; animTimer=setTimeout(resumeTick, delay);
   } else if(animIndex < exploredLen+pathLen){
    const pathIdx=animIndex-exploredLen;
    applyPathProgress(path, pathIdx+1);
    animIndex++; animTimer=setTimeout(resumeTick, delay);
   } else {
    setStatus('done','Resumed and finished.');
    document.getElementById('liveBadge').style.display='none';
   }
  }
  resumeTick();
 } else {
  if(animTimer) clearTimeout(animTimer);
  setStatus('running','Paused ⏸ — press Resume to continue.');
 }
}
function stepOnce(){
 isPaused=true; document.getElementById('pauseBtn').textContent='▶ Resume';
 if(animTimer) clearTimeout(animTimer);
 const path=lastPath, explored=lastExplored;
 const exploredLen=explored?explored.length:0;
 const pathLen=path?path.length:0;
 if(animIndex < exploredLen){
  applyExploredFrontier(path||[], explored, animIndex+1);
  animIndex++;
 } else if(animIndex < exploredLen+pathLen){
  applyPathProgress(path, animIndex-exploredLen+1);
  animIndex++;
 }
 document.getElementById('stepInfo').textContent=`Step ${animIndex}/${exploredLen+pathLen}`;
}
function replay(){
 if(!lastPath && !lastExplored) { toast('Nothing to replay — solve first.', true); return; }
 animateHuman(lastPath, lastExplored);
}
async function solve(){
 const text=document.getElementById('mazeText').value.trim();
 if(!text){toast('Paste a maze first', true);return;}
 const algo=document.getElementById('algo').value;
 const diagonal=document.getElementById('diagonal').checked;
 document.getElementById('solveBtn').disabled=true; document.getElementById('solveBtn').textContent='⏳ Solving…';
 setStatus('running','Taking a moment to look for a good route…');
 try{
  const res=await fetch('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({grid:text,algorithm:algo,diagonal})}).then(r=>r.json());
  if(res.error){toast(res.error, true); setStatus('','Error: '+res.error); return;}
  lastPath=res.path; lastExplored=res.explored||[]; lastMaze=res.maze.grid;
  // store for animation
  // build grid fresh before anim
  buildGridDOM(res.maze.grid, 18);
  currentPathSet=new Set((res.path||[]).map(p=>p.join(',')));
  document.getElementById('asciiArea').style.display='block';
  document.getElementById('asciiArea').textContent=res.rendered;
  const m=res.metrics;
  document.getElementById('metrics').innerHTML=`<div class="stat"><b>${m.time_ms}ms</b><small>Time</small></div><div class="stat"><b>${m.nodes_expanded}</b><small>Explored</small></div><div class="stat"><b>${m.path_length}</b><small>Steps</small></div><div class="stat"><b>${m.path_cost.toFixed(1)}</b><small>Cost</small></div>`;
  document.getElementById('benchmarkArea').innerHTML=`<p style="color:var(--muted);font-size:.82rem;margin:.6rem 0 0"><span style="color:var(--accent);font-weight:700">${res.algorithm}</span> • Frontier max ${m.max_frontier} • Branching ${m.branching}</p>`;
  document.getElementById('costInfo').textContent=res.path? `Cost ${m.path_cost.toFixed(1)} • ${m.path_length} moves` : 'No path';
  if(!res.path){ toast('I could not find a route through this maze.', true); setStatus('', 'No path — try another maze.'); return; }
  animateHuman(res.path, res.explored||[]);
 } catch(e){ toast(String(e), true); setStatus('', String(e)); }
 finally{ document.getElementById('solveBtn').disabled=false; document.getElementById('solveBtn').textContent='Find a route'; }
}
async function benchmark(){
 const text=document.getElementById('mazeText').value.trim();
 if(!text){toast('Paste a maze first', true);return;}
 setStatus('running','Benchmarking all algorithms…');
 const res=await fetch('/api/benchmark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({grid:text})}).then(r=>r.json());
 if(res.error){toast(res.error,true); setStatus('',res.error);return;}
 let html='<table class="benchmark-table"><tr><th>Algorithm</th><th>Time(ms)</th><th>Expanded</th><th>Frontier</th><th>Steps</th><th>Cost</th></tr>';
 res.results.forEach(r=>{const m=r.metrics;html+=`<tr><td style="text-align:left;padding-left:.7rem">${r.algorithm}</td><td>${m.time_ms}</td><td>${m.nodes_expanded}</td><td>${m.max_frontier}</td><td>${m.path_length}</td><td>${m.path_cost.toFixed?m.path_cost.toFixed(1):m.path_cost}</td></tr>`});
 html+='</table>';
 const maxE=Math.max(...res.results.map(r=>r.metrics.nodes_expanded),1);
 html+='<div class="bars">'+res.results.map(r=>`<div class="bar" style="height:${Math.max(8, (r.metrics.nodes_expanded/maxE)*52)}px" title="${r.algorithm}: ${r.metrics.nodes_expanded}"></div>`).join('')+'</div>';
 const fastest=res.results.reduce((a,b)=>a.metrics.time_ms<b.metrics.time_ms?a:b);
 const fewest=res.results.reduce((a,b)=>a.metrics.nodes_expanded<b.metrics.nodes_expanded?a:b);
 html+=`<p style="color:var(--muted);font-size:.78rem;margin-top:.4rem">⚡ Fastest: <b style="color:var(--accent)">${fastest.algorithm}</b> • 🧠 Fewest expansions: <b style="color:var(--accent)">${fewest.algorithm}</b></p>`;
 document.getElementById('benchmarkArea').innerHTML=html;
 if(res.best_path){ lastPath=res.best_path; lastExplored=null; renderGrid(res.maze,res.best_path); setStatus('done','Benchmark done — showing best path.'); }
 document.getElementById('metrics').innerHTML='';
}
async function generate(){
 const w=clampSize(document.getElementById('genW').value);
 const h=clampSize(document.getElementById('genH').value);
 document.getElementById('genW').value=w; document.getElementById('genH').value=h;
 setStatus('running',`Generating ${w}×${h} maze…`);
 try{
  const res=await fetch(`/api/generate?w=${w}&h=${h}`).then(r=>r.json());
  if(res.error){ toast(res.error, true); return; }
  document.getElementById('mazeText').value=res.grid.join('\n');
  stopAnimation(); renderGrid(res,null);
  document.getElementById('metrics').innerHTML=''; document.getElementById('benchmarkArea').innerHTML='';
  document.getElementById('costInfo').textContent=`${w}×${h} generated`;
  setStatus('','Generated — press Solve & Walk to explore.');
  toast(`Generated ${w}×${h} maze`);
 } catch(e){ toast(String(e),true); }
}

function clearPath(){ stopAnimation(); lastPath=null; lastExplored=null; const t=document.getElementById('mazeText').value; if(t) renderGrid({grid:t.split('\n').filter(Boolean)},null); document.getElementById('metrics').innerHTML=''; document.getElementById('benchmarkArea').innerHTML=''; document.getElementById('stepInfo').textContent='—'; document.getElementById('progressText').textContent=''; setStatus('','Cleared.'); }
// speed label
document.getElementById('speed').addEventListener('input', e=>{ document.getElementById('speedVal').textContent=e.target.value+'ms'; });
// init
document.getElementById('mazeText').value=examples.labyrinth;
solve();
</script>
</body>
</html>
"""

class MazeHandler(BaseHTTPRequestHandler):
    """Translate browser requests into calls to the maze package."""

    server_version = "MazeWalk/1.0"

    def log_message(self, format: str, *args: object) -> None:
        logger.info("%s - %s", self.address_string(), format % args)

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400) -> None:
        code = "server_error" if status >= 500 else "bad_request"
        self.send_json({"error": {"code": code, "message": message}}, status)

    def send_page(self) -> None:
        body = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error_json("Content-Length must be an integer")
            return None
        if length < 0 or length > MAX_REQUEST_BYTES:
            self.send_error_json(f"Request body is limited to {MAX_REQUEST_BYTES} bytes", 413)
            return None
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_error_json("Request body must be valid UTF-8 JSON")
            return None
        if not isinstance(value, dict):
            self.send_error_json("JSON body must be an object")
            return None
        return value

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        try:
            if parsed.path in {"/", "/index.html"}:
                self.send_page()
                return
            if parsed.path == "/api/algorithms":
                self.send_json({"algorithms": list(ALGORITHM_NAMES)})
                return
            if parsed.path == "/api/generate":
                width = odd_size(query.get("w", [25])[0], 25)
                height = odd_size(query.get("h", [15])[0], 15)
                weighted = as_bool(query.get("weighted", [False])[0])
                seed_text = query.get("seed", [None])[0]
                seed = int(seed_text) if seed_text and seed_text.lstrip("-").isdigit() else None
                maze = generate_maze(width, height, weighted=weighted, seed=seed)
                self.send_json({**maze_json(maze), "weighted": weighted})
                return
            self.send_error_json("Not found", 404)
        except Exception:
            logger.exception("GET request failed")
            self.send_error_json("The request could not be completed", 500)

    def do_POST(self) -> None:
        data = self.read_json()
        if data is None:
            return
        try:
            if self.path == "/api/generate":
                maze = generate_maze(
                    odd_size(data.get("width", 25), 25),
                    odd_size(data.get("height", 15), 15),
                    weighted=as_bool(data.get("weighted", False)),
                    seed=data.get("seed"),
                )
                self.send_json({**maze_json(maze), "weighted": as_bool(data.get("weighted", False))})
                return

            grid = data.get("grid")
            if not isinstance(grid, str) or not grid.strip():
                self.send_error_json("grid must be a non-empty string")
                return
            maze = Maze.from_text(grid)

            if self.path == "/api/solve":
                if as_bool(data.get("diagonal", False)):
                    maze = Maze(maze.rows, maze.start, maze.goal, allow_diagonal=True)
                algorithm_name = str(data.get("algorithm", "astar-manhattan"))
                algorithm = make_algorithm(algorithm_name)
                path, metrics = algorithm.solve(maze.start, maze.goal, maze=maze)
                solution = Solution(tuple(path), cost=metrics.path_cost) if path else None
                explored = getattr(metrics, "explored_order", None) or getattr(metrics, "visited", []) or []
                self.send_json({
                    "algorithm": algorithm_name,
                    "path": [[point.row, point.column] for point in path] if path else None,
                    "explored": [[point.row, point.column] for point in explored],
                    "metrics": metrics.as_dict(),
                    "rendered": render(maze, solution),
                    "maze": maze_json(maze),
                })
                return

            if self.path == "/api/benchmark":
                results = run_benchmark_suite([make_algorithm(name) for name in ALGORITHM_NAMES], maze)
                best = min(results, key=lambda item: item.metrics.path_cost if item.path else float("inf"))
                self.send_json({
                    "results": [
                        {"algorithm": result.algorithm_name,
                         "path": [[point.row, point.column] for point in result.path] if result.path else None,
                         "metrics": result.metrics.as_dict()}
                        for result in results
                    ],
                    "best_path": [[point.row, point.column] for point in best.path] if best.path else None,
                    "maze": maze_json(maze),
                })
                return

            self.send_error_json("Not found", 404)
        except (ValueError, TypeError) as error:
            self.send_error_json(str(error))
        except Exception:
            logger.exception("POST request failed")
            self.send_error_json("The request could not be completed", 500)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        server = ThreadingHTTPServer((host, port), MazeHandler)
    except OSError as exc:
        msg = f"Failed to start Maze Walk on {host}:{port}: {exc}"
        print(msg)
        logger.error(msg)
        raise SystemExit(1) from exc
    url = f"http://{host}:{port}"
    print(f"Maze Walk is running at {url}", flush=True)
    print("Press Ctrl+C to stop", flush=True)
    logger.info("Maze Walk is running at %s", url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Maze Walk...", flush=True)
        logger.info("Stopping Maze Walk")
    finally:
        server.server_close()


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run the Maze Walk browser app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()
    run_server(arguments.host, arguments.port)
