"""
Tests for HermesTriageModule v2.3.0
Full coverage + hardened production edge-cases + Mind integration
"""

import pytest
from hermes_triage import (
    HermesTriageModule,
    RiskThresholds,
    TriageReport,
    action_to_vector,
    triage_inject_prompt,
    HermesMind,
    MindVerdict,
)


# ====================== FIXTURES ======================

@pytest.fixture
def default_hermes():
    return HermesTriageModule(
        target={"AcOr": 0.2, "IP": 0.5, "InEx": -0.1},
        use_ema=False,
        forecast_steps=3
    )


@pytest.fixture
def ema_hermes():
    return HermesTriageModule(
        target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0},
        use_ema=True,
        ema_alpha=0.5
    )


# ====================== VALIDATION ======================

def test_validate_target_strict_mode():
    with pytest.raises(ValueError, match="out of bounds"):
        HermesTriageModule(target={"AcOr": 1.5}, strict_target=True)


def test_validate_target_non_strict_clamping():
    hermes = HermesTriageModule(target={"AcOr": 1.5, "IP": -2.0}, strict_target=False)
    assert hermes.target["AcOr"] == 1.0
    assert hermes.target["IP"] == -1.0


def test_observation_invalid_type(default_hermes):
    with pytest.raises(ValueError, match="expected number"):
        default_hermes._validate_observation({"AcOr": "0.8", "IP": 0.1, "InEx": 0.2})


# ====================== STATISTICS ======================

def test_median_odd_and_even():
    hermes = HermesTriageModule(use_ema=False)
    # odd
    state = hermes.compute_state([
        {"AcOr": -0.5, "IP": 0.0, "InEx": 0.0},
        {"AcOr": 0.1, "IP": 0.0, "InEx": 0.0},
        {"AcOr": 0.5, "IP": 0.0, "InEx": 0.0},
    ])
    assert abs(state["AcOr"] - 0.1) < 1e-9
    # even
    state = hermes.compute_state([
        {"AcOr": 0.2, "IP": 0.0, "InEx": 0.0},
        {"AcOr": 0.8, "IP": 0.0, "InEx": 0.0},
    ])
    assert abs(state["AcOr"] - 0.5) < 1e-9


def test_ema_calculation(ema_hermes):
    observations = [
        {"AcOr": 0.0, "IP": 0.0, "InEx": 0.0},
        {"AcOr": 1.0, "IP": 0.0, "InEx": 0.0},
        {"AcOr": 1.0, "IP": 0.0, "InEx": 0.0},
    ]
    state = ema_hermes.compute_state(observations)
    # Real EMA: 0.0 -> 0.5 -> 0.75
    assert abs(state["AcOr"] - 0.75) < 1e-9


def test_empty_history():
    hermes = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0})
    state = hermes.compute_state([])
    assert all(v == 0.0 for v in state.values())
    rep = hermes.report()
    assert rep.tension == 0.0
    assert rep.stable is True


# ====================== LEVER ======================

def test_lever_priority_when_deltas_equal():
    """Priority: AcOr > IP > InEx when delta magnitudes are equal."""
    hermes = HermesTriageModule(target={"AcOr": 0, "IP": 0, "InEx": 0})
    current = {"AcOr": 0.5, "IP": 0.5, "InEx": 0.5}
    axis, delta, direction = hermes.lever(current)
    assert axis == "AcOr"
    assert direction == "excess"


def test_lever_balanced():
    hermes = HermesTriageModule(target={"AcOr": 0.3, "IP": 0.4, "InEx": -0.2})
    axis, delta, direction = hermes.lever({"AcOr": 0.3, "IP": 0.4, "InEx": -0.2})
    assert axis is None
    assert direction == "balanced"


# ====================== REPORT & FORECAST ======================

def test_report_stable_condition(default_hermes):
    rep = default_hermes.report({"AcOr": 0.2, "IP": 0.5, "InEx": -0.1})
    assert rep.stable is True
    assert "Hold course" in rep.advice or "Stable" in rep.advice


def test_forecast_steps_zero(default_hermes):
    current = {"AcOr": 0.5, "IP": 0.5, "InEx": 0.5}
    assert default_hermes.forecast(current, steps=0) == []


def test_forecast_convergence(default_hermes):
    forecast = default_hermes.forecast({"AcOr": 0.9, "IP": 0.9, "InEx": 0.9}, steps=10)
    last = forecast[-1]
    assert abs(last["AcOr"] - 0.2) < 0.2
    assert abs(last["IP"] - 0.5) < 0.2
    assert abs(last["InEx"] - (-0.1)) < 0.2


# ====================== HARDENED EDGE-CASES ======================

def test_ema_alpha_clamping():
    """EMA alpha must be clamped to [0.01, 0.99]."""
    h1 = HermesTriageModule(use_ema=True, ema_alpha=-10)
    h2 = HermesTriageModule(use_ema=True, ema_alpha=999)
    assert h1.ema_alpha == 0.01
    assert h2.ema_alpha == 0.99


