import pytest
from kentaur_osps import (
    HermesTriageModule, 
    KentaurAbstractor, 
    AbstractionLevel
)

@pytest.fixture
def abstractor():
    return KentaurAbstractor()

def test_diagnose_concrete(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.2, "IP": 0.5, "InEx": 0.0})
    # Высокий AcOr, низкий IP
    report = hermes.report({"AcOr": 0.9, "IP": 0.1, "InEx": 0.2})
    level = abstractor.diagnose_level(report)
    assert level == AbstractionLevel.CONCRETE

def test_diagnose_philosophical(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.2})
    # Высокий IP (анализ), глубокий InEx (внутренний фокус)
    report = hermes.report({"AcOr": 0.1, "IP": 0.9, "InEx": -0.8})
    level = abstractor.diagnose_level(report)
    assert level == AbstractionLevel.PHILOSOPHICAL

def test_diagnose_tactical(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    report = hermes.report({"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    level = abstractor.diagnose_level(report)
    assert level == AbstractionLevel.TACTICAL

def test_shift_up_from_concrete_swamp(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.2, "IP": 0.5, "InEx": 0.0})
    # Агент паникует в деталях (Высокий риск)
    report = hermes.report({"AcOr": 0.9, "IP": 0.1, "InEx": 0.2})
    
    shift = abstractor.prescribe_shift(report)
    assert shift is not None
    assert shift.target_level == AbstractionLevel.STRATEGIC
    assert "Зумируйся вверх" in shift.shift_command

def test_shift_down_from_philosophical(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.2})
    # Агент завис в абстракциях
    report = hermes.report({"AcOr": 0.1, "IP": 0.9, "InEx": -0.8})
    
    shift = abstractor.prescribe_shift(report)
    assert shift is not None
    assert shift.target_level == AbstractionLevel.TACTICAL
    assert "Спустись на землю" in shift.shift_command

def test_no_shift_when_tactical(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    report = hermes.report({"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    
    shift = abstractor.prescribe_shift(report)
    assert shift is None

import pytest
from kentaur_osps import (
    HermesTriageModule, 
    KentaurAbstractor, 
    AbstractionLevel
)

@pytest.fixture
def abstractor():
    return KentaurAbstractor()

def test_diagnose_concrete(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.2, "IP": 0.5, "InEx": 0.0})
    # Высокий AcOr, низкий IP
    report = hermes.report({"AcOr": 0.9, "IP": 0.1, "InEx": 0.2})
    level = abstractor.diagnose_level(report)
    assert level == AbstractionLevel.CONCRETE

def test_diagnose_philosophical(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.2})
    # Высокий IP (анализ), глубокий InEx (внутренний фокус)
    report = hermes.report({"AcOr": 0.1, "IP": 0.9, "InEx": -0.8})
    level = abstractor.diagnose_level(report)
    assert level == AbstractionLevel.PHILOSOPHICAL

def test_diagnose_tactical(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    report = hermes.report({"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    level = abstractor.diagnose_level(report)
    assert level == AbstractionLevel.TACTICAL

def test_shift_up_from_concrete_swamp(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.2, "IP": 0.5, "InEx": 0.0})
    # Агент паникует в деталях (Высокий риск)
    report = hermes.report({"AcOr": 0.9, "IP": 0.1, "InEx": 0.2})
    
    shift = abstractor.prescribe_shift(report)
    assert shift is not None
    assert shift.target_level == AbstractionLevel.STRATEGIC
    assert "Зумируйся вверх" in shift.shift_command

def test_shift_down_from_philosophical(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.2})
    # Агент завис в абстракциях
    report = hermes.report({"AcOr": 0.1, "IP": 0.9, "InEx": -0.8})
    
    shift = abstractor.prescribe_shift(report)
    assert shift is not None
    assert shift.target_level == AbstractionLevel.TACTICAL
    assert "Спустись на землю" in shift.shift_command

def test_no_shift_when_tactical(abstractor):
    hermes = HermesTriageModule(target={"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    report = hermes.report({"AcOr": 0.5, "IP": 0.5, "InEx": 0.0})
    
    shift = abstractor.prescribe_shift(report)
    assert shift is None
