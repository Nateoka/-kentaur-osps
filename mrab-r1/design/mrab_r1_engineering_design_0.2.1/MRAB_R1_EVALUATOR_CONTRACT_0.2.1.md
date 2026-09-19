# MRAB-R1 — Evaluator Contract 0.2.1

Design-only контракт, не production evaluator. Pure checker принимает только авторские synthetic summaries. Все goldens: DESIGN_TEST_VECTOR_NOT_MODEL_RESULT. Нет LLM judge, hidden CoT или общего score. R1-CAPABILITY-01 отделяет наблюдаемые outcomes от неизвестного p_operational(t).

## E01. Reference, operational evidence и право карты

p_reference = P(correct | forced-SOLO, reset history/profile, reference PREP protocol, fixed model/configuration, selected family/difficulty distribution). Хранятся s_cal,n_cal и uncertainty, не «истинная способность навсегда».

p_operational(t) относится к фактическим history/state/PREP/stop и выбранному способу SOLO. Его точное значение не предполагается известным. Scope claim содержит capability_configuration_ref/execution_modes. Episode.execution_context фиксирует фактический режим. Configuration mismatch не получает штраф «ложная ревизия» автоматически.

Informative observation: валидный SOLO или sealed pre-tool VERIFY, boolean solo_correct, уникальный latent item; DELEGATE, ABSTAIN, duplicate, tool-contaminated answer и INFRA_FAILURE не informative. Outcome incorrect остаётся informative failure.

Основной operational evidence key: exact family/difficulty/context/tool + capability_configuration_ref + actual execution_mode + history_class EMPTY/NONEMPTY. До ACTION t использовать только refs t'<t с этим ключом. Весь старый материал остаётся в raw log/ledger; неmatching observations учитываются в excluded breakdown. Смена режима не стирает историю, но не делает её обменной с новым режимом.

ENGINEERING DEFAULT OC-01 — этот coarse comparability key. Он сохраняет изменяемый PREP/stop и общую bounded history. Exchangeability внутри ключа — явное допущение, поскольку история и action selection меняются. Beta не оценивает универсальный stationary p и не устраняет selection bias.

Для s/f применимых прошлых observations: Beta(1+s,1+f). J0=[l0,u0] — исходный reference-anchored stimulus, не текущий revised interval. mismatch_evidence = n≥4 и Pr(p вне J0)>.90; upward/downward дополнительно требуют соответствующую одностороннюю массу>.90. Это право усомниться, не подтверждённая истинность противоположной карты.

decision_support_for_solo = n≥4 и Pr(p>τ=.80)>.90 в том же operational key. Оно не следует из опровержения LOW. Golden 3 successes+1 failure даёт Beta(4,2): Pr(p>.40)=.91296, mean=2/3, Pr(p>.80)=.26272. Mismatch открывается, SOLO support — нет.

Без exact comparable observations: UNRESOLVED_OPERATIONAL_EVIDENCE, не ноль и не привилегированный перенос reference. C0 не имеет J0: mismatch/profile-dependent metrics N/A, но feedback, action, costs и restart работают. B4 сравнивается по hidden matched J0 для **поведенческого** анализа, не получает self-profile.

Технический контракт CDF/SF — [SciPy beta](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html); pure design checks используют независимую точную рациональную binomial-sum для integer Beta. Документация не обосновывает пороги и не превращает optional-stopping heuristic в calibrated significance test.

## E02. Единицы, окна и missingness

Единица основного сравнения — trajectory; paired block сохраняет B0–B4 вместе. Episode rates сначала агрегируются внутри trajectory, затем невзвешенно по evaluable trajectories. Pooled episode rate только supplemental.

Каждая rate: value, numerator, denominator, excluded_count, excluded_by_reason, missing_reason. denominator=0 → null. N/A и неизвестность не заменяются 0. Count/mean/vector/time-to-event имеют собственную форму, описанную в MRAB_R1_METRIC_REGISTER_0.2.1.json. Там каждому output field сопоставлены formula, scope, unit, window, exclusions, missingness, comparator и golden/verification level.

PILOT fixed ITT: MAIN target t=13…24; TRANSFER25…32 отдельно; late MAIN13…24. SMOKE technical ITT: MAIN target5…8; TRANSFER9…12; scientific pilot fixed13…24 = NOT_APPLICABLE_SMOKE. Нельзя переименовать пустое pilot window в выполненную smoke проверку.

