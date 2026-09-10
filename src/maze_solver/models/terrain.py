"""Terrain definitions for weighted pathfinding."""

from __future__ import annotations

from enum import Enum


class TerrainType(Enum):
    """Terrain with movement cost. WALL is impassable (inf)."""

    GRASS = 1
    DIRT = 2
    MUD = 5
    WATER = 10
    WALL = float("inf")

    @property
    def cost(self) -> float:
        return float(self.value)

    @property
    def char(self) -> str:
        return _TERRAIN_TO_CHAR[self]

    @property
    def label(self) -> str:
        return self.name.lower()

    @classmethod
    def from_char(cls, char: str) -> "TerrainType":
        try:
            return _CHAR_TO_TERRAIN[char]
        except KeyError as exc:
            raise ValueError(f"Unknown terrain character: {char!r}") from exc

    def is_passable(self) -> bool:
        return self is not TerrainType.WALL


_TERRAIN_TO_CHAR: dict[TerrainType, str] = {
    TerrainType.GRASS: " ",
    TerrainType.DIRT: ".",
    TerrainType.MUD: "m",
    TerrainType.WATER: "w",
    TerrainType.WALL: "#",
}

# Extended aliases -- allow multiple chars per terrain for file flexibility
_CHAR_TO_TERRAIN: dict[str, TerrainType] = {
    " ": TerrainType.GRASS,
    "g": TerrainType.GRASS,
    "G": TerrainType.GRASS,  # careful: G also used for GOAL role; handled separately
    ".": TerrainType.DIRT,
    "d": TerrainType.DIRT,
    "m": TerrainType.MUD,
    "M": TerrainType.MUD,
    "w": TerrainType.WATER,
    "W": TerrainType.WATER,
    "#": TerrainType.WALL,
}

# Cost lookup for weighted expansion rate
TERRAIN_COSTS: dict[TerrainType, float] = {t: t.cost for t in TerrainType}
