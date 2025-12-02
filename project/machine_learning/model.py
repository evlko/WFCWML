from abc import ABC, abstractmethod
from enum import Enum, auto


class ModelMode(Enum):
    TRAINIG = auto()
    EVALUATION = auto()


class Model(ABC):
    @abstractmethod
    def save_weights(self, filename: str) -> None:
        pass

    @abstractmethod
    def load_weights(self, filename: str) -> None:
        pass
