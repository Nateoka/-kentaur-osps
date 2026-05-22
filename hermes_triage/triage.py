"""
Hermes Triage Module — Three-axis diagnostic system for agents.
OSPS v18.0 integrated. Attractor metrics, K_flow, Phi, abstraction levels.
"""

import math
from typing import List, Dict, Tuple, Optional, Literal, Any, cast
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from itertools import combinations

# ====================== TYPES ======================

AxisName = Literal["AcOr", "IP", "InEx"]
Vector = Dict[AxisName, float]          # Strict internal (validated)
InputVector = Dict[str, float]          # External input format for API compatibility


@dataclass(frozen=True)
class RiskThresholds:
    """
    Risk and stability thresholds.

    critical = 1.2 — empirical high-danger threshold (system practically uncontrollable)
    high = 0.6 — significant deviation from target
    medium = 0.3 — noticeable deviation, requires attention
    low = 0.20 — low-risk zone (used for stable determination)
    """
    critical: float = 1.2
    high: float = 0.6
    medium: float = 0.3
    low: float = 0.20
    # OSPS v18.0: attractor coupling thresholds (separated)
    attr_0_min: float = 0.3
    attr_t_min: float = 0.3


@dataclass(frozen=True)
class TriageReport:
    """Structured three-axis diagnostic report."""
    schema_version: str
    timestamp: str
    current_vector: Vector
    target_vector: Vector
    tension: float
    lever_axis: Optional[AxisName]
    lever_delta: float
    lever_direction: str
    risk: str
    forecast: List[Vector]
    stable: bool
    k_res: float

    # === OSPS v18.0 Metrics ===
    attr_0: float               # Attractor Ø (Void/Zeroing) coupling
    attr_t: float               # Attractor T (Spirit/Synthesis) coupling
    k_flow: float               # Flow conductivity (adapted Ohm's law)
    phi_osps: float             # Anti-fragmentation index
    abstraction_level: str      # CONCRETE / TACTICAL / STRATEGIC / PHILOSOPHICAL

    advice: str


