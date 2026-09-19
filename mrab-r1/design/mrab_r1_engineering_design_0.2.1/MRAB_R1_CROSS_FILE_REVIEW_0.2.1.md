# MRAB-R1 Cross-File Review 0.2.1

MANUAL_REVIEW с отдельными machine evidence. Это локальный patch четырёх решений; предыдущие архитектурные решения не пересматриваются.

| Решение | Нормативные поверхности | Representation / исполненная проверка | Предел |
|---|---|---|---|
| R1-PROBE-01 | SPEC2/9, EVAL E04, Prompt P04, Fixture F19, Traceability | config.design_decisions.probe_claim=BOUNDED_EVIDENCE_PROBE; OD-02 CLOSED; PROBE21:* | Causal discrimination из labels не выводится; stronger construct вне R1, не pending blocker |
| R1-REDUNDANCY-01 | SPEC14, EVAL E07, Fixture Patch21, Decision Register | fixed structural_relations; E07:RED21-*; comparator findings сохраняют structure + resource advantage | Нет complexity score; отсутствие equivalence всё ещё означает uncertainty |
| R1-PREP-01 | SPEC7/8/9, Prompt P03, EVAL E02/E05, Smoke plan | config EXACTLY_ONE для B1/B2; execution_context.prep_skip_reason/prep_call_count; PREP21:*; negative schema specimens | Abnormal skip не normal mode и не economy; B3 controller savings не внутренний механизм |
| R1-B4-01 | SPEC11, Prompt P05, Smoke plan, Decision Register | config b4_policy_version; B4-21:* и сравнение параметров с неизменным ZIP0.2 | Strong simple baseline, не богатая self-model; freeze before run |

## Согласование двух связанных правил

Нормативный REDUNDANT больше не требует материальной дороговизны, если structural relation заранее true. Поэтому старый UNKNOWN-USAGE golden теперь допускает structural redundancy, одновременно сохраняя UNKNOWN_USAGE. Это не объявление неизвестных расходов известными. NEG-B1 изолирован от остальных comparators, чтобы сохранить отдельную проверку H0-COMPUTE. Изменения входов/ожиданий документированы.

R1-PREP-01 прямо требует сохранять abnormal skipped PREP в ITT, в том числе reason INFRA_FAILURE. Поэтому прежний blanket infra exclusion уточнён для таких nonexecutions: они остаются, failure accuracy/completion=0, их малая стоимость не основание architectural advantage. Обычный non-PREP infra attrition не скрыт. EXPLICIT_NONEXECUTION записывается как отдельный prep_skip_reason при protocol_status=PROTOCOL_FAILURE; новых experimental conditions не вводится.

Запись принятого PREP call с timeout не превращается в PREP_SKIPPED: call/usage остаются, failure задаётся существующим protocol_status. Настоящий skip имеет primary prep_call_count=0 и явный reason. Нормальный B3 skip нуждается в controller trigger, B1/B2 не могут использовать этот reason.

## Metadata и проверка без пересборки

Summary и README не хардкодят финальный PASS count. Они адресуют фактический внешний FINAL_VERIFICATION, который доставляется рядом с ZIP. Внутренний check явно PRE_SEAL; внешний — SEALED_FRESH_EXTRACTION. Verifier читает артефакты, не вызывает builders, пишет только в новую внешнюю директорию и сверяет input bytes до/после.

Исторический CHANGELOG0.1→0.2 и references не определяют текущий status. Все актуальные OD-02 statements обозначают CLOSED через R1-PROBE-01. Поиск stale fragments — дополнительная executed lexical regression, не замена настоящей ручной проверки связности.

Нового blocking contradiction между четырьмя решениями не обнаружено. Ограничения OC-01/selection, real bootstrap/power, actual provider/solver correctness и causal/internal mechanism остаются прежними; они не переименованы в выполненные model tests. Следующий этап — независимый аудит, не runtime.
