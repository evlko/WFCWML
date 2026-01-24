import numpy as np
from catboost import CatBoostClassifier

from project.machine_learning.model import Model
from project.wfc.grid import Grid
from project.wfc.judge import (
    ContinueDecisionData,
    Decision,
    DecisionType,
    Judge,
    RollbackDecisionData,
)


class CatboostJudge(Model, Judge):
    FEATURE_NAMES = [
        "entropy_mean",
        "entropy_std",
        "p_collapsed",
        "p_uncollapsed",
        "p_walkable_collapsed",
        "p_entropy_1",
        "p_entropy_2",
        "p_entropy_3",
        "entropy_gradient_mean",
        "entropy_gradient_max",
    ]

    def __init__(
        self,
        seed: int | None = None,
        rollback_threshold: float = 0.5,
        rollback_penalty: int = 1,
        weights: str | None = None,
    ):
        super().__init__(seed, rollback_penalty)
        self.rollback_threshold = rollback_threshold
        self._model = CatBoostClassifier()
        if weights is not None:
            self.load_weights(weights)

    def _extract_features(self, grid: Grid) -> np.ndarray:
        entropies = grid.entropy.astype(float).flatten()
        n_cells = grid.width * grid.height

        walkable = np.array(
            [
                cell.is_walkable if cell is not None else np.nan
                for cell in grid.grid.flatten()
            ],
            dtype=float,
        )

        features = {}

        features["entropy_mean"] = np.nanmean(entropies)
        features["entropy_std"] = np.nanstd(entropies)

        features["p_collapsed"] = np.sum(entropies == 0) / n_cells
        features["p_uncollapsed"] = np.sum(entropies > 1) / n_cells

        collapsed_mask = entropies == 0
        if np.any(collapsed_mask):
            walkable_collapsed = walkable[collapsed_mask]
            features["p_walkable_collapsed"] = np.nansum(walkable_collapsed == 1) / np.sum(
                collapsed_mask
            )
        else:
            features["p_walkable_collapsed"] = 0.0

        for k in [1, 2, 3]:
            features[f"p_entropy_{k}"] = np.sum(entropies == k) / n_cells

        entropy_grid = grid.entropy.astype(float)
        grad_y = np.abs(np.diff(entropy_grid, axis=0))
        grad_x = np.abs(np.diff(entropy_grid, axis=1))
        all_gradients = np.concatenate([grad_x.flatten(), grad_y.flatten()])

        features["entropy_gradient_mean"] = np.nanmean(all_gradients)
        features["entropy_gradient_max"] = np.nanmax(all_gradients)

        return np.array([features[name] for name in self.FEATURE_NAMES]).reshape(1, -1)

    def decide(self, grid: Grid) -> Decision:
        features = self._extract_features(grid)

        probabilities = self._model.predict_proba(features)
        # Class 1 = should_continue (success), Class 0 = should NOT continue (failure)
        continue_probability = probabilities[0, 1]

        if continue_probability >= self.rollback_threshold:
            return Decision(type=DecisionType.CONTINUE, data=ContinueDecisionData())
        return Decision(
            type=DecisionType.ROLLBACK, data=RollbackDecisionData(steps=1)
        )

    def load_weights(self, filename: str) -> None:
        self._model.load_model(filename)

    def save_weights(self, filename: str) -> None:
        self._model.save_model(filename)
