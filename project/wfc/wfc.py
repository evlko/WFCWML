from project.wfc.grid import Grid
from project.wfc.history import History
from project.wfc.judge import Judge
from project.wfc.outcomes import FailOutcome, SuccessOutcome
from project.wfc.step_result import StepResult


class WFC:
    def __init__(self, grid: Grid, judge: Judge, history: History) -> None:
        self.grid = grid
        self.judge = judge
        self.history = history
        self._is_initialized = False

    def _initialize(self) -> None:
        """Initialize the grid for the WFC process."""
        self.grid.initialize()
        self.history.clear()
        self._is_initialized = True

    def step(self, early_stopping: bool = True) -> StepResult:
        """Perform one step in the WFC process: find, collapse, and update neighbors."""
        result = StepResult()
        if not self._is_initialized:
            self._initialize()

        # find point and fail if None
        point = self.grid.find_least_entropy_cell()
        result.chosen_point = point
        if point is None and early_stopping:
            result.outcome = SuccessOutcome.COLLAPSED
            return result

        # find possible patterns and fail if None
        possible_patterns = self.grid.get_valid_patterns(p=point)
        if not possible_patterns and early_stopping:
            result.outcome = FailOutcome.ZERO_CHOICE
            result.failed_point = point
            return result

        # get random pattern from judge and place it
        chosen_pattern = self.judge.select(objects=possible_patterns, grid=self.grid, point=point)
        if chosen_pattern is None:
            result.outcome = FailOutcome.JUDGE_ERROR
            result.failed_point = point
            return result
        result.chosen_pattern = chosen_pattern
        self.grid.place_pattern(p=point, pattern=chosen_pattern)

        # find a cell with zero entropy and fail if one such exists
        zero_entropy_cell = self.grid.update_neighbors_entropy(p=point)
        if zero_entropy_cell and early_stopping:
            result.outcome = FailOutcome.ZERO_ENTROPY
            result.failed_point = zero_entropy_cell
            return result

        # otherwise return success
        result.success = True
        return result

    def generate(self) -> bool:
        """Run the generation process until the grid is fully collapsed or fails."""
        self._initialize()
        while not self.is_complete():
            step = self.step()
            self.history.add_step(step=step, grid=self.grid)
            if not step.success:
                return False
        return True

    def is_complete(self) -> bool:
        """Check if the grid has been fully collapsed."""
        return self.grid.is_collapsed()
