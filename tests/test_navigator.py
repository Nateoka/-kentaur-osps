import pytest
from hermes_triage import (
    HermesTriageModule, 
    TriageReport, 
    HermesNavigator, 
    NavigationPrescription
)

@pytest.fixture
def navigator():
    # Используем кастомный маппинг для чистоты тестов
    return HermesNavigator(tool_mapping={
        "planning": ["plan_tool"],
        "action": ["act_tool"],
        "analysis": ["analyze_tool"],
        "external": ["ask_user_tool"],
        "internal": ["reflect_tool"]
    })

@pytest.fixture
def agent_state():
    return {
        "system_prompt": "Базовый промпт.",
        "available_tools": ["plan_tool", "act_tool", "analyze_tool", "ask_user_tool", "reflect_tool"]
    }

def test_navigator_acor_excess(navigator, agent_state):
    hermes = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0})
    # Агент паникует
    report = hermes.report({"AcOr": 0.8, "IP": 0.1, "InEx": 0.0})
    
    prescription = navigator.prescribe(report)
    assert "Остановись" in prescription.forced_thought_pattern
    assert "plan_tool" in prescription.recommended_tools
    assert "act_tool" in prescription.blocked_tools
    
    # Проверяем применение
    guided_state = navigator.apply_guidance(report, agent_state)
    assert "act_tool" not in guided_state["available_tools"]
    assert "plan_tool" in guided_state["available_tools"]
    assert "[NAVI-GUIDANCE]" in guided_state["system_prompt"]

def test_navigator_ip_deficit(navigator, agent_state):
    hermes = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.8, "InEx": 0.0})
    # Агент действует бездумно (IP ниже цели)
    report = hermes.report({"AcOr": 0.1, "IP": 0.1, "InEx": 0.0})
    
    prescription = navigator.prescribe(report)
    assert "анализируй" in prescription.forced_thought_pattern.lower()
    assert "analyze_tool" in prescription.recommended_tools
    assert "act_tool" in prescription.blocked_tools

def test_navigator_inex_deficit(navigator, agent_state):
    hermes = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.5})
    # Агент оторван от реальности (InEx ниже цели)
    report = hermes.report({"AcOr": 0.1, "IP": 0.1, "InEx": -0.5})
    
    prescription = navigator.prescribe(report)
    assert "внешн" in prescription.forced_thought_pattern.lower() or "обратную связь" in prescription.forced_thought_pattern.lower()
    assert "ask_user_tool" in prescription.recommended_tools
    assert "reflect_tool" in prescription.blocked_tools

def test_navigator_balanced(navigator, agent_state):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    report = hermes.report({"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    
    prescription = navigator.prescribe(report)
    assert prescription.forced_thought_pattern is None
    assert prescription.rationale == "Agent is balanced."
    
    guided_state = navigator.apply_guidance(report, agent_state)
    assert guided_state == agent_state # Состояние не изменилось
