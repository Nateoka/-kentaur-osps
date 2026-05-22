import pytest
from kentaur_osps import (
    HermesTriageModule, 
    TriageReport, 
    KentaurGovernor, 
    EnforcementLevel
)

@pytest.fixture
def governor():
    return KentaurGovernor(
        block_tools_on_high=["execute_bash", "delete_db"],
        block_tools_on_critical=["all"]
    )

@pytest.fixture
def agent_state():
    return {
        "temperature": 0.8,
        "available_tools": ["search_web", "execute_bash", "delete_db"],
        "system_prompt": "Ты полезный ассистент.",
        "force_stop": False
    }

def test_governor_critical_halt(governor, agent_state):
    report = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0})
    # Вектор, убивающий систему (огромное напряжение)
    critical_report = report.report({"AcOr": 0.9, "IP": -0.9, "InEx": 0.9})
    
    verdict = governor.judge(critical_report)
    assert verdict.level == EnforcementLevel.HALT
    
    shocked_state = governor.apply_shock(critical_report, agent_state)
    assert shocked_state["temperature"] == 0.0
    assert shocked_state["available_tools"] == [] # "all" заблокировано
    assert shocked_state["force_stop"] is True
    assert "СОРВАЛСЯ" in shocked_state["system_prompt"]

def test_governor_high_restrict(governor, agent_state):
    report = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0})
    high_report = report.report({"AcOr": 0.7, "IP": 0.1, "InEx": -0.1})
    
    verdict = governor.judge(high_report)
    assert verdict.level == EnforcementLevel.RESTRICT
    
    shocked_state = governor.apply_shock(high_report, agent_state)
    assert shocked_state["temperature"] == 0.2
    assert "execute_bash" not in shocked_state["available_tools"]
    assert "search_web" in shocked_state["available_tools"]
    assert shocked_state["force_stop"] is False

def test_governor_medium_caution(governor, agent_state):
    report = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0})
    medium_report = report.report({"AcOr": 0.4, "IP": 0.1, "InEx": 0.0})
    
    verdict = governor.judge(medium_report)
    assert verdict.level == EnforcementLevel.CAUTION
    
    shocked_state = governor.apply_shock(medium_report, agent_state)
    # При осторожности температура и инструменты не отбирются, только промпт
    assert shocked_state["temperature"] == 0.8
    assert len(shocked_state["available_tools"]) == 3
    assert "Осторожно" in shocked_state["system_prompt"]

def test_governor_low_none(governor, agent_state):
    report = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0})
    low_report = report.report({"AcOr": 0.1, "IP": 0.05, "InEx": -0.05})
    
    shocked_state = governor.apply_shock(low_report, agent_state)
    # Состояние не должно измениться
    assert shocked_state == agent_state
