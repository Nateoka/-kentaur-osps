from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, cast
from .triage import HermesTriageModule, TriageReport, Vector, InputVector
from .governor import HermesGovernor, GovernorVerdict
from .navigator import HermesNavigator, NavigationPrescription
from .abstractor import HermesAbstractor, AbstractionShift
from .memory import HermesMemory
from .profiler import HermesProfiler


@dataclass(frozen=True)
class MindVerdict:
    """Единый вердикт нервной системы агента. Всё, что нужно знать агентному циклу."""
    report: TriageReport
    governor_verdict: GovernorVerdict
    navigator_prescription: NavigationPrescription
    abstraction_shift: Optional[AbstractionShift]
    subconscious_reflex: Optional[str]
    
    modified_agent_state: Dict[str, Any]
    directives_for_prompt: str # Единая склеенная строка всех инъекций


class HermesMind:
    """
    Единая нервная система агента (Оркестратор/Facade).
    Объединяет Триаж, Губернатора, Навигатор, Профайлер, Память и Абстрактор.
    """

    def __init__(self, 
                 target: Optional[Dict[str, float]] = None,
                 profile: str = "analyst",
                 tool_mapping: Optional[Dict[str, List[str]]] = None):
        
        self.profiler = HermesProfiler()
        self.memory = HermesMemory(similarity_threshold=0.8)
        self.abstractor = HermesAbstractor()
        self.navigator = HermesNavigator(tool_mapping=tool_mapping)
        self.governor = HermesGovernor()
        
        # Инициализируем ядро с нужным профилем
        profile_data = self.profiler.get(profile)
        self.core = HermesTriageModule(
            target=profile_data.target,
            risk_thresholds=profile_data.risk_thresholds,
            strict_target=False
        )

    def switch_profile(self, profile_name: str) -> None:
        """Сменить роль агента на лету."""
        self.core = self.profiler.apply_by_name(self.core, profile_name)

    def process(self, 
                current_vector: Vector, 
                agent_loop_state: Dict[str, Any],
                context: str = "") -> MindVerdict:
        """
        Главный цикл обработки состояния агента.
        Принимает текущий вектор и состояние цикла, возвращает вердикт и модифицированное состояние.
        """
        directives: List[str] = []
        modified_state = dict(agent_loop_state)

        # 1. ТРИАЖ: Измеряем пульс
        report = self.core.report(current_vector)

        # 2. ПАМЯТЬ: Проверяем подсознательные рефлексы (были ли ожоги?)
        reflex = self.memory.get_reflex_prompt(current_vector)
        if reflex:
            directives.append(reflex)

        # 3. АБСТРАКТОР: Не зависли ли мы в деталях или в философии?
        shift = self.abstractor.prescribe_shift(report)
        if shift:
            directives.append(shift.shift_command)

        # 4. ГУБЕРНАТОР: Удар током (если риск высок)
        gov_verdict = self.governor.judge(report)
        if gov_verdict.level.name != "NONE":
            directives.append(f"[GOVERNOR]: {gov_verdict.reason}")
            modified_state = self.governor.apply_shock(report, modified_state)

        # 5. НАВИГАТОР: Когнитивная терапия (какие инструменты использовать)
        nav_prescription = self.navigator.prescribe(report)
        if nav_prescription.forced_thought_pattern:
            directives.append(f"[NAVIGATOR]: {nav_prescription.forced_thought_pattern}")
            modified_state = self.navigator.apply_guidance(report, modified_state)

        # 6. ФОРМИРОВАНИЕ ЕДИНОГО ПРОМПТА
        if directives:
            unified_directive = "\n".join(directives)
            modified_state["system_prompt"] = (
                f"=== СИСТЕМНЫЕ ДИРЕКТИВЫ HERMES ===\n{unified_directive}\n"
                f"=== КОНЕЦ ДИРЕКТИВ ===\n\n" + modified_state.get("system_prompt", "")
            )

        # 7. ЗАПИСЬ В ПАМЯТЬ (Если было наказание, запишем на будущее)
        if gov_verdict.level.name in ["HALT", "RESTRICT"]:
            self.memory.record(
                context=context or "Agent loop iteration",
                state_vector=current_vector,
                outcome=gov_verdict.level.name.lower(),
                lesson=f"При векторе {current_vector} получил {gov_verdict.level.name}. Рычаг: {report.lever_axis}."
            )

        return MindVerdict(
            report=report,
            governor_verdict=gov_verdict,
            navigator_prescription=nav_prescription,
            abstraction_shift=shift,
            subconscious_reflex=reflex,
            modified_agent_state=modified_state,
            directives_for_prompt=directives[-1] if directives else "No directives."
        )
