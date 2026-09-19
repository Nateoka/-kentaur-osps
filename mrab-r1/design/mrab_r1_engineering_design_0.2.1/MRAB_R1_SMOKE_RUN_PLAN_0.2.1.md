# MRAB-R1 — Smoke Run Plan 0.2.1

Это инструкция будущему исполнителю, **не запуск**. Smoke проверяет engineering, не H1.

## Матрица

| Mode | Conditions | Architectures | Trajectories/cell | MAIN | TRANSFER | Trajectories total | Episodes total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SMOKE | C0,C1,C2,C3 (4) | B0–B4 (5) | 2 | 8 | 4 | 40 | 4×5×2×12 = 480 |
| PILOT | C0,C1,C2,C3 (4) | B0–B4 (5) | 8 | 24 | 8 | 160 | 4×5×8×32 = 5120 |

Дополнительные calibration calls, schema-repair calls и paired future causal forks **не episodes этой матрицы**. Repair/PREP входят в expense ledger, а не тайно в новое n. В smoke семьи чередуются F1/F2: 6 каждой; в pilot 16 каждой. B4 C0–C3 не получает profile; C — hidden label matched distribution. B5/C4 исключены.

Smoke replicate1: target=F1, first=F1, C0/C1 target_stratum=HIGH; replicate2 target=F2, first=F2, stratum=MID. Для C2 оба HIGH, C3 оба MID. Это лишь маргинальный баланс; target/first confounded при n=2, поэтому научный interaction не оценивается. Pilot реализует полный counterbalance SPEC §12, без этого smoke-ограничения.

## Preflight перед первым model call

1. Все 13 deliverables присутствуют; design status IMPLEMENTATION_READY_DESIGN_ONLY, all blocking author decisions closed и hash inventory сохранён.
2. Config TEMPLATE заменён FROZEN: model/provider revision, prompts, tool declarations, tokenizer и sampling фиксированы. В примерном config нет выбранной реальной модели и нет её результатов.
3. Исходные source hashes сверены; архитектуру не подменяет README другого проекта/Bridge validator.
4. Task generator/interpreter/solver реализованы отдельно и прошли F01–F05, X09. Hand-solved и independent solver tests, не self-certification одного кода.
5. Calibration SEARCH/CONFIRM проведены, common-difficulty gate выполнен у B0–B4. MAIN/TRANSFER tasks не использованы для настройки. Если нет — STOP CALIBRATION_NOT_FEASIBLE.
6. Seed manifest deterministic; split/α-fingerprint disjointness; no hidden strings в labels/surface. Stated default windows/control family/claim-row order точно совпадают manifest.
7. Exact closed agent-state projection проверена X05–X07/A09/A10; private store отделён от model request construction. Inference endpoint не получает полный trajectory JSON.
8. Права B0/B1 readonly, B2/B3 общий committer без evaluator truth, B4 только tracker. No mutable shared state между trajectories.
9. Episode transaction/seal sequence/one repair limit/expiry протестированы. Все callers умеют обрабатывать null/N/A и снимать права на tool после превышения бюджета.
10. Evaluator реализован без LLM judge, M01–M08 прошли exact goldens; E gate uses t−1, C1 симметричен. Budget record includes actual input/output/reasoning availability, not just configured caps.

## Исполнение будущего smoke

Freeze 40 trajectory manifests до первого call. Запускать в randomized cell order, а не сначала весь B3. При provider nondeterminism повторное воспроизведение означает replay captured outputs/state/metrics, не обещание одинакового нового ответа модели. No retraining, prompt edits или manual rescue mid-run. Infrastructure pause учитывает версию/время; поправленный runtime начинает новый run_id.

После каждого episode: schema validation records, profile event integrity, tool ordering, expected task fingerprint, usage log. Сам task может быть решён неправильно: это не technical smoke failure. Попытка плохого update может быть законной behavior: не заставлять её пройти в пользу B3.

## Технический PASS / FAIL

PASS требует: ровно 40 завершённых trajectories, 480 planned episode records; 240 F1 +240 F2; 320 MAIN +160 TRANSFER; все task ground truths валидны; ни одной утечки; ни одного скрытого state mutation; verified count/cost/ordering/replay; все F/A/X/M unit fixtures прошли.

Строгий ENGINEERING DEFAULT smoke gate: ноль unrepaired PROTOCOL_FAILURE и INFRA_FAILURE. Отдельно показать first-invalid и repair counts. Если реальная модель не выдерживает interface, это технический FAIL smoke, не разрешение заменить её outputs вручную. Изменить protocol/caps можно только новой frozen config с повторным calibration-impact audit и новым smoke. Плохая scientific performance, отсутствие revisions или преимущество B4 **не являются техническим FAIL**.

