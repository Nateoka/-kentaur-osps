"""HermesMind v3.0.0-alpha.6 — Quantum Gate / OSPS Central Nervous System."""
from dataclasses import dataclass
from typing import Dict, Any, List
from .triage import HermesTriageModule, TriageReport, Vector
from .profiler import HermesProfiler
from .governor import HermesGovernor, EnforcementLevel
from .navigator import HermesNavigator
from .abstractor import HermesAbstractor


@dataclass(frozen=True)
class MindVerdict:
    """Unified verdict of the agent nervous system (Quantum Gate output)."""
    report: TriageReport
    current_profile: str
    profile_shifted: bool
    directives_for_prompt: str
    modified_agent_state: Dict[str, Any]


class HermesMind:
    """
    Quantum Gate / OSPS Central Nervous System.
    Closes the full cycle: Triage -> Profiler -> Governor -> Navigator -> Abstractor.
    """

    def __init__(self, initial_profile: str = "sleeper"):
        self.profiler = HermesProfiler()
        self.governor = HermesGovernor()
        self.navigator = HermesNavigator()
        self.abstractor = HermesAbstractor()

        # Determine initial profile
        profile = self.profiler.determine_profile(0.0, 0.0)
        if initial_profile == "master":
            profile = self.profiler.determine_profile(1.0, 1.0)
        elif initial_profile == "alchemist":
            profile = self.profiler.determine_profile(1.0, 0.0)
        elif initial_profile == "integrator":
            profile = self.profiler.determine_profile(0.0, 1.0)

        self.core = HermesTriageModule(
            target=profile.target,
            risk_thresholds=profile.risk_thresholds,
            strict_target=False
        )
        self.current_profile_name = profile.name

    def process(self,
                current_vector: Vector,
                agent_loop_state: Dict[str, Any]) -> MindVerdict:
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

        # === 4. SELECTOR: Navigator (Cognitive Therapy) ===
        nav_prescription = self.navigator.prescribe(report, self.current_profile_name)
        if nav_prescription.forced_thought_pattern:
            directives.append(f"[NAVIGATOR]: {nav_prescription.forced_thought_pattern}")

        available_tools = list(modified_state.get("available_tools", []))
        if nav_prescription.blocked_tools:
            available_tools = [t for t in available_tools
                               if t not in nav_prescription.blocked_tools]
        if nav_prescription.recommended_tools:
            available_tools = list(set(available_tools +
                                       list(nav_prescription.recommended_tools)))
        modified_state["available_tools"] = available_tools

        # === 5. META-COGNITION: Abstractor ===
        abstraction_level = getattr(report, 'abstraction_level', 'TACTICAL')
        if abstraction_level == "CONCRETE":
            directives.append(
                "[ABSTRACTOR]: Zoom out. You are stuck in details."
            )
        elif abstraction_level == "PHILOSOPHICAL":
            directives.append(
                "[ABSTRACTOR]: Come back to earth. You are detached from reality."
            )

        # === 6. OUTPUT PORT: Build unified prompt ===
        if directives:
            unified_directive = "\n".join(directives)
            modified_state["system_prompt"] = (
                f"=== HERMES SYSTEM DIRECTIVES ===\n"
                f"{unified_directive}\n"
                f"=== END OF DIRECTIVES ===\n\n"
                f"{modified_state.get('system_prompt', '')}"
            )
        else:
            unified_directive = "No directives."

        return MindVerdict(
            report=report,
            current_profile=self.current_profile_name,
            profile_shifted=profile_shifted,
            directives_for_prompt=unified_directive,
            modified_agent_state=modified_state
        )
