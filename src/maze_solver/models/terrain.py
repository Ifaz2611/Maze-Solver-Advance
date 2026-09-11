"""Terrain definitions - simplified to unweighted exploration only."""

from __future__ import annotations

from enum import Enum


class TerrainType(Enum):
    """Only open ground and walls - no weighted terrain."""

    GRASS = 1
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
        # Back-compat: old terrain chars (., m, w, etc.) all map to GRASS
        if char in _CHAR_TO_TERRAIN:
            return _CHAR_TO_TERRAIN[char]
        raise ValueError(f"Unknown terrain character: {char!r}")

    def is_passable(self) -> bool:
        return self is not TerrainType.WALL


_TERRAIN_TO_CHAR: dict[TerrainType, str] = {
    TerrainType.GRASS: " ",
    TerrainType.WALL: "#",
}

# All walkable chars map to GRASS (back-compat for old weighted mazes)
_CHAR_TO_TERRAIN: dict[str, TerrainType] = {
    " ": TerrainType.GRASS,
    "g": TerrainType.GRASS,
    "G": TerrainType.GRASS,
    ".": TerrainType.GRASS,
    "d": TerrainType.GRASS,
    "m": TerrainType.GRASS,
    "M": TerrainType.GRASS,
    "w": TerrainType.GRASS,
    "W": TerrainType.GRASS,
    "#": TerrainType.WALL,
}

TERRAIN_COSTS: dict[TerrainType, float] = {t: t.cost for t in TerrainType}
