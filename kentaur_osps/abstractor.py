"""KentaurAbstractor v2.3.0 — Meta-cognitive abstraction level management."""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from .core import TriageReport, Vector
from .memory import KentaurMemory


class AbstractionLevel(Enum):
    """Agent thinking levels (Abstraction Ladder)."""
    CONCRETE = 1       # Focus on details, syntax, micro-errors
    TACTICAL = 2       # Focus on current task, algorithm
    STRATEGIC = 3      # Focus on architecture, patterns, system
    PHILOSOPHICAL = 4  # Focus on root causes, purposes, meaning


@dataclass(frozen=True)
class AbstractionShift:
    """Directive to change thinking level."""
    current_level: AbstractionLevel
    target_level: AbstractionLevel
    shift_command: str  # Prompt injection


class KentaurAbstractor:
    """
    Manages abstract thinking. Prevents the agent from getting stuck
    in the "Concrete Swamp" or floating into "Philosophical Space".
    """

    def __init__(self, concrete_stuck_threshold: int = 2, philosophical_lose_threshold: int = 1):
        self.concrete_stuck_threshold = concrete_stuck_threshold
        self.philosophical_lose_threshold = philosophical_lose_threshold

    def diagnose_level(self, report: TriageReport, memory: Optional[KentaurMemory] = None) -> AbstractionLevel:
        """Determine current abstraction level from vector."""
        if report.lever_axis == "AcOr" and report.lever_direction == "excess":
            return AbstractionLevel.CONCRETE
        if report.lever_axis == "IP" and report.lever_direction == "excess":
            if report.current_vector.get("InEx", 0.0) < -0.3:
                return AbstractionLevel.PHILOSOPHICAL
            return AbstractionLevel.STRATEGIC
        return AbstractionLevel.TACTICAL

    def prescribe_shift(self, report: TriageReport, memory: Optional[KentaurMemory] = None) -> Optional[AbstractionShift]:
        """Determine if forced zoom shift is needed."""
        current_level = self.diagnose_level(report, memory)

        # 1. Stuck in details (Concrete Swamp)
        if current_level == AbstractionLevel.CONCRETE:
            if report.risk in ["medium", "high", "critical"]:
                return AbstractionShift(
                    current_level=AbstractionLevel.CONCRETE,
                    target_level=AbstractionLevel.STRATEGIC,
                    shift_command=(
                        "[ABSTRACTION SHIFT UP]: You are stuck in details and micro-errors. "
                        "Stop fixing syntax. Zoom out. Describe the architectural problem "
                        "causing these errors. Solve at pattern level, then return to code."
                    )
                )

        # 2. Lost in abstract space (Philosophical Space)
        if current_level == AbstractionLevel.PHILOSOPHICAL:
            return AbstractionShift(
                current_level=AbstractionLevel.PHILOSOPHICAL,
                target_level=AbstractionLevel.TACTICAL,
                shift_command=(
                    "[ABSTRACTION SHIFT DOWN]: You drifted into abstract thinking "
                    "and lost touch with reality. Come back to earth. "
                    "Formulate one concrete, measurable step to execute right now."
                )
            )

        return None