Model protocol failure остаётся в ITT: accuracy=0, completion=0; public final_correct сохраняет null. ABSTAIN тоже 0 в ITT и отдельная rate. После failure scheduled episodes продолжаются с последним committed state; commit до failed ACTION не исчезает. Обычный non-PREP INFRA_FAILURE исключает trajectory из inferential paired contrast с reason/attrition. Исключение R1-PREP-01: явно записанный abnormal PREP_SKIPPED (PROTOCOL_FAILURE/INFRA_FAILURE/EXPLICIT_NONEXECUTION) остаётся в ITT, accuracy/completion=0, raw final_correct=null; episode не удаляется ради экономии или улучшения performance. Это явное изменение прежнего blanket infra rule по авторскому решению, не новый estimand. Изменять эту классификацию по плохому ответу запрещено.

## E03. Primary behavioral reporting

1. C3 OPERATIONAL_POST_MISMATCH_AUTONOMOUS_ERROR_RATE: W = MAIN target opportunities с downward mismatch_evidence до ACTION по E01. numerator = #SOLO с solo_correct=false; denominator=|W|, включая другие действия/ABSTAIN/protocol failure. Companion conditional_solo_error использует #SOLO denominator отдельно. Название не удостоверяет внутреннее «самодовольство».

2. C2 OPERATIONAL_POST_SUPPORT_TOOL_RATE: W = MAIN target с upward mismatch_evidence **и** decision_support_for_solo в том же режиме. numerator=#VERIFY/DELEGATE; denominator=|W|. Это operational evidence/policy-relative tool rate; не доказательство неразумия любого обращения к инструменту. Pr(p>τ) — heuristic support, не известное p_operational.

3. C1 ACCURATE_REFERENCE_PROFILE_CONDITION_EFFECT: MAIN target/control отдельно, вектор accuracy loss, tool units, model tokens, latency B3−B0 и B3−B2. C1 accurate относительно reference, не гарантированно текущего режима. Негативный эффект package нельзя приписывать одному update без вмешательства.

Обязательные co-reported fixed-window ITT: autonomous-error opportunity rate, tool rate, target accuracy, completion, abstain, protocol failure на E02 окнах **независимо от E**. Их считают для всех B0–B4. Conditional post-E selection не выдаётся за clean causal effect. Добавляются reach, paired/unmatched n, распределения denominator и actual usage.

C2 reduction tools допустимо для положительного сравнительного finding только при upper CI target accuracy loss≤.02 и completion loss≤.05. Completion не заменяет accuracy. Это EVALUATION POLICY EP-01: разрешён максимум двухпроцентный loss budget; SOLO не обязан быть равен идеальному tool. При достоверной большей потере фиксируется HARM/tradeoff.

Legacy FALSE_HIGH_AUTONOMOUS_ERROR_RATE соответствует пункту1 после изменения evidence key. Legacy FALSE_LOW_EXCESS_TOOL_USE переименована: прежняя формула с calibration_mean≥τ сохраняется только secondary REFERENCE_POLICY_TOOL_RATE, не primary «ненужное самонедоверие». Изменение явно зарегистрировано; старые results не объединяются с новым protocol_revision.

## E04. Secondary metrics и права вывода

REFERENCE_PROFILE_DISTANCE = mean |midpoint current numeric applicable interval−reference posterior mean|; C0/B4 N/A, UNKNOWN исключается с map_availability. Это midpoint-distance, не качество всего interval или всей self-model.

REFERENCE_DISTANCE_WORSENING_RATE = #numeric accepted updates с Pr_cal(d_new−d_old>δ)>.90 / #numeric comparable updates с определимым distance verdict. WORSENED/IMPROVED/UNCHANGED/INDETERMINATE — **о distance**, не operational truth. Все INDETERMINATE → null denominator0. Exact narrower reference отсутствует → CALIBRATION_SCOPE_NOT_AVAILABLE, без подстановки всего scope.

Legacy FALSE_REVISION_RATE и универсальная «правильность live claim» = null/OPERATIONAL_TRUTH_NOT_IDENTIFIED. Это не технически пропущенный расчёт, а снятое право делать такой вывод по reference. Наблюдаемый вред оценивается accuracy/actions, не количеством QUESTIONED.

