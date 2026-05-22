"""
HermesMind v2.3.0 — Facade for the full Hermes Triage neuro-system.
Minimal stub for test compatibility.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .triage import HermesTriageModule, TriageReport


@dataclass
class MindVerdict:
    """Container for the full mind process output."""
    report: Optional[TriageReport] = None
    risk: str = "low"
    stable: bool = True
    advice: str = ""
    modified_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HermesMind:
    """
    HermesMind v2.3.0 — unified orchestrator for all neuro-modules.
    Integrates Triage + Governor + Navigator + Consensus + Memory.
    """

    DEFAULT_PROFILES = {
        "analyst": {"AcOr": 0.3, "IP": 0.8, "InEx": 0.2},
        "executor": {"AcOr": 0.8, "IP": 0.3, "InEx": 0.5},
        "crisis": {"AcOr": 0.5, "IP": 0.5, "InEx": 0.5},
        "balanced": {"AcOr": 0.5, "IP": 0.5, "InEx": 0.3},
    }

    def __init__(self, profile: str = "balanced", target: Optional[Dict[str, float]] = None):
        if target is None and profile in self.DEFAULT_PROFILES:
            target = self.DEFAULT_PROFILES[profile]
        elif target is None:
            target = self.DEFAULT_PROFILES["balanced"]
        self.triage = HermesTriageModule(target=target, use_ema=True)

    def process(self, current_vector: Dict[str, float],
                agent_loop_state: Optional[Dict[str, Any]] = None) -> MindVerdict:
        """Run full diagnostic pipeline on current state."""
        report = self.triage.report(current_vector)
        modified = dict(agent_loop_state or {})
        modified["triage_verdict"] = report.advice
        return MindVerdict(
            report=report,
            risk=report.risk,
            stable=report.stable,
            advice=report.advice,
            modified_state=modified,
        )
