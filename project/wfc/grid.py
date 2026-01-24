import uuid
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

import numpy as np

from project.config import HIDDEN_CELL
from project.wfc.direction import Direction
from project.wfc.pattern import MetaPattern
from project.wfc.repository import Repository


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y


@dataclass(frozen=True)
class Rect:
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Width and height must be positive, got width={self.width}, height={self.height}")

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
    ) -> None:
        self.width = rect.width
        self.height = rect.height
        self.patterns = patterns
        self.initialize()

    @property
    def center(self) -> tuple[int, int]:
        return self.width // 2, self.height // 2

    @property
    def is_collapsed(self) -> bool:
        """Check if the entire grid has been filled with patterns."""
        return not np.any(self.grid == None)

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
        self.grid = np.full((self.height, self.width), None, dtype=object)
        self.entropy = np.full((self.height, self.width), len(self.patterns), dtype=int)

    def iter_cells(self):
        for x in range(self.height):
            for y in range(self.width):
                yield x, y, self.grid[x, y]

    @staticmethod
    def get_patterns_property(
        patterns: np.ndarray,
        property_func: Callable[[MetaPattern], Any] = lambda pattern: pattern.uid
    ) -> np.ndarray:
        vectorized_func = np.vectorize(
            lambda p: property_func(p) if p is not None else HIDDEN_CELL,
            otypes=[object]
        )
        return vectorized_func(patterns)

    def is_empty_point(self, point: Point) -> bool:
        return self.grid[point.x, point.y] is None

    def in_grid_bounds(self, point: Point) -> bool:
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
        uncollapsed_mask = self.entropy > 0
        if not np.any(uncollapsed_mask):
            return None
        
        min_entropy = np.min(self.entropy[uncollapsed_mask])
        min_entropy_cells = np.argwhere(self.entropy == min_entropy)
        
        if len(min_entropy_cells) == 1:
            x, y = min_entropy_cells[0]
            return Point(x=x, y=y)
        
        center_array = np.array(self.center)
        distances = np.linalg.norm(min_entropy_cells - center_array, axis=1)
        closest_idx = np.argmin(distances)
        x, y = min_entropy_cells[closest_idx]
        return Point(x=x, y=y)

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

    def get_any_collapsed_neighbor(self, p: Point) -> Point | None:
        for neighbor_point in self.get_neighbors(p=p):
            if not self.is_empty_point(point=neighbor_point):
                return neighbor_point
        return None

    def get_valid_patterns(
        self, p: Point, depth: int = 0, max_depth: int = 1
    ) -> set[MetaPattern]:
        possible_patterns = set(self.patterns)

        for neighbor_point, direction in self.get_neighbors(p=p, add_direction=True):
            if self.is_empty_point(point=neighbor_point):
                if depth >= max_depth:
                    continue
                neighbor_possible_patterns = self.get_valid_patterns(
                    neighbor_point, depth=depth + 1, max_depth=max_depth
                )
                allowed_patterns = set()
                for potential_pattern in neighbor_possible_patterns:
                    allowed_patterns.update(
                        potential_pattern.rules.get_allowed_neighbors(direction)
                    )
            else:
                neighbor_pattern = self.grid[neighbor_point.x, neighbor_point.y]
                allowed_patterns = neighbor_pattern.rules.get_allowed_neighbors(
                    direction
                )

            possible_patterns = possible_patterns.intersection(allowed_patterns)

        return possible_patterns

    def place_pattern(self, p: Point, pattern: MetaPattern) -> None:
        """Place a pattern in the grid at the specified position."""
        self.grid[p.x, p.y] = pattern
        self.entropy[p.x, p.y] = 0

    def reset_point(self, p: Point) -> None:
        """Reset the specified point to None."""
        self.grid[p.x, p.y] = None
        self.entropy[p.x, p.y] = len(self.patterns)
        collapsed_neighbors = self.get_any_collapsed_neighbor(p)
        self.update_entropy(p)
        if collapsed_neighbors:
            self.update_entropy(collapsed_neighbors)

    def update_entropy(self, p: Point) -> None:
        queue = deque(self.get_neighbors(p))
        visited = {p}

        while queue:
            current_point = queue.popleft()
            if not self.is_empty_point(current_point):
                continue

            old_entropy = self.entropy[current_point.x, current_point.y]
            new_entropy = len(self.get_valid_patterns(current_point))

            if old_entropy == new_entropy:
                continue

            self.entropy[current_point.x, current_point.y] = new_entropy
            for neighbor in self.get_neighbors(current_point):
                if neighbor not in visited:
                    queue.append(neighbor)
                    visited.add(neighbor)

    def serialize(
        self,
        path: str | Path,
        name: str | None = None,
        property_func: Callable[[MetaPattern], Any] = lambda pattern: pattern.uid,
    ) -> None:
        """
        Serialize the grid to a file, saving a specific property of each pattern.
        NB: serialization with aim to further deserialization can be done only with uid.
        """
        if name is None:
            name = str(uuid.uuid4())

        output_path = Path(path) / f"{name}.dat"
        properties = self.get_patterns_property(
            property_func=property_func, patterns=self.grid
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            for row in properties:
                f.write(",".join(map(str, row)) + "\n")

    def deserialize(self, repository: Repository, path: str | Path) -> None:
        """
        Deserialize a file to reconstruct the grid.
        NB: works by uid.
        """
        file_path = Path(path)
        grid = []
        with file_path.open("r") as f:
            for line in f:
                row = [
                    repository.get_pattern_by_uid(int(value))
                    if int(value) != HIDDEN_CELL else None
                    for value in line.strip().split(",")
                ]
                grid.append(row)
        self.grid = np.array(grid, dtype=object)
        self.height = len(grid)
        self.width = len(grid[0]) if grid else 0

    def __str__(self) -> str:
        """Custom string representation of the grid showing uids or 'None'."""
        return "\n".join(
            " | ".join(f"{cell.uid:03}" if cell else "-01" for cell in row)
            for row in self.grid
        )
