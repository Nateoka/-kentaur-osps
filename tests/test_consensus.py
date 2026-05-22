import pytest
from kentaur_osps import (
    HermesTriageModule, 
    KentaurConsensus, 
    ConsensusState
)

@pytest.fixture
def consensus():
    return KentaurConsensus(tension_threshold=0.5)

def test_consensus_autonomous(consensus):
    """Агенты близко друг к другу — работают автономно"""
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    
    reports = {
        "agent_1": hermes.report({"AcOr": 0.4, "IP": 0.6, "InEx": 0.1}),
        "agent_2": hermes.report({"AcOr": 0.5, "IP": 0.5, "InEx": 0.0}),
    }
    
    verdicts = consensus.resolve(reports)
    assert verdicts["agent_1"].state == ConsensusState.AUTONOMOUS
    assert verdicts["agent_2"].state == ConsensusState.AUTONOMOUS

def test_consensus_aligning_with_anchor(consensus):
    """Агенты разбежались, самый стабильный становится Якорем"""
    stable_hermes = HermesTriageModule(target={"AcOr": 0.2, "IP": 0.8, "InEx": -0.1})
    panic_hermes = HermesTriageModule(target={"AcOr": 0.8, "IP": 0.1, "InEx": 0.5})
    
    reports = {
        "stable_agent": stable_hermes.report({"AcOr": 0.2, "IP": 0.8, "InEx": -0.1}), # Kres ~ 1.0
        "panic_agent": panic_hermes.report({"AcOr": 0.1, "IP": 0.9, "InEx": -0.5}) # Высокое напряжение
    }
    
    verdicts = consensus.resolve(reports)
    
    assert verdicts["stable_agent"].state == ConsensusState.ALIGNING
    assert verdicts["stable_agent"].is_anchor is True
    
    assert verdicts["panic_agent"].state == ConsensusState.ALIGNING
    assert verdicts["panic_agent"].is_anchor is False
    assert verdicts["panic_agent"].anchor_id == "stable_agent"
    assert verdicts["panic_agent"].alignment_target == stable_hermes.target

def test_consensus_crisis(consensus):
    """Все агенты в критическом риске — роевый кризис"""
    critical_hermes = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0})
    
    reports = {
        "agent_1": critical_hermes.report({"AcOr": 0.9, "IP": 0.9, "InEx": 0.9}), # Tension > 1.5
        "agent_2": critical_hermes.report({"AcOr": -0.9, "IP": -0.9, "InEx": -0.9}),
    }
    
    verdicts = consensus.resolve(reports)
    assert verdicts["agent_1"].state == ConsensusState.CRISIS
    assert verdicts["agent_2"].state == ConsensusState.CRISIS
    assert "SWARM CRISIS" in verdicts["agent_1"].directive

def test_consensus_alignment_modification(consensus):
    """Проверяем, что apply_alignment меняет таргет у не-якоря"""
    hermes = HermesTriageModule(target={"AcOr": 0.0, "IP": 0.0, "InEx": 0.0})
    report = hermes.report({"AcOr": 0.5, "IP": 0.5, "InEx": 0.5})
    
    from kentaur_osps import ConsensusVerdict
    fake_verdict = ConsensusVerdict(
        state=ConsensusState.ALIGNING,
        is_anchor=False,
        anchor_id="leader",
        alignment_target={"AcOr": 0.8, "IP": 0.2, "InEx": 0.0},
        directive="Sync"
    )
    
    aligned_hermes = consensus.apply_alignment(fake_verdict, hermes)
    # Таргет должен был измениться
    assert aligned_hermes.target["AcOr"] == 0.8
    assert aligned_hermes.target["IP"] == 0.2
