from project.wfc.wfc import StepResult


class History:
    def __init__(self, capacity: int | None = None):
        self._capacity = capacity
        self._history: list[StepResult] = []

    def add_step(self, step: StepResult) -> None:
        self._history.append(step)
        if self._capacity and len(self._history) > self._capacity:
            self._history.pop(0)
