"""HermesConsensus v2.3.0 — Swarm policy and multi-agent alignment module."""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, cast
from .triage import HermesTriageModule, TriageReport, Vector, InputVector


class ConsensusState(Enum):
    """State of the consensus-building process."""
    DIVERGENT = "divergent"     # Agents disagree
    CONVERGING = "converging"   # Moving toward agreement
    REACHED = "reached"         # Consensus achieved
    FAILED = "failed"           # Cannot reach consensus


@dataclass
class ConsensusVerdict:
    """Result of a consensus round."""
    state: ConsensusState
    alignment_target: Vector
    confidence: float = 0.0
    dissenting_agents: List[str] = field(default_factory=list)
    summary: str = ""


class HermesConsensus:
    """
    Swarm consensus / multi-agent alignment module.
    Mediates between multiple HermesTriageModule instances (agents)
    to find a common alignment target.
    """

    def __init__(self, quorum: float = 0.6, max_rounds: int = 3):
        self.quorum = max(0.1, min(1.0, quorum))
        self.max_rounds = max(1, max_rounds)

    def align(self, agents: List[HermesTriageModule]) -> ConsensusVerdict:
        """
        Run a consensus round across agents.
        Returns an alignment target that satisfies the quorum.
        """
        if not agents:
            return ConsensusVerdict(
                state=ConsensusState.FAILED,
                alignment_target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0},
                summary="No agents to align."
            )

        targets = [dict(a.target) for a in agents]
        return self._vote_on_targets(targets)

    def _vote_on_targets(self, targets: List[Vector]) -> ConsensusVerdict:
        """Vote on targets: find the one closest to the mean."""
        if not targets:
            return ConsensusVerdict(
                state=ConsensusState.FAILED,
                alignment_target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0},
                summary="No targets provided."
            )

        # Compute mean target
        mean: Vector = {"AcOr": 0.0, "IP": 0.0, "InEx": 0.0}
        for t in targets:
            for ax in mean:
                mean[ax] += t.get(ax, 0.0)
        n = len(targets)
        for ax in mean:
            mean[ax] /= n

        # Find target closest to mean
        best_dist = float("inf")
        best_target = mean
        for t in targets:
            dist = sum((t.get(ax, 0) - mean[ax]) ** 2 for ax in mean)
            if dist < best_dist:
                best_dist = dist
                best_target = t

        # Check quorum
        agreeing = 0
        dissenting = []
        for i, t in enumerate(targets):
            dist = sum((t.get(ax, 0) - best_target[ax]) ** 2 for ax in mean)
            if dist < 0.1:  # within tolerance
                agreeing += 1
            else:
                dissenting.append(f"agent_{i}")

        confidence = agreeing / n if n > 0 else 0.0
        state = ConsensusState.REACHED if confidence >= self.quorum else ConsensusState.DIVERGENT

        return ConsensusVerdict(
            state=state,
            alignment_target=dict(best_target),
            confidence=round(confidence, 2),
            dissenting_agents=dissenting,
            summary=f"Consensus: {agreeing}/{n} agents aligned (quorum={self.quorum})."
        )

    def apply_alignment(self, agent_module: HermesTriageModule,
                        verdict: ConsensusVerdict) -> HermesTriageModule:
        """Apply consensus verdict to an agent module (re-target)."""
        if verdict.state != ConsensusState.REACHED:
            return agent_module

        aligned_module = HermesTriageModule(
            target=cast(InputVector, verdict.alignment_target),
            history_limit=agent_module.history_limit,
            use_ema=agent_module.use_ema,
            ema_alpha=agent_module.ema_alpha,
            risk_thresholds=agent_module.risk_thresholds,
            strict_target=False,
            forecast_steps=agent_module.forecast_steps
        )
        aligned_module.history = list(agent_module.history)
        return aligned_module
