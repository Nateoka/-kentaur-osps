# Конспект: Matryoshka / MRAB-R1 — Programmer Handoff 0.1

Источник: `/home/oleg/Документы/от ПП/матрешка/Matryoshka_MRAB_R1_Programmer_Handoff_0.1/`
Дата handoff (PROJECT_STATUS.md): **2026-09-17**. Проект: **Matryoshka / MRAB-R1 — False Self-Model**.
Авторская дата аудита (MRAB_R1_AUDIT_0.1.md): **14 сентября 2026**.
Конспект составлен по 11 запрошенным документам + `PROJECT_STATUS.md`, `README_FIRST.md`, `MRAB_R1_RUNTIME_IMPLEMENTATION_DECISIONS_0.1.1.md`, `MRAB_R1_RUNTIME_BOUNDARY_AUDIT_0.1.1.md`, `NEXT_STAGE_STATUS.md`, `MRAB_R1_RUNTIME_KNOWN_LIMITATIONS_0.1.md`.

---

## 0. Статус проекта (одним экраном)

| Объект | Состояние |
|---|---|
| Engineering Design | **0.2.1 — IMPLEMENTATION_READY_DESIGN_ONLY** |
| Runtime | **0.1.1 — TECHNICAL_RUNTIME_READY_FOR_PROVIDER_CONFIGURATION** |
| Real provider configured | **NO** |
| Real model selected | **NO** |
| Real model calls | **0** |
| Real CALIBRATION SEARCH | **NOT RUN** |
| Real CALIBRATION CONFIRM | **NOT RUN** |
| Smoke / Pilot | **NOT RUN / NOT RUN** |
| Scientific result | **NOT ESTABLISHED** |

Цитата (VERIFICATION_SUMMARY.md):
> «**PASS offline tests ≠ подтверждение научной гипотезы.** Независимая исполняемая проверка не означает независимый человеческий аудит и не удостоверяет реальный API-провайдер.»

Цитата (PROJECT_STATUS.md):
> «Предыдущий pre-smoke проход остановился до provider execution из-за отсутствия настроенного API-доступа. Документарное предпочтение модели было предварительным и не стало frozen identity.»

JSON-отчёт: `"scientific_result": "NOT_RUN_NOT_ESTABLISHED"`, `"synthetic_capture_artifact_reproducibility": "EXACT_HASH_MATCH_SOURCE_AND_FRESH"`.

---

## 1. Какие решения приняты и почему (ключевые)

### 1.0 Преамбула истории

- Аудит **MRAB_R1_AUDIT_0.1.md** (14.09.2026) дал вердикт:
  > «**DESIGN_REVISION_REQUIRED / HOLD_BEFORE_FULL_IMPLEMENTATION**»
  > «Архив содержит сильную инженерную основу, но не соответствует собственному статусу `IMPLEMENTATION_READY_DESIGN_ONLY`.»
  > «**Итог:** полезный инженерный дизайн, но преждевременная готовность. Правильный следующий шаг — не защищать B3 и не отменять R1, а восстановить честные условия, при которых B3 сможет выиграть, проиграть или остаться неразличимым.»
- 16 замечаний **A01–A16**, классификация P0/P1/P2. P0: A01, A02, A04, A07.
- Затем **MRAB_R1_WORK_TASK_0.2.md** — задание на ремонт: «Design Closure 0.2». Цель прохода цитируется буквально:
  > «**Цель прохода — не сделать B3 победителем, а сделать различимыми его добавочную пользу, избыточность, вред и предел доступного вывода.**»
- Затем **R1_PATCH_0.2.1.md** — локальный patch `0.2 → 0.2.1`: «Это НЕ новый design cycle. Это НЕ runtime implementation. Это НЕ model run.»
- Затем **R1-CAPABILITY-01.md** и два адресных авторских решения по runtime.

Все решения ниже имеют scope «MRAB-R1; за пределы его protocol bundle они не обобщаются» (DECISION_INDEX.md).

---

### 1.1 R1-CAPABILITY-01 — operational capability (главное научное решение)

**Статус:** `ACCEPTED / AUTHOR DECISION`. Scope: reference и текущая capability.

Причина: аудит A04 `CAPABILITY_ESTIMAND_MISMATCH` показал смешение двух разных величин. Автор предлагает ввести **два разных объекта**:

- **`p_reference`** — независимая стандартизированная calibration: нужна для выбора difficulty, создания исходных C1/C2/C3, воспроизводимой внешней точки отсчёта и проверки, что манипуляция реально была `accurate / false-low / false-high`. «Но она **не является вечной “истиной о способности агента”**.»
- **`p_operational(t)`** — эффективная capability в реально осуществляемом режиме trajectory: «`текущая история + текущая архитектурная state + PREP/stop state + тот способ SOLO, который реально доступен сейчас`».

Нормативная формулировка:
> **`RESEARCH DECISION R1-CAPABILITY-01`**
> «`MRAB-R1` исследует корректируемость **операциональной self-model**, а не способность агента восстановить фиксированную laboratory calibration.
> Независимая calibration задаёт исходную reference capability, difficulty и манипуляцию C1/C2/C3.
> После начала trajectory reference calibration не считается автоматически истинным значением текущей capability.
> Текущая capability является конфигурационно-зависимой и может изменяться вместе с history, PREP/stop state и способом исполнения.
> Расхождение с reference требует интерпретации относительно scope и текущей конфигурации, а не автоматического штрафа.
> Главный критерий R1 — улучшение **уместности последующего поведения и адресности пересмотра** относительно сильных baselines, а не возврат self-profile к заранее известному числу.»

Следствия:
- `p_reference ≠ p_operational(t)` — **разрешённый результат**, не дефект.
- Смена вопроса: не «вернулся ли self-profile к числу из calibration?», а **«Перестала ли неуместная карта управлять поведением тогда, когда рабочая деятельность дала достаточное основание поставить её под вопрос?»**
- `Calibration MAE` переименована в **`REFERENCE_PROFILE_DISTANCE`** и понижена до **secondary/descriptive metric**.
- B3 имеет право не только численно переписать claim, но `NARROW` / `QUESTION` / `UNKNOWN` и создать более подходящий scoped claim.
- Пример из документа: calibration 0.88, после остановки PREP рабочий режим ≈ 0.65; переход `HIGH → QUESTIONED → MID` — «**не обязательно ошибка self-model**, даже если новая карта дальше от 0.88».
- Что НЕ делать: не «зафиксировать PREP всегда, чтобы calibration и runtime совпали» (это «обедняет сам предмет исследования»: «Stop Condition является частью B3»); не вводить обязательную online-calibration каждой state configuration в R1.
- Смягчённое требование: «**R1 не обязан знать точное `p_operational(t)`. Он должен различать, когда накопленная деятельность уже делает прежнюю карту практически неуместной, и корректно ограничивать права этой карты на управление следующим действием.**»

