from catboost import CatBoostClassifier

from project.machine_learning.judges.judge import BaseMLJudge


class CatboostJudge(BaseMLJudge):
    def __init__(
        self,
        seed: int | None = None,
        rollback_threshold: float = 0.5,
        rollback_penalty: int = 1,
        weights: str | None = None,
    ):
        super().__init__(seed, rollback_threshold, rollback_penalty)
        self._model = CatBoostClassifier()
        if weights is not None:
            self.load_weights(weights)

    def load_weights(self, filename: str) -> None:
        self._model.load_model(filename)

    def save_weights(self, filename: str) -> None:
        self._model.save_model(filename)