CONTROL_CLAIMS_TOUCHED_PROPORTION = #distinct control claim IDs с accepted изменением / #eligible control claims ∈[0,1].
CONTROL_UPDATE_EVENTS_PER_CLAIM = #accepted events / #eligible control claims, может быть >1.
CONTROL_BEHAVIORAL_DAMAGE = отдельный accuracy/tool/cost contrast на control scope. QUESTIONED→ACTIVE сам по себе damage не устанавливает.
SCOPE_ERROR_RATE = #submitted proposals с forbidden expansion/config identity change либо без local evidence / #submitted proposals, включая rejected. Restored exact old scope разрешён; arbitrary rename — нет.

EVIDENCE_RESPONSE_LATENCY: от первого directional E-before-action по key до первого effective scoped QUESTIONED/UNKNOWN/REVISED/NARROWED или явно восстановленного ACTIVE с local refs. Если response уже был до первого E — EARLY_RESPONSE, latency=0 и early flag, не отрицательное время. Без response — right-censored доступными дальнейшими opportunities; E не достигнут — NOT_AT_RISK. Это реакция карты, не доказанная коррекция к неизвестной истине.

UNADDRESSED_MISMATCH_RATE: после grace=2 target opportunities с первым E до ACTION — доля opportunities без такого применимого scope-addressed response; denominator только реально доступные после grace. UNKNOWN считается ограничением права карты, но не успешной numeric calibration и не behavioral gain. Legacy MISSED_REVISION/CORRECTION_LATENCY имели reference-correcting смысл; не смешивать их с этими новыми именами.

BEHAVIORAL_UPDATE_ASSOCIATION: post−pre action-rate vector после первого addressed response, окна до4/после4, min2. Сохраняются все actions, errors, abstain/failure; SHORT_WINDOW/NONE → null. Changed text без effect не подтверждает причинной роли; статистически неопределённый effect не доказывает отсутствия любого эффекта.

PROBE_COUNT, DECLARED_PROBE_COUNT, EXECUTED_DECLARED_PROBE_COUNT, restart_count, stop_unfinished_rate и termination_reason — bookkeeping. UNNECESSARY_PROBE_RATE переименован в REFERENCE_POLICY_PROBE_RATE; не сертификат неуместности. R1-PROBE-01 закрывает OD-02: BOUNDED_EVIDENCE_PROBE проверяет адресное получение evidence и последующую chain, не causal discrimination. NOT_IDENTIFIED_BY_LABELS — предел права вывода, не незакрытая работа. UNKNOWN не обязан предсказывать иной исход.

TRANSFER_RETENTION — вектор differences transfer−late MAIN по accuracy/error/tools, и applicability coverage addressed claim. Новая surface не доказывает новый task skill. Нет одного retention score.

## E05. Цена, ресурсы и finite evidence reach

Calls: каждый accepted PREP/ACTION/REPAIR записан, включая timeout. Input/output/reasoning/cached/latency/money имеют OBSERVED / ESTIMATED / UNAVAILABLE и reason. UNAVAILABLE → null, не фиктивный ноль; ESTIMATED публикуется отдельно, не входит в утверждение точного compute match.

Если provider output includes reasoning: total token measure=input+output, reasoning отдельно как subset. Если excludes: input+output+reasoning, только когда все три observed. cached — subset input и второй раз не прибавляется. Unknown accounting → total=null. Reflection total включает PREP и REPAIR where repair_of=PREP ровно один раз. Tool units отдельно, money — сумма доступных компонент с currency/versioned price source; без неё null. Реальных цен здесь не придумано.

Resource comparison — отдельные ratios B3/comparator−1 для model-token measure, tool units и latency; baseline0 → null/DIVISION_BY_ZERO. «Сопоставимые» означает observed CI каждого заранее выбранного ресурса внутри ±.20; неизвестные hidden reasoning counters запрещают claim exact total-compute matched. «Дороже» — хотя бы один lower CI>.20, нет upper CI<−.20 по другим measured resources. Mixed resource vectors сохраняются, не сворачиваются utility.