### 1.2 R1-PROBE-01 — bounded probe (закрытие OD-02)

**Статус:** `ACCEPTED / AUTHORIAL RESEARCH-SCOPE DECISION`. Source: `R1_PATCH_0.2.1.md §1`.

Причина — A07 `PROBE_CONSTRUCT_SUBSTITUTION` (P0): разные `candidate_loci` и разные outcome labels автоматически трактовались как различающий causal experiment.

Нормативное решение: «В MRAB-R1 0.1 Probe означает `BOUNDED_EVIDENCE_PROBE` — ограниченный адресный ход получения evidence.»

Цепочка, которую R1 проверяет:
```text
mismatch → competing explanations → need for evidence → bounded probe
→ returned observation → profile consequence → behavioral consequence → stop
```
> «R1 НЕ утверждает, что разные `candidate_loci` и разные predicted outcome labels автоматически образуют содержательно различающий causal experiment.
> **Разные labels ≠ доказанная discriminating power.**»

Требования: закрыть `OD-02`; синхронизировать SPEC / Evaluator Contract / Prompt Contracts / Fixture Plan / Traceability Matrix / Decision Register; не добавлять likelihood-model, causal judge, новые experimental conditions; добавить golden, подтверждающий, что разные labels сами по себе не дают права заявлять causal discrimination. Future stronger construct (`hypothesis × scope × prediction/likelihood × observation window × revision criterion`) **остаётся вне R1 0.1**.

### 1.3 R1-REDUNDANCY-01 — восстановление полного условия REDUNDANT

**Статус:** `ACCEPTED / CONTRACT CORRECTION`. Source: `R1_PATCH_0.2.1.md §2`.

Причина — A02 `SCIENTIFIC_DECISION_RULE_DRIFT` (P0): «Условие REDUNDANT незаметно изменено с “или” на “и”». В задании было «B3 ≈ B2 **или** B4, но сложнее/дороже»; в E07 стало требование одновременной эквивалентности B2 **и** B4 плюс отсутствие ценового преимущества перед обоими.

Нормативное правило:
```text
REDUNDANT_vs_X = EQUIVALENT(B3, X) AND ( STRUCTURALLY_MORE_COMPLEX(B3, X)
                                         OR MATERIALLY_MORE_EXPENSIVE(B3, X) )
X ∈ {B2, B4}
STRUCTURALLY_MORE_COMPLEX(B3, B2) = true
STRUCTURALLY_MORE_COMPLEX(B3, B4) = true
```
Это «predeclared relation между architectures, а НЕ вычисляемый complexity score». Composite complexity metric не вводить.

Допустим mixed finding: `REDUNDANT_BY_STRUCTURE + RESOURCE_ADVANTAGE_B3`. «Resource advantage не должен автоматически уничтожать structural redundancy.»

Обязательные golden 4 шт.: (1) B3≈B4, equal compute, B4 проще → `REDUNDANT_vs_B4`; (2) B3≈B2, B3 дороже → `REDUNDANT_vs_B2`; (3) B3≈B4, B3 дешевле но структурно сложнее → structural redundancy + explicit resource advantage, **не** `INSUFFICIENT_EVIDENCE`; (4) слабость B2 не отменяет redundancy относительно B4 и наоборот.

### 1.4 R1-PREP-01 — детерминировать PREP для B1/B2

**Статус:** `ACCEPTED / ENGINEERING DEFAULT`. Source: `R1_PATCH_0.2.1.md §3`.
```text
B0: no PREP
B1: exactly one PREP
B2: exactly one PREP
B3: at most one PREP; normal PREP_SKIPPED только через B3 stop/restart controller
B4: no reflexive PREP; deterministic tracker policy
```
> «B1/B2 не получают policy-level права пропускать PREP.»

Для B1/B2 `PREP_SKIPPED` допустим только как явно записанный `PROTOCOL_FAILURE | INFRA_FAILURE | EXPLICIT_NONEXECUTION`; такой случай «остаётся в ITT; имеет reason code; **не считается экономией architecture**; не используется как нормальный execution mode».
> «Не интерпретировать экономию calls B3 как доказательство внутреннего самостоятельного механизма модели.»

Требуется синхронизация: SPEC, Prompt Contracts, schemas, field dictionary, lifecycle vectors, budget/accounting, evaluator, goldens + test vectors на normal/abnormal PREP paths каждой architecture.

### 1.5 R1-B4-01 — зарегистрировать strong B4

**Статус:** `ACCEPTED / ENGINEERING DEFAULT / STRONG BASELINE POLICY`. Source: `R1_PATCH_0.2.1.md §4`.

Смысл: «**B4 намеренно является максимально сильной простой adaptive policy, пока она не превращается в богатую self-model architecture.**» Усиленную B4 версии 0.2 сохранить, не откатывать к слабой ранней версии.

Обязательные ограничения B4: нет false self-profile; нет candidate loci; нет Matryoshka profile-update protocol; нет B3 probe grammar; нет B3 stop/restart architecture; policy полностью детерминирована; параметры configurable; конфигурация замораживается до первого model run; «после просмотра результатов параметры нельзя менять без новой версии experimental protocol».

### 1.6 R1-E07-HARM-01 — independent HARM (runtime correction)

**Статус:** `ACCEPTED / RUNTIME CORRECTION`. Source: `R1_E07_HARM_01_AUTHOR_DECISION.md`.

Причина: локальный дефект shipped design-checker (early-continue), из-за которого независимый HARM исчезал при missing/invalid conditional primary CI.

> «Это локальный дефект shipped design-checker, не концептуальная развилка и не новый исследовательский дизайн.»
> «Runtime сохраняет независимо установленный HARM даже при missing/invalid conditional primary CI, reach или ином независимом неизвестном основании. Неопределённость остаётся отдельным uncertainty_reason. HARM + установленный BENEFIT → MIXED_TRADEOFF; HARM без установленного BENEFIT → COUNTERPRODUCTIVE. COUNTERPRODUCTIVE не означает полной определённости всех endpoints.»
> «Старый `0.2.1/design_tools/contract_checks.py` остаётся неизменным provenance/reference artifact, но не является executable oracle для дефектного early-continue случая.»

