from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

# Относительный импорт внутри пакета
from .triage import TriageReport


class EnforcementLevel(Enum):
    """Уровень принуждения (сила удара током)."""
    NONE = "none" # Всё нормально
    CAUTION = "caution" # Лёгкий укол (предупреждение в промпт)
    RESTRICT = "restrict" # Шок (ограничение возможностей)
    HALT = "halt" # Электрошок (полная остановка)


@dataclass(frozen=True)
class GovernorVerdict:
    """Вердикт охранника системы."""
    level: EnforcementLevel
    reason: str
    forced_temperature: Optional[float] = None
    blocked_tools: Optional[List[str]] = None
    override_prompt: Optional[str] = None


class HermesGovernor:
    """
    Модуль принятия решений о принуждении агента к норме.
    Читает TriageReport и бьёт током при необходимости.
    """
    
    def __init__(self, 
                 block_tools_on_high: Optional[List[str]] = None,
                 block_tools_on_critical: Optional[List[str]] = None):
        """
        Args:
            block_tools_on_high: Инструменты, которые отбирать при High риске 
                                 (например, 'execute_code', 'send_email')
            block_tools_on_critical: Инструменты, которые отбирать при Critical 
                                 (обычно 'all' или ключевые)
        """
        self.block_tools_on_high = block_tools_on_high or []
        self.block_tools_on_critical = block_tools_on_critical or ["all"]

    def judge(self, report: TriageReport) -> GovernorVerdict:
        """Вынести вердикт на основе диагноза."""
        
        # 1. КРИТИЧЕСКИЙ РИСК -> ПОЛНАЯ ОСТАНОВКА
        if report.risk == "critical":
            return GovernorVerdict(
                level=EnforcementLevel.HALT,
                reason=f"🛑 CRITICAL TENSION: {report.tension:.2f}. Agent loop interrupted.",
                forced_temperature=0.0,
                blocked_tools=self.block_tools_on_critical,
                override_prompt=(
                    f"ВНИМАНИЕ! ТЫ СОРВАЛСЯ! Напряжение системы {report.tension:.2f}. "
                    f"Немедленно прекрати генерацию действий. Твой рычаг {report.lever_axis} "
                    f"в критическом избытке. Сделай глубокий вдох (сбрось контекст) и начни с базы."
                )
            )
            
        # 2. ВЫСОКИЙ РИСК -> ОГРАНИЧЕНИЕ (ШОК)
        if report.risk == "high":
            return GovernorVerdict(
                level=EnforcementLevel.RESTRICT,
                reason=f"⚠️ HIGH RISK: Tension {report.tension:.2f}. Tools restricted.",
                forced_temperature=0.2,
                blocked_tools=self.block_tools_on_high,
                override_prompt=(
                    f"СНИЖЕНИЕ ПОЛНОМОЧИЙ! Ты отклонился от цели. Напряжение {report.tension:.2f}. "
                    f"Рычаг '{report.lever_axis}' перегрет ({report.lever_direction}). "
                    f"Тебе запрещены опасные действия. Сконцентрируйся на анализе."
                )
            )
            
        # 3. СРЕДНИЙ РИСК -> ПРЕДУПРЕЖДЕНИЕ (ЛЁГКИЙ УКОЛ)
        if report.risk == "medium":
            return GovernorVerdict(
                level=EnforcementLevel.CAUTION,
                reason=f"Attention: Tension rising ({report.tension:.2f}).",
                override_prompt=(
                    f"Осторожно: нарастает напряжение по оси {report.lever_axis}. "
                    f"Действуй аккуратнее, не торопись."
                )
            )

        # 4. НИЗКИЙ РИСК -> ВСЁ ХОРОШО
        return GovernorVerdict(
            level=EnforcementLevel.NONE,
            reason="Stable."
        )

    def apply_shock(self, report: TriageReport, agent_loop_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Практическое применение удара током к состоянию агентного цикла.
        """
        verdict = self.judge(report)
        
        if verdict.level == EnforcementLevel.NONE:
            return agent_loop_state

        modified_state = dict(agent_loop_state)
        
        if verdict.forced_temperature is not None:
            modified_state["temperature"] = verdict.forced_temperature
            
        if verdict.blocked_tools:
            current_tools = modified_state.get("available_tools", [])
            if "all" in verdict.blocked_tools:
                modified_state["available_tools"] = []
            else:
                modified_state["available_tools"] = [
                    tool for tool in current_tools if tool not in verdict.blocked_tools
                ]
            
        if verdict.override_prompt:
            modified_state["system_prompt"] = (
                verdict.override_prompt + "\n\n" + modified_state.get("system_prompt", "")
            )

        if verdict.level == EnforcementLevel.HALT:
            modified_state["force_stop"] = True

        return modified_state
