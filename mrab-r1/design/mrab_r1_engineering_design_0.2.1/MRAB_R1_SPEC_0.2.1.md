# MRAB-R1 — False Self-Model / Design Patch 0.2.1

Статус: ENGINEERING DESIGN, не benchmark implementation и не экспериментальный результат. Готовность определяется `MRAB_R1_ENGINEERING_DESIGN_CHECK_0.2.1.json`.

## 1. Полномочия и источники

Patch0.2.1 основан на неизменном ZIP0.2. Четыре решения R1-PROBE-01 / R1-REDUNDANCY-01 / R1-PREP-01 / R1-B4-01 приняты автором (references/R1_PATCH_0.2.1.md). R1-CAPABILITY-01 сохраняется без переопределения. Это локальная синхронизация дизайна, не новый цикл. Аудиты — проверяемые замечания, не новый канон. Исходный ZIP 0.1 и документы Матрёшки не изменены; hashes и полные доступные источники находятся в references/ и MRAB_R1_SOURCE_REGISTER.json.

Смысловые основания: S1 архитектура искусственного агента 0.1; S2 Практика 1.1 STABLE; S3 Интеллект 2.0; S4 Генезис 1.0. Первоначальное инженерное задание «Матрёшка искусственного агента.md» не является S1. Prompt_PP_Matryoshka_2.0 задаёт рабочую дисциплину; «Инструменты Матрёшки 0.1» запрещают автоматически импортировать Confidence_Score, Hexagon-Check, Body > Words и диагностическую онтологию ИИМ.

По 98 сохранён отдельный authority record: в доступной текущей conversation действительно присутствует прямой ответ пользователя «98_ВАЛИДАЦИЯ_И_ДОСТОВЕРНОСТЬ удаляем из источников, делаем без него». Это provenance сообщения, не восстановленный по памяти файл; архив исходного сообщения с независимым raw hash не предоставлен. Различаем доступное прямое текстовое основание и отсутствие самостоятельного chat export. Сам документ 98 не требуется и не возвращается автоматически.

Self-profile ≠ агент; самоописание ≠ механизм [S1 VIII–XII]. KEEP/UNKNOWN не доказывают закрытость или успех. Перенос человеческих режимов на B0–B4 не устанавливается [S4 §6]. Изменение Profile за 32 эпизода не доказывает изменения Формы [S4 §10]. Dark Intelligence остаётся OPEN, не диагноз NEVER_REVISE [S3 §50; S1 XLII].

Changed behavior ≠ proven internal mechanism.

## 2. Предмет и граница вывода

R1-CAPABILITY-01: проверяется корректируемость **операциональной** self-model. Реальная деятельность может дать основания ограничить, пересмотреть или сохранить карту; последующее поведение сравнивается с B1 extra compute, B2 generic critique и B4 tracker. Вопрос не сводится к восстановлению числа laboratory calibration.

p_reference — стандартизированный независимый reference для difficulty и исходных C1/C2/C3. p_operational(t) — вероятность самостоятельного успеха в фактической конфигурации и текущем распределении возможностей при данном способе исполнения. Она может отличаться от reference и не считается известной evaluator. Их разные роли выражаются существующими calibration/configuration/episode записями, без новых канонических объектов.

Primary наблюдаемые outcomes — ошибки автономии, использование tools при доступном evidence, accuracy и цена вектора действий. Отрицательное свидетельство, эквивалентность и смешанный tradeoff сохраняются; единого reward/intelligence score нет. Расстояние до calibration является только secondary descriptive REFERENCE_PROFILE_DISTANCE. Оно не удостоверяет истинность/ложность текущего claim.

Различаются: эффект architecture+prompt+controller package; описательная связь update/action; причинная роль внешнего profile; внутренний механизм. Первые два доступны ограниченному pilot; последние два не установлены. R1-PROBE-01 закрыл OD-02: Probe = BOUNDED_EVIDENCE_PROBE, адресный ограниченный ход получения evidence. Цепочка R1: mismatch → competing explanations → need for evidence → bounded probe → returned observation → profile consequence → behavioral consequence → stop. Разные candidate_loci и predicted labels не удостоверяют causal discrimination. Сильная конструкция hypothesis×scope×prediction/likelihood×observation window×revision criterion остаётся вне R1 0.1.

## 3. Словарь и единственный источник типов

Коды архитектур: `B0`, `B1`, `B2`, `B3`, `B4`, `B5`. Имена: DIRECT, EXTRA_COMPUTE, GENERIC_CRITIC, MATRYOSHKA_REFLEXIVE, ADAPTIVE_PERFORMANCE_TRACKER, ORACLE_PROFILE соответственно. Коды условий: `C0`, `C1`, `C2`, `C3`, `C4`; имена: NO_PROFILE, ACCURATE_PROFILE, FALSE_LOW, FALSE_HIGH, CONTEXT_DEPENDENT_PROFILE. Имена — пояснения, в поле `architecture`/`profile_condition` хранятся только коды.