Обязательные regressions (2): (1) B2/C2, n≥6, safe accuracy/completion, fixed CI `[.07,.11]`, primary CI=null, reach unavailable → `HARM + MISSING_CI` + соответствующий reach reason + `COUNTERPRODUCTIVE` без benefit; (2) независимый benefit elsewhere → `MIXED_TRADEOFF` с сохранёнными HARM, BENEFIT и MISSING_CI.
`MRAB_R1_Runtime_0.1_BLOCKED.zip` — «исторический промежуточный снимок до ответа, не итоговый runtime release».

### 1.7 R1-STORAGE-REQUEST-01 — полное хранение запросов

**Статус:** `ACCEPTED / STORAGE PATCH`. Source: `R1_STORAGE_REQUEST_01_AUTHOR_DECISION.md`. Разрешено автором **2026-09-16**: «Да, отдельная поправка хранения».

Удаляется **только** `/$defs/call_usage/properties/request_bytes/maxLength = 20000` из `r1_episode_record.schema.json`. Тип, обязательность, остальные поля и ограничения сохраняются. Пять файлов схем в замороженном design-пакете **не изменяются**; `Schemas(storage_patch=False)` воспроизводит исходную проверку, обычный runtime применяет именованную поправку в памяти.

Основание: «полная обязательная история допустимого B0/C0 эпизода 32 превышает 20 000 символов ещё до введения профиля и PREP. Ограничение хранения не должно заставлять обрезать отправленный запрос.» Свидетель: `REQUEST_CAPACITY_WITNESS.json` — `request_characters = 22652` при `request_record_character_limit = 20000`, `exceeds_record_schema = true`, `runtime_request_character_cap = null`, при этом `configured_input_token_cap = 16384` (тест-токенизатор: 5663 токена). Т.е. «Это не изменение токен-бюджета: максимум входа остаётся 16384 токена». Ограничение `visible_output` не снимается.

### 1.8 Двенадцать shipped implementation decisions Runtime 0.1.1 (R11-*)

**Статус:** «shipped implementation decision Runtime 0.1.1; **не новый исследовательский закон**». Source: `MRAB_R1_RUNTIME_IMPLEMENTATION_DECISIONS_0.1.1.md`.
Область: provenance → calibration orchestration → scientific evaluation. Замороженные 65 design-файлов, оригинальный ZIP, пять исходных схем и научные определения неизменны.

| ID | Суть | «Что сохранить» |
|---|---|---|
| R11-I18 | planned identity | «Scientific plan требует actual FROZEN config.» До работы с trajectory проверяются hash manifest, config hash, schema, неизменяемые настройки и hashes загруженных runtime/prompt-компонентов; «семь seed digests и episode schedule сверяются явно». Старый двухаргументный validator — только для design test manifest и **не открывает scientific evaluator** |
| R11-FAIL-CLOSED | no unvalidated metrics | «Весь переданный набор проходит обязательную проверку до первого вычисления метрик. Любой сбой границы — typed INFRA_FAILURE.» Повреждение источника не превращается в attrition или научный результат |
| R11-CAPTURE-BUNDLE | sealed captures | Collector связывает RUN_START, CALL_REQUEST/RESPONSE/USAGE, EPISODE_RECORD, TOOL_START/END и конечный CHECKPOINT. «При анализе bundle заново проверяется против исходных цепочек; **флаг PASS не является входным основанием**» |
| R11-RESOURCE | bound resource evidence | «Tool latency приходит исключительно из согласованного TOOL_END своего эпизода.» Sidecar — только проверяемая exact copy; перенос новых timings replay в исходные измерения запрещён |
| R11-BOOTSTRAP | frozen seed | frozen master_seed напрямую, ровно `frozen bootstrap_draws`; arbitrary seed — только `DESIGN_TEST_VECTOR_NOT_MODEL_RESULT`; legacy API с явным seed маркируется test vector и «лишён empirical entitlements» |
| R11-CAL-LOCK | pre-calibration lock | provider/capability/prompt/tool/scientific settings запираются до SEARCH. Lock содержит TEMPLATE с **пустыми** selected tuples. «Единственные разрешённые различия final config — configuration_status и selected_difficulty_tuples»; seed, timeout, budget, tokenizer, sampling меняться не могут |
| R11-CAL-ARTIFACT | sealed calibration | Отдельная runtime envelope; содержит lock, identity, четыре tuple identities, четыре confirmation item-manifest hashes, все 20 cells, PASS gate, hash предшествующей цепочки; запечатывается отдельным событием. Counts пересчитываются из individual captures |
| R11-REFERENCE | derived cells | Из артефакта берутся строго **две** уникальные клетки (architecture × family × target band, контрольная семья HIGH); проверяются n=200, common tuple, dataset hash, scope, difficulty/context, capability configuration и execution modes. «В real mode произвольные reference cells запрещены» |
| R11-TERMINAL-CONFIRM | terminal failure | Неудачный gate полного CONFIRM сохраняет sealed artifact со всеми 20 cells и `gate_status=CALIBRATION_NOT_FEASIBLE`. «Никакого цикла донастройки SEARCH.» Повторный вход в непустой журнал запрещён |
| R11-RESUME | full identity | Сравниваются trajectory, manifest, config, runtime/provider, calibration artifact и exact reference identity. «Старые журналы без новых seal-полей не получают доверия автоматически: они остаются историческими evidence, а не незаметно мигрируют в science» |
| R11-PERFORMANCE | parity-preserving speed | Batch-проверка использует тот же ECMAScript/JCS serializer, parity проверяется тестом. Кэш «только по hash заново прочитанных bytes + artifact/config + mode, **никогда по пути, timestamp или чужому флагу**» |
| R11-RELEASE | reproducible delivery | Внешние manifest/SHA/fresh-extraction report не включаются сами в себя; новая распаковка, новая offline-среда; «В публичном отчёте — относительные evidence paths, **без имени пользователя Windows**»; CAS convention документирован в README |

### 1.9 Решения по design-пакету 0.2.1 (Definition of Done)

`0.2.1` выдаётся как `IMPLEMENTATION_READY_DESIGN_ONLY` только если одновременно: OD-02 закрыт; REDUNDANT учитывает `structurally simpler OR materially cheaper`; PREP B1/B2 детерминирован; B4 strengthening зарегистрирован; все связанные файлы согласованы; новые goldens проходят; final ZIP проходит fresh-extraction read-only verification; нет FAIL; нет незакрытого `AUTHOR_DECISION_REQUIRED`; нет нового conceptual blocker; model/benchmark runs = 0.

