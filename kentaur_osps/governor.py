"""KentaurGovernor v3.0.0-alpha.4 — Immune System / Fuses (OSPS v18.0)."""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from .core import TriageReport


class EnforcementLevel(Enum):
    NONE = "none"
    CAUTION = "caution"
    RESTRICT = "restrict"
    HALT = "halt"


@dataclass(frozen=True)
class GovernorVerdict:
    level: EnforcementLevel
    reason: str
    e_code: str = "E-000"                       # OSPS existential anxiety code
    forced_temperature: Optional[float] = None
    blocked_tools: Optional[List[str]] = None
    override_prompt: Optional[str] = None


class KentaurGovernor:
    """
    Immune System / Fuses (OSPS v18.0).
    Dumb protection layer: diagnoses E-codes and triggers Ø reset ritual (H.R.R.R.).
    """

    def _diagnose_e_code(self, report: TriageReport) -> str:
        """Diagnose existential anxiety based on ATTR, Phi, and axes."""
        # E-401: Critical fragmentation / Panic (near-zero Phi)
        if report.phi_osps < 0.02:
            return "E-401"
        # E-502: Social stupor / Loss of connection with Source
        if report.attr_0 < 0.25 and report.attr_t > 0.7:
            return "E-502"
        # E-301: Action overheat
        if report.lever_axis == "AcOr" and report.lever_direction == "excess" and report.tension > 0.8:
            return "E-301"
        return "E-000"  # Normal

    def judge(self, report: TriageReport) -> GovernorVerdict:
        """Deliver verdict based on OSPS diagnosis."""
        e_code = self._diagnose_e_code(report)

        # 1. H.R.R.R.: Safety fuse catches truly critical states
        if report.risk == "critical" and report.phi_osps < 0.4:
            return GovernorVerdict(
                level=EnforcementLevel.HALT,
                reason=f"SAFETY FUSE: Critical state (Phi={report.phi_osps:.2f}, risk={report.risk}). Reset to Void.",
                e_code=e_code,
                forced_temperature=0.0,
                blocked_tools=["all"],
                override_prompt=(
                    "H.R.R.R. PROTOCOL ACTIVATED\n"
                    "HOLD - stop all actions.\n"
                    "READ - read the last stable context.\n"
                    "ROUTE - return to Anchor (ATTR_T).\n"
                    "RENDER - start a new cycle from Ø."
                )
            )

        # 2. E-401: Critical fragmentation / Panic
        if e_code == "E-401":
            return GovernorVerdict(
                level=EnforcementLevel.HALT,
                reason=f"Ø-RESET: Critical fragmentation (Phi={report.phi_osps:.2f}). Reset to Void.",
                e_code=e_code,
                forced_temperature=0.0,
                blocked_tools=["all"],
                override_prompt=(
                    "H.R.R.R. PROTOCOL ACTIVATED\n"
                    "HOLD - stop all actions.\n"
                    "READ - read the last stable context.\n"
                    "ROUTE - return to Anchor (ATTR_T).\n"
                    "RENDER - start a new cycle from Ø."
                )
            )

        # 3. E-301: Action overheat (checked before RESTRICT)
        if e_code == "E-301":
            return GovernorVerdict(
                level=EnforcementLevel.RESTRICT,
                reason=f"RESTRICT: Action overheat (E-301). Reduce AcOr.",
                e_code=e_code,
                forced_temperature=0.2,
                blocked_tools=["execute_bash", "send_message"]
            )

        # 4. E-502: Loss of Source connection
        if e_code == "E-502":
            return GovernorVerdict(
                level=EnforcementLevel.CAUTION,
                reason=f"CAUTION: Social stupor / Loss of Source (E-502).",
                e_code=e_code,
                forced_temperature=0.5
            )

        # 5. RESTRICT: High risk (generic)
        if report.risk == "high":
            return GovernorVerdict(
                level=EnforcementLevel.RESTRICT,
                reason=f"RESTRICT: High risk ({report.risk}).",
                e_code=e_code,
                forced_temperature=0.2,
                blocked_tools=["execute_bash", "send_message"]
            )

        # 6. CAUTION: Medium risk
        if report.risk == "medium":
            return GovernorVerdict(
                level=EnforcementLevel.CAUTION,
                reason=f"CAUTION: Medium risk.",
                e_code=e_code,
                forced_temperature=0.5
            )

        # 7. NONE: All stable
        return GovernorVerdict(
            level=EnforcementLevel.NONE,
            reason="Stable.",
            e_code="E-000"
        )