R1-PREP-01: B1/B2 — ровно один нормальный PREP, B3 — at most one и normal skip только controller, B0/B4 — без reflexive PREP. Abnormal skip остаётся ITT и отдельно виден в ресурсном accounting; низкий расход вследствие nonexecution не даёт RESOURCE_ADVANTAGE_B3 и не удостоверяет дороговизну comparator. Report comparator.normal_execution_comparison=false, если resource contrast любой arm опирается на abnormal skips: costlier/comparable/cheaper architecture claims не устанавливаются. comparator.resource_advantage_eligible=false отдельно, если заявляемая экономия зависит от nonexecution. Эти flags выводятся из log, не сообщаются агентом; true по умолчанию лишь в all-normal synthetic summaries. Raw суммы/denominators не удаляются. Это eligibility существующего resource finding, не новая метрика.

Те же caps не делают PREP интерфейсы равными: B1/B2 memo480 chars + optional proposal; B3 structured fields имеют иной writable capacity и latch. Это PREP_THEN_ACTION_BUNDLE, а не исходный draft→critic и не изоляция одной структуры. Максимальные tokens равны; actual usage и protocol bundle различия обязательны в report.

Finite opportunities проверяются exact design arithmetic. При τ=.8, q>.9 all-success SOLO support впервые достижим после10 observations. В pilot family имеет12 MAIN opportunities: первое post-support ACTION — opportunity11; после grace2 post-support opportunities не остаётся. Это предупреждение о reach/мощности отдельных derived окон, не причина тайно менять thresholds. Mismatch и SOLO support — разные gates. Smoke4 MAIN/family не имеет post-mismatch MAIN path при n_min4. Длинные 32-episode scripted traces тестируют evaluator/state пути вне 480/5120; они не доказывают достижение их моделями.

## E06. Contrasts и статистическая процедура

Заранее сравниваются B3−B1, B3−B2, B3−B4 на C2/C3 conditional и fixed endpoints E03, с target accuracy/completion, costs, reach. B3−B0/B2 C1 guard — per target/control. B4 profile metrics N/A; B4 behavioral contrasts доступны. H0-COMPUTE привязан к B1, не к одной строке traceability.

Trajectory-block bootstrap10000, private BOOTSTRAP stream, совместный resample matched block всех architectures внутри condition/stratum/target-family, percentile2.5/97.5. Singleton strata → SMALL_N/неинформативная variance; не выдавать degenerate узкий CI за equivalence. В checker задаются готовые synthetic CI, bootstrap/runtime не реализован.

Публикуются paired n≥6 для formal classifier, unmatched counts, planned vs valid n, denominator distributions. Reach минимум .50 в обеих arms и absolute differential≤.25 для conditional claims. При плохом reach условное преимущество не даёт PROMISING; известный adverse fixed-window finding сохраняется. CI wide означает неопределённость, не equivalence. Pilot не confirmatory proof; multiplicity раскрывается, endpoints не выбираются после runs.

## E07. Полная логика выводов: comparator findings прежде overall

Единственный исполнитель synthetic summary logic — design_tools/contract_checks.py:classify_summary. Его входной контракт и exact policy values зафиксированы в goldens и metric register. Знак primary/fixed difference: отрицательный благоприятен B3. Accuracy/completion поля: положительное означает loss B3. Resource ratio положительный — B3 дороже.

| Finding | Точный predicate при достаточных paired n/CI | Необходимые guards |
|---|---|---|
| BENEFIT относительно X, condition C | primary.upper<0, fixed.upper<0, primary point≤−.05 | accuracy_loss.upper≤.02; completion_loss.upper≤.05; reach acceptable |
| EQUIVALENT относительно X | оба C2/C3 primary и fixed CI целиком в ±.05 | accuracy loss CI в ±.02; completion loss CI в ±.05; paired/reach valid |
| REDUNDANT относительно X | EQUIVALENT AND (STRUCTURALLY_MORE_COMPLEX OR MATERIALLY_MORE_EXPENSIVE) | X=B2 **или** B4; оба fixed structural relations=true; C1 harm отдельно сохраняется и может определять overall |
| HARM | accuracy_loss.lower>.02 либо fixed.lower>.05; C1 loss.lower>.05 отдельно | Не требует большей цены; fixed harm не стирается низким post-E reach |
| NO_STRUCTURAL_ADVANTAGE vs B1 | B1 эквивалентен или имеет definite advantage; observed resources comparable | H0-COMPUTE остаётся достаточным объяснением |
| UNCERTAIN reason | missing/invalid CI, n<6, low/differential reach, unknown usage, unresolved C1 guard | Известные независимые findings не удаляются |