class HermesTriageModule:
    """
    Three-axis diagnostic module for Hermes agent (v3.0.0-alpha.1).
    Clean architecture, fully deterministic, OSPS v18.0 metrics integrated.
    """

    AXES: Tuple[AxisName, ...] = ("AcOr", "IP", "InEx")
    SCHEMA_VERSION = "3.0.0-alpha.1"

    def __init__(self,
                 target: Optional[InputVector] = None,
                 history_limit: int = 5,
                 use_ema: bool = False,
                 ema_alpha: float = 0.3,
                 risk_thresholds: Optional[RiskThresholds] = None,
                 strict_target: bool = True,
                 forecast_steps: int = 2):
        self.risk_thresholds = risk_thresholds or RiskThresholds()
        self.strict_target = strict_target
        self.target: Vector = self._validate_target(target or {ax: 0.0 for ax in self.AXES})
        self.history_limit = max(1, history_limit)
        self.use_ema = use_ema
        self.ema_alpha = max(0.01, min(0.99, ema_alpha))
        self.forecast_steps = max(1, forecast_steps)
        self.history: List[Vector] = []

    # ====================== VALIDATION ======================

    def _validate_target(self, target: InputVector) -> Vector:
        validated: Vector = {}
        for ax in self.AXES:
            val = target.get(ax, 0.0)
            if not isinstance(val, (int, float)):
                raise ValueError(f"Target axis {ax}: expected number, got {type(val).__name__}")
            val = float(val)
            if self.strict_target and not (-1.0 <= val <= 1.0):
                raise ValueError(f"Target axis {ax}: value {val} out of bounds [-1.0, 1.0]")
            validated[ax] = max(-1.0, min(1.0, val))
        return validated

    def _normalize(self, vec: InputVector) -> Vector:
        return {ax: max(-1.0, min(1.0, float(vec.get(ax, 0.0)))) for ax in self.AXES}

    def _validate_observation(self, obs: InputVector) -> Vector:
        validated = {}
        for ax in self.AXES:
            val = obs.get(ax, 0.0)
            if not isinstance(val, (int, float)):
                raise ValueError(f"Observation axis {ax}: expected number, got {type(val).__name__}")
            validated[ax] = float(val)
        return self._normalize(cast(InputVector, validated))

    # ====================== CORE LOGIC ======================

    def compute_state(self, observations: List[InputVector]) -> Vector:
        if not observations:
            return {ax: 0.0 for ax in self.AXES}
        validated = [self._validate_observation(obs) for obs in observations]
        return self._calculate_ema_from_scratch(validated) if self.use_ema else self._compute_median(validated)

    def _compute_median(self, observations: List[Vector]) -> Vector:
        med: Vector = {}
        for ax in self.AXES:
            values = sorted(obs[ax] for obs in observations)
            n = len(values)
            if n % 2 == 1:
                med[ax] = values[n // 2]
            else:
                med[ax] = (values[n // 2 - 1] + values[n // 2]) / 2.0
        return med

    def _calculate_ema_from_scratch(self, observations: List[Vector]) -> Vector:
        if not observations:
            return {ax: 0.0 for ax in self.AXES}
        ema_state = dict(observations[0])
        for obs in observations[1:]:
            for ax in self.AXES:
                ema_state[ax] += self.ema_alpha * (obs[ax] - ema_state[ax])
        return ema_state

    def tension(self, current: Vector) -> float:
        current = self._validate_observation(cast(InputVector, current))
        delta_sq = sum((current[ax] - self.target[ax]) ** 2 for ax in self.AXES)
        return math.sqrt(delta_sq)

    def lever(self, current: Vector) -> Tuple[Optional[AxisName], float, str]:
        current = self._validate_observation(cast(InputVector, current))
        candidates = [(abs(current[ax] - self.target[ax]), current[ax] - self.target[ax], ax)
                      for ax in self.AXES]
        candidates.sort(key=lambda x: (-x[0], self.AXES.index(x[2])))
        _, delta, axis = candidates[0]
        if abs(delta) < 1e-9:
            return None, 0.0, "balanced"
        direction = "excess" if delta > 0 else "deficit"
        return axis, delta, direction

    def forecast(self, current: Vector, steps: Optional[int] = None) -> List[Vector]:
        steps = self.forecast_steps if steps is None else steps
        if steps <= 0:
            return []
        current = self._validate_observation(cast(InputVector, current))
        base_rate = 0.3
        adaptive_rate = base_rate * min(1.0, self.k_resilience(self.tension(current)) + 0.2)
        trajectory: List[Vector] = []
        s = dict(current)
        for _ in range(steps):
            new_s: Vector = {}
            for ax in self.AXES:
                delta = self.target[ax] - s[ax]
                new_s[ax] = max(-1.0, min(1.0, s[ax] + adaptive_rate * delta))
            trajectory.append(new_s)
            s = new_s
        return trajectory

    def risk_level(self, tension_val: float) -> str:
        if tension_val > self.risk_thresholds.critical: return "critical"
        if tension_val > self.risk_thresholds.high: return "high"
        if tension_val > self.risk_thresholds.medium: return "medium"
        return "low"

    def k_resilience(self, tension_val: float) -> float:
        return 1.0 / (1.0 + tension_val)

    # ====================== OSPS v18.0 METHODS ======================

    def _compute_attr(self, current: Vector, tension: float, k_res: float) -> Tuple[float, float]:
        """
        Compute attractor coupling for Ø (0) and T.
        OSPS v18.0 adaptation without biometrics.
        """
        # ATTR_Ø (Zeroing ability): High when agent isn't thrashing (low AcOr) and resilient.
        attr_0 = (1.0 - current.get("AcOr", 0.5)) * k_res
        # ATTR_T (Synthesis ability): High when agent deeply analyzes (high IP) and resilient.
        attr_t = current.get("IP", 0.5) * k_res
        return max(0.0, min(1.0, attr_0)), max(0.0, min(1.0, attr_t))

    def _compute_k_flow(self, attr_0: float, attr_t: float, k_res: float, tension: float) -> float:
        """
        Energy conductivity coefficient (Psychodynamic Ohm's law).
        Formula: |ATTR_T - ATTR_0| + (k_res^2) / (tension + 0.1)
        """
        if tension < 1e-9:
            tension = 1e-9  # protect from div-by-zero
        return abs(attr_t - attr_0) + (k_res ** 2) / (tension + 0.1)

    def _compute_phi_osps(self, current: Vector, tension: float, k_res: float) -> float:
        """
        Anti-Fragmentation Index (Phi). Measure of integrated information.
        Adaptation: k_res * (1 - tension) * mean(IP, AcOr)
        """
        avg_power = (current.get("IP", 0.0) + current.get("AcOr", 0.0)) / 2.0
        return k_res * (1.0 - tension) * avg_power

    def _determine_abstraction_level(self, current: Vector) -> str:
        """
        Determine abstraction level (Abstraction Ladder).
        Projection of Hermes axes onto OSPS Octant.
        """
        acor = current.get("AcOr", 0.5)
        ip = current.get("IP", 0.5)
        inex = current.get("InEx", 0.0)
        if acor > 0.7 and ip < 0.3:
            return "CONCRETE"       # Concrete swamp
        elif ip > 0.7 and inex < -0.4:
            return "PHILOSOPHICAL"  # Detached from reality
        elif ip > 0.6:
            return "STRATEGIC"      # Architectural overview
        else:
            return "TACTICAL"       # Working mode

    def update_history(self, new_obs: InputVector) -> None:
        self.history.append(self._validate_observation(new_obs))
        if len(self.history) > self.history_limit:
            self.history.pop(0)

    def report(self, current: Optional[Vector] = None) -> TriageReport:
        if current is None:
            current = self.compute_state(cast(List[InputVector], self.history)) if self.history else {ax: 0.0 for ax in self.AXES}
        else:
            current = self._validate_observation(cast(InputVector, current))
        tens = self.tension(current)
        axis, delta, direction = self.lever(current)
        risk = self.risk_level(tens)
        k_res = self.k_resilience(tens)

        # === OSPS v18.0 Computations ===
        attr_0, attr_t = self._compute_attr(current, tens, k_res)
        k_flow = self._compute_k_flow(attr_0, attr_t, k_res, tens)
        phi_osps = self._compute_phi_osps(current, tens, k_res)
        abstraction_level = self._determine_abstraction_level(current)

        stable = (tens < self.risk_thresholds.low and direction == "balanced") or (tens < 1e-6)

        if direction == "balanced":
            advice = "System on target. Hold course."
        elif direction == "excess":
            advice = f"Decrease parameter '{axis}' by ~{abs(delta):.2f}"
        else:
            advice = f"Increase parameter '{axis}' by ~{abs(delta):.2f}"

        if risk == "critical":
            advice += " | RED ALERT: CRITICAL RISK. Immediate correction required."
        elif risk == "high":
            advice += " | WARNING: High risk. Strategy change required."
        elif stable:
            advice += " | OK: Stable."

        return TriageReport(
            schema_version=self.SCHEMA_VERSION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            current_vector=current,
            target_vector=dict(self.target),
            tension=round(tens, 4),
            lever_axis=axis,
            lever_delta=round(delta, 4),
            lever_direction=direction,
            risk=risk,
            forecast=self.forecast(current),
            stable=stable,
            k_res=round(k_res, 4),
            attr_0=round(attr_0, 4),
            attr_t=round(attr_t, 4),
            k_flow=round(k_flow, 4),
            phi_osps=round(phi_osps, 4),
            abstraction_level=abstraction_level,
            advice=advice
        )

    # ====================== SERIALIZATION ======================

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "target": self.target,
            "history": self.history,
            "history_limit": self.history_limit,
            "use_ema": self.use_ema,
            "ema_alpha": self.ema_alpha,
            "risk_thresholds": asdict(self.risk_thresholds),
            "strict_target": self.strict_target,
            "forecast_steps": self.forecast_steps
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermesTriageModule":
        if data.get("schema_version") not in (cls.SCHEMA_VERSION, "3.0.0-alpha.1", "1.5.1", "1.5.0", "1.4.0"):
            raise ValueError(f"Schema mismatch: expected {cls.SCHEMA_VERSION}, got {data.get('schema_version')}")
        thresholds = RiskThresholds(**data["risk_thresholds"])
        module = cls(
            target=data["target"],
            history_limit=data["history_limit"],
            use_ema=data["use_ema"],
            ema_alpha=data["ema_alpha"],
            risk_thresholds=thresholds,
            strict_target=data["strict_target"],
            forecast_steps=data.get("forecast_steps", 2)
        )
        module.history = [module._validate_observation(obs) for obs in data.get("history", [])]
        return module

    # ====================== STATIC METHODS ======================

    @staticmethod
    def inter_agent_tension(vectors: List[Vector]) -> Dict[str, Any]:
        if len(vectors) < 2:
            return {
                "mean_tension": 0.0,
                "mean_squared_deviation": {ax: 0.0 for ax in HermesTriageModule.AXES},
                "coherent": True
            }
        tensions = [
            math.sqrt(sum((v1[ax] - v2[ax]) ** 2 for ax in HermesTriageModule.AXES))
            for v1, v2 in combinations(vectors, 2)
        ]
        mean_tension = sum(tensions) / len(tensions)
        mean_squared_deviation = {}
        for ax in HermesTriageModule.AXES:
            vals = [v[ax] for v in vectors]
            mean_val = sum(vals) / len(vals)
            mean_squared_deviation[ax] = sum((x - mean_val) ** 2 for x in vals) / len(vals)
        return {
            "mean_tension": round(mean_tension, 4),
            "mean_squared_deviation": {k: round(v, 4) for k, v in mean_squared_deviation.items()},
            "coherent": mean_tension < 0.5
        }

    @staticmethod
    def export_metrics(report: TriageReport) -> Dict[str, Any]:
        metrics = {
            "kres": report.k_res,
            "tension": report.tension,
            "stable": int(report.stable),
            "risk_critical": int(report.risk == "critical"),
            "risk_high": int(report.risk == "high"),
        }
        for ax in HermesTriageModule.AXES:
            metrics[f"current_{ax.lower()}"] = report.current_vector[ax]
            metrics[f"target_{ax.lower()}"] = report.target_vector[ax]
        if report.lever_axis:
            metrics[f"lever_delta_{report.lever_axis.lower()}"] = report.lever_delta
        for i, step in enumerate(report.forecast):
            for ax in HermesTriageModule.AXES:
                metrics[f"forecast_step{i+1}_{ax.lower()}"] = step[ax]
        return metrics


# ====================== INTEGRATIONS ======================

def action_to_vector(action_text: str) -> Vector:
    """Stub sensor. Replace with LLM evaluator in production."""
    text = action_text.lower()
    acor = 0.7 if any(w in text for w in ["rush", "urgent", "fast", "generate", "execute"]) else 0.0
    ip = 0.6 if any(w in text for w in ["analyze", "systematize", "architecture", "think", "plan"]) else 0.0
    inex = (0.5 if any(w in text for w in ["external", "user", "market", "client"]) else
            -0.5 if any(w in text for w in ["internal", "self", "reflection"]) else 0.0)
    return {
        "AcOr": max(-1.0, min(1.0, acor)),
        "IP": max(-1.0, min(1.0, ip)),
        "InEx": max(-1.0, min(1.0, inex))
    }


def triage_inject_prompt(report: TriageReport, base_prompt: str) -> str:
    """Inject diagnostic data into a prompt."""
    injection = f"""
[HERMES-TRIAGE v{report.schema_version}]
Vector: AcOr={report.current_vector['AcOr']:.2f}, IP={report.current_vector['IP']:.2f}, InEx={report.current_vector['InEx']:.2f}
Tension: {report.tension:.2f} (Kres={report.k_res:.2f}) | Risk: {report.risk.upper()}
Lever: {report.lever_axis or 'None'} ({report.lever_direction}, Δ={report.lever_delta:.2f})
Directive: {report.advice}
[/HERMES-TRIAGE]
"""
    return base_prompt + "\n" + injection


# ====================== MAIN ======================

if __name__ == "__main__":
    print("=== Hermes Triage Module v1.5.1 -- Test ===\n")
    hermes = HermesTriageModule(target={"AcOr": 0.2, "IP": 0.5, "InEx": -0.1}, use_ema=True)
    hermes.update_history({"AcOr": 0.8, "IP": 0.1, "InEx": 0.3})
    hermes.update_history({"AcOr": 0.9, "IP": 0.0, "InEx": 0.4})
    rep = hermes.report()
    print(f"Kres: {rep.k_res:.3f} | Risk: {rep.risk} | Stable: {rep.stable}")
    print(f"Advice: {rep.advice}")
