import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto

from project.wfc.grid import Grid


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


CONTINUE_DECISION = Decision(DecisionType.CONTINUE, ContinueDecisionData())


class Judge(ABC):
    """Judge decides whether to continue, rollback, or stop during WFC process."""

    def __init__(self, seed: int | None = None, rollback_penalty: int = 1):
        self.seed = seed
        self.rollback_penalty = rollback_penalty
        random.seed(seed)

    @abstractmethod
    def decide(self, grid: Grid) -> Decision:
        """Decide whether to continue, rollback, or stop."""
        pass


class RandomJudge(Judge):
    """Judge that randomly decides to rollback based on a probability."""

    def __init__(
        self,
        seed: int | None = None,
        rollback_chance: float = 0,
        rollback_penalty: int = 1,
    ):
        super().__init__(seed, rollback_penalty)
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
