"""KentaurMind v3.0.0-alpha.6 — Quantum Gate / OSPS Central Nervous System."""
from dataclasses import dataclass
from typing import Dict, Any, List
from .core import KentaurCore, TriageReport, Vector
from .profiler import KentaurProfiler
from .governor import KentaurGovernor, EnforcementLevel
from .navigator import KentaurNavigator
from .abstractor import KentaurAbstractor
from .memory import KentaurMemory


@dataclass(frozen=True)
class MindVerdict:
    """Unified verdict of the agent nervous system (Quantum Gate output)."""
    report: TriageReport
    current_profile: str
    profile_shifted: bool
    directives_for_prompt: str
    modified_agent_state: Dict[str, Any]


class KentaurMind:
    """
    Quantum Gate / OSPS Central Nervous System.
    Closes the full cycle: Triage -> Profiler -> Governor -> Navigator -> Abstractor.
    """

    def __init__(self, initial_profile: str = "sleeper", memory_size: int = 100):
        self.profiler = KentaurProfiler()
        self.governor = KentaurGovernor()
        self.navigator = KentaurNavigator()
        self.abstractor = KentaurAbstractor()
        self.memory = KentaurMemory(similarity_threshold=0.82, max_episodes=memory_size)

        # Determine initial profile
        profile = self.profiler.determine_profile(0.0, 0.0)
        if initial_profile == "master":
            profile = self.profiler.determine_profile(1.0, 1.0)
        elif initial_profile == "alchemist":
            profile = self.profiler.determine_profile(1.0, 0.0)
        elif initial_profile == "integrator":
            profile = self.profiler.determine_profile(0.0, 1.0)

        self.core = KentaurCore(
            target=profile.target,
            risk_thresholds=profile.risk_thresholds,
            strict_target=False
        )
        self.current_profile_name = profile.name

    def process(self,
                current_vector: Vector,
                agent_loop_state: Dict[str, Any],
                context: str = "") -> MindVerdict:
        """
        Full Quantum Gate cycle (Input -> Collapse -> Output).
        """
        directives: List[str] = []
        modified_state = dict(agent_loop_state)

        # === 1. INPUT PORT: Triage ===
        report = self.core.report(current_vector)

        # === 2. SELECTOR: Profiler ===
        new_profile = self.profiler.determine_profile(
            getattr(report, 'attr_0', 0.0),
            getattr(report, 'attr_t', 0.0),
            self.current_profile_name
        )

        profile_shifted = False
        if new_profile.name != self.current_profile_name:
            profile_shifted = True
            self.current_profile_name = new_profile.name
            self.core = self.profiler.apply(self.core, new_profile)
            report = self.core.report(current_vector)
            directives.append(
                f"[PROFILE SHIFT]: {new_profile.name} - {new_profile.description}"
            )

        # === 3. SELECTOR: Governor (Fuses) ===
        gov_verdict = self.governor.judge(report)
        if gov_verdict.level in (EnforcementLevel.HALT, EnforcementLevel.RESTRICT):
            self.core.fuse_conflicts += 1
            report = self.core.report(current_vector)  # Recalculate with lower Phi

        if gov_verdict.forced_temperature is not None:
            modified_state["temperature"] = gov_verdict.forced_temperature

        if gov_verdict.blocked_tools:
            current_tools = list(modified_state.get("available_tools", []))
            if "all" in gov_verdict.blocked_tools:
                modified_state["available_tools"] = []
            else:
                modified_state["available_tools"] = [
                    t for t in current_tools if t not in gov_verdict.blocked_tools
                ]

        if gov_verdict.override_prompt:
            directives.append(gov_verdict.override_prompt)
        if gov_verdict.level == EnforcementLevel.HALT:
            modified_state["force_stop"] = True

        # === MEMORY: Check reflexes after Governor ===
        reflex = self.memory.get_reflex_prompt(current_vector)
        if reflex:
            directives.append(reflex)

        # === Record crisis in memory with auto-generated lesson ===
        if gov_verdict.level in (EnforcementLevel.HALT, EnforcementLevel.RESTRICT):
            self.memory.record(
                context=context or "Agent loop step",
                state_vector=dict(current_vector),
                outcome=gov_verdict.level.value,
                lesson=None  # Auto-generate contextual lesson
            )

        # === 4. SELECTOR: Navigator (Cognitive Therapy) ===
        nav_prescription = self.navigator.prescribe(report, self.current_profile_name)
        if nav_prescription.forced_thought_pattern:
            directives.append(f"[NAVIGATOR]: {nav_prescription.forced_thought_pattern}")
        modified_state = self.navigator.apply_guidance(
            report, modified_state, self.current_profile_name
        )

        # === 5. META-COGNITION: Abstractor ===
        shift = self.abstractor.prescribe_shift(report)
        if shift:
            directives.append(shift.shift_command)

        # === 6. OUTPUT PORT: Build unified prompt ===
        if directives:
            unified_directive = "\n".join(directives)
            modified_state["system_prompt"] = (
                f"=== HERMES DIRECTIVES ===\n"
                f"{unified_directive}\n"
                f"=== END ===\n\n"
                f"{modified_state.get('system_prompt', '')}"
            )

        return MindVerdict(
            report=report,
            current_profile=self.current_profile_name,
            profile_shifted=profile_shifted,
            directives_for_prompt=unified_directive if directives else "No directives.",
            modified_agent_state=modified_state
        )
