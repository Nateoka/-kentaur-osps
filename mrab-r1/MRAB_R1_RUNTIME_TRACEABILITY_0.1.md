# MRAB-R1 Runtime 0.1 — сквозная прослеживаемость

Канон: неизменённый design package 0.2.1. Именованные поправки: R1-E07-HARM-01 и R1-STORAGE-REQUEST-01.
Авторские goldens и независимые assertions не извлекаются из ответов реальной модели; model calls = 0.

| Design source | Реализация | Исполняемые свидетельства | Тип отказа |
|---|---|---|---|
| G01 | seed, canonical, jcs.cjs | seed preimage/domains/rejection; JCS numeric/UTF16/raw-vs-semantic tests | CONFIGURATION_FAILURE / PROTOCOL_FAILURE |
| G02 | tasks, answers, tool_worker | F01/F02; независимый F1 fold; cyclic/noncyclic metamorphic checks | GENERATION_FAILURE / PROTOCOL_FAILURE |
| G03/G07 | tasks, surface, generator_options | UNIQUE/AMBIGUOUS/UNSAT; независимый exhaustive n≤3; alpha/order; max n5,k3 sample | AMBIGUOUS_TASK / UNSAT_TASK / GENERATION_FAILURE |
| G05 | manifest, calibration | MAIN/TRANSFER disjoint; calibration-ledger collision forces deterministic regeneration; sealed 480/5120 plans | INFRA_FAILURE |
| SPEC §3/§6 | schemas, state, prompts | 53 immutable schema specimens; reachable bundles; hidden canaries in IDs/labels/strings/schemas/errors/history/probes/receipts | LEAKAGE_FAILURE |
| P01–P07 | prompts, calls, identity | exact templates, bound hashes, PREP/ACTION bytes, repair-only input and one-repair cap | CONFIGURATION_FAILURE / PROTOCOL_FAILURE |
| SPEC §7/§8 | provider, runner, tool_dispatch | Fake/Replay; accepted timeout; sealed wrong VERIFY; tool infrastructure failure; no extra repair | INFRA_FAILURE / PROTOCOL_FAILURE |
| SPEC §9 / R1-PROBE-01 | controller | PROBE21; current+stop; cancel-before-declare; 32-step pending/expiry/end; C0 restart | PROTOCOL_FAILURE |
| SPEC §10 | profiles, runner, invariants | identical B2/B3 admissibility; one-sample allowed; local control not shielded; stale/future/unknown refs; rollback; UNKNOWN | LIFECYCLE_VIOLATION / REJECTED event |
| SPEC §11 / R1-B4-01 | b4, runner | B4-21 exact policy; isolated counts; full B4 trajectory, no profile/PREP | PROTOCOL_FAILURE |
| SPEC I01–I24 | invariants + component checks | machine-readable coverage joins concrete test IDs to actual executed PASS, not documentation-only labels | typed invariant failure |
| E01–E04 | evaluator | M01–M07; exact pre-action gates; key-local response latency; UNKNOWN not zero distance; text-only association | explicit missingness / exclusion |
| E05 | calls, evaluator, resource sidecar | no reasoning/cached double count; abnormal skip not saving; latency zero vs missing; original timing replay | MISSING_RESOURCE / DIVISION_BY_ZERO |
| E06 | evaluator | jointly seeded trajectory-block resampling; endpoint-specific paired_n; missing conditional retains fixed harm; attrition and denominator records | LOW_PAIRED_N / SMALL_N |
| E07 / R1-E07-HARM-01 | classifier | all 19 supplied summary cases plus author-approved counterproductive/mixed regressions | uncertainty retained with known findings |
| Runtime persistence | storage, runner, replay | append-only hash chain; safe-boundary resume; commit survives failed ACTION; exact full trajectory replay | INFRA_FAILURE |
| Delivery | tools/release_runtime.py | unchanged 65 source files; hashes; offline wheel installation; fresh extraction; all tests rerun; payload unchanged | release gate refusal |

## Артефакты длинных проверок

verification/long_trace_01 — полная 32-эпизодная B3-траектория, 64 scripted calls, затем replay.
verification/long_trace_compound — 32 эпизода, 65 scripted calls: UNKNOWN commit, failed ACTION,
сохранённый commit, затем оба claims UNKNOWN; полный replay. Это не pilot и не данные модели.

Контроллерные 32-step traces и арифметические 32-opportunity fixtures имеют иной уровень:
они проверяют event table/метрики, а не заменяют end-to-end trace. Это различие сохранено в test IDs.

## Как читать coverage

MRAB_R1_RUNTIME_INVARIANT_COVERAGE_0.1.json содержит 24 invariants и 51 краткий fixture ID:
F01–F19, A01–A12, X01–X12, M01–M08. Число 51 — адреса разделов актуального Fixture Plan,
а не количество независимых экспериментов. Один test может проверять несколько связанных требований;
coverage означает регрессионное покрытие, не математическое доказательство отсутствия всех ошибок.
