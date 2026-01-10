from enum import Enum, auto


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

    @property
    def _vector(self):
        vectors = {
            Direction.UP: (1, 0),
            Direction.DOWN: (-1, 0),
            Direction.LEFT: (0, 1),
            Direction.RIGHT: (0, -1),
        }
        return vectors[self]
    
    @property
    def dx(self):
        return self._vector[0]

    @property
    def dy(self):
        return self._vector[1]

    @property
    def opposite(self) -> "Direction":
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }
        return opposites[self]
