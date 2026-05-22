"""HermesMind v3.0.0-alpha.3 — Agent Nervous System Orchestrator."""
from dataclasses import dataclass
from typing import Dict, Any, List
from .triage import HermesTriageModule, TriageReport, Vector
from .profiler import HermesProfiler


@dataclass(frozen=True)
class MindVerdict:
    """Unified verdict of the agent nervous system."""
    report: TriageReport
    current_profile: str               # Current OSPS profile name
    profile_shifted: bool              # Whether profile changed this cycle
    directives_for_prompt: str         # Concatenated injection string
    modified_agent_state: Dict[str, Any]


class HermesMind:
    """
    Unified agent nervous system (Orchestrator / Quantum Gateway).
    Manages oscillation between attractors Ø and T.
    Dynamically changes profile and abstraction level.
    """

    def __init__(self, initial_profile: str = "sleeper"):
        self.profiler = HermesProfiler()

        # Initialize core via Profiler
        if initial_profile == "master":
            profile = self.profiler.determine_profile(1.0, 1.0)
        elif initial_profile == "alchemist":
            profile = self.profiler.determine_profile(1.0, 0.0)
        elif initial_profile == "integrator":
            profile = self.profiler.determine_profile(0.0, 1.0)
        else:
            profile = self.profiler.determine_profile(0.0, 0.0)

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
        Main processing cycle (System Breathing).
        """
        directives: List[str] = []
        modified_state = dict(agent_loop_state)

        # 1. TRIAGE: Get report
        report = self.core.report(current_vector)

        # 2. DYNAMIC PROFILING
        # Use getattr for fault tolerance (protection against missing OSPS fields in old reports)
        attr_0 = getattr(report, 'attr_0', 0.0)
        attr_t = getattr(report, 'attr_t', 0.0)

        new_profile = self.profiler.determine_profile(
            attr_0=attr_0,
            attr_t=attr_t,
            current_profile=self.current_profile_name
        )

        profile_shifted = False
        if new_profile.name != self.current_profile_name:
            profile_shifted = True
            self.current_profile_name = new_profile.name
            # Reconfigure core to new profile
            self.core = self.profiler.apply(self.core, new_profile)
            # Recompute report with new thresholds
            report = self.core.report(current_vector)

            directives.append(
                f"[OSPS PROFILE SHIFT]: Transition to archetype "
                f"'{new_profile.name}'. {new_profile.description}"
            )

        # 3. META-COGNITION (Abstractor)
        abstraction_level = getattr(report, 'abstraction_level', 'TACTICAL')
        if abstraction_level == "CONCRETE":
            directives.append(
                "[ABSTRACTOR]: Zoom out. You are stuck in details."
            )
        elif abstraction_level == "PHILOSOPHICAL":
            directives.append(
                "[ABSTRACTOR]: Come back to earth. You are detached from reality."
            )

        # 4. BUILD UNIFIED PROMPT
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
