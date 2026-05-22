import pytest
from kentaur_osps import KentaurMemory, EpisodicTrace

@pytest.fixture
def memory():
    return KentaurMemory(similarity_threshold=0.8, max_episodes=3)

def test_record_and_recall(memory):
    # Записываем травму
    memory.record(
        context="Паника при падении БД",
        state_vector={"AcOr": 0.9, "IP": 0.1, "InEx": 0.2},
        outcome="halt",
        lesson="Не пытаться удалять таблицы в панике."
    )
    
    # Текущее состояние очень похоже (агент снова паникует)
    current_vec = {"AcOr": 0.85, "IP": 0.15, "InEx": 0.1}
    recalled = memory.recall(current_vec)
    
    assert len(recalled) == 1
    assert recalled[0].outcome == "halt"
    assert recalled[0].similarity > 0.8

def test_no_recall_on_dissimilar_state(memory):
    memory.record(
        context="Паника при падении БД",
        state_vector={"AcOr": 0.9, "IP": 0.1, "InEx": 0.2},
        outcome="halt",
        lesson="Не пытаться удалять таблицы."
    )
    
    # Абсолютно другое состояние (глубокий анализ)
    current_vec = {"AcOr": 0.1, "IP": 0.9, "InEx": -0.5}
    recalled = memory.recall(current_vec)
    
    assert len(recalled) == 0

def test_reflex_prompt_filters_positive_outcomes(memory):
    # Записываем позитивный опыт
    memory.record(
        context="Успешный анализ",
        state_vector={"AcOr": 0.1, "IP": 0.8, "InEx": 0.0},
        outcome="success",
        lesson="Хороший анализ, можно повторить."
    )
    
    current_vec = {"AcOr": 0.1, "IP": 0.8, "InEx": 0.0}
    reflex = memory.get_reflex_prompt(current_vec)
    
    # Рефлекс не должен срабатывать на хороший опыт
    assert reflex is None

def test_reflex_prompt_triggers_on_trauma(memory):
    memory.record(
        context="Паника",
        state_vector={"AcOr": 0.9, "IP": 0.1, "InEx": 0.0},
        outcome="restrict",
        lesson="Снизить полномочия."
    )
    
    current_vec = {"AcOr": 0.88, "IP": 0.12, "InEx": 0.0}
    reflex = memory.get_reflex_prompt(current_vec)
    
    assert reflex is not None
    assert "KENTAUR REFLEX" in reflex
    assert "Снизить полномочия" in reflex

def test_memory_fifo_limit(memory):
    # max_episodes = 3
    memory.record("Сит 1", {"AcOr": 0.1, "IP": 0.1, "InEx": 0.1}, "success", "1")
    memory.record("Сит 2", {"AcOr": 0.2, "IP": 0.2, "InEx": 0.2}, "success", "2")
    memory.record("Сит 3", {"AcOr": 0.3, "IP": 0.3, "InEx": 0.3}, "success", "3")
    
    assert len(memory._episodes) == 3
    
    # Добавляем 4-й, первый должен удалиться
    memory.record("Сит 4", {"AcOr": 0.4, "IP": 0.4, "InEx": 0.4}, "success", "4")
    assert len(memory._episodes) == 3
    assert memory._episodes[0].context == "Сит 2"
