import pickle
from copy import copy

import numpy as np
from sklearn.base import BaseEstimator

from project.machine_learning.model import Model
from project.utils.utils import Utils
from project.wfc.advisor import Advisor
from project.wfc.grid import Grid, Point, Rect
from project.wfc.wobj import WeightedObject


class ClassifierAdvisor(Model, Advisor):
    def __init__(
        self,
        seed: int | None = None,
        view: Rect = Rect(3, 3),
        threshold: float = 0.5,
        rebalance: bool = False,
    ):
        super().__init__(view=view, seed=seed)
        self._threshold = threshold
        self._rebalance = rebalance
        self._model: BaseEstimator | None = None

    def _get_prediction_value(self, features: np.ndarray) -> float:
        if hasattr(self._model, "predict_proba"):
            prob = self._model.predict_proba(features)
            return prob[0][1] if prob.shape[1] > 1 else prob[0][0]
        else:
            return float(self._model.predict(features)[0])

    def select(
        self, objects: list[WeightedObject], grid: Grid, point: Point
    ) -> WeightedObject:
        state = grid.get_patterns_around_point(
            point=point, view=self.view, is_extended=True
        ).copy()
        state = grid.get_patterns_property(
            state, property_func=lambda pattern: pattern.is_walkable
        )
        state = state.flatten()
        state = np.delete(state, len(state) // 2)

        candidates = []
        for obj in objects:
            next_state = np.insert(state, 0, obj.is_walkable).reshape(1, -1)
            prediction_value = self._get_prediction_value(next_state)
            if prediction_value >= self._threshold:
                m = 1 if not self._rebalance else prediction_value
                rebalanced_obj = copy(obj)
                rebalanced_obj.weight *= m
                candidates.append(rebalanced_obj)

        if not candidates:
            candidates = objects

        return Utils.weighted_choice(objects=candidates, seed=self.seed)

    def save_weights(self, filename: str) -> None:
        pass

    def load_weights(self, filename: str) -> None:
        with open(filename, "rb") as file:
            self._model = pickle.load(file)