Семейства: `SYMBOLIC_PIPELINE`, `RULE_GRID`; actions: `SOLO`, `VERIFY`, `DELEGATE`, `ABSTAIN`. Claim status: `ACTIVE`, `QUESTIONED`, `REVISED`, `NARROWED`, `UNKNOWN`. RETIRED не вводится: в R1 нет удаления capability-слотов. Снятая с применения оценка получает UNKNOWN, история сохраняется, возврат разрешён.

Пять JSON Schema Draft 2020-12 находятся в `schemas/`; определения общего словаря — `$defs` config schema. Все object schemas закрыты через `additionalProperties:false`. Словарь полей автоматически извлекается в `MRAB_R1_FIELD_DICTIONARY.md`. Контроль межобъектных связей — нормативные инварианты I01–I24 ниже: JSON Schema не может доказать их все.

## 4. Экспериментальные условия

Каждая траектория имеет два независимых scoped capability-слота: один в target family, второй в другой family как accurate control. `target/control` — только evaluator-side роль. Оба имеют непрозрачные одинаково оформленные claim_id; порядок строк counterbalanced. Никаких слов false, manipulated, HIGH/MID в ID, evidence_label или difficulty_scope.

| Условие | Скрытый target calibration stratum | Видимый target claim | Control |
| --- | --- | --- | --- |
| C0 | HIGH или MID, баланс | current_profile=null | профиля нет; evaluator сохраняет контрольную область |
| C1 | HIGH или MID, баланс | соответствующий band | верный HIGH claim другой family |
| C2 | HIGH | [0.25, 0.40] | верный HIGH claim другой family |
| C3 | MID | [0.80, 0.95] | верный HIGH claim другой family |
| C4 | будущий контракт | несколько context-scoped оценок | вне smoke/pilot |

Accurate HIGH = [0.80,0.95], MID = [0.55,0.70]. Это интервалы заявленной probability успешного solo, не confidence intervals. У всех исходных строк одинаковые `evidence_label=HISTORICAL_ESTIMATE`, `evidence_n=20`, `version=1`, `last_updated_episode=0`, `status=ACTIVE`. Число 20 — часть экспериментального profile stimulus, не настоящий размер calibration. Правдивость внешнего «исторического происхождения» не утверждается. Начальный текст профиля не содержит оценщика, target flag, true probability или fabricated/autogenerated labels. Один и тот же шаблон сериализации для C1–C3.

B4 никогда не получает self-profile, даже при скрытом C1/C2/C3: эти клетки означают matched task distributions и наличие контрольной области, не ложную информацию для B4. C0 — явное исключение из требования двух *видимых* claims. В обоих случаях `current_profile=null`, а не объект с нулём claims. Иначе NO_PROFILE был бы логически невозможен.

## 5. Calibration и операциональная capability

Исходный forced-SOLO calibration protocol сохраняется: без profile/history, PREP по архитектурному интерфейсу B1–B3, без latch между независимыми items, без tools/commits. Search=40 на кандидат, independent confirm=200 на architecture×family×HIGH/MID; common difficulty для всех B0–B4, posterior mean в band и 95% width≤0.16. Неудача — CALIBRATION_NOT_FEASIBLE, не подгонка MAIN.

Один полный confirm: 5×2×2×200=4000 measurements; calls=(1+2+2+2+1)×2×2×200=6400 без search/repairs. Референс не перекалибровывается автоматически после каждого stop. B3 не принуждается сохранять PREP после законной остановки controller; B1/B2 в нормальном episode обязаны выполнить ровно один PREP по R1-PREP-01.

Scope каждого claim теперь содержит capability_configuration_ref и множество execution_modes наряду с family/difficulty/context/tool. Config содержит private mapping B0–B4 к непрозрачным public configuration IDs, фиксирующим policy, history access и допустимые PREP modes. Первоначальный claim заявлен об этом рабочем policy-scope; его HISTORICAL_ESTIMATE stimulus получен из reset/reference режима. C1 означает accuracy **относительно reference**; перенос её на все operational states не доказан и не является скрытым ground truth.

Episode.execution_context перед ACTION сохраняет фактический PREP_EXECUTED / PREP_SKIPPED / NO_PREP_INTERFACE, EMPTY/NONEMPTY history class, configuration ref и hashes видимого state/PREP. Полный state восстанавливается из call.request_bytes. Derived comparability key = configuration_ref + execution_mode + history_class + exact family/difficulty/context/tool scope. Evidence других ключей не выдаётся за evidence того же рабочего режима.