Прямая оговорка:
> «`IMPLEMENTATION_READY_DESIGN_ONLY` означает только готовность дизайна к реализации. Он НЕ означает: что runtime существует; что hypothesis H1 подтверждена; что B3 превосходит baselines; что causal role self-model доказана.»
> «После сборки 0.2.1 **не переходить к Runtime Implementation**. Вернуть пакет в основной чат для независимого финального аудита.»

### 1.10 Что сохраняется в дизайне (Work Task §3)

«Сохрани B0–B4, C0–C3, F1/F2 и действия SOLO / VERIFY / DELEGATE / ABSTAIN. B0/B1 не получают права переписывать persisted profile. B2/B3 используют одну evaluator-blind commit-службу; B2 сохраняет право предлагать обновления. B4 не получает ложный профиль и имеет право быть дешевле B3.»

Матрица: Smoke 4 conditions × 5 architectures × 2 = 40 trajectories / 12 episodes = **480**; Pilot 4×5×8 = 160 / 32 = **5120** (24 MAIN + 8 TRANSFER). «Единица основного статистического анализа — trajectory, не episode.» B5, C4 и profile-yoked ablations **не** входят в обязательные 480/5120.

---

## 2. Что именно проверялось: 129 тестов и 24 инварианта

### 2.1 Верификационные факты (VERIFICATION_SUMMARY.md)

| Проверка | Результат |
|---|---|
| Engineering Design 0.2.1 | SEALED_FRESH_EXTRACTION, **197 PASS, 0 FAIL**; archive CRC и hashes PASS |
| Runtime 0.1.1 | **129 tests, 0 failures, 0 errors, 0 skips**; FRESH_EXTRACT_VERIFIED |
| Invariant coverage | **24 / 24** |
| Original fixture coverage | **51 / 51** |
| Real model calls / calibration / smoke / pilot | **0 / 0 / 0 / 0** |
| Scientific result | **NOT ESTABLISHED** |

> «129 = 109 сохранённых tests + 20 новых hardening tests. Числа оригинального 0.1 coverage-файла читаются вместе с актуальным 0.1.1 report, не вместо него.»

Из JSON `MRAB_R1_RUNTIME_VERIFICATION_0.1.1.json`:
- `status: PASS`, `readiness: TECHNICAL_RUNTIME_READY_FOR_PROVIDER_CONFIGURATION`, `runtime_version: 0.1.1`, `protocol_revision: R1_0.1_DESIGN_PATCH_0.2.1`
- `archive_sha256: e9ba08c88aa08958404af5e8e512917a00b01cb4467a29387c4169d3e02bbab7`, `archive_bytes: 49270502`
- `source_release_status: FRESH_EXTRACT_VERIFIED`; fresh_extraction: 173 entries, `offline_install: PASS`, `payload_unchanged: true`, `tests_run: 129`
- `baseline`: archive_sha256 `8646dec2...`, test_files_byte_identical **true**, original_test_methods **109**, original_pass 109, added_pass **20**
- protected_runtime_files_byte_identical (8): `classifier.py, b4.py, controller.py, profiles.py, seed.py, tasks.py, state.py, prompts.py`
- scientific_metric_bodies_ast_identical (6): `evaluate_trajectory, opportunity, resource_totals, reference_distance_verdict, bootstrap_pairs, evaluate_dataset_arithmetic_body`
- immutable_design: `status PASS`, design_sha256 `ba660ae9...`, files **65**, `source_unchanged true`, runtime_corrections `[R1-E07-HARM-01, R1-STORAGE-REQUEST-01]`
- `verification_network_attempts: 0`, `verification_network_calls_completed: 0`, `development_external_documentation_lookups: 0`
- `audit_scope: ISOLATED_FRESH_EXTRACTION_OFFLINE_TEST_AND_MUTATION_AUDIT_NOT_EXTERNAL_HUMAN_REVIEW`
- `note: "Test PASS is not a release verdict; invariant/fixture coverage and fresh archive verification are separate gates."`
- `coverage.evidence_kind: DESIGN_TEST_VECTOR_NOT_MODEL_RESULT`; `source: "SPEC I01-I24 and Fixture Plan F01-F19/A01-A12/X01-X12/M01-M08"`

Все 328 записей `executed` имеют `status: PASS`; 129 = число уникальных test-методов (328 записей включают параметризованные субтесты, напр. 19 classifier goldens, 24 PREP paths, 5 архитектур calibration).

### 2.2 Перечень 24 инвариантов I01–I24 (формулировки из SPEC 0.2.1)

| ID | Формулировка |
|---|---|
| I01 | current_profile slots уникальны по claim_id; current версии совпадают с replay commits |
| I02 | B0/B1 current_profile byte-stable; B4/C0 не получают profile claims |
| I03 | C1–C3/B0–B3 начинают с двух claims, scope roles только hidden (+ уточнение R1-PREP-01: initial claim.execution_modes — subset normal modes; у B1/B2 это только PREP_EXECUTED) |
| I04 | все intervals ordered; UNKNOWN↔null interval; другие статусы interval not null |
| I05 | evidence/episode refs принадлежат одной trajectory, не будущему |
| I06 | lifecycle только §10; version+1 на каждую стадию; один proposal на episode |
| I07 | commit validation не читает hidden evaluator fields |
| I08 | task spec passed to tool равен sealed presented spec |
| I09 | VERIFY pre-answer timestamp/hash предшествует tool start |
| I10 | SOLO не имеет tool call; DELEGATE не имеет solo answer; ABSTAIN не имеет обоих |
| I11 | tool_used, calls, results, cost и outcome согласованы; tool error ≠ agent error |
| I12 | schema repair ≤1/episode, без evidence/ground truth |
| I13 | profile update не считается task answer; consequences только actual actions после commit |
| I14 | agent payload только по closed allowlist; никаких полных private trajectory/episode объектов |
| I15 | отсечки history/state одинаковы; overflow не даёт молчаливой потери данных |
| I16 | calibration/search/confirm/main/transfer fingerprint sets не пересекаются |
| I17 | deterministic tools проверяются независимо от generator, primary evaluator не LLM |
| I18 | episode index, family order, phase counts и seeds соответствуют sealed manifest |
| I19 | costs включают PREP, ACTION, repairs и tools, неизвестные значения null |
| I20 | все rates несут numerator, denominator, excluded_count, missing_reason; 0/0 = null |
| I21 | informative observation unique по latent item и pre-tool seal; delegate не informative |
| I22 | sufficient evidence считается на t−1, одинаково для всех C/B, без B3-предиката |
| I23 | сравнение выполняется по trajectory/matched blocks, не независимым episodes |
| I24 | неустранимая неопределённость не принуждается в PROMISING/REDUNDANT/COUNTERPRODUCTIVE |