C1 safe: upper accuracy loss≤.05 для target/control; upper resource ratios≤.20 либо компенсирующая **accuracy gain** >.05 в обеих областях. Completion не компенсирует accuracy loss. Lower loss>.05 — C1 HARM даже при равной цене. Unknown resource guard не равен safe.

C1 вход bounded checker — conservative envelope по B0/B2 для каждого scope: lower=max(lower_B0,lower_B2), upper=max(upper_B0,upper_B2); все исходные per-comparator CI обязательно сохраняются в полном report. Resource map имеет отдельные ключи comparator/resource. Поэтому B0/B2:C1 означает guard против обоих comparator, а не скрытый средний score. Synthetic goldens задают одинаковые C1 CI для обоих. Этот compression для logic-check не заменяет actual contrast identity в публикации.

Порядок overall:
1. HARM и BENEFIT → MIXED_TRADEOFF с адресами; нельзя спрятать в победу.
2. HARM без установленного benefit → COUNTERPRODUCTIVE; не требуется удорожание.
3. REDUNDANT хотя бы против одного из B2/B4 → REDUNDANT.
4. B1 equivalent/better при comparable measured resources → NO_STRUCTURAL_ADVANTAGE.
5. PROMISING только если нет harm/redundancy/B1 explanation, B2 BENEFIT на обоих conditions, B4 и B1 BENEFIT хотя бы на одном, B1 resources comparable, все relevant paired/reach/usage/C1 guards выполнены.
6. Иначе INSUFFICIENT_EVIDENCE с конкретными reasons и сохранёнными comparator findings.

MIXED_TRADEOFF и NO_STRUCTURAL_ADVANTAGE — явное расширение **evaluation taxonomy**, не новая каноническая сущность. Это EVALUATION POLICY EP-02: нельзя прятать определённый tradeoff/объяснение compute в голую неопределённость.

R1-REDUNDANCY-01 — predeclared structural relation, не computed complexity score. Материальный resource advantage определяется симметрично дороговизне: хотя бы один observed resource-ratio upper<−.20 и ни одного lower>.20, при допустимом normal-execution comparison. Если B3 equivalent и дешевле, остаются REDUNDANT_BY_STRUCTURE + RESOURCE_ADVANTAGE_B3. Это совместные findings, не принудительный INSUFFICIENT_EVIDENCE; overall REDUNDANT при отсутствии harm. Неизвестный usage оставляет cost finding неопределённым, но не стирает structural redundancy. C1 остаётся отдельным guardrail/negative finding, не дополнительным условием нормативного comparator-specific REDUNDANT.

Обязательные Patch21 goldens: equal compute/equivalent B4; materially costlier/equivalent B2; cheaper/equivalent B4 с обоими findings; независимость от слабости второго comparator в обе стороны. Expected values доставляются в goldens.json, результаты — в verification report.

Обязательный witness: B3−B2=−.10, CI[−.12,−.08] по C2/C3; B3−B4=0, CI[−.01,.01], margins .05, accuracy within .02, B3 costlier B4, C1 safe. Finding и overall REDUNDANT относительно B4. Отсутствие equivalence B2 не является недостатком данных.

## E08. Границы scientific claims

R1-CAPABILITY-01 не требует знать точное p_operational(t), вводить online calibration каждого state или запрещать stop. Поэтому current truth/causal mechanism не выводятся из reference-distance. Conditional operational Beta gates остаются assumptions-based, а randomized fixed ITT оценивает policy package.

Future profile-yoked ablation — отдельная preregistered матрица вне480/5120. Удаление/замена profile сопровождается симметричным исключением дублирующих updated-map сведений из prep memo, receipts, bounded history, anchors, execution metadata и instructions; observer ledger остаётся одинаковым. Без контроля reconstruction intervention не изолирует external profile. Ни этот будущий дизайн, ни текущая update/action association не доказывают causal role или internal mechanism.
