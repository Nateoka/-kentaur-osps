"""
HermesProfiler v2.3.0 — Agent profiling module.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProfilerReport:
    """Agent profile snapshot."""
    profile_name: str
    vector: Dict[str, float]
    traits: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HermesProfiler:
    """
    Agent profiling — determines the current agent profile based on
    the triage vector and history.
    """

    PROFILES = {
        "analyst": {"AcOr": 0.3, "IP": 0.8, "InEx": 0.2},
        "executor": {"AcOr": 0.8, "IP": 0.3, "InEx": 0.5},
        "crisis": {"AcOr": 0.5, "IP": 0.5, "InEx": 0.5},
        "balanced": {"AcOr": 0.5, "IP": 0.5, "InEx": 0.3},
        "architect": {"AcOr": 0.3, "IP": 0.7, "InEx": 0.2},
    }

    def __init__(self) -> None:
        self.history: List[Dict[str, float]] = []

    def profile(self, vector: Dict[str, float]) -> str:
        """Determine the closest matching profile."""
        if not vector:
            return "balanced"
        best = "balanced"
        best_dist = float("inf")
        for name, target in self.PROFILES.items():
            dist = sum((vector.get(k, 0) - target.get(k, 0)) ** 2 for k in ["AcOr", "IP", "InEx"])
            if dist < best_dist:
                best_dist = dist
                best = name
        return best

    def update(self, vector: Dict[str, float]) -> ProfilerReport:
        """Record a vector and return a profile report."""
        self.history.append(dict(vector))
        if len(self.history) > 10:
            self.history.pop(0)
        name = self.profile(vector)
        return ProfilerReport(profile_name=name, vector=dict(vector))

    def get(self, name: str) -> "ProfileData":
        """Get profile config by name."""
        vec = self.PROFILES.get(name, self.PROFILES["balanced"])
        return ProfileData(target=dict(vec))

    def apply(self, module: Any, profile_name: str) -> Any:
        """Apply a profile to a triage module (switch target)."""
        from .triage import HermesTriageModule
        profile = self.get(profile_name)
        return HermesTriageModule(
            target=profile.target,
            history_limit=module.history_limit,
            use_ema=module.use_ema,
            ema_alpha=module.ema_alpha,
            risk_thresholds=module.risk_thresholds,
            strict_target=False,
        )


@dataclass
class ProfileData:
    """Profile configuration for HermesMind."""
    target: Dict[str, float]
    risk_thresholds: Optional[Any] = None