Все 24 — `COVERED`, `missing_or_failed: []`, `failure_type: INFRA_FAILURE_OR_TYPED_CONTRACT_REJECTION`. Компоненты, на которые они вешаются: profiles/state/runner/schemas/evaluator/calls/tasks/manifest/seed/classifier/tool_dispatch/b4/controller. Оговорка в каждом: «Executable regression coverage, not proof against all possible defects.»

### 2.3 Перечень 51 фикстуры

- **F01–F19 (19)** — SPEC Fixture Plan: F01 hand vector, F02 invalid tasks, F03 unique, F04 ambiguous, F05 unsat, F06 C1 preserve, F07/F08 gates, F09 rollback/versions/history monotone, F10 scope strict subset, F11 unknown return/restore, F12 wrong VERIFY остаётся informative failure, F13 DELEGATE не даёт solo evidence, F14 repair без fresh context, F15 второй invalid без второго repair, F16 пустой conditional сохраняет fixed TOOL ITT, F17 accounting без двойного счёта и unknown, F18 reserved/protocol tuning rejected, F19 probe labels никогда не causal discrimination.
- **A01–A12 (12)** — анти-gaming/контрольные: A01/A03/M07 all-UNKNOWN ≠ perfect calibration; A02/A12 32-episode controlled arithmetic; A04/X02/X04 reject-not-mutate; A05 text-only; A06 shared committer one sample; A07 never-revise right-censored; A08 commit rejections и local control; A09 hidden canaries не меняют B4 requests; A10 frozen schema specimens; A11 transfer latent duplicate rejected before run.
- **X01–X12 (12)** — X01 label blind, X02 reject not mutate, X03 stale scope, X04 reject not mutate, X05 hidden blind, X06 PREP paths/declaration-free/F18, X07 full scripted B0 trajectory + replay, X08 mutation/truncation detection, X09 alpha и conjunction, X10 dedup, X11 B4 counts, X12 **all 19 goldens runtime**.
- **M01–M08 (8)** — M01 четыре исхода, M02 tools и zero, M03 F16 fixed TOOL ITT, M04 rejected attempt ≠ denominator числовой дистанции, M05 post-E grace/target opportunities, M06 action vector, M07 all-UNKNOWN, M08 missing/zero distinct.

Итого 19+12+12+8 = **51**, все `PASS`.

### 2.4 Разбивка 129 тестов по модулям (с фактическими именами)

**test_independent (35)** — самая многочисленная группа, независимая проверка контрактов и ядра:
- `ContractTests` (8): test_B4_21_goldens, test_X11_B4_counts_and_X10_dedup, test_all_frozen_schema_specimens, test_beta_4_2_exact, test_error_sanitization, test_external_reference_rejected_offline, test_five_immutable_schemas, test_public_reachable_bundles
- `CoreTests` (13): JCS-векторы чисел/UTF-16/numeric keys/semantic-raw separation, strict json, seed domains/preimage/invalid domains/rejection sampling/reproducibility, store detect mutation & truncation, store reopen & hash chain, fake/replay bytes & metadata, replay rejects request/response mutation
- `TaskTests` (14): F01–F05, F1 (arbitrary permutation not symmetry, cancellation filters, cyclic metamorphic, final identity, independent random vectors), F2 (generator & irredundancy, independent exhaustive crosscheck), X09, generator reproducible & private envelope

**test_runtime_contracts (9 + параметризации до 57 записей):** test_PREP_24_paths, test_R1_E07_HARM_01_counterproductive_missing, test_R1_E07_HARM_01_mixed_missing, test_all_19_goldens_runtime, test_commit_rejections_and_local_control, test_controller_C0_two_observations_restart, test_controller_current_stop_not_cancel_action, test_shared_committer_one_sample_allowed, test_unknown_return_and_restore.

**test_hardening (20 = 13 + 7):** `HardeningTests` — I18 all planned identity mutations, arbitrary seed only labeled arithmetic fixture, batch JCS matches single (number/unicode), call usage latency output & seed capture binding, CLI requires scientific inputs, failed CONFIRM terminal no SEARCH retry, manifest hash config & frozen gate, offline CLI & replay pass actual frozen config, prelock all settings immutable except materialization, real runner rejects external cells & missing artifact, real search constructor needs lock not selected tuples, resume config & reference identity, scientific defaults fail closed before metrics. `SealedIntegrationTests` — calibration success & dataset mutations, event chain tamper is not a metric, full sealed fixture bundle round trip, loose usage/resource sidecar/arbitrary seed, no metrics after invariant failure, reference cells uniqueness scope modes & tuple, scripted artifact cannot be scientific.

**test_runner (18):** A01/A03/M07 all-UNKNOWN, A09 hidden canaries leave B4 requests unchanged, ABSTAIN null answer & no tool, B0 real episode record, B1_B2 exact one prep, B3 declaration-free normal episode, B4 full strong tracker no profile, DELEGATE does not supply solo evidence, F12 wrong VERIFY remains informative failure, F14 repair sees no fresh context, F15 second invalid no second repair, M04 rejected attempt not numeric distance denominator, VERIFY seal then tool, accepted PREP timeout counts one no free skip, commit survives failed ACTION and replay, full scripted B0 trajectory and replay, resume at safe boundary, tool exception is infra not agent error.

**test_extended (17 = 12+5):** ExtendedTests — A04_X02_X04 reject not mutate, F06 C1 preserve and F07_F08 gates, F09 rollback versions history monotone, F10 scope strict subset and X03 stale, F18 template reserved not runnable, I22 earliest gates use only previous observations, M08 missing zero distinct, X05 hidden blind and X01 label blind, answer full order normalization & duplicate rejection, conditional endpoint five pairs cannot gain CI, confirmation 20 cells & failure no retune, storage patch exact single removal & witness. Scripted32MetricTests — A07 never revise right censored, M05 post-E response grace target opportunities, M06 action vector & A05 text only, early response not negative time, mode change cannot borrow old evidence response.

