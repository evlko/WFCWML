from dataclasses import dataclass, field

from project.wfc.direction import Direction
from project.wfc.pattern import MetaPattern


@dataclass
class NeighborRuleSet:
    allowed_up: set[MetaPattern] = field(default_factory=set)
    allowed_down: set[MetaPattern] = field(default_factory=set)
    allowed_left: set[MetaPattern] = field(default_factory=set)
    allowed_right: set[MetaPattern] = field(default_factory=set)

    def __post_init__(self):
        self.allowed_neighbors: dict[Direction, set[MetaPattern]] = {
            Direction.UP: self.allowed_up,
            Direction.RIGHT: self.allowed_right,
            Direction.DOWN: self.allowed_down,
            Direction.LEFT: self.allowed_left,
        }

    def get_allowed_neighbors(
        self, direction: Direction | None = None
    ) -> set[MetaPattern] | dict[Direction, set[MetaPattern]]:
        """Returns allowed neighbors for a given direction or all directions if none specified."""
        if direction is None:
            return self.allowed_neighbors.values()
        return self.allowed_neighbors.get(direction, set())