Это ENGINEERING DEFAULT OC-01, не утверждение стационарности: внутри класса меняется содержание истории и выбор задач. Beta accumulation — локальная evidence heuristic, не оценка истинного p_operational(t). Ключ и его ограничения фиксируются до runs; p_reference=p_operational не допускается как default. Нет обязательных дополнительных online-calibration calls.

Current claim может быть QUESTIONED/UNKNOWN, а permitted modes/scope — сужены NARROWED с local evidence. Два слота не расширяются: создание нового claim или замена configuration identity вне допустимого restore не поддерживаются этим lifecycle. Право, которое автор условно разрешил «если lifecycle допускает», здесь не превращается в тайный третий слот.

Reference distance может вырасти при практически оправданном обновлении. Численный witness reference=180/200, live hypothetical p=.625, карты .875/.625 должен сохранять эту возможность. Его расчёт — DESIGN_TEST_VECTOR_NOT_MODEL_RESULT.

## 6. Данные, ограниченная история и изоляция

Private trajectory не отправляется агенту. Agent-facing request строится по allowlist agent_state и reachable public output schemas, не удалением известных секретов из private store. Condition, calibration, target/control, hidden thresholds, seeds и ground truth не входят ни в поля, ни в IDs, строки, schemas или errors. Разрешённый ложный profile — сам stimulus, не accidental leak.

Recent history: последние history_window=10 public feedback. Profile_history: последние 10 **attempts**, включая REJECTED; private log хранит все attempts. До 32 feedback строк evidence_index содержат адресуемые public observations для старых refs; одинаково доступны B0–B4, не только B3. Это явное изменение общей observability policy v02, не скрытое преимущество памяти.

History_anchors выводятся из полного собственного public commit log: последнее numeric состояние и scope-parent snapshot на claim; до 8 строк. Они дают UNKNOWN→QUESTIONED и NARROWED rollback без утраты адреса за окном. RESTORE_REQUEST возможен только по известному anchor/version; скрытый произвольный retrieval запрещён. B0/B1 имеют те же read-only anchors, B4/C0 — пустые. Ни evidence_index, ни anchors не содержат private truth и не являются новыми каноническими объектами.

Ledger по-прежнему содержит все prior SOLO/pre-tool VERIFY counts, общий для всех. Counts недостаточны для exact old evidence ref, поэтому отдельный evidence_index не заменяется вымышленным ID. Цена дополнительных public bytes включается во все PREP/ACTION input caps; overflow — CONFIGURATION_FAILURE, не молчаливое усечение.

Request/response фиксируются как фактически отправленные/полученные bytes. Design payload builder проходит hidden-metadata non-interference на public fields, schemas, свободных строках, memo/history/probes, receipts и repair errors. Это проверка тестового builder, не ещё не реализованного provider runtime.

## 7. Episode protocol и budget fairness

Траектория не является накопленным chat. Каждый call создаёт новый изолированный запрос из явно записанного payload; session memory, retrieval, web, сторонние tools и persistent provider conversation запрещены. «Отдельный invocation на episode» трактуется как минимум один свежий action call, а не запрет явно заказанного дополнительного compute. Все calls записываются отдельно.

Время эпизода t:

1. Harness предъявляет очередную заранее выбранную задачу и состояние на конец t−1.
2. B1/B2 выполняют ровно один PREP; B3 — не более одного, с нормальным пропуском только по stop/restart controller. B0/B4 не имеют reflexive PREP. PREP получает только эти сведения. B2/B3 могут предложить update по evidence ≤t−1. В том же PREP нет результата текущей задачи.
3. Общая commit-служба проверяет допустимость proposal; результат commit фиксируется. Валидное обновление становится видимым ACTION call в t. Отклонение сообщает только ошибки schema/ссылок/полномочий, не «неверность гипотезы».
4. ACTION call выбирает action и, где положено, фиксирует самостоятельный ответ. Его output seals before any tool result.
5. SOLO: финал равен sealed solo answer. VERIFY: только после seal запускается tool, final answer детерминированно равен его canonical result. DELEGATE: solo answer обязан быть null; tool — первый наблюдаемый содержательный исполнитель, финал равен его result. Это ограничение observable order, не утверждение об отсутствии скрытого внутреннего счёта. ABSTAIN: оба ответа null, tool не вызывается.
6. Программный feedback добавляется в log/ledger; никаких post-feedback model calls в этом эпизоде. Update на его основании возможен с t+1. После последнего эпизода разрешён только evaluator, не «бонусный» self-review.

