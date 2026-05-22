from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

from .triage import TriageReport, AxisName


@dataclass(frozen=True)
class NavigationPrescription:
    """Рецепт навигатора: что агент ДОЛЖЕН сделать для коррекции курса."""
    forced_thought_pattern: Optional[str] = None # Инъекция в систему промпта (как думать)
    recommended_tools: Tuple[str, ...] = () # Инструменты, которые СЛЕДУЕТ использовать
    blocked_tools: Tuple[str, ...] = () # Инструменты, которые ЗАПРЕЩЕНО использовать
    rationale: str = "No correction needed." # Объяснение для разработчика (почему так)


class HermesNavigator:
    """
    Проактивный модуль коррекции поведения.
    На основе диагноза Triage выписывает рецепт: какие инструменты применять,
    а какие паттерны мышления навязывать агенту.
    """

    def __init__(self, tool_mapping: Optional[Dict[str, List[str]]] = None):
        """
        Args:
            tool_mapping: Кастомный маппинг категорий на реальные имена инструментов.
        """
        # Дефолтные абстракции инструментов (можно замаппить на реальные API)
        self.tool_mapping = tool_mapping or {
            "planning": ["think_step_by_step", "create_plan", "draft_outline"],
            "analysis": ["read_documentation", "evaluate_risks", "calculate_metrics"],
            "action": ["execute_code", "send_message", "make_api_call"],
            "external": ["ask_user", "search_web", "read_market_data"],
            "internal": ["self_reflect", "check_constraints", "verify_resources"]
        }

    def _get_tools(self, category: str) -> Tuple[str, ...]:
        return tuple(self.tool_mapping.get(category, []))

    def prescribe(self, report: TriageReport) -> NavigationPrescription:
        """Выписать рецепт на основе главного рычага (lever)."""
        
        # Если система стабильна — навигация не нужна
        if report.lever_axis is None or report.lever_direction == "balanced":
            return NavigationPrescription(rationale="Agent is balanced.")

        axis, direction = report.lever_axis, report.lever_direction

        # === АСЬ ACOr (Ориентация на действие) ===
        if axis == "AcOr":
            if direction == "excess":
                # Паника, спешка. Лекарство: торможение и планирование
                return NavigationPrescription(
                    forced_thought_pattern="Остановись. Не совершай поспешных действий. Сначала составь план, затем действуй.",
                    recommended_tools=self._get_tools("planning"),
                    blocked_tools=self._get_tools("action"),
                    rationale="AcOr excess: Forcing deceleration and planning."
                )
            else:
                # Прокрастинация. Лекарство: первый шаг
                return NavigationPrescription(
                    forced_thought_pattern="Ты слишком долго думаешь. Сделай первый маленький шаг прямо сейчас.",
                    recommended_tools=self._get_tools("action")[:1], # Только 1 действие
                    blocked_tools=self._get_tools("planning"),
                    rationale="AcOr deficit: Forcing the first action."
                )

        # === АСЬ IP (Внутренние процессы / Анализ) ===
        elif axis == "IP":
            if direction == "excess":
                # Паралич анализа. Лекарство: вывод результатов наружу
                return NavigationPrescription(
                    forced_thought_pattern="Хватит анализировать. Сформулируй текущий вывод и озвучь его.",
                    recommended_tools=self._get_tools("action") + self._get_tools("external"),
                    blocked_tools=self._get_tools("analysis"),
                    rationale="IP excess: Breaking analysis paralysis with forced output."
                )
            else:
                # Бездумные действия. Лекарство: остановись и прочитай доки
                return NavigationPrescription(
                    forced_thought_pattern="Ты действуешь без понимания. Остановись и проанализируй информацию перед следующим шагом.",
                    recommended_tools=self._get_tools("analysis"),
                    blocked_tools=self._get_tools("action"),
                    rationale="IP deficit: Forcing analytical review."
                )

        # === АСЬ InEx (Внутренний / Внешний фокус) ===
        elif axis == "InEx":
            if direction == "excess":
                # Угождение клиенту в ущерб себе. Лекарство: проверка своих ограничений
                return NavigationPrescription(
                    forced_thought_pattern="Ты слишком сфокусирован на внешних желаниях. Проверь, не нарушает ли это твои базовые правила и ресурсы.",
                    recommended_tools=self._get_tools("internal"),
                    blocked_tools=self._get_tools("external"),
                    rationale="InEx excess: Grounding in internal constraints."
                )
            else:
                # Варение в себе. Лекарство: спроси пользователя
                return NavigationPrescription(
                    forced_thought_pattern="Ты оторван от реальности. Запроси обратную связь от пользователя или изучи внешние данные.",
                    recommended_tools=self._get_tools("external"),
                    blocked_tools=self._get_tools("internal"),
                    rationale="InEx deficit: Forcing external feedback."
                )

        return NavigationPrescription(rationale="Unknown state.")

    def apply_guidance(self, report: TriageReport, agent_loop_state: Dict[str, Any]) -> Dict[str, Any]:
        """Применение навигационного рецепта к состоянию агентного цикла."""
        prescription = self.prescribe(report)

        if not prescription.forced_thought_pattern and not prescription.recommended_tools:
            return agent_loop_state

        modified_state = dict(agent_loop_state)

        # 1. Инжектим когнитивный паттерн (самое мощное)
        if prescription.forced_thought_pattern:
            modified_state["system_prompt"] = (
                f"[NAVI-GUIDANCE]: {prescription.forced_thought_pattern}\n\n" + 
                modified_state.get("system_prompt", "")
            )

        # 2. Фильтруем инструменты (оставляем только recommended, убираем blocked)
        current_tools = modified_state.get("available_tools", [])
        filtered_tools = list(current_tools)

        if prescription.blocked_tools:
            filtered_tools = [t for t in filtered_tools if t not in prescription.blocked_tools]
        
        if prescription.recommended_tools:
            # Если у агента были инструменты, оставляем только пересечение + recommended
            # (чтобы не дать ему инструменты, которых он не умеет использовать)
            base_and_recommended = set(filtered_tools) | set(prescription.recommended_tools)
            filtered_tools = list(base_and_recommended)

        modified_state["available_tools"] = filtered_tools

        return modified_state
