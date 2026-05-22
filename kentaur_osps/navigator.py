"""KentaurNavigator v3.0.0-alpha.5 — OSPS Cognitive Therapy (Archetype + Abstraction routing)."""
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from .core import TriageReport


@dataclass(frozen=True)
class NavigationPrescription:
    forced_thought_pattern: Optional[str] = None
    recommended_tools: Tuple[str, ...] = ()
    blocked_tools: Tuple[str, ...] = ()
    rationale: str = "No correction needed."


class KentaurNavigator:
    """
    OSPS v18.0 Cognitive Therapy.
    Routing depends on Archetype (from Profiler) and Abstraction Level.
    """

    def prescribe(self, report: TriageReport,
                  current_profile: str = "sleeper") -> NavigationPrescription:
        level = getattr(report, 'abstraction_level', 'TACTICAL')

        if current_profile == "master":
            return self._master_navigate(level)
        elif current_profile == "alchemist":
            return self._alchemist_navigate(level)
        elif current_profile == "integrator":
            return self._integrator_navigate(level)
        elif current_profile == "sleeper":
            return self._sleeper_navigate()
        return self._fallback_navigate(report)

    def _master_navigate(self, level: str) -> NavigationPrescription:
        if level == "PHILOSOPHICAL":
            return NavigationPrescription(
                forced_thought_pattern="Vision expanded. Refocus on materialization.",
                recommended_tools=("render_project", "delegate_task"),
                rationale="Master + PHILOSOPHICAL: Materialization required."
            )
        return NavigationPrescription(rationale="Master is autonomous.")

    def _alchemist_navigate(self, level: str) -> NavigationPrescription:
        if level == "CONCRETE":
            return NavigationPrescription(
                forced_thought_pattern="You are stuck in details. Break the form. Find the pattern.",
                recommended_tools=("analyze_logs", "delete_file", "restructure"),
                blocked_tools=("execute_bash", "send_message"),
                rationale="Alchemist + CONCRETE: Creative destruction."
            )
        elif level == "STRATEGIC":
            return NavigationPrescription(
                forced_thought_pattern="Ideal state. Remove the old and design the new.",
                recommended_tools=("restructure", "design_pattern"),
                rationale="Alchemist + STRATEGIC: Creative destruction."
            )
        return NavigationPrescription(rationale="Alchemist is balanced.")

    def _integrator_navigate(self, level: str) -> NavigationPrescription:
        if level == "PHILOSOPHICAL":
            return NavigationPrescription(
                forced_thought_pattern="You drifted away. Land. Make a concrete step.",
                recommended_tools=("execute_bash", "send_message"),
                blocked_tools=("think_step_by_step",),
                rationale="Integrator + PHILOSOPHICAL: Grounding."
            )
        elif level == "CONCRETE":
            return NavigationPrescription(
                forced_thought_pattern="Micromanagement danger. Delegate.",
                recommended_tools=("design_pattern", "review_pr"),
                blocked_tools=("execute_bash",),
                rationale="Integrator + CONCRETE: Escape details."
            )
        return NavigationPrescription(rationale="Integrator is balanced.")

    def _sleeper_navigate(self) -> NavigationPrescription:
        return NavigationPrescription(
            forced_thought_pattern="Activity reduced. Follow instructions strictly.",
            recommended_tools=("read_file", "search_web"),
            blocked_tools=("execute_bash", "send_message", "delete_file"),
            rationale="Sleeper: Read-only mode."
        )

    def _fallback_navigate(self, report: TriageReport) -> NavigationPrescription:
        if report.lever_axis == "AcOr" and report.lever_direction == "excess":
            return NavigationPrescription(
                forced_thought_pattern="Reduce impulsivity. Plan first.",
                recommended_tools=("think_step_by_step",),
                blocked_tools=("execute_bash",),
                rationale="Fallback: AcOr excess."
            )
        return NavigationPrescription(rationale="Fallback: Balanced.")

    def apply_guidance(self, report: TriageReport,
                       agent_loop_state: Dict[str, Any],
                       current_profile: str = "sleeper") -> Dict[str, Any]:
        """Apply navigation prescription to agent loop state."""
        presc = self.prescribe(report, current_profile)
        modified = dict(agent_loop_state)

        # Inject thought pattern into system prompt
        if presc.forced_thought_pattern:
            modified["system_prompt"] = (
                f"[NAVI-GUIDANCE]: {presc.forced_thought_pattern}\n\n"
                f"{modified.get('system_prompt', '')}"
            )

        # Filter tools
        current_tools = list(modified.get("available_tools", []))
        # Filter tools by name
        if presc.blocked_tools:
            current_tools = [t for t in current_tools
                             if t.get("function", {}).get("name", str(t)) not in presc.blocked_tools]
        modified["available_tools"] = current_tools

        return modified