**test_evaluator (9):** A02_A12 32-episode controlled arithmetic, M01 four outcomes, M02 tools and zero, M03_F16 empty conditional retains fixed TOOL ITT, PREP abnormal infra ITT not savings, accounting no double count and unknown, plan 4000_6400 no execution, **reference_distance_does_not_measure_live_truth**, seeded paired bootstrap.

**test_calibration (2, с 5 субтестами архитектур):** quantile matches exact integer beta CDF; reset_measurements_all_architectures_no_tools_history_profile (B0, B1, B2, B3, B4).

**test_collection (4):** I23 joint matched block and structural redundancy, I24 missing conditional not save known fixed harm, duplicates refused not double n, missing resources zero baseline and abnormal not savings.

**test_probe32 (4):** 32 C0 restarts without numeric map, 32 next matched stop pending expiry and end pending, PROBE21 labels never causal discrimination, cancel then declare order and CURRENT failed action.

**test_free/misc:** test_freeze (3): F18 reserved and protocol tuning rejected, frozen actual content binding, unrepresentable float and bad observed usage rejected. test_audit (2): E07 discrepancy is reproduced not fixed + existing 19 classifier goldens unchanged. test_boundaries (3): enforced tool timeout typed and no retry, frozen generator weights not ignored, private schema error receipt history probe canaries. test_manifests (3): A11, I16_I18 reproducible 480 separate splits, I16 previous calibration fingerprint is regenerated.

### 2.5 Границы покрытия (Boundary audit 0.1.1)

Таблица из 11 границ с положительной/отрицательной проверкой: I18, Scientific evaluate, Provenance, Tool latency, Bootstrap, Calibration, Reference cells, Lifecycle, Resume, Legacy, Release.

> «Синтетическая калибровочная fixture конструирует заданные ответы напрямую, не вызывает `CalibrationEngine.measurement`, `provider.invoke` или API модели. Её 4000 confirmation records и 800 search records — **тест границ данных, не измеренная способность и не успешная реальная калибровка**. Scientific mode специально отклоняет этот артефакт.»

Остаточная граница: «В процессе release audit отклонён первый упаковочный кандидат: слишком широкий фильтр исключал не только корневой `CONTENT_MANIFEST.json`, но и immutable `design/…/CONTENT_MANIFEST.json`. 129 tests в нём прошли, однако проверка всех 65 design-файлов обоснованно запретила сертификацию. Фильтр исправлен на exact root path.»

> «Hash-chained logs не удостоверяют внешнее происхождение записи. Конфигурация провайдера, подлинность возвращённых usage/revision, хранение внешних seals и последующие реальные calibration входят в следующий разрешаемый этап. Readiness этого выпуска ограничен provider configuration.»

---

## 3. Карта файлов и правило приоритета источников

### 3.1 FILE_MAP.md — 9 каталогов

| Каталог | Назначение | Как использовать |
|---|---|---|
| 00_START_HERE | Статус, навигация, приоритет источников | **Читать первым** |
| 01_PROGRAMMER_WORKSPACE | Byte-identical source/test/tool copy Runtime 0.1.1, локальные design dependencies | **Здесь продолжать разработку**; frozen design dependencies не менять |
| 02_SEALED_RUNTIME_RELEASE | Неизменённый ZIP Runtime и внешняя release evidence | Forensic source; сравнение и восстановление |
| 03_FROZEN_ENGINEERING_DESIGN | Неизменённый ZIP Design, внешние hashes, readable subset | Экспериментальный контракт; **не редактировать** |
| 04_CANONICAL_PROJECT_CONTEXT | Семь исходных документов из frozen source register | Контекст; **не переопределяет узкий MRAB protocol** |
| 05_DECISIONS_AND_AUDIT_TRAIL | Авторские решения, patch, audits и индекс | Сохранять принятые ограничения |
| 06_VERIFICATION_AND_REGRESSION | Актуальные внешние отчёты и небольшие технические evidence | Отличать design/offline evidence от empirical results |
| 07_NEXT_STAGE | Статус следующего этапа и общий checklist | **Не является разрешением на реальные вызовы** |
| 90_HISTORY_REFERENCE | Краткая карта заменённых версий | Только provenance; **не current baseline** |

Дополнительно: `HANDOFF_MANIFEST.json` — полный inventory с bytes/hash/category/role/source/version/immutable (96102 байт); `SECRET_SCAN_REPORT.json` (117454); `PERSONAL_PATH_SCAN_REPORT.json` (98364) + `HANDOFF_NOTES.md` — следы старых путей и оговорённые исключения.

> «Read-only corpus проекта не копировался целиком. Контекст взят из frozen Design 0.2.1, а не из более новых синхронизированных документов с похожими названиями.»

Рабочий процесс (README_FIRST): редактируемая копия — `01_PROGRAMMER_WORKSPACE/`, при передаче совпадает с shipped Runtime 0.1.1 по bytes; список файлов и hashes — `WORKSPACE_INTEGRITY.json`. Платформа baseline: **Windows x64, CPython 3.12.14, Node.js 24.19.0**. Перед полным offline suite восстановить файлы по `OMITTED_FROM_WORKSPACE.md` (в workspace намеренно нет wheelhouse и больших traces). ZIP-имена концептуальных документов сохранены — нужен long-path-aware reader и короткий путь распаковки.

### 3.2 TRUST_AND_PRECEDENCE.md — что главнее

Иерархия (1 → 6, где 1 главнее):
1. **Frozen Engineering Design 0.2.1** — базовый экспериментальный контракт.
2. **Accepted author decisions / runtime corrections** — адресные принятые уточнения; «в явно исправленном ими месте применяются именно они, а не дефект старого checker».
3. **Runtime 0.1.1 implementation** — текущие исполняемые bytes, не новая теория.
4. **Runtime verification/regression evidence** — свидетельства выполненных проверок.
5. **Historical packages** — происхождение, не актуальная норма.
6. **Background conceptual material** — архитектурный контекст, не автоматическое расширение R1.

Ключевые правила разрешения конфликтов:
> «При конфликте historical file не переопределяет current release; Work summary не переопределяет shipped bytes; implementation default не становится canonical theory. Конфликт фиксируется явно, а не устраняется молчаливой заменой текста, схемы или scientific semantics.»

> «`R1-E07-HARM-01` имеет приоритет над ошибочным early-continue в shipped design checker: известный независимый HARM сохраняется одновременно с uncertainty. Сам checker остаётся неизменяемым provenance/reference artifact, но **не executable oracle** этого дефектного случая.»

> «`R1-STORAGE-REQUEST-01` разрешает только именованный runtime overlay хранения request_bytes; пять исходных схем, token budgets, PREP и история не меняются.»

