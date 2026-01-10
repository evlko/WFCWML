from project.wfc.grid import Grid, Point
from project.wfc.history import History
from project.wfc.judge import Action, ActionType, Judge
from project.wfc.outcomes import FailOutcome, SuccessOutcome
from project.wfc.step_result import StepResult


class WFC:
    def __init__(self, grid: Grid, judge: Judge) -> None:
        self.grid = grid
        self.judge = judge
        self.history = History()
        self._is_initialized = False

    @property
    def is_complete(self) -> bool:
        """Check if the grid has been fully collapsed."""
        return self.grid.is_collapsed

    def _initialize(self) -> None:
        """Initialize the grid for the WFC process."""
        self.grid.initialize()
        self.history.clear()
        self._is_initialized = True

    def _ensure_initialized(self) -> None:
        """Ensure the WFC process is initialized."""
        if not self._is_initialized:
            self._initialize()

    def _select_point(self, result: StepResult, early_stopping: bool) -> Point | None:
        """Select the next point to collapse and handle early stopping if no point found."""
        point = self.grid.find_least_entropy_cell()
        result.chosen_point = point

        if point is None and early_stopping:
            result.outcome = SuccessOutcome.COLLAPSED
        return point

    def _validate_patterns(
        self, point: Point, result: StepResult, early_stopping: bool
    ) -> list | None:
        """Validate available patterns for the given point and handle early stopping if no patterns."""
        possible_patterns = self.grid.get_valid_patterns(p=point)

        if not possible_patterns and early_stopping:
            result.outcome = FailOutcome.ZERO_CHOICE
            result.failed_point = point
            return None

        possible_patterns = list(possible_patterns)
        possible_patterns = sorted(possible_patterns, key=lambda x: x.uid)

        return possible_patterns

    def _handle_judge_action(
        self,
        action: Action,
        point: Point,
        result: StepResult,
        early_stopping: bool,
    ) -> bool:
        match action.type:
            case ActionType.PLACE:
                return self._handle_place_action(action, point, result, early_stopping)
            case ActionType.ROLLBACK:
                self._handle_rollback_action(action)
                return True
        return False

    def _handle_place_action(
        self, action: Action, point: Point, result: StepResult, early_stopping: bool
    ) -> bool:
        chosen_pattern = action.data.object
        if chosen_pattern is None:
            result.outcome = FailOutcome.JUDGE_ERROR
            result.failed_point = point
            return False

        result.chosen_pattern = chosen_pattern
        self.grid.place_pattern(p=point, pattern=chosen_pattern)

        # Update neighbors and check for zero entropy
        self.grid.update_entropy(p=point)
        if self.grid.zero_entropy_cell and early_stopping:
            result.outcome = FailOutcome.ZERO_ENTROPY
            result.failed_point = self.grid.zero_entropy_cell
            return False

        return True

    def _handle_rollback_action(self, action: Action) -> None:
        self.rollback(steps=action.data.steps)

    def step(self, early_stopping: bool = True) -> StepResult:
        """Perform one step (do propagation) in the WFC process: find cell, place pattern and update entropy."""
        result = StepResult()
        possible_patterns = None
        action_type = ActionType.PLACE

        try:
            self._ensure_initialized()

            # Step 1: Select point to collapse
            point = self._select_point(result, early_stopping)
            if point is None:
                return result

            # Step 2: Validate available patterns
            possible_patterns = self._validate_patterns(point, result, early_stopping)
            if possible_patterns is None:
                return result

            # Step 3: Handle judge action
            action = self.judge.act(
                objects=possible_patterns, grid=self.grid, point=point
            )
            action_type = action.type
            step_successful = self._handle_judge_action(
                action, point, result, early_stopping
            )
            if not step_successful:
                return result

            # Step 4: Mark step as successful
            result.success = True
            return result
        finally:
            self.history.add_step(
                step=result,
                grid=self.grid,
                action_type=action_type,
                possible_patterns=possible_patterns,
            )

    def rollback(self, steps: int = 1) -> None:
        for _ in range(steps):
            last_step = self.history.get_last_rollback_snapshot(pop=True)
            if last_step is None:
                break
            self.grid.reset_point(p=last_step.point)

    def generate(self) -> bool:
        """Runs the generation process until completion or failure."""
        self._initialize()

        last_step = True
        while not self.is_complete and last_step:
            last_step = self.step().success

        return self.is_complete
