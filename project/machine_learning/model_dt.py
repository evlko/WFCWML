import pickle

from project.machine_learning.model import Model
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
        state = grid.get_patterns_property(state, property_func = lambda pattern: pattern.is_walkable)
        
        return max(objects, key=lambda obj: obj.weight)

    def save_weights(self, filename: str) -> None:
        pass

    def load_weights(self, filename: str) -> None:
        with open(filename, 'rb') as file:
            self._model = pickle.load(file)