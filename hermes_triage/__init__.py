"""
Hermes Triage Module - Three-axis diagnostic system for agents.
Version: 2.3.0
"""

from .triage import (
    HermesTriageModule,
    RiskThresholds,
    TriageReport,
    Vector,
    AxisName,
    action_to_vector,
    triage_inject_prompt,
)

from .governor import (
    HermesGovernor,
    EnforcementLevel,
    GovernorVerdict,
)

from .mind import (
    HermesMind,
    MindVerdict,
)

__version__ = "3.0.0-alpha.4"
__all__ = [
    "HermesTriageModule",
    "RiskThresholds",
    "TriageReport",
    "Vector",
    "AxisName",
    "action_to_vector",
    "triage_inject_prompt",
    "HermesMind",
    "MindVerdict",
]
