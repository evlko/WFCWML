from project.wfc.advisor import Advisor
from project.wfc.grid import Grid, Point
from project.wfc.history import ActionType, History
from project.wfc.judge import CONTINUE_DECISION, Decision, DecisionType, Judge
from project.wfc.outcomes import FailOutcome, SuccessOutcome
from project.wfc.step_result import StepResult


class WFC:
    def __init__(
        self,
        grid: Grid,
        judge: Judge,
        advisor: Advisor,
        max_rollbacks: int | None = None,
    ) -> None:
        self.grid = grid
        self.judge = judge
        self.advisor = advisor
        self.max_rollbacks = self._calculate_max_rollbacks(max_rollbacks, grid)
        self.rollback_count = 0
        self.history = History()
        self._is_initialized = False

    def _calculate_max_rollbacks(self, max_rollbacks: int | None, grid: Grid) -> int | None:
        if max_rollbacks is None:
            return int((grid.area) ** 0.5)
        elif max_rollbacks == -1:
            return None
        else:
            return max_rollbacks

    @property
    def is_complete(self) -> bool:
        """Check if the grid has been fully collapsed."""
        return self.grid.is_collapsed

    def _initialize(self) -> None:
        """Initialize the grid for the WFC process."""
        self.grid.initialize()
        self.history.clear()
        self.rollback_count = 0
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

    def rollback(self, decision: Decision) -> None:
        steps = decision.data.steps
        self.rollback_count += steps

        for _ in range(steps):
            last_step = self.history.get_last_rollback_snapshot(pop=True)
            if last_step is None:
                break
            self.grid.reset_point(
                p=last_step.action_point, penalty=self.judge.rollback_penalty
            )

    def step(self, early_stopping: bool = True) -> StepResult:
        """Perform one step (do propagation) in the WFC process: find cell, place pattern and update entropy."""
        result = StepResult()
        possible_patterns = None
        action_type = ActionType.PLACE

        try:
            self._ensure_initialized()

            # Step 1: Check if rollback limit exceeded (maxr_rollbacks = None means inf)
            if self.max_rollbacks and self.rollback_count >= self.max_rollbacks:
                result.outcome = FailOutcome.ROLLBACK_LIMIT_EXCEEDED
                return result

            # Step 2: Check if judge decides to rollback or stop (before selecting point)
            decision = CONTINUE_DECISION
            if self.history.rollback_steps > 0:
                decision = self.judge.decide(grid=self.grid)

            if decision.type == DecisionType.STOP:
                result.outcome = FailOutcome.JUDGE_STOPPED
                return result

            if decision.type == DecisionType.ROLLBACK:
                self.rollback(decision)
                action_type = ActionType.ROLLBACK
                result.success = True
                return result

            # Step 3: Select point to collapse
            point = self._select_point(result, early_stopping)
            if point is None:
                return result

            # Step 4: Validate available patterns
            possible_patterns = self._validate_patterns(point, result, early_stopping)
            if possible_patterns is None:
                return result

            # Step 5: Use advisor to select pattern
            chosen_pattern = self.advisor.select(
                objects=possible_patterns, grid=self.grid, point=point
            )

            if chosen_pattern is None:
                result.outcome = FailOutcome.JUDGE_ERROR
                result.failed_point = point
                return result

            result.chosen_pattern = chosen_pattern
            self.grid.place_pattern(p=point, pattern=chosen_pattern)

            # Step 6: Update neighbors and check for zero entropy
            self.grid.update_entropy(p=point)
            if self.grid.zero_entropy_cell and early_stopping:
                result.outcome = FailOutcome.ZERO_ENTROPY
                result.failed_point = self.grid.zero_entropy_cell
                return result

            result.success = True
            return result
        finally:
            self.history.add_step(
                step=result,
                grid=self.grid,
                action_type=action_type,
                possible_patterns=possible_patterns,
            )

    def generate(self) -> bool:
        """Runs the generation process until completion or failure."""
        self._initialize()

        while not self.is_complete:
            if not self.step().success:
                break

        return self.is_complete
