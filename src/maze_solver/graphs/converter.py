from collections.abc import Mapping

from ..models.edge import Edge
from ..models.maze import Maze
from ..models.square import Square
from .graph import Graph


def to_graph(maze: Maze) -> Mapping[Square, tuple[Edge, ...]]:
    """Convert walkable maze squares to an adjacency mapping (legacy dict form)."""
    return {
        square: tuple(Edge(square, neighbor, weight=1.0) for neighbor in maze.neighbors(square))
        for row in maze.rows
        for square in row
        if square.walkable
    }


def to_weighted_graph(maze: Maze) -> Graph:
    """Convert maze to explicit Graph - uniform cost 1 for exploration."""
    graph = Graph()
    for row in maze.rows:
        for square in row:
            if not square.walkable:
                continue
            if square not in graph.adjacency:
                graph.adjacency[square] = ()
            for neighbor in maze.neighbors(square):
                edge = Edge(square, neighbor, weight=1.0)
                graph.add_edge(edge)
    return graph
