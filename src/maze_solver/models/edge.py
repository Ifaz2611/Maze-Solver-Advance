from dataclasses import dataclass

from .square import Square


@dataclass(frozen=True)
class Edge:
    source: Square
    target: Square
    weight: float = 1.0

    def __post_init__(self) -> None:
        # If weight not explicitly set but target has terrain cost, derive it
        if self.weight == 1.0 and hasattr(self.target, "cost"):
            # Only override if target cost differs from 1.0 ; keep explicit 1.0 for unweighted
            # Use object.__setattr__ because dataclass is frozen
            target_cost = float(self.target.cost)
            if target_cost != 1.0 and target_cost != float("inf"):
                object.__setattr__(self, "weight", target_cost)
