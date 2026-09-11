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
        return self.role != Role.WALL

    @property
    def cost(self) -> float:
        """Cost to ENTER this square - uniform 1 for exploration."""
        if not self.walkable:
            return float("inf")
        return 1.0
