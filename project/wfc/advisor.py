import random
from abc import ABC, abstractmethod

from project.utils.utils import Utils
from project.wfc.grid import Grid, Point, Rect
from project.wfc.wobj import WeightedObject


class Advisor(ABC):
    """Advisor selects which tile to place during WFC process."""

    def __init__(self, seed: int | None = None, view: Rect = Rect(1, 1)):
        self.seed = seed
        self.view = view
        random.seed(seed)

    @abstractmethod
    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        """Select a tile from available options."""
        pass


class RandomAdvisor(Advisor):
    """Advisor that selects tiles randomly based on their weights."""

    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        return Utils.weighted_choice(objects=objects, seed=self.seed)


class GreedyAdvisor(Advisor):
    """Advisor that always selects the tile with the highest weight."""

    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        return max(objects, key=lambda obj: obj.weight)
