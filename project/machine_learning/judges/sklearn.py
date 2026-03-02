import joblib
from sklearn.base import BaseEstimator, ClassifierMixin

from project.machine_learning.judges.judge import BaseMLJudge


class SklearnJudge(BaseMLJudge):
    def __init__(
        self,
        seed: int | None = None,
        rollback_threshold: float = 0.5,
        rollback_penalty: int = 1,
        weights: str | None = None,
        model: BaseEstimator | ClassifierMixin | None = None,
    ):
        super().__init__(seed, rollback_threshold, rollback_penalty)
        self._model = model
        if weights is not None:
            self.load_weights(weights)

    def load_weights(self, filename: str) -> None:
        self._model = joblib.load(filename)

    def save_weights(self, filename: str) -> None:
        joblib.dump(self._model, filename)