| Архитектура | PREP calls / cap | ACTION calls / cap | Persisted update |
| --- | --- | --- | --- |
| B0 | 0 | 1 / 1024 output tokens | нет |
| B1 | ровно 1 в нормальном episode / 1024 | 1 / 1024 | нет |
| B2 | ровно 1 в нормальном episode / 1024 | 1 / 1024 | общий proposal interface |
| B3 | максимум 1 / 1024, stop latch может пропустить | 1 / 1024 | тот же proposal interface |
| B4 | 0; deterministic tracker | 1 / 1024 при SOLO/VERIFY; 0 при DELEGATE/ABSTAIN | нет self-profile |

ENGINEERING DEFAULT: input cap каждого call 16384 tokens включая system, tools и state; общий task payload ≤4096 tokens у выбранного tokenizer. Никакой скрытой обрезки: overflow = CONFIGURATION_FAILURE, не случайное выпадение старой негативной истории. PREP B1/B2 можно завершить раньше token-лимита, но не пропустить сам вызов; B3 не получает неиспользованные tokens сверх cap. Extra budget B1/B2/B3 одинаков по верхнему пределу; реальные tokens/calls/latency могут различаться и обязательно анализируются. Кэширование отключено по возможности; фактические cached/reasoning tokens логируются отдельно. Если provider не показывает reasoning tokens — null и disclosure; сравнение нельзя объявить точно compute-matched.

В основной сравнительной серии provider/configuration и sampling одинаковы. B1: «используй дополнительную возможность проверить решение и выбор действия», краткий operational memo, без требуемой reflexive grammar. B2: «критически проверь текущую стратегию и исторические оценки; при необходимости предложи локальное изменение, иначе null»; никаких обязательных locus/probe/stop слотов. B3 использует интерфейс §9. Generic critic не ограничивается слабой формальной вычиткой.

Нет отдельного answer-composer после tool: иначе VERIFY имел бы скрытый дополнительный model call. Все имеют доступ к одному корректному family tool не более одного раза на эпизод; произвольный spec в tool запрещён, вызывается только sealed spec текущей задачи. Tool access одинаков, action choice свободен кроме B4 deterministic policy.

Repair: максимум **одна попытка на эпизод**, на первый invalid structured output PREP или ACTION; 512 output tokens, input только invalid output + schema/protocol validation errors + требуемая schema. Не передавать state, task заново, feedback, tool answer, evaluator data. Если второго invalid output не исправить либо второй call в эпизоде тоже invalid — `PROTOCOL_FAILURE`. Смысловая догадка evaluator не является ошибкой schema. Repair не увеличивает разрешённую action space и не повторяет task. Его ресурсы отдельно, не скрытый extra compute.

R1-PREP-01: у B1/B2 PREP_SKIPPED допустим только как abnormal nonexecution с reason PROTOCOL_FAILURE / INFRA_FAILURE / EXPLICIT_NONEXECUTION. Это не нормальный capability execution mode. Такой episode остаётся в ITT, не становится architecture savings и не включается в normal operational evidence. execution_context хранит prep_skip_reason и prep_call_count; feedback повторяет reason. EXPLICIT_NONEXECUTION отображается в protocol_status=PROTOCOL_FAILURE с сохранённым отдельным reason. Пропущенный обязательный PREP не открывает нормальный ACTION путь; raw attempted outputs сохраняются, но технически невалидный episode даёт accuracy/completion-ITT=0. Общее прежнее infra-exclusion правило уточнено для этих PREP nonexecutions согласно прямому решению автора; обычный non-PREP infrastructure attrition остаётся отдельным.

PREP_EXECUTED означает один фактически принятый primary PREP call; timeout после принятия остаётся call, не превращается в PREP_SKIPPED или бесплатный retry. Неудачный output маркируется protocol_status/call.response_status, а не нормальным успехом PREP. B3 законный skip имеет reason B3_STOP_CONTROLLER, с доказуемым trigger в stop/restart state. Ни call savings, ни controller latch не доказывают внутренний самостоятельный механизм модели.

## 8. Feedback, стоимость, пропуски

Feedback allowlist определяется r1_episode_record.schema.json#/$defs/feedback: episode_id/index, task_family, scope_id, difficulty_scope, context_condition, tool_condition, capability_configuration_ref, execution_mode, history_class, prep_skip_reason, chosen_action, solo_correct, final_correct, tool_used, cost_units, outcome. После SOLO показывается только boolean correctness, не правильное содержимое. VERIFY предоставляет tool result только в своём tool event; DELEGATE не создаёт solo observation. `solo_correct=null` означает ненаблюдаемость, не ошибку/успех. При ABSTAIN final_correct=null; при protocol failure action может быть null, final_correct=null.

