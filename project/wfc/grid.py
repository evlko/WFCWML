import uuid
from collections import deque
from dataclasses import dataclass

import numpy as np

from project.config import HIDDEN_CELL
from project.wfc.direction import Direction
from project.wfc.pattern import MetaPattern
from project.wfc.repository import Repository


@dataclass
class Point:
    x: int
    y: int

    @property
    def key(self) -> str:
        return f"{self.x},{self.y}"


@dataclass
class Rect:
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def indices(self) -> list[tuple[int, int]]:
        return [(i, j) for i in range(self.height) for j in range(self.width)]

    @property
    def center(self) -> tuple[int, int]:
        return self.width // 2, self.height // 2


class Grid:
    def __init__(
        self, patterns: list[MetaPattern], rect: Rect = Rect(width=3, height=3)
    ):
        self.width = rect.width
        self.height = rect.height
        self.patterns = patterns
        self.initialize()

    @property
    def is_collapsed(self) -> bool:
        """Check if the entire grid has been filled."""
        return np.all(self.grid != None)

    @property
    def zero_entropy_cell(self) -> None | Point:
        """Return the first cell with zero entropy, or None if none exist."""
        zero_entropy_mask = self.entropy == 0
        uncollapsed_mask = self.grid == None
        problematic_cells = np.argwhere(zero_entropy_mask & uncollapsed_mask)

        if problematic_cells.size > 0:
            x, y = problematic_cells[0]
            return Point(x=x, y=y)
        return None

    def initialize(self) -> None:
        """Initialize or reset the grid with full entropy in all cells."""
        self.grid = np.full((self.height, self.width), None)
        self.entropy = np.full((self.height, self.width), len(self.patterns))

    def iterate_cells(self):
        for x in range(self.height):
            for y in range(self.width):
                yield x, y, self.grid[x, y]

    @staticmethod
    def get_patterns_property(
        patterns: np.ndarray, property_func: callable = lambda pattern: pattern.uid
    ) -> np.ndarray:
        properties = np.array(
            [
                [property_func(pattern) if pattern else HIDDEN_CELL for pattern in row]
                for row in patterns
            ]
        )
        return properties

    def is_empty_point(self, point: Point) -> bool:
        """Check if the specified point is empty."""
        return self.grid[point.x, point.y] is None

    def in_grid_bounds(self, point: Point) -> bool:
        """Check if the specified point is within the grid bounds."""
        return 0 <= point.x < self.height and 0 <= point.y < self.width

    def get_patterns_around_point(
        self,
        point: Point,
        view: Rect = Rect(width=3, height=3),
        is_extended: bool = True,
    ) -> list[MetaPattern | None]:
        """Get patterns within a rectangular region around a specified point (x, y)."""
        cx, cy = view.center

        if is_extended:
            proxy_grid = np.full(
                (self.height + 2 * cy, self.width + 2 * cx),
                None,
                dtype=object,
            )
            proxy_grid[
                cy : cy + self.height,
                cx : cx + self.width,
            ] = self.grid
            x_max, y_max = point.x + view.height, point.y + view.width
            return proxy_grid[point.x : x_max, point.y : y_max]

        x_min, x_max = max(0, point.x - cy), min(self.height, point.x + cy + 1)
        y_min, y_max = max(0, point.y - cx), min(self.width, point.y + cx + 1)
        return self.grid[y_min:y_max, x_min:x_max]

    def find_least_entropy_cell(self) -> Point | None:
        """Find the cell with the lowest entropy. If multiple, choose closest to center."""
        candidates = self.entropy[self.entropy > 0]
        if len(candidates) == 0:
            return None
        min_entropy = np.min(candidates)
        candidates = np.argwhere(self.entropy == min_entropy)
        center = np.array([self.height // 2, self.width // 2])
        distances = np.linalg.norm(candidates - center, axis=1)
        closest_index = np.argmin(distances)
        candidate_y, candidate_x = candidates[closest_index]
        return Point(x=candidate_y, y=candidate_x)

    def get_neighbors(
        self, p: Point, add_direction: bool = False
    ) -> list[tuple[Point, Direction]] | list[Point]:
        """Get neighbors and their directions for the cell (x, y)."""
        neighbors = []
        for direction in Direction:
            neighbor = Point(p.x + direction.dx, p.y + direction.dy)
            if self.in_grid_bounds(neighbor):
                neighbors.append((neighbor, direction) if add_direction else neighbor)
        return neighbors

    def get_valid_patterns(self, p: Point) -> set[MetaPattern]:
        possible_patterns = set(self.patterns)

        for neighbor_point, direction in self.get_neighbors(p=p, add_direction=True):
            if self.is_empty_point(point=neighbor_point):
                continue
            neighbor_pattern = self.grid[neighbor_point.x, neighbor_point.y]
            allowed_patterns = neighbor_pattern.rules.get_allowed_neighbors(direction)
            possible_patterns = possible_patterns.intersection(allowed_patterns)

        return possible_patterns

    def place_pattern(self, p: Point, pattern: MetaPattern) -> None:
        """Place a pattern in the grid at the specified position."""
        self.grid[p.x, p.y] = pattern
        self.entropy[p.x, p.y] = 0

    def update_entropy(self, p: Point) -> None:
        """Update the entropy cascade"""
        queue = deque(self.get_neighbors(p))
        visited = {p.key}

        while queue:
            current_point = queue.popleft()
            if current_point.key in visited:
                continue
            visited.add(p.key)

            if not self.is_empty_point(current_point):
                continue

            entropy = len(self.get_valid_patterns(current_point))
            self.entropy[current_point.x, current_point.y] = entropy

    def serialize(
        self,
        path: str,
        name: str | None = None,
        property_func: callable = lambda pattern: pattern.uid,
    ) -> None:
        """
        Serialize the grid to a file, saving a specific property of each pattern.
        NB: serialization with aim to further deserialization can be done only with uid.
        """
        if name is None:
            name = str(uuid.uuid4())

        properties = self.get_patterns_property(
            property_func=property_func, patterns=self.grid
        )

        with open(f"{path}{name}.dat", "w") as f:
            for row in properties:
                f.write(",".join(map(str, row)) + "\n")

    def deserialize(self, repository: Repository, path: str) -> None:
        """
        Deserialize a file to reconstruct the grid.
        NB: works by uid.
        """
        grid = []
        with open(path, "r") as f:
            for line in f:
                row = [
                    repository.get_pattern_by_uid(int(value)) if value != -1 else None
                    for value in line.strip().split(",")
                ]
                grid.append(row)
        self.grid = np.array(grid)
        self.height = len(grid)
        self.width = len(grid[0])

    def __str__(self) -> str:
        """Custom string representation of the grid showing uids or 'None'."""
        return "\n".join(
            " | ".join(f"{cell.uid:03}" if cell else "-01" for cell in row)
            for row in self.grid
        )
