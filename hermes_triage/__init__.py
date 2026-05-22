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

from .mind import (
    HermesMind,
    MindVerdict,
)

__version__ = "2.3.0"
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
