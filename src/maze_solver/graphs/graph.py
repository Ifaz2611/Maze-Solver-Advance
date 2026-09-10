"""Explicit graph representation for weighted mazes."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models.edge import Edge
from ..models.square import Square


@dataclass
class Graph:
    """Adjacency-list graph with weighted edges."""

    adjacency: dict[Square, tuple[Edge, ...]] = field(default_factory=dict)

    def neighbors(self, square: Square) -> tuple[Edge, ...]:
        return self.adjacency.get(square, ())

    def nodes(self) -> tuple[Square, ...]:
        return tuple(self.adjacency.keys())

    def add_edge(self, edge: Edge) -> None:
        lst = list(self.adjacency.get(edge.source, ()))
        lst.append(edge)
        self.adjacency[edge.source] = tuple(lst)
        # ensure target node exists even if it has no outgoing edges yet
        if edge.target not in self.adjacency:
            self.adjacency.setdefault(edge.target, ())

    def weight(self, source: Square, target: Square) -> float:
        for edge in self.adjacency.get(source, ()):
            if edge.target == target:
                return edge.weight
        raise KeyError(f"No edge from {source} to {target}")

    def __len__(self) -> int:
        return len(self.adjacency)

    def edge_count(self) -> int:
        return sum(len(v) for v in self.adjacency.values())
