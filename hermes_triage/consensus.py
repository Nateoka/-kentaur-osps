from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple, cast
from .triage import HermesTriageModule, TriageReport, Vector, InputVector


class ConsensusState(Enum):
    """Состояние когерентности роя."""
    AUTONOMOUS = "autonomous" # Низкое напряжение, агенты работают сами по себе
    ALIGNING = "aligning" # Высокое напряжение, идёт синхронизация на Якорь
    CRISIS = "crisis" # Все агенты нестабильны, рой заморожен


@dataclass(frozen=True)
class ConsensusVerdict:
    """Вердикт консилиума для конкретного агента."""
    state: ConsensusState
    is_anchor: bool
    anchor_id: Optional[str]
    alignment_target: Optional[Vector] # Вектор, к которому должен стремиться агент
    directive: Optional[str] # Инструкция для промпта


class HermesConsensus:
    """
    Модуль политического разрешения конфликтов в рое агентов.
    Синхронизирует векторы агентов с наиболее устойчивым (Якорем).
    """
    
    def __init__(self, tension_threshold: float = 0.5, critical_risk: str = "critical"):
        """
        Args:
            tension_threshold: Порог mean_tension, выше которого рой начинает синхронизацию.
            critical_risk: Уровень риска, при котором агент не может стать Якорем.
        """
        self.tension_threshold = tension_threshold
        self.critical_risk = critical_risk

    def resolve(self, agent_reports: Dict[str, TriageReport]) -> Dict[str, ConsensusVerdict]:
        """
        Провести консилиум и вынести вердикт для каждого агента.
        
        Args:
            agent_reports: Словарь {agent_id: TriageReport}
        """
        if not agent_reports:
            return {}

        # 1. Замеряем межагентное напряжение
        vectors = [rep.current_vector for rep in agent_reports.values()]
        swarm_tension = HermesTriageModule.inter_agent_tension(vectors)
        
        # 2. Если напряжение низкое — каждый сам за себя
        if swarm_tension["coherent"]:
            return {
                agent_id: ConsensusVerdict(
                    state=ConsensusState.AUTONOMOUS,
                    is_anchor=False,
                    anchor_id=None,
                    alignment_target=None,
                    directive=None
                )
                for agent_id in agent_reports
            }

        # 3. Ищем Якорь — агента с максимальным Kres, не находящегося в критическом риске
        anchor_id: Optional[str] = None
        max_kres: float = -1.0
        
        for agent_id, report in agent_reports.items():
            if report.risk == self.critical_risk:
                continue # Критически больной не может быть Якорем
            if report.k_res > max_kres:
                max_kres = report.k_res
                anchor_id = agent_id

        # 4. Если Якорь не найден (все в критическом риске) -> РОЕВОЙ КРИЗИС
        if anchor_id is None:
            return {
                agent_id: ConsensusVerdict(
                    state=ConsensusState.CRISIS,
                    is_anchor=False,
                    anchor_id=None,
                    alignment_target=None,
                    directive="🚨 SWARM CRISIS: Все агенты дестабилизированы. Заморозка действий. Ожидание внешнего вмешательства."
                )
                for agent_id in agent_reports
            }

        # 5. Формируем вердикты: Якорь держит курс, остальные выравниваются
        verdicts = {}
        anchor_report = agent_reports[anchor_id]
        
        for agent_id, report in agent_reports.items():
            if agent_id == anchor_id:
                verdicts[agent_id] = ConsensusVerdict(
                    state=ConsensusState.ALIGNING,
                    is_anchor=True,
                    anchor_id=anchor_id,
                    alignment_target=anchor_report.target_vector, # Якорь стремится к своей же цели
                    directive="ЯКОРЬ: Ты самый стабильный агент. Удерживай курс, остальные подстроятся под тебя."
                )
            else:
                # Цель для не-якоря: подстроиться под текущее состояние Якоря (тактически) 
                # или под цель Якоря (стратегически). Выбираем стратегическую синхронизацию.
                verdicts[agent_id] = ConsensusVerdict(
                    state=ConsensusState.ALIGNING,
                    is_anchor=False,
                    anchor_id=anchor_id,
                    alignment_target=anchor_report.target_vector,
                    directive=(
                        f"СИНХРОНИЗАЦИЯ: Рой рассинхронизирован. Твой якорь — Агент {anchor_id}. "
                        f"Смест фокус и приведи свой вектор к цели якоря."
                    )
                )

        return verdicts

    def apply_alignment(self, verdict: ConsensusVerdict, agent_module: HermesTriageModule) -> HermesTriageModule:
        """
        Применяет вердикт к модулю агента, подменяя его таргет на таргет Якоря.
        Возвращает НОВЫЙ инстанс модуля (чистота данных).
        """
        if verdict.state != ConsensusState.ALIGNING or verdict.is_anchor or not verdict.alignment_target:
            return agent_module

        # Пересоздаём модуль с новой целью (strict_target=False на случай, если цель якоря была вне дефолта)
        aligned_module = HermesTriageModule(
            target=cast(InputVector, verdict.alignment_target),
            history_limit=agent_module.history_limit,
            use_ema=agent_module.use_ema,
            ema_alpha=agent_module.ema_alpha,
            risk_thresholds=agent_module.risk_thresholds,
            strict_target=False,
            forecast_steps=agent_module.forecast_steps
        )
        # Переносим историю
        aligned_module.history = list(agent_module.history)
        return aligned_module