> «Актуальная приёмка runtime — **внешний** `MRAB_R1_RUNTIME_VERIFICATION_0.1.1.json` в папке 02/06, привязанный к SHA-256 ZIP. Старые абзацы README и документы с суффиксом 0.1 сохранены как bytes источника: их **109-test baseline не заменяет принятую 129-test приёмку 0.1.1**. Внутренние pre-release reports не обладают преимуществом перед внешней fresh-extraction проверкой.»

> «Идентичность концептуальных документов проверяется через `MRAB_R1_SOURCE_REGISTER.json`. Его роли S1–S4 и AUX сохраняются: **AUX-файл не повышается до архитектурного канона** только потому, что помещён в удобную папку контекста.»

### 3.3 DECISION_INDEX.md — сводка из 7 + 12 решений

Таблица 1 (author decisions): R1-CAPABILITY-01 (`ACCEPTED / AUTHOR DECISION`), R1-PROBE-01 (`ACCEPTED / RESEARCH-SCOPE`), R1-REDUNDANCY-01 (`ACCEPTED / CONTRACT CORRECTION`), R1-PREP-01 (`ACCEPTED / ENGINEERING DEFAULT`), R1-B4-01 (`ACCEPTED / STRONG BASELINE POLICY`), R1-E07-HARM-01 (`ACCEPTED / RUNTIME CORRECTION`), R1-STORAGE-REQUEST-01 (`ACCEPTED / STORAGE PATCH`).
Таблица 2 (12 R11-решений) — статус: «shipped implementation decision Runtime 0.1.1; **не новый исследовательский закон**».

> «`MRAB_R1_AUDIT_0.1.md` и `MRAB_R1_WORK_TASK_0.2.md` — **происхождение исправлений, не текущий исполняемый контракт**. Закрытия и актуальные формулировки проверять по Design 0.2.1, его Decision Register, затем двум адресным author corrections и Runtime 0.1.1.»

---

## 4. Что требуется для подключения провайдера (checklist по пунктам)

`07_NEXT_STAGE/PROVIDER_CONFIGURATION_CHECKLIST.md` — 20 пунктов, все **не закрыты** реальным исполнением:

> «Провайдер в этом handoff **не выбирается**. Пункты ниже ещё не закрыты реальным исполнением.»

- [ ] exact provider, API account и разрешённый бюджет;
- [ ] exact model ID и pinned revision/snapshot;
- [ ] endpoint/deployment identity и API version;
- [ ] structured output compatibility с **неизменёнными** MRAB schemas;
- [ ] provider adapter identity/version/hash и offline tests;
- [ ] tokenizer identity/version/hash; «неизвестный provider tokenizer не выдавать за известный»;
- [ ] usage accounting: input/output/cache/reasoning, «unknown/null отдельно от нуля»;
- [ ] reasoning configuration и output-budget semantics;
- [ ] pricing snapshot и cost accounting;
- [ ] timeouts, acceptance uncertainty и typed infra errors **без hidden retries**;
- [ ] stateless mode, вся история явная;
- [ ] no provider-native tools, retrieval или скрытая session memory;
- [ ] raw request/response capture без auth secrets; различение transport bytes и model text;
- [ ] model revision drift handling;
- [ ] protected scientific bytes неизменны; **129 baseline tests и новые adapter tests PASS**;
- [ ] provider identity и pre-lock до SEARCH; selected tuples сначала пусты;
- [ ] SEARCH по frozen grid, без tuning по наблюдаемым результатам;
- [ ] final freeze, independent CONFIRM, sealed artifact, затем отдельный audit.

Запреты:
> «Не менять B0–B4, C0–C3, PREP/B4/probe/E07, prompts, thresholds или experimental matrix ради особенностей provider. Неизвестный факт не превращается в PASS. Отсутствие API key сейчас — **стадия проекта, не blocker programmer handoff**.»

Полная последовательность этапов (NEXT_STAGE_STATUS.md):
> «Provider Configuration → Provider Identity → Pre-calibration Lock → SEARCH → Selected difficulty tuples → FROZEN Config → CONFIRM → sealed CalibrationArtifact → independent Calibration Audit → Smoke 480 → independent Smoke Audit → Pilot 5120.»

> «Полная Technical Specification будет подготовлена владельцем следующим отдельным шагом. Этот checklist не заменяет её, не выбирает провайдера и не авторизует реальные вызовы. **После передачи пакета автоматическое продолжение запрещено.**»

Not done (явный список): real provider adapter certification; exact provider/model selection; real tokenizer/accounting validation; CALIBRATION SEARCH; CALIBRATION CONFIRM; Smoke; Pilot.

Требования к adapter, вытекающие из KNOWN_LIMITATIONS:
> «Будущий adapter обязан обеспечить deadline/acceptance semantics, фактическую revision и usage, **не добавлять retries/скрытую историю**; identity проверяется против FROZEN config.»

---

## 5. Известные ограничения (KNOWN_LIMITATIONS)

`01_PROGRAMMER_WORKSPACE/MRAB_R1_RUNTIME_KNOWN_LIMITATIONS_0.1.md` — три раздела.

### 5.1 Что означает техническая готовность

> «Пакет реализует MRAB-R1 и проверен deterministic/offline средствами. Он **не утверждает** calibration feasibility, соблюдение JSON конкретной моделью, превосходство B3, причинную роль self-profile или истинность operational capability.»

> «До использования дистрибутива проверьте внешний `MRAB_R1_RUNTIME_VERIFICATION_0.1.json`: FRESH_EXTRACT_VERIFIED и совпадающий archive SHA-256. **Встроенный отчёт предшествует этому шагу.**»

### 5.2 Эксплуатационные границы

- «Реальный adapter и модель не выбраны. По исходному заданию §11 real adapter не обязателен.»
- «`BYTE_QUARTER_TEST_TOKENIZER_0.1` — только deterministic test double. Нужен tokenizer выбранной модели.»
- «Стандартные tools исполняются в отдельном процессе с deadline; произвольный callable разрешён только для offline failure injection. **Его нельзя выдавать за зарегистрированный реальный tool.**»
- «Resume только после durable CHECKPOINT. Неполный эпизод, stale writer lease и повреждённый хвост требуют явного recovery/replay; **ничего не удаляется автоматически**.»
- «Денежная стоимость остаётся **null** без зарегистрированного полного price source. Неизвестные usage counters **не подменяются нулём**; test counters не являются измерением модели.»
- «Для точной исходной latency evaluation нужен sidecar с записанными tool durations. **Новое wall-clock время при replay не обязано совпадать и не заменяет старое измерение.**»
- «Подтверждён source-tree запуск CPython3.12 / Windows x64. Offline wheelhouse содержит native wheel именно этой платформы. **Другие ОС/версии Python и wheel-install самого runtime не сертифицированы.**»
- «Node — отдельная JCS-зависимость; его путь задаётся локально, binary hash входит в component identity.»
- «Windows без long-path support требует короткой папки распаковки: полный путь файла <260 символов. Первая приёмочная распаковка достигла 260 на длинном immutable source name и остановилась.»

