from enum import Enum, auto


class Outcome(Enum):
    """Base class for all outcomes."""

    pass


class FailOutcome(Outcome):
    ZERO_CHOICE = auto()
    ZERO_ENTROPY = auto()
    JUDGE_ERROR = auto()


class SuccessOutcome(Outcome):
    COLLAPSED = auto()
