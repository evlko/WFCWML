from enum import Enum, auto


class Outcome(Enum):
    """Base class for all outcomes."""

    pass


class FailOutcome(Outcome):
    ZERO_CHOICE = auto()
    ZERO_ENTROPY = auto()
    JUDGE_ERROR = auto()
    ROLLBACK_LIMIT_EXCEEDED = auto()
    JUDGE_STOPPED = auto()


class SuccessOutcome(Outcome):
    COLLAPSED = auto()
