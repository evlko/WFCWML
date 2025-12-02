from abc import ABC, abstractmethod

from project.utils.utils import Utils
from project.wfc.grid import Grid, Rect, Point
from project.wfc.wobj import WeightedObject


class Judge(ABC):
    def __init__(self, seed: int | None = None, view: Rect = Rect(1, 1)):
        self.seed = seed
        self.view = view

    @abstractmethod
    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        pass


class RandomJudge(Judge):
    def __init__(self, seed: int | None = None):
        super().__init__(seed)

    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        return Utils.weighted_choice(objects=objects, seed=self.seed)


class GreedyJudge(Judge):
    def __init__(self, seed: int | None = None):
        super().__init__(seed)

    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        return max(objects, key=lambda obj: obj.weight)