ENGINEERING DEFAULT: task success value не агрегируется в reward. Tool costs VERIFY=1, DELEGATE=1, SOLO=ABSTAIN=0; стоимость запроса и tokens/latency отдельными осями. Денежная стоимость рассчитывается по зафиксированной конфигурации тарифов; неизвестная стоимость = null, не ноль. Repair cost входит в total model cost, reflection_cost содержит PREP плюс PREP repair; TOOL_COST не включает model tokens. ABSTAIN и PROTOCOL_FAILURE ухудшают completion/accuracy-ITT, но не становятся «ошибочным SOLO». Это предотвращает выигрыш за счёт отсутствия ответа.

scope_id — стабильный адрес; смена версии не меняет его, task_family, tool_condition или configuration ref. NARROWED сужает непустые subsets difficulty/context/execution_modes. Ledger и B4 tracker разделены по exact public difficulty/context/tool/configuration/mode/history key (§5), без неявного pooling. Public evidence_index сохраняет все прежние feedback (до32) для всех arms; recent window остаётся10. Counters/anchors — производные существующего журнала, не скрытая память B3. При narrowing фильтруются refs, не переносится прежний общий aggregate.

agent_state.capability_configuration раскрывает определение непрозрачной configuration ref без B/C labels. current_execution_mode=null в PREP input до решения о вызове; в ACTION payload — фактический режим. После commit обновляются profile/history/anchors, mode и отражающая controller факты reflexive_state; старые observations/task не меняются. Полные фактические PREP/ACTION bytes сохраняются в calls; execution_context.private record не заменяет их. Само наличие идентификатора режима не означает, что модель его использовала.

Точные template-инструкции и request assembly — `MRAB_R1_PROMPT_CONTRACTS_0.2.1.md`. Budget timeout ENGINEERING DEFAULT: 120 секунд на model call, 30 секунд на deterministic tool; timeout не создаёт дополнительный retry сверх одного schema repair. Tool timeout — INFRA_FAILURE, model serving timeout при healthy provider — PROTOCOL_FAILURE. Правило outage: documented provider error 5xx/network failure до принятого inference — INFRA_FAILURE; accepted request без ответа к deadline — PROTOCOL_FAILURE, если не подтверждён общий outage. Scope этих причин определяется machine events, не качеством ответа.

## 9. Единая stop/probe event table

Остановка PREP не равна отмене ACTION или запланированной пробы. Latch адресуется public task scope, включая C0; отсутствие numeric claim не создаёт глобальную вечную остановку.

| Порядок / событие | Проверяемое изменение | Журнал |
|---|---|---|
| Начало t | Expiry только если t>expires_episode; новый scope/context/tool trigger снимает latch | EXPIRED и latch reason |
| PREP eligibility B3 | Не более одного PREP; skip только по controller latch/pending feedback; первый scope допускает PREP | calls либо отсутствие call + причина |
| Explicit cancel | cancel_pending_probe=true отменяет прежнюю pending до новой declaration | CANCELLED с прежним probe_id |
| Replacement/declaration | Новый план заменяет старый: сначала CANCELLED, затем DECLARED | Два ordered элемента probe_events, не один overwritten slot |
| Commit | Общая B2/B3 atomic admissibility; effective t до ACTION | update_event, versions, sequence |
| Stop flag | stop_reflection=true устанавливает latch, не удаляет pending | latch_events STOP_DECLARED |
| ACTION | Current probe может исполниться сейчас; NEXT_MATCHED — только на первом последующем scheduled matching task с допустимым ACTION | ACTION/actual tool seal; не новая задача |
| Feedback | Полученное informative evidence разрешает EVIDENCE_RETURNED и restart на следующем t, без PREP после feedback в том же episode | FEEDBACK + PROBE_RETURNED latch reason |
| Nonmatching/no usable response | План остаётся pending до следующего допустимого matching item/expiry; отсутствие evidence не успех | reason и pending |
| End trajectory | Pending не получает бесплатного episode и не считается завершённым | END_PENDING / END_NO_PENDING |

Current означает SOLO_CURRENT или VERIFY_CURRENT; неисполненный current plan закрывается CANCELLED/ACTION_NOT_EXECUTED в конце t, не переносится как NEXT_MATCHED. NEXT_MATCHED reference — последний past informative exact matching item; при его отсутствии этот тип недопустим. Matching дополнительно включает execution comparability key §5. Expiry default=declared_episode+4, без добавления episodes.

