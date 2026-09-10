from collections.abc import Iterable

from ..models.square import Square


def path_positions(path: Iterable[Square]) -> frozenset[tuple[int, int]]:
    return frozenset(square.position for square in path)
