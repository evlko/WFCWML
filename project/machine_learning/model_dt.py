import pickle

import numpy as np

from project.machine_learning.model import Model
from project.utils.utils import Utils
from project.wfc.grid import Grid, Point, Rect
from project.wfc.judge import Judge
from project.wfc.wobj import WeightedObject


class ModelDT(Model, Judge):
    def __init__(self, seed: int | None = None, view: Rect = Rect(3, 3)):
        super().__init__(view=view, seed=seed)
        self._model = None

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
            prediction = self._model.predict(next_state)
            if prediction:
                candidates.append(obj)
        if not candidates:
            candidates = objects

        return Utils.weighted_choice(objects=candidates, seed=self.seed)

    def save_weights(self, filename: str) -> None:
        pass

    def load_weights(self, filename: str) -> None:
        with open(filename, "rb") as file:
            self._model = pickle.load(file)