def test_observation_clamping():
    """Values outside [-1, 1] in observations must be silently clamped."""
    hermes = HermesTriageModule()
    dirty = {"AcOr": 2.7, "IP": -1.8, "InEx": 0.5}
    state = hermes.compute_state([dirty])
    assert state["AcOr"] == 1.0
    assert state["IP"] == -1.0
    assert state["InEx"] == 0.5


def test_from_dict_dirty_history():
    """Deserialize dirty data from storage with clamping."""
    dirty_data = {
        "schema_version": "1.5.1",
        "target": {"AcOr": 0.0, "IP": 0.0, "InEx": 0.0},
        "history": [
            {"AcOr": 5.0},                              # missing axes + out of bounds
            {"AcOr": -0.5, "IP": 1.8, "InEx": 0.1}     # out of bounds
        ],
        "history_limit": 5,
        "use_ema": False,
        "ema_alpha": 0.3,
        "risk_thresholds": {"critical": 1.2, "high": 0.6, "medium": 0.3, "low": 0.2},
        "strict_target": True,
        "forecast_steps": 2
    }
    restored = HermesTriageModule.from_dict(dirty_data)
    assert restored.history[0]["AcOr"] == 1.0   # 5.0 -> 1.0
    assert restored.history[0]["IP"] == 0.0     # default
    assert restored.history[0]["InEx"] == 0.0   # default
    assert restored.history[1]["IP"] == 1.0     # 1.8 -> 1.0


def test_from_dict_invalid_schema():
    invalid = {
        "schema_version": "99.99.99",
        "target": {"AcOr": 0, "IP": 0, "InEx": 0},
        "history": [],
        "history_limit": 5,
        "use_ema": False,
        "ema_alpha": 0.3,
        "risk_thresholds": {"critical": 1.2, "high": 0.6, "medium": 0.3, "low": 0.2},
        "strict_target": True
    }
    with pytest.raises(ValueError, match="Schema mismatch"):
        HermesTriageModule.from_dict(invalid)


# ====================== INTEGRATIONS ======================

def test_action_to_vector():
    vec = action_to_vector("Rush to generate content for the client")
    assert vec["AcOr"] > 0.6
    assert vec["InEx"] > 0.4


def test_triage_inject_prompt(default_hermes):
    rep = default_hermes.report()
    prompt = triage_inject_prompt(rep, "You are an AI assistant.")
    assert "[HERMES-TRIAGE" in prompt
    assert "Vector:" in prompt
    assert "Directive:" in prompt


def test_full_mind_integration():
    """Verify that the basic Mind assembles without errors."""
    mind = HermesMind(profile="analyst")
    verdict = mind.process(
        current_vector={"AcOr": 0.3, "IP": 0.6, "InEx": 0.0},
        agent_loop_state={"temperature": 0.7, "available_tools": [], "system_prompt": "Test"}
    )
    assert isinstance(verdict, MindVerdict)
    assert verdict.report is not None


# ====================== SERIALIZATION ======================

def test_serialization_roundtrip(default_hermes):
    default_hermes.update_history({"AcOr": 0.9, "IP": 0.1, "InEx": 0.3})
    data = default_hermes.to_dict()
    restored = HermesTriageModule.from_dict(data)
    assert restored.target == default_hermes.target
    assert restored.history == default_hermes.history
    assert restored.SCHEMA_VERSION == default_hermes.SCHEMA_VERSION


def test_inter_agent_tension():
    vectors = [
        {"AcOr": 0.8, "IP": 0.1, "InEx": 0.3},
        {"AcOr": 0.1, "IP": 0.8, "InEx": -0.5},
    ]
    result = HermesTriageModule.inter_agent_tension(vectors)
    assert "mean_tension" in result
    assert "mean_squared_deviation" in result
    assert isinstance(result["coherent"], bool)


def test_osps_v18_metrics():
    """Verify OSPS v18.0 attractor, conductivity, and anti-fragmentation metrics."""
    hermes = HermesTriageModule(target={"AcOr": 0.2, "IP": 0.8, "InEx": 0.0})

    # Deep reflection state: high IP, moderate AcOr → T coupling > Ø coupling
    report = hermes.report({"AcOr": 0.3, "IP": 0.9, "InEx": -0.2})
    assert report.attr_t > report.attr_0  # High IP → T coupling stronger
    assert report.abstraction_level in ("STRATEGIC", "PHILOSOPHICAL")
    assert report.k_flow > 0.0
    assert report.phi_osps > 0.0
    assert hasattr(report, 'attr_0')
    assert hasattr(report, 'attr_t')
    assert hasattr(report, 'k_flow')
    assert hasattr(report, 'phi_osps')
    assert hasattr(report, 'abstraction_level')

    # Panic state: high AcOr, very low IP → Ø coupling stronger
    report_panic = hermes.report({"AcOr": 0.9, "IP": 0.05, "InEx": 0.5})
    assert report_panic.attr_0 > report_panic.attr_t  # High AcOr → Ø coupling stronger
    assert report_panic.abstraction_level == "CONCRETE"

# ====================== RUNNER ======================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
