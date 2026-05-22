import pytest
from kentaur_osps import KentaurMind, EnforcementLevel

@pytest.fixture
def mind():
    return KentaurMind(profile="analyst")

@pytest.fixture
def agent_state():
    return {
        "temperature": 0.8,
        "available_tools": ["search_web", "execute_bash", "think_step_by_step"],
        "system_prompt": "Ты полезный ассистент.",
        "force_stop": False
    }

def test_mind_balanced_state(mind, agent_state):
    vector = {"AcOr": 0.1, "IP": 0.9, "InEx": 0.2} # Идеальный аналитик
    verdict = mind.process(vector, agent_state)
    
    assert verdict.report.risk == "low"
    assert verdict.governor_verdict.level.name == "NONE"
    assert "СИСТЕМНЫЕ ДИРЕКТИВЫ" not in verdict.modified_agent_state["system_prompt"]

def test_mind_panic_triggers_all_systems(mind, agent_state):
    vector = {"AcOr": 0.9, "IP": 0.1, "InEx": 0.5} # Паника!
    verdict = mind.process(vector, agent_state, context="Срочный фикс")
    
    # Губернатор должен сработать
    assert verdict.governor_verdict.level.name in ["RESTRICT", "HALT"]
    
    # Навигатор должен запретить действия и дать планирование
    assert "think_step_by_step" in verdict.navigator_prescription.recommended_tools or \
           "execute_bash" in verdict.navigator_prescription.blocked_tools
    
    # Абстрактор должен зумить вверх
    assert verdict.abstraction_shift is not None
    assert "Зумируйся вверх" in verdict.abstraction_shift.shift_command
    
    # Промпт должен быть модифицирован
    assert "СИСТЕМНЫЕ ДИРЕКТИВЫ HERMES" in verdict.modified_agent_state["system_prompt"]
    
    # Память должна была записать травму
    assert len(mind.memory._episodes) == 1

def test_mind_reflex_from_memory(mind, agent_state):
    # Искусственно создаём прошлую травму
    mind.memory.record("Старая ошибка", {"AcOr": 0.85, "IP": 0.15, "InEx": 0.0}, "halt", "Не делай так!")
    
    # Попадаем в похожую ситуацию
    vector = {"AcOr": 0.88, "IP": 0.12, "InEx": 0.1}
    verdict = mind.process(vector, agent_state)
    
    # Память должна была сработать
    assert verdict.subconscious_reflex is not None
    assert "SUBCONSCIOUS REFLEX" in verdict.modified_agent_state["system_prompt"]

def test_mind_profile_switch(mind, agent_state):
    # Переключаем в кризисный режим
    mind.switch_profile("crisis")
    
    # Вектор, который для аналитика был бы нормой, для кризиса - смерть
    vector = {"AcOr": 0.4, "IP": 0.4, "InEx": 0.1}
    verdict = mind.process(vector, agent_state)
    
    assert verdict.report.risk in ["high", "critical"]