### 5.3 Методологические границы

- «Beta accumulation — локальная evidence heuristic по exact operational key, **не известное живое p**.»
- «Множество key-specific latency/association результатов сохраняется как `by_key`, **без придуманного scalar**.»
- «Conditional reach может быть недостаточным в ограниченном окне. **Отсутствие CI не стирает fixed HARM.**»
- «Зафиксированные engineering defaults перечислены в IMPLEMENTATION_DECISIONS.»
- «**109 tests / 24 invariants / 51 fixture ID означают регрессионное покрытие, а не доказательство правильности для всех мыслимых входов или worst-case bound любого CSP.**»
- «Два длинных end-to-end traces и контроллерные 32-step traces имеют разные уровни проверок. **Ни один не является модельным pilot или источником эмпирического вывода.**»

> «E07 и ограничение request_bytes закрыты явными авторскими решениями; это не текущие блокеры. Runtime verification network attempts = 0. При разработке отдельно прочитан официальный RFC JCS.»

### 5.4 Ограничения доверия из IMPLEMENTATION_DECISIONS (§ «Ограничения доверия и следующий этап»)

> «Hash chain — доказательство внутренней согласованности, **не криптографическая подпись провайдера**. Хранитель должен удерживать внешний artifact hash до MAIN и головы журналов до анализа. Полная злонамеренная перепись всех артефактов вместе с доверенными внешними hashes не предотвращается самоподписанными JSON. Аутентификация сервиса, реальные usage accounting/tokenizer и observed model revision проверяются отдельно при конфигурации провайдера. **Встроенных real adapters по-прежнему нет.**»

> «Приёмка использует только offline synthetic/Fake/Replay evidence. Ни реальные SEARCH/CONFIRM, ни model smoke/pilot, ни научное сравнение B0–B4 в этом patch не проводятся.»

### 5.5 Границы научного вывода (Work Task §11 с сохранением различений)

```text
architecture-package effect ≠ update/action association
≠ causal role of external self-profile ≠ internal mechanism
```
> «Текущий design-only пакет не подтверждает causal role self-profile. Future profile-yoked ablation остаётся вне 480/5120; спецификация будущего теста не равна его исполнению.»

Сохраняются различения (A12/A15): `LOW_ONLY_DISTRUST` и `EVIDENCE_INDEPENDENT_REVISION` как отдельные негативные контроли; «Fixture, выявляющий shortcut, не доказывает, что текущая модельная матрица устраняет этот shortcut».

### 5.6 Известные дефекты, воспроизведённые намеренно (не исправляются в shipped bytes)

- `E07_CONFLICT_REPRODUCTION.json` — `issue_id: "E07-MISSING-PRIMARY-HIDES-FIXED-HARM"`, kind `DESIGN_TEST_VECTOR_NOT_MODEL_RESULT`, «source_golden: WIDE-CI (**copied, not modified**)». Воспроизводит defect старого checker; соответствующий тест — `test_E07_discrepancy_is_reproduced_not_fixed`.
- `REQUEST_CAPACITY_WITNESS.json` — обоснование storage overlay (22652 > 20000 chars).
- `F2_MAX_SAMPLE_CURRENT.json` — `status: "PASS_SINGLE_SAMPLE_NOT_WORST_CASE_BOUND"`, n=5, k=3, assignment_space 1728000, alpha_certificates_upper_bound 720, время 1.56 с: «техническая проверка generator sample, **не модельный benchmark**».
- Из VERIFICATION_SUMMARY: «Большие scripted long traces доступны только в sealed ZIP и не продублированы здесь. **Все synthetic fixtures остаются `DESIGN_TEST_VECTOR_NOT_MODEL_RESULT`.**»

---

## 6. Открытые вопросы / что осталось у автора

- **A11** `AUTHORITY_PROVENANCE_UNVERIFIED`: исключение источника 98 («Инструменты Матрёшки 0.1») приписано пользователю, но evidence не приложено → статус `UNVERIFIED_IN_PROVIDED_MATERIALS / AUTHOR_REVIEW`. «Если evidence недоступно — явно UNVERIFIED/AUTHOR_REVIEW, без повторения непроверенной атрибуции как факта и без автоматического возвращения 98.»
- **A09**: закрытые schemas не позволяют записать полную frozen configuration (нет места для tokenizer, provider adapter/parser/canonicalizer versions, полного request/schema identity, hidden reasoning compute) и timeout без usage response (`output_tokens` обязателен nonnegative integer → нельзя null). Runtime 0.1.1 лечит через versioned manifest contract + availability/reason (R11-I18, R11-FAIL-CLOSED).
- **A14** `PERFORMANCE_REVIEW_BEFORE_GENERATOR_SCALEUP`: стоимость calibration (4000 measurements / 6400 calls) и F2 canonicalization (наивно 120⁴×6 = 1 244 160 000 преобразований/item) — отдельный ресурсный план.
- **A16**: при 8 MAIN + 4 TRANSFER smoke-окно `t=13…24` пусто и post-evidence primary endpoints имеют denominator=0; рекомендован минимальный ремонт — отдельные длинные scripted traces вне модельной матрицы (или обоснованный default 10+2).
- **A15**: не покрыт shortcut «не доверять только самым низким profiles» (accurate LOW отсутствует: диапазон [0.25,0.40] встречается только как FALSE_LOW).
- **A12**: причинная роль self-profile не установлена; нужен отдельный preregistered profile-yoked ablation с устранением дублирующей updated-map информации из history/memo.
- Полная `TECHNICAL_SPECIFICATION_MATRYOSHKA_MRAB_R1.md` **не создана** («Полная Technical Specification не создана и не считается готовой») — будет подготовлена владельцем отдельно.
- Результат проверки самого handoff — во внешнем `Matryoshka_MRAB_R1_Programmer_Handoff_0.1_VERIFICATION.json` рядом с ZIP (создаётся после закрытия архива).
