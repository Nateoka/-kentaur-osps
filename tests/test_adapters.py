import pytest
from kentaur_osps import (
    KentaurMind, KentaurToolFilter, HermesReActLoop, 
    GovernorVerdict, NavigationPrescription, EnforcementLevel
)

def test_tool_filter_halts_all():
    filter_engine = KentaurToolFilter()
    tools = [
        {"type": "function", "function": {"name": "search_web"}},
        {"type": "function", "function": {"name": "execute_bash"}}
    ]
    gov = GovernorVerdict(level=EnforcementLevel.HALT, reason="", blocked_tools=["all"])
    nav = NavigationPrescription()
    
    result = filter_engine.filter_tools(tools, gov, nav)
    assert result == []

def test_tool_filter_blocks_specific():
    filter_engine = KentaurToolFilter()
    tools = [
        {"type": "function", "function": {"name": "search_web"}},
        {"type": "function", "function": {"name": "execute_bash"}}
    ]
    gov = GovernorVerdict(level=EnforcementLevel.RESTRICT, reason="", blocked_tools=["execute_bash"])
    nav = NavigationPrescription(blocked_tools=("execute_bash",))
    
    result = filter_engine.filter_tools(tools, gov, nav)
    assert len(result) == 1
    assert result[0]["function"]["name"] == "search_web"

def test_react_loop_governor_halt():
    # Создаем разум в кризисном профиле
    mind = KentaurMind(profile="crisis")
    loop = HermesReActLoop(
        mind=mind,
        llm_client=None, # Используем мок
        tools=[{"type": "function", "function": {"name": "execute_bash"}}],
        max_iterations=3
    )
    
    # Вектор паники
    panic_vector = {"AcOr": 0.9, "IP": 0.1, "InEx": 0.5}
    result = loop.run("Срочно удали базу!", panic_vector)
    
    assert "ОСТАНОВЛЕН ГУБЕРНАТОРОМ" in result
