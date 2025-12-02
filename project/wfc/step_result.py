from dataclasses import dataclass

from project.wfc.grid import Point
from project.wfc.outcomes import Outcome
from project.wfc.pattern import MetaPattern


@dataclass
class StepResult:
    """Cautious planning today paves the way for a brighter tomorrow."""

    success: bool = False
    chosen_point: Point | None = None
    chosen_pattern: MetaPattern | None = None
    outcome: Outcome | None = None
    failed_point: Point | None = None
