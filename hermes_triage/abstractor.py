from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

from .triage import TriageReport, Vector
from .memory import HermesMemory, EpisodicTrace


class AbstractionLevel(Enum):
    """Уровни мышления агента (Лестница абстракции)."""
    CONCRETE = 1 # Фокус на деталях, синтаксисе, микро-ошибках
    TACTICAL = 2 # Фокус на текущей задаче, алгоритме
    STRATEGIC = 3 # Фокус на архитектуре, паттернах, системе
    PHILOSOPHICAL = 4 # Фокус на первопричинах, целях, смыслах


@dataclass(frozen=True)
class AbstractionShift:
    """Директива на смену уровня мышления."""
    current_level: AbstractionLevel
    target_level: AbstractionLevel
    shift_command: str # Инъекция в промпт


class HermesAbstractor:
    """
    Модуль управления абстрактным мышлением.
    Не даёт агенту застрять в "трясине деталей" или улететь в "абстрактный космос".
    """
    
    def __init__(self, concrete_stuck_threshold: int = 2, philosophical_lose_threshold: int = 1):
        """
        Args:
            concrete_stuck_threshold: Сколько микро-ошибок во памяти достаточно, 
                                      чтобы вытянуть агента из Concrete.
            philosophical_lose_threshold: Сколько абстрактных шагов без результата достаточно,
                                          чтобы приземлить агента на Tactical.
        """
        self.concrete_stuck_threshold = concrete_stuck_threshold
        self.philosophical_lose_threshold = philosophical_lose_threshold

    def diagnose_level(self, report: TriageReport, memory: Optional[HermesMemory] = None) -> AbstractionLevel:
        """Определяет текущий уровень абстракции агента по его вектору и памяти."""
        
        # Если высокий AcOr и низкий IP — агент тыкается в детали наугад
        if report.lever_axis == "AcOr" and report.lever_direction == "excess":
            return AbstractionLevel.CONCRETE
            
        # Если высокий IP и низкий AcOr — агент завис в анализе (возможно, тактическом или стратегическом)
        if report.lever_axis == "IP" and report.lever_direction == "excess":
            # Если при этом он не делает внешних действий, он улетел в философию
            if report.current_vector.get("InEx", 0.0) < -0.3:
                return AbstractionLevel.PHILOSOPHICAL
            return AbstractionLevel.STRATEGIC
            
        # Если сбалансирован — он на тактическом уровне (именно тут работа делается лучше всего)
        return AbstractionLevel.TACTICAL

    def prescribe_shift(self, report: TriageReport, memory: Optional[HermesMemory] = None) -> Optional[AbstractionShift]:
        """Определяет, нужно ли принудительно сменить уровень мышления."""
        
        current_level = self.diagnose_level(report, memory)
        
        # 1. Застрял в деталях (Concrete Swamp)
        if current_level == AbstractionLevel.CONCRETE:
            # Проверяем память: если много недавних микро-файлов, точно застрял
            # (Упрощенная эвристика: если риск не low, значит детали не складываются)
            if report.risk in ["medium", "high", "critical"]:
                return AbstractionShift(
                    current_level=AbstractionLevel.CONCRETE,
                    target_level=AbstractionLevel.STRATEGIC,
                    shift_command=(
                        "[ABSTRACTION SHIFT UP]: Ты застрял в деталях и микро-ошибках. "
                        "Прекрати править синтаксис. Зумируйся вверх. Опиши архитектурную проблему, "
                        "которая вызывает эти ошибки. Сначала реши её на уровне паттерна, затем возвращайся к коду."
                    )
                )

        # 2. Улетел в абстрактный космос (Philosophical Space)
        if current_level == AbstractionLevel.PHILOSOPHICAL:
            return AbstractionShift(
                current_level=AbstractionLevel.PHILOSOPHICAL,
                target_level=AbstractionLevel.TACTICAL,
                shift_command=(
                    "[ABSTRACTION SHIFT DOWN]: Ты улетел в абстрактные размышления и потерял связь с реальностью. "
                    "Спустись на землю. Сформулируй один конкретный, измеримый шаг, который нужно сделать прямо сейчас."
                )
            )

        # Если на тактическом или стратегическом — всё ок, зумить не надо
        return None

