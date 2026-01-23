import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto

from project.wfc.grid import Grid, Rect


class DecisionType(StrEnum):
    CONTINUE = auto()
    ROLLBACK = auto()
    STOP = auto()


@dataclass
class DecisionData(ABC):
    pass


@dataclass
class ContinueDecisionData(DecisionData):
    pass


@dataclass
class RollbackDecisionData(DecisionData):
    steps: int


@dataclass
class StopDecisionData(DecisionData):
    reason: str = "Judge decided to stop"


@dataclass
class Decision:
    type: DecisionType
    data: DecisionData


class Judge(ABC):
    """Judge decides whether to continue, rollback, or stop during WFC process."""

    def __init__(self, seed: int | None = None, view: Rect = Rect(1, 1)):
        self.seed = seed
        self.view = view
        random.seed(seed)

    @abstractmethod
    def decide(self, grid: Grid) -> Decision:
        """Decide whether to continue, rollback, or stop."""
        pass


# Judge implementations
class RandomJudge(Judge):
    """Judge that randomly decides to rollback based on a probability."""

    def __init__(self, seed: int | None = None, rollback_chance: float = 0):
        super().__init__(seed)
        self.rollback_chance = rollback_chance

    def decide(self, grid: Grid) -> Decision:
        if random.random() < self.rollback_chance:
            return Decision(
                type=DecisionType.ROLLBACK, data=RollbackDecisionData(steps=1)
            )
        return Decision(type=DecisionType.CONTINUE, data=ContinueDecisionData())


class AlwaysContinueJudge(Judge):
    """Judge that always decides to continue."""

    def decide(self, grid: Grid) -> Decision:
        return Decision(type=DecisionType.CONTINUE, data=ContinueDecisionData())