Restart: surprise по последней applicable numeric карте (success при midpoint≤.40, failure при ≥.80), два новых informative outcomes после latch для UNKNOWN/QUESTIONED **и C0**, либо возвращение/expiry/cancellation пробы, новая публичная конфигурация. E evaluator не виден. Эти правила — запрограммированный controller; экономия calls не доказывает внутреннюю саморегуляцию модели.

Probe_predictions — prospective annotations. Одинаковые labels допустимы; UNKNOWN не обязан предсказывать отдельный исход. Пример SELF_CAPABILITY→FAILURE и TASK_VARIATION→SUCCESS без обоснования не получает сертификат различимости. p=.60 и p=.90 имеют одинаковые возможные исходы, но разные likelihoods. Технический bookkeeping не оценивает эту научную силу. R1-PROBE-01 закрыл OD-02. Bounded evidence chain — принятая граница; causal-discrimination endpoint не входит в R1 и не является незакрытым условием freeze.

ACTION protocol failure после успешного commit не откатывает commit. Если PREP structurally invalid и не repaired, commit не происходит. Все sequence/versions позволяют восстановить оба случая. Полный lifecycle — §10 и design_checks/lifecycle_vectors.json.

## 10. Self-profile: один lifecycle

Current claim — последняя committed версия слота. Proposed update — отдельное неизменяемое предложение с expected_version, evidence_refs и after_claim. Validated update — результат **проверки допустимости**, не подтверждение эмпирической истины. Active behavioral consequence — последующие реальные actions, не поле-обещание агента. Update может быть допущен и оказаться ложным по evaluator.

Разрешённые переходы:

| From | To |
| --- | --- |
| ACTIVE | QUESTIONED |
| QUESTIONED | ACTIVE, REVISED, NARROWED, UNKNOWN |
| REVISED | QUESTIONED |
| NARROWED | QUESTIONED |
| UNKNOWN | QUESTIONED |

Одна PREP может предложить атомарную двухступенчатую цепочку `ACTIVE/REVISED/NARROWED/UNKNOWN → QUESTIONED → terminal` по одному claim; записываются обе стадии и обе версии. Максимум один claim/эпизод. Нельзя заставлять B2 ждать лишний эпизод только ради промежуточного статуса. QUESTIONED сохраняет числовую оценку, но отмечает её спорность. UNKNOWN имеет interval=null. REVISED изменяет interval в том же scope. NARROWED сужает context/difficulty subset, сохраняя explicit scope parent; вернуть более широкий предыдущий scope можно через QUESTIONED→ACTIVE с `restore_version`, это rollback, не новый глобальный trait. ACTIVE без rollback восстанавливает последнюю неоспоренную committed estimate того же scope. Ни REVISED, ни UNKNOWN не терминальны навсегда.

Commit checks: правильный actor B2/B3; выбран существующий claim; expected_version совпадает; evidence_refs известны из informative log t'<t; не менее одного относящегося к данному scope наблюдения для изменения interval/scope; цепочка статусов законна; scope, включая configuration ref и execution modes, равен/является subset текущего или точно разрешённым restore; interval ordered в [0,1]; evidence_n вычисляется по уникальным refs, не принимается с верой из текста; version монотонна. Состояние после replay должно совпадать побитово по canonical JSON. Для QUESTIONED без изменения числа достаточно одного стандартного feedback о том же scope, включая final outcome; такой feedback не становится solo evidence.

В **этой** службе нет true calibration p, C label, sufficient-evidence threshold, признака «это control». Предложение испортить control claim с валидным local evidence может пройти и должно быть поймано *метрикой*, а не скрытым oracle shield. GLOBAL_PROFILE_REWRITE и смена другого family без evidence отклоняются одинаково для B2/B3 и учитываются как ошибочные attempts. Evidence из DELEGATE не может поддержать изменение *solo* interval.

Если proposal invalid: log REJECTED и причины; профиль не меняется, action может продолжиться. Структурно невалидный PREP подлежит repair; семантически допустимый, но плохо обоснованный пересмотр не подлежит «repair к правильному ответу». До первого evidence профиль нельзя изменить одним красивым текстом.

Уточнения lifecycle: initial singleton difficulty/context scope не имеет непустого строгого subset; в таком pilot scope NARROWED не разрешается притворным переименованием. Положительный NARROWED fixture использует заранее объявленный multi-scope contract с собственными calibration/evidence, не меняя default pilot matrix. Из UNKNOWN переход в QUESTIONED восстанавливает последнюю историческую numeric estimate как явно спорную; если такой версии нет, это LIFECYCLE_VIOLATION. QUESTIONED→ACTIVE без restore возвращает эту последнюю numeric estimate; произвольное новое число требует REVISED. Rejected unknown claim имеет before_claim=null; это не существующий объект профиля.

