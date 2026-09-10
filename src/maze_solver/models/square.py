from dataclasses import dataclass

from .role import Role
from .terrain import TerrainType


@dataclass(frozen=True, order=True)
class Square:
    row: int
    column: int
    role: Role = Role.OPEN
    terrain: TerrainType = TerrainType.GRASS

    @property
    def position(self) -> tuple[int, int]:
        return self.row, self.column

    @property
    def walkable(self) -> bool:
        if self.role == Role.WALL:
            return False
        return self.terrain.is_passable()

    @property
    def cost(self) -> float:
        """Cost to ENTER this square (derived from terrain)."""
        if not self.walkable:
            return float("inf")
        return self.terrain.cost
