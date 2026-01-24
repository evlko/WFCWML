from catboost import CatBoostClassifier

from project.machine_learning.model import Model
from project.wfc.grid import Grid
from project.wfc.judge import Decision, Judge


class CatboostJudge(Model, Judge):
    def __init__(
        self,
        seed: int | None = None,
        rollback_threshold: float = 0,
        rollback_penalty: int = 1,
        weights: str | None = None,
    ):
        super().__init__(seed, rollback_penalty)
        self.rollback_threshold = rollback_threshold
        self._model = CatBoostClassifier()
        if weights is not None:
            self.load_weights(weights)

    def decide(self, grid: Grid) -> Decision:
        pass

    def load_weights(self, filename: str) -> None:
        self._model.load_model(filename)

    def save_weights(self, filename: str) -> None:
        pass