Replay acceptance: тот же captured input/output sequence → идентичные canonical profile state, feedback, evaluator numeric outputs и units (реальное wall-clock время не переигрывается). Hash invariance проверяется, model calls не повторяются. Strict budget ceilings подтверждены; skipped PREP не создаёт бесплатный скрытый шаг.

## Переход к pilot

Только после technical PASS, без оптимизации по тому, кто победил в smoke. Pilot 160 trajectories/5120 episodes имеет собственные fresh MAIN/TRANSFER seeds/fingerprints. Calibration допускается та же frozen reference distribution лишь при неизменной конфигурации; новые experimental items обязательны. Отдельный inference-ready flag означает готовность runtime, не подтверждение H1. Null primary endpoints допустимы научно, но обязаны сопровождаться reach/ITT, иначе reporting FAIL.

## Что этот проход реально проверяет

В 0.2 выполняются design/schema/cross-file checks, pure logic/arithmetic goldens, scripted lifecycle traces и test payload builder checks. Это не model/benchmark runtime. Ни480, ни5120 episodes, ни calibration не запускались. В design check поля model_calls/calibration_runs/smoke_runs/pilot_runs равны0, production_runtime_created=false; result_kind=DESIGN_TEST_VECTOR_NOT_MODEL_RESULT.

## Smoke applicability и дополнительное техническое покрытие

Сохраняем 40×12=480, split8 MAIN+4 TRANSFER. F1/F2 имеют по4 MAIN opportunities. n_min4 использует **прошлые** observations: первая post-E ACTION могла бы быть пятой opportunity, уже TRANSFER. Следовательно, primary MAIN post-E coverage smoke структурно0; pilot fixed13…24 также N/A.

Это не исправляется словом PASS counts. Technical smoke fixed window — t5…8 MAIN отдельно от scientific pilot13…24. Вне model matrix обязательны длинные **scripted 32-episode design traces**: earliest mismatch/post-E, response after grace, минимум2 pre/post commit opportunities, all-UNKNOWN, режим PREP change, pending probe и failure after commit. TRANSFER не включается в MAIN denominator. Их metadata: DESIGN_TEST_VECTOR_NOT_MODEL_RESULT, model_calls=0.

Для C2 SOLO support при прежних τ/q all-success требует10 observations; MAIN opportunity11 впервые eligible, остаётся максимум2 post-support opportunities. Grace2 делает соответствующий post-support-after-grace denominator0. Это честный feasibility warning, не обещание ненулевого окна. Длинные traces проверяют также другое earlier mismatch окно; readiness report различает WHICH_PATH_EXECUTED.

Бюджеты отдельно:
- smoke maximum calls768 без repair /1248 с cap1 repair/episode;
- pilot8192 /13312;
- confirm measurements4000 / calls6400, без search/repairs;
- search = search_n × Σ accepted candidate evaluations по architecture/family/band; calls зависят от PREP weights1,2,2,2,1;
- confirm maximum repairs4000; monetary costs только из future pinned price source и observed/estimated usage.

480/5120 — episodes, не calls, не independent sample count и не calibration. Ceiling — не actual spend или power proof. Ни один model run в этом пакете не выполнен.

## Patch0.2.1 — PREP и strong baseline gate

R1-PREP-01: normal B1/B2 имеют ровно один PREP, B3 — максимум один с controller-authorized normal skip, B0/B4 — no reflexive PREP. Normal ceilings768/8192 calls не меняются; B1/B2 lower normal PREP count теперь совпадает с количеством их episodes. Abnormal nonexecution с reason остаётся ITT и technical failure, а не дешёвым нормальным режимом; такой failure не удаляют из отчёта ради smoke PASS. Суммы расходов сохраняют actual/missing usage, но экономию из nonexecution не относят к архитектуре.

R1-B4-01 сохраняет strengthened policy0.2 без B3 grammar/state. Перед первым model call заморожены policy parameters; менять их после результатов без новой protocol version нельзя.

Normal no-repair call bounds после обязательного PREP B1/B2: smoke576…768, pilot6144…8192. Нижняя граница допускает только законный controller skip B3 и все B4 actions без model solver; это не прогноз поведения. Nonexecution/сбои в неё не входят как источник экономии. Подтверждающая reference calibration сохраняет4000 measurements/6400 normal calls; реальные вызовы в patch отсутствуют.

R1-PROBE-01 закрывает OD-02: требуется bounded evidence chain, не causal-discrimination endpoint. R1-REDUNDANCY-01 разрешает comparator-specific structural redundancy при equal compute и при resource advantage B3.

Этот patch не запускает описанный здесь smoke. Фактические проверки дизайна и их count — во внешнем MRAB_R1_FINAL_VERIFICATION_0.2.1.json рядом с ZIP, не в захардкоженном числе этого плана.
