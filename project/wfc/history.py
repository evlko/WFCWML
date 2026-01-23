import csv
import random
import uuid
from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto

from project.wfc.grid import Grid, Point
from project.wfc.pattern import MetaPattern
from project.wfc.step_result import StepResult


class ActionType(StrEnum):
    """Action types for history tracking."""

    PLACE = auto()
    ROLLBACK = auto()


class SerializationStrategy(Enum):
    ALL = auto()  # Serialize all snapshots
    BALANCED = auto()  # Balance between successful and failed generations


@dataclass
class CellState:
    entropy: int
    is_walkable: int | None  # None if cell is not collapsed, 0 or 1 otherwise
    pattern_uid: int | None  # None if cell is not collapsed


@dataclass
class GridState:
    width: int
    height: int
    cells: list[CellState]  # Flattened list of cell states (row-major order)

    @classmethod
    def from_grid(cls, grid: Grid) -> "GridState":
        cells = []
        for x in range(grid.height):
            for y in range(grid.width):
                pattern = grid.grid[x, y]
                entropy = int(grid.entropy[x, y])
                if pattern is not None:
                    cells.append(
                        CellState(
                            entropy=entropy,
                            is_walkable=pattern.is_walkable,
                            pattern_uid=pattern.uid,
                        )
                    )
                else:
                    cells.append(
                        CellState(entropy=entropy, is_walkable=None, pattern_uid=None)
                    )
        return cls(width=grid.width, height=grid.height, cells=cells)


@dataclass
class Snapshot:
    step_number: int
    action_type: ActionType
    action_point: Point
    grid_state: GridState
    possible_pattern_uids: list[int] = field(default_factory=list)
    chosen_pattern_uid: int | None = None
    chosen_pattern_is_walkable: int | None = None


@dataclass
class GenerationResult:
    success: bool
    snapshots: list[Snapshot]


class History:
    def __init__(self):
        self._snapshots: list[Snapshot] = []
        self._rollback_snapshots: list[Snapshot] = []

    @property
    def snapshots(self) -> list[Snapshot]:
        return self._snapshots

    @property
    def steps(self) -> int:
        return len(self._snapshots)

    def add_step(
        self,
        step: StepResult,
        grid: Grid,
        action_type: ActionType,
        possible_patterns: list[MetaPattern] | None = None,
    ) -> None:
        if step.chosen_point is None:
            return

        grid_state = GridState.from_grid(grid)

        snapshot = Snapshot(
            step_number=len(self._snapshots),
            action_type=action_type,
            action_point=(step.chosen_point.x, step.chosen_point.y),
            grid_state=grid_state,
            possible_pattern_uids=(
                [p.uid for p in possible_patterns] if possible_patterns else []
            ),
            chosen_pattern_uid=step.chosen_pattern.uid if step.chosen_pattern else None,
            chosen_pattern_is_walkable=(
                step.chosen_pattern.is_walkable if step.chosen_pattern else None
            ),
        )

        self._snapshots.append(snapshot)
        self._rollback_snapshots.append(snapshot)

    def get_last_rollback_snapshot(self, pop: bool = True) -> Snapshot | None:
        if self._rollback_snapshots:
            if pop:
                return self._rollback_snapshots.pop()
            return self._rollback_snapshots[-1]
        return None

    def clear(self) -> None:
        self._snapshots.clear()
        self._rollback_snapshots.clear()


class GenerationHistory:
    def __init__(self):
        self._results: list[GenerationResult] = []

    @property
    def results(self) -> list[GenerationResult]:
        return self._results

    def add(self, result: GenerationResult) -> None:
        self._results.append(result)

    def clear(self) -> None:
        self._results.clear()

    @staticmethod
    def _get_csv_headers(grid_width: int, grid_height: int) -> list[str]:
        headers = [
            "generation_uid",
            "generation_success",
            "step_number",
            "action_type",
            "action_x",
            "action_y",
            "num_possible_patterns",
            "chosen_pattern_uid",
            "chosen_pattern_is_walkable",
        ]

        for x in range(grid_height):
            for y in range(grid_width):
                headers.extend(
                    [
                        f"cell_{x}_{y}_entropy",
                        f"cell_{x}_{y}_is_walkable",
                    ]
                )

        return headers

    @staticmethod
    def _snapshot_to_row(
        snapshot: Snapshot, generation_uid: str, generation_success: bool
    ) -> list:
        row = [
            generation_uid,
            generation_success,
            snapshot.step_number,
            snapshot.action_type.name,
            snapshot.action_point[0],
            snapshot.action_point[1],
            len(snapshot.possible_pattern_uids),
            (
                snapshot.chosen_pattern_uid
                if snapshot.chosen_pattern_uid is not None
                else -1
            ),
            (
                snapshot.chosen_pattern_is_walkable
                if snapshot.chosen_pattern_is_walkable is not None
                else -1
            ),
        ]

        for cell in snapshot.grid_state.cells:
            row.extend(
                [
                    cell.entropy,
                    cell.is_walkable if cell.is_walkable is not None else -1,
                ]
            )

        return row

    def serialize(
        self,
        strategy: SerializationStrategy = SerializationStrategy.BALANCED,
        file: str | None = None,
        directory: str = "data/history/raw/",
    ) -> None:
        if not self.results:
            return

        if file is None:
            file = f"{uuid.uuid4()}.csv"

        match strategy:
            case SerializationStrategy.ALL:
                generations_to_serialize = self.results
            case SerializationStrategy.BALANCED:
                success_gens = [g for g in self.results if g.success]
                failure_gens = [g for g in self.results if not g.success]
                min_count = min(len(success_gens), len(failure_gens))
                if min_count > 0:
                    generations_to_serialize = random.sample(
                        success_gens, min_count
                    ) + random.sample(failure_gens, min_count)
                else:
                    generations_to_serialize = self.results
            case _:
                raise ValueError(f"Unknown strategy: {strategy}")

        if not generations_to_serialize:
            return

        first_snapshot = generations_to_serialize[0].snapshots[0]
        grid_width = first_snapshot.grid_state.width
        grid_height = first_snapshot.grid_state.height

        headers = self._get_csv_headers(grid_width, grid_height)

        with open(directory + file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            for _, generation in enumerate(generations_to_serialize):
                generation_uid = str(uuid.uuid4())
                for snapshot in generation.snapshots:
                    row = self._snapshot_to_row(
                        snapshot, generation_uid, generation.success
                    )
                    writer.writerow(row)