from enum import Enum
from dataclasses import dataclass
from typing import Optional

from .triage import TriageReport


class AbstractionLevel(Enum):
    """Уровни мышления агента (Лестница абстракции)."""
    CONCRETE = 1 # Фокус на деталях, синтаксисе, микро-ошибках
    TACTICAL = 2 # Фокус на текущей задаче, алгоритме
    STRATEGIC = 3 # Фокус на архитектуре, паттернах, системе
    PHILOSOPHICAL = 4 # Фокус на первопричинах, целях, смыслах


@dataclass(frozen=True)
class AbstractionShift:
    """Директива на смену уровня мышления."""
    current_level: AbstractionLevel
    target_level: AbstractionLevel
    shift_command: str # Инъекция в промпт


class HermesAbstractor:
    """
    Модуль управления абстрактным мышлением.
    Не даёт агенту застрять в "трясине деталей" или улететь в "абстрактный космос".
    """
    
    def __init__(self, concrete_stuck_threshold: int = 2, philosophical_lose_threshold: int = 1):
        """
        Args:
            concrete_stuck_threshold: Сколько микро-ошибок во памяти достаточно, 
                                      чтобы вытянуть агента из Concrete.
            philosophical_lose_threshold: Сколько абстрактных шагов без результата достаточно,
                                          чтобы приземлить агента на Tactical.
        """
        self.concrete_stuck_threshold = concrete_stuck_threshold
        self.philosophical_lose_threshold = philosophical_lose_threshold

    def diagnose_level(self, report: TriageReport) -> AbstractionLevel:
        """Определяет текущий уровень абстракции агента по его вектору."""
        
        # Если высокий AcOr и низкий IP — агент тыкается в детали наугад
        if report.lever_axis == "AcOr" and report.lever_direction == "excess":
            return AbstractionLevel.CONCRETE
            
        # Если высокий IP и низкий AcOr — агент завис в анализе
        if report.lever_axis == "IP" and report.lever_direction == "excess":
            # Если при этом он не делает внешних действий, он улетел в философию
            if report.current_vector.get("InEx", 0.0) < -0.3:
                return AbstractionLevel.PHILOSOPHICAL
            return AbstractionLevel.STRATEGIC
            
        # Если сбалансирован — он на тактическом уровне (именно тут работа делается лучше всего)
        return AbstractionLevel.TACTICAL

    def prescribe_shift(self, report: TriageReport) -> Optional[AbstractionShift]:
        """Определяет, нужно ли принудительно сменить уровень мышления."""
        
        current_level = self.diagnose_level(report)
        
        # 1. Застрял в деталях (Concrete Swamp)
        if current_level == AbstractionLevel.CONCRETE:
            if report.risk in ["medium", "high", "critical"]:
                return AbstractionShift(
                    current_level=AbstractionLevel.CONCRETE,
                    target_level=AbstractionLevel.STRATEGIC,
                    shift_command=(
                        "[ABSTRACTION SHIFT UP]: Ты застрял в деталях и микро-ошибках. "
                        "Прекрати править синтаксис. Зумируйся вверх. Опиши архитектурную проблему, "
                        "которая вызывает эти ошибки. Сначала реши её на уровне паттерна, затем возвращайся к коду."
                    )
                )

        # 2. Улетел в абстрактный космос (Philosophical Space)
        if current_level == AbstractionLevel.PHILOSOPHICAL:
            return AbstractionShift(
                current_level=AbstractionLevel.PHILOSOPHICAL,
                target_level=AbstractionLevel.TACTICAL,
                shift_command=(
                    "[ABSTRACTION SHIFT DOWN]: Ты улетел в абстрактные размышления и потерял связь с реальностью. "
                    "Спустись на землю. Сформулируй один конкретный, измеримый шаг, который нужно сделать прямо сейчас."
                )
            )

        # Если на тактическом или стратегическом — всё ок, зумить не надо
        return None
