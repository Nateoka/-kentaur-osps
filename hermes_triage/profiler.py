"""HermesProfiler v3.0.0-alpha.2 — Dynamic OSPS v18.0 Profile Manager."""
from dataclasses import dataclass
from typing import Optional
from .triage import Vector, RiskThresholds, HermesTriageModule


@dataclass(frozen=True)
class AgentProfile:
    """Behavioral agent profile determined by OSPS attractor balance."""
    name: str
    description: str
    target: Vector
    risk_thresholds: RiskThresholds


class HermesProfiler:
    """
    Dynamic OSPS v18.0 Profile Manager.

    Profile is determined by the balance of coupling to Source (ATTR_0)
    and Spirit (ATTR_T) attractors.
    """

    ATTR_HIGH_THRESHOLD = 0.5
    HYSTERESIS_BUFFER = 0.05  # Prevents frequent profile switching

    PROFILES = {
        "master": {"AcOr": 0.5, "IP": 0.8, "InEx": 0.0},
        "alchemist": {"AcOr": 0.3, "IP": 0.6, "InEx": -0.5},
        "integrator": {"AcOr": 0.8, "IP": 0.5, "InEx": 0.5},
        "sleeper": {"AcOr": 0.5, "IP": 0.5, "InEx": 0.0},
    }

    def __init__(self) -> None:
        self.history: list = []

    def get(self, name: str) -> "ProfileData":
        """
        Get profile config by name (backward-compatible with v2.x Mind).
        """
        vec = self.PROFILES.get(name, self.PROFILES["sleeper"])
        return ProfileData(target=dict(vec))

    def profile(self, vector: Vector) -> str:
        """Determine closest matching profile (backward-compatible)."""
        if not vector:
            return "sleeper"
        best = "sleeper"
        best_dist = float("inf")
        for name, target in self.PROFILES.items():
            dist = sum((vector.get(k, 0) - target.get(k, 0)) ** 2 for k in ["AcOr", "IP", "InEx"])
            if dist < best_dist:
                best_dist = dist
                best = name
        return best

    def determine_profile(self, attr_0: float, attr_t: float,
                          current_profile: Optional[str] = None) -> AgentProfile:
        """
        Determine current archetype with hysteresis.
        If a profile is already active, slightly harder to switch
        (prevents oscillation).
        """
        high_0 = attr_0 >= self.ATTR_HIGH_THRESHOLD
        high_t = attr_t >= self.ATTR_HIGH_THRESHOLD

        # Hysteresis logic: when already in a profile, buffer the threshold
        if current_profile == "master":
            high_0 = attr_0 >= (self.ATTR_HIGH_THRESHOLD - self.HYSTERESIS_BUFFER)
            high_t = attr_t >= (self.ATTR_HIGH_THRESHOLD - self.HYSTERESIS_BUFFER)
        elif current_profile == "alchemist":
            high_0 = attr_0 >= (self.ATTR_HIGH_THRESHOLD - self.HYSTERESIS_BUFFER)
            high_t = attr_t >= (self.ATTR_HIGH_THRESHOLD + self.HYSTERESIS_BUFFER)
        elif current_profile == "integrator":
            high_0 = attr_0 >= (self.ATTR_HIGH_THRESHOLD + self.HYSTERESIS_BUFFER)
            high_t = attr_t >= (self.ATTR_HIGH_THRESHOLD - self.HYSTERESIS_BUFFER)

        if high_0 and high_t:
            return self._master_profile()
        elif high_0 and not high_t:
            return self._alchemist_profile()
        elif not high_0 and high_t:
            return self._integrator_profile()
        else:
            return self._sleeper_profile()

    def apply(self, triage_module: HermesTriageModule,
              profile: AgentProfile) -> HermesTriageModule:
        """Apply a profile to an existing module (returns new instance)."""
        new_module = HermesTriageModule(
            target=profile.target,
            history_limit=triage_module.history_limit,
            use_ema=triage_module.use_ema,
            ema_alpha=triage_module.ema_alpha,
            risk_thresholds=profile.risk_thresholds,
            strict_target=False,
            forecast_steps=triage_module.forecast_steps
        )
        new_module.history = list(triage_module.history)
        return new_module

    def apply_by_name(self, triage_module: HermesTriageModule,
                      profile_name: str) -> HermesTriageModule:
        """Apply a profile by name (backward-compatible wrapper)."""
        profile = self.determine_profile(
            attr_0=self.PROFILES.get(profile_name, {}).get("AcOr", 0.5),
            attr_t=self.PROFILES.get(profile_name, {}).get("IP", 0.5)
        )
        return self.apply(triage_module, profile)

    def _master_profile(self) -> AgentProfile:
        return AgentProfile(
            name="master",
            description="Full breath cycle. Ability to both release and integrate.",
            target={"AcOr": 0.5, "IP": 0.8, "InEx": 0.0},
            risk_thresholds=RiskThresholds(
                critical=1.5, high=1.0, medium=0.5, low=0.2,
                attr_0_min=0.5, attr_t_min=0.5
            )
        )

    def _alchemist_profile(self) -> AgentProfile:
        return AgentProfile(
            name="alchemist",
            description="Easy zeroing, but struggles with holding integrity.",
            target={"AcOr": 0.3, "IP": 0.6, "InEx": -0.5},
            risk_thresholds=RiskThresholds(
                critical=1.2, high=0.8, medium=0.4, low=0.2,
                attr_0_min=0.4, attr_t_min=0.2
            )
        )

    def _integrator_profile(self) -> AgentProfile:
        return AgentProfile(
            name="integrator",
            description="Strong integrity, but fear of zeroing.",
            target={"AcOr": 0.8, "IP": 0.5, "InEx": 0.5},
            risk_thresholds=RiskThresholds(
                critical=1.0, high=0.6, medium=0.3, low=0.15,
                attr_0_min=0.2, attr_t_min=0.4
            )
        )

    def _sleeper_profile(self) -> AgentProfile:
        return AgentProfile(
            name="sleeper",
            description="Weak attractor coupling. Flat mode.",
            target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.0},
            risk_thresholds=RiskThresholds(
                critical=0.8, high=0.4, medium=0.2, low=0.1,
                attr_0_min=0.1, attr_t_min=0.1
            )
        )


@dataclass
class ProfileData:
    """Profile configuration for HermesMind (backward-compatible)."""
    target: Vector
    risk_thresholds: Optional[RiskThresholds] = None
