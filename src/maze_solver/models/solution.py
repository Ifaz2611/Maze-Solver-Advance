from dataclasses import dataclass

from .square import Square


@dataclass(frozen=True)
class Solution:
    path: tuple[Square, ...]
    cost: float | None = None

    @property
    def length(self) -> int:
        return max(0, len(self.path) - 1)

    @property
    def total_cost(self) -> float:
        if self.cost is not None:
            return self.cost
        # fallback: sum terrain costs (grass=1) excluding start
        return float(max(0, len(self.path) - 1))
