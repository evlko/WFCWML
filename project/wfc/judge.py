import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto

from project.utils.utils import Utils
from project.wfc.grid import Grid, Point, Rect
from project.wfc.wobj import WeightedObject


class ActionType(StrEnum):
    PLACE = auto()
    ROLLBACK = auto()


@dataclass
class ActionData(ABC):
    pass


@dataclass
class PlaceActionData(ActionData):
    object: WeightedObject


@dataclass
class RollbackActionData(ActionData):
    steps: int


@dataclass
class Action:
    type: ActionType
    data: ActionData


class Judge(ABC):
    def __init__(self, seed: int | None = None, view: Rect = Rect(1, 1)):
        self.seed = seed
        self.view = view
        random.seed(seed)

    @abstractmethod
    def act(self, objects: list[WeightedObject], grid: Grid, point: Point) -> Action:
        pass

    @abstractmethod
    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        pass


class RandomJudge(Judge):
    def __init__(self, seed: int | None = None, rollback_chance: float = 0):
        super().__init__(seed)
        self.rollback_chance = rollback_chance

    def act(self, objects: list[WeightedObject], grid: Grid, point: Point) -> Action:
        if random.random() < self.rollback_chance:
            return Action(type=ActionType.ROLLBACK, data=RollbackActionData(steps=1))
        return Action(
            type=ActionType.PLACE,
            data=PlaceActionData(object=self.select(objects, grid, point)),
        )

    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        return Utils.weighted_choice(objects=objects, seed=self.seed)


class GreedyJudge(Judge):
    def __init__(self, seed: int | None = None, rollback_chance: float = 0):
        super().__init__(seed)
        self.rollback_chance = rollback_chance

    def act(self, objects: list[WeightedObject], grid: Grid, point: Point) -> Action:
        if random.random() < self.rollback_chance:
            return Action(type=ActionType.ROLLBACK, data=RollbackActionData(steps=1))
        return Action(
            type=ActionType.PLACE,
            data=PlaceActionData(object=self.select(objects, grid, point)),
        )

    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        return max(objects, key=lambda obj: obj.weight)