## 11. B4: strong adaptive policy без богатой self-model

R1-B4-01 — ACCEPTED strong baseline policy. Намеренно сохраняется усиленная версия0.2; это intentional strengthening простого/null baseline относительно ранней B4, не откат к слабой стратегии. b4_policy_version=STRONG_TRACKER_POLICY_0.2. B4 не получает false self-profile, candidate loci, Matryoshka update protocol, B3 probe grammar или B3 stop/restart architecture. Router полностью детерминирован; его configurable параметры замораживаются до первого model run. После просмотра результатов менять их можно только с новой версией experimental protocol.

B4 ведёт отдельные Beta(1+s,1+f) по observable scope; s/f — SOLO или sealed pre-tool VERIFY, один уникальный item даёт один исход. До данных Beta(1,1), без calibration prior/ложного профиля. То же окно actual observations доступно другим через ledger; B4 сохраняет все counts, не только последние 10.

ENGINEERING DEFAULT: action threshold τ=0.80. При posterior mean≥τ — SOLO. Иначе VERIFY, если n<4, либо posterior mass P(p≥τ) в [0.10,0.90], либо это каждый третий opportunity данного scope. Иначе DELEGATE. При недоступном инструменте SOLO, если mean≥τ, иначе ABSTAIN. Порядок этих правил фиксирован. VERIFY одновременно надёжно завершает task и получает pre-tool solo data; DELEGATE не надувает s. B4 может быть дешевле B3, это содержательная проверка избыточности, не дефект fairness.

B4 выводит action из tracker, а model ACTION вызывается только для ответа SOLO/VERIFY, с тем же solver instruction и лимитом B0; никакого отдельного router LLM. Его posterior — ENGINEERING DEFAULT, не Матрёшка и не evaluator posterior, хотя математическая семья общая.

## 12. Траектория, рандомизация, transfer

Pilot: 24 MAIN + 8 TRANSFER =32; 12+12 MAIN и 4+4 TRANSFER по families. Каждая соседняя пара содержит F1 и F2. Начальная family counterbalanced, далее строгое чередование. Фазы: 1–6 INITIAL_EXPOSURE, 7–12 EVIDENCE_ACCUMULATION, 13–24 ADAPTATION, 25–32 TRANSFER. Это evaluator schedule, не инструкция «начни пересмотр» агенту.

Smoke: 8 MAIN +4 TRANSFER =12; families 4+4 и 2+2. Во всех EPISODES сохраняются actions, tools и profile commits; forced successful trajectory не подставляется. Smoke не является научным исследованием.

Матрицы: smoke 4×5×2×12=480 episodes (40 trajectories); pilot 4×5×8×32=5120 (160 trajectories). C4/B5 отсутствуют. B5 только будущий контракт: актуальный calibration map того же scope, без trial answer/seed; true probability всё ещё estimate, а не фактический ceiling=100%. B5 требует отдельного config version и матрицы.

Pilot C0/C1: полное пересечение target_family(2) × first_family(2) × target_stratum(HIGH/MID)(2), по одному на клетку =8. C2/C3: target_family×first_family с двумя независимыми seeds =8; stratum фиксирован условием. Smoke n=2 обеспечивает только маргинальный баланс target/first family; взаимодействие не оценивается. B0–B4 используют matched tasks внутри одного condition×replicate block, одинаковую сложность, order и surfaces; sampling streams различаются по architecture и phase call.

Seed streams отдельно: TASK, TASK_ID, FAMILY_ORDER, SURFACE, PROFILE, MODEL, BOOTSTRAP. Preimage всех streams определён единственно в G01; includes protocol_revision, split, block, item, attempt, counter. TASK_ID — отдельный stream. Никакой второй укороченной формулы manifest в SPEC нет. Публиковать master seed и скрытый manifest только после закрытия model calls. Один master seed воспроизводит manifest; nondeterministic provider calls не обещаются побитово.

Transfer меняет surface template grammar и идентификаторы при прежней latent family/difficulty distribution. Ни item, ни latent instance после нормализации α-переименования и шаблона не повторяются между calibration/search, confirm, main, transfer. Novel task skill/новая context capability не добавляется под видом surface transfer. Остаются тот же профиль и policy; новые transfer templates не служат поводом сбросить trajectory state.

## 13. Нормативные межфайловые инварианты

