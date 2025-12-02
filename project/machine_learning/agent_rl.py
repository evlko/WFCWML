import pickle
import random
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from project.machine_learning.model import Model, ModelMode
from project.wfc.grid import Point, Rect
from project.wfc.judge import GreedyJudge, Judge
from project.wfc.pattern import MetaPattern
from project.wfc.wfc import WFC, StepResult


@dataclass
class QValue:
    state: bytes
    action: int
    value: float = 0.0


class AgentRL(Model, Judge):
    def __init__(
        self,
        wfc: WFC,
        mode: ModelMode = ModelMode.TRAINIG,
        epsilon: float = 0.1,
        alpha: float = 0.5,
        gamma: float = 0.9,
        view: Rect = Rect(3, 3),
        exploration_judge: Judge = GreedyJudge(),
    ):
        self.mode = mode
        self.wfc = wfc
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.view = view
        self.exploration_judge = exploration_judge
        self.q_table: dict[tuple, QValue] = defaultdict(float)

    def save_weights(self, filename: str) -> None:
        """Save Q-table to a file."""
        with open(filename, "wb") as f:
            pickle.dump(self.q_table, f)

    def load_weights(self, filename: str) -> None:
        """Load Q-table from a file."""
        with open(filename, "rb") as f:
            self.q_table = pickle.load(f)

    def select(self, point: Point) -> MetaPattern:
        """Choose a pattern based on epsilon-greedy policy."""
        possible_patterns = self._get_possible_patterns(point)
        state = self._observe(point).flatten().tobytes()

        if (random.random() < self.epsilon) and self.mode == ModelMode.TRAINIG:
            return self.exploration_judge.select()

        return max(
            possible_patterns,
            key=lambda pattern: self.q_table.get((state, pattern.uid), 0),
        )

    def _observe(self, point: Point) -> np.ndarray:
        """Get a view of patterns around a given point."""
        return self.wfc.grid.get_patterns_around_point(point=point, view=self.view)

    def _get_possible_patterns(self, point: Point) -> list[MetaPattern]:
        """Retrieve possible patterns for the specified point."""
        return self.wfc.grid.get_valid_patterns(p=point)

    def _update_q_table(self, state, action, reward, next_state):
        """Update Q-values using Q-learning update rule."""
        current_q_value = self.q_table[(state, action)]

        # strange
        max_next_q = max(
            self.q_table[(next_state, next_action)]
            for next_action in [
                pattern.uid for pattern in self._get_possible_patterns(Point(0, 0))
            ]
        )

        self.q_table[(state, action)] = current_q_value + self.alpha * (
            reward + self.gamma * max_next_q - current_q_value
        )

    def train(self, step_result: StepResult) -> bool:
        point = step_result.chosen_point
        initial_state = self._observe(point).flatten().tobytes()
        possible_patterns = self._get_possible_patterns(point)

        for pattern in possible_patterns:
            self.wfc.grid.entropy[
                step_result.failed_point.x, step_result.failed_point.y
            ] = 999
            self.wfc.grid.place_pattern(p=point, pattern=pattern)
            zero_entropy_cell = self.wfc.grid.update_neighbors_entropy(p=point)

            reward = -1 if zero_entropy_cell else 1
            new_state = self.observe(point).flatten().tobytes()
            self._update_q_table(initial_state, pattern.uid, reward, new_state)

            if zero_entropy_cell is None:
                return True

        return False
