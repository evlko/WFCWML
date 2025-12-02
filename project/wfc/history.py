import csv
import random
import uuid
from dataclasses import dataclass
from enum import Enum, auto

from project.wfc.grid import Grid, Rect
from project.wfc.pattern import MetaPattern
from project.wfc.step_result import StepResult


class SerializationStrategy(Enum):
    ALL = auto()
    BALANCED = auto()


@dataclass
class HistoryStep:
    success: bool
    choosen_pattern: MetaPattern
    view_around: list[MetaPattern | None]


class History:
    def __init__(
        self, capacity: int | None = None, view: Rect = Rect(width=3, height=3)
    ):
        self._capacity = capacity
        self._view = view
        self._history: list[HistoryStep] = []

    def add_step(self, step: StepResult, grid: Grid) -> None:
        if step.chosen_pattern is not None and step.chosen_point is not None:
            view_around = grid.get_patterns_around_point(
                point=step.chosen_point, view=self._view
            )
            history_step = HistoryStep(
                success=step.success,
                choosen_pattern=step.chosen_pattern,
                view_around=view_around.flatten().tolist(),
            )
            self._history.append(history_step)
            if self._capacity and len(self._history) > self._capacity:
                self._history.pop(0)

    def clear(self) -> None:
        self._history.clear()

    def serialize(
        self,
        strategy: SerializationStrategy = SerializationStrategy.BALANCED,
        file: str | None = None,
        directory: str = "data/history/raw/",
    ) -> None:
        if not self._history:
            return

        if file is None:
            file = f"{uuid.uuid4()}.csv"

        match strategy:
            case SerializationStrategy.ALL:
                steps_to_serialize = self._history
            case SerializationStrategy.BALANCED:
                success_steps = [step for step in self._history if step.success]
                failure_steps = [step for step in self._history if not step.success]
                min_count = min(len(success_steps), len(failure_steps))
                if min_count > 0:
                    balanced_steps = random.sample(
                        success_steps, min_count
                    ) + random.sample(failure_steps, min_count)
                    steps_to_serialize = balanced_steps
                else:
                    return
            case _:
                raise ValueError(f"Unknown strategy: {strategy}")

        view_size = len(self._history[0].view_around)

        headers = ["success", "choosen_pattern.uid", "choosen_pattern.is_walkable"]
        for i in range(view_size):
            headers.extend([f"{i}.uid", f"{i}.is_walkable"])

        with open(directory + file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            for step in steps_to_serialize:
                row = [
                    step.success,
                    step.choosen_pattern.uid,
                    step.choosen_pattern.is_walkable,
                ]
                for pattern in step.view_around:
                    if pattern is not None:
                        row.extend([pattern.uid, pattern.is_walkable])
                    else:
                        row.extend([None, None])

                writer.writerow(row)