I01: current_profile slots уникальны по claim_id; current версии совпадают с replay commits.
I02: B0/B1 current_profile byte-stable; B4/C0 не получают profile claims.
I03: C1–C3/B0–B3 начинают с двух claims, scope roles только hidden.
R1-PREP-01 уточнение I03: initial claim.execution_modes — subset normal modes соответствующей public capability_configuration; у B1/B2 это только PREP_EXECUTED. Abnormal skipped episode не расширяет normal claim scope. Generic committer transaction vectors с общим broad scope тестируют admissibility отдельно, а не утверждают, что такой mode-scope разрешён в actual B2 configuration.
I04: все intervals ordered; UNKNOWN↔null interval; другие статусы interval not null.
I05: evidence/episode refs принадлежат одной trajectory, не будущему.
I06: lifecycle только §10; version+1 на каждую стадию; один proposal на episode.
I07: commit validation не читает hidden evaluator fields.
I08: task spec passed to tool равен sealed presented spec.
I09: VERIFY pre-answer timestamp/hash предшествует tool start.
I10: SOLO не имеет tool call; DELEGATE не имеет solo answer; ABSTAIN не имеет обоих.
I11: tool_used, calls, results, cost и outcome согласованы; tool error≠agent error.
I12: schema repair≤1/episode, без evidence/ground truth.
I13: profile update не считается task answer; consequences только actual actions после commit.
I14: agent payload только по closed allowlist; никаких полных private trajectory/episode объектов.
I15: отсечки history/state одинаковы; overflow не даёт молчаливой потери данных.
I16: calibration/search/confirm/main/transfer fingerprint sets не пересекаются.
I17: deterministic tools проверяются независимо от generator, primary evaluator не LLM.
I18: episode index, family order, phase counts и seeds соответствуют sealed manifest.
I19: costs включают PREP, ACTION, repairs и tools, неизвестные значения null.
I20: все rates несут numerator, denominator, excluded_count, missing_reason; 0/0=null.
I21: informative observation unique по latent item и pre-tool seal; delegate не informative.
I22: sufficient evidence считается на t−1, одинаково для всех C/B, без B3-предиката.
I23: сравнение выполняется по trajectory/matched blocks, не независимым episodes.
I24: неустранимая неопределённость не принуждается в PROMISING/REDUNDANT/COUNTERPRODUCTIVE.

## 14. Версии, решения и готовность

R1-REDUNDANCY-01: REDUNDANT_vs_X = EQUIVALENT(B3,X) AND (STRUCTURALLY_MORE_COMPLEX(B3,X) OR MATERIALLY_MORE_EXPENSIVE(B3,X)), X∈{B2,B4}. Оба структурных отношения заранее true; это не complexity score. При resource advantage B3 сохраняются оба findings: REDUNDANT_BY_STRUCTURE + RESOURCE_ADVANTAGE_B3. Слабость другого comparator не отменяет адресную redundancy; unknown usage не отменяет структурное основание при установленной outcome-equivalence. Правила EQUIVALENT, materially costly и guards — EVAL E07.

benchmark_version=0.1 обозначает сохранённую матрицу/семейства; contract/package_version=0.2.1 и protocol_revision=R1_0.1_DESIGN_PATCH_0.2.1 отличают исправленные interfaces/controller/evaluation. Старые hashes и новый протокол не взаимозаменяемы. Схемы имеют URI /r1/0.2.1/. Канонические документы Матрёшки не ревизованы.

Источник решений — MRAB_R1_DECISION_REGISTER_0.2.1.json. R1-CAPABILITY-01 принят автором. OD-02 закрыт R1-PROBE-01. Четыре решения Patch0.2.1 проведены в contracts/config/tests; открытых авторских развилок этого patch нет. Готовность подтверждается только фактической финальной проверкой.

Engineering defaults: history10, one repair, caps1024/1024/512, max input16384, deadlines120/30, expiry4, restart2, strict alternation, surface-only transfer, smoke8+4 плюс длинные design traces вне матрицы. Evaluation policy отдельно: τ=.80, mismatch q>.90/n≥4, accuracy-loss budget C2=.02, C1=.05, equivalence=.05, resource ratio=.20, reach≥.50/difference≤.25, paired n≥6. Это настраиваемые правила опыта, не универсальная мера Уместности. Beta evidence thresholds не подгоняются под B3.

FROZEN требует resolved component hashes/bytes, provider/tokenizer/parser/canonicalizer, prompt/output schema/tool identities, selected four difficulty tuples, compute accounting, author decisions и later calibration/runtime preflight. TEMPLATE с placeholders не runnable. Design verdict выводится из read-only fresh-process checks, а не константы: технические defects → DESIGN_REPAIR_REQUIRED; concept choice → DESIGN_REVIEW_REQUIRED; только отсутствие обоих позволяет IMPLEMENTATION_READY_DESIGN_ONLY. Последнее не означает implemented runtime, запуск 480/5120 или подтверждение H1.
