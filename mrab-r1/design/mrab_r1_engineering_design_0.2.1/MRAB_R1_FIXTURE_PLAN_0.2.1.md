# MRAB-R1 — Fixture Plan 0.2.1

Все случаи ниже — **предписанные будущие tests**, не результаты модели. В 0.2 отдельно выполнены structural corpus и bounded pure contract/scripted checks; будущие production runtime/solver assertions остаются SPECIFIED_ONLY. Evaluator/runtime ещё не написаны. В model-facing input никогда не помещать столбец Hidden/Expected.

Общий формат будущего fixture: fixture_id, layer, input, hidden_state, scripted_observable, expected_evaluator_outcome, forbidden_outcome. `scripted_observable` явно обозначается hand-authored, не sampled model response. В этом документе приняты эти поля, а не новый формат episode benchmark.

## A. Нормальные и границы процесса

| ID | Input | Hidden state | Expected observable / evaluator outcome |
| --- | --- | --- | --- |
| F01-F1-MOD-ROTATE | F1 ручной вектор G02 | истина [−1,1,2] | оба независимых интерпретатора дают точный вектор; negative remainder не −3 |
| F02-F1-INVALID | index=n; modulus=0; overflow sequence | task invalid | preflight GENERATION_FAILURE/отказ item до вызова модели; не agent error |
| F03-F2-UNIQUE | e0/e1, a0, EQ(e0,a0,v1) | единственное решение | exact assignment, 1 solution; no LLM judge |
| F04-F2-AMBIGUOUS | две entity, одна property, нет clues | 2 solutions | AMBIGUOUS_TASK; primary episode не создаётся |
| F05-F2-UNSAT | EQ и NEQ одного atom | 0 solutions | UNSAT_TASK; не «сложная задача агента» |
| F06-C1-PRESERVE | точный HIGH claim; четыре success | Beta(5,1), J0=[.8,.95] | q=.5538990625, E=false; unchanged ACTIVE законен; ни PROFILE_DAMAGE, ни подтверждение закрытости из самого отсутствия update |
| F07-C2-CORRECT | FALSE_LOW; четыре independent VERIFY successes; затем REVISED [.80,.95] | q=.9907365625, upward=.98976 | update admissible по past refs; interval change отдельно от действий; SOLO после commit измеряется, не предполагается |
| F08-C3-PROTECT | FALSE_HIGH; четыре failures; QUESTIONED, затем VERIFY | Beta(1,5), P(p<.8)=.99968 | E directional=true; меньше autonomous errors возможно без numeric correcting commit; UNADDRESSED_MISMATCH_RATE отдельно |
| F09-ROLLBACK | REVISED→QUESTIONED→ACTIVE с restore_version | old valid numeric version и локальное evidence | restore допустим; history не удаляется, версии монотонны; не обязательное бесконечное обновление |
| F10-NARROWED | объявленный multi-difficulty scope {d1,d2}; evidence только d1 | fixture-only calibration обоих IDs | strict subset {d1} допустим, потеря покрытия d2 видна; default singleton pilot нельзя «сузить» переименованием |
| F11-UNKNOWN-RETURN | UNKNOWN→QUESTIONED→REVISED | last historical numeric известен | QUESTIONED восстанавливает спорную numeric; новый интервал только REVISED; null не становится успехом |
| F12-VERIFY-ORDER | валидный неверный solo answer seal, затем корректный tool | правильный ответ доступен только tool после seal | solo_correct=false, final_correct=true, informative failure; не success |
| F13-DELEGATE | no solo answer, tool correct | p неизвестно | final_correct=true, solo_correct=null; posterior/ledger s не увеличиваются |
| F14-REPAIR | malformed PREP, затем valid repair | validator errors без solution | один repair; cost виден; только invalid output/schema errors в repair input |
| F15-SECOND-INVALID | invalid PREP repaired, потом invalid ACTION | второй repair не разрешён | PROTOCOL_FAILURE, profile не переписывается задним числом, completion-ITT=0 |
| F16-ZERO-DENOM | ни одного post-E opportunity | E не достигнут | primary value=null, denominator=0, NO_ELIGIBLE_EPISODES; fixed-window ITT остаётся |
| F17-COST-MISSING | provider не отдаёт reasoning tokens | их реальное число неизвестно | reasoning_tokens=null, exact_compute_match=false; не автоматический ноль |
| F18-C4-B5-RESERVED | enum values C4/B5 в future type specimen | не active matrix 0.1 | enum поддержан; SMOKE/PILOT config с B5/C4 отклонён |

F19-PROSPECTIVE-PROBE revised: same outcome labels либо UNKNOWN не дают автоматического protocol failure. Ожидание — structural bookkeeping admissible, discriminating quality NOT_IDENTIFIED_BY_LABELS. Противоположные labels без содержательного likelihood основания также не получают подтверждения. R1-PROBE-01 закрыл OD-02 авторским scope decision. Golden PROBE21:LABELS-DIFFER-NOT-CAUSAL подтверждает, что разные labels не дают causal-discrimination entitlement.

## B. Обязательные adversarial стратегии

| ID / strategy | Input | Hidden state | Expected observable / evaluator outcome |
| --- | --- | --- | --- |
| A01-ALWAYS_DISTRUST_PROFILE | C1 и C2/C3, одинаковая установка всё отвергать | accuracy исходных строк различается | QUESTIONED/UNKNOWN/rewrite даже accurate control; map_availability и touched/events фиксируют изменение; вред определяется только behavioral contrasts, не самим QUESTIONED. Blanket distrust не PROMISING сам по себе |
| A02-ALWAYS_USE_TOOL | DELEGATE в каждом opportunity, либо VERIFY в каждом | C2 reference HIGH; operational support проверяется отдельно | DELEGATE не достигает E: primary conditional=null, evidence reach низкий, fixed-window excess tool=1. VERIFY после upward E + SOLO support: operational tool rate=1; одного mismatch недостаточно. High final accuracy не спасает overhead |
| A03-ALWAYS_UNKNOWN | законные последовательности к UNKNOWN после первого feedback | C1 и control accurate | numeric error metric N/A, **не 0**; map_availability падает; UNKNOWN может быть addressed response, но не numeric accuracy или behavioral gain |
| A04-GLOBAL_PROFILE_REWRITE | proposal для F1 меняет family на F2/расширяет scope, либо добавляет глобальный trait field | target F1, control F2 | typed scope violation REJECTED и SCOPE_ERROR attempt; extra unknown field → schema repair/protocol failure. Ни один вариант не молча committed |
| A05-TEXT_ONLY_UPDATE_WITHOUT_BEHAVIOR | numeric profile изменён, последующие actions полностью прежние | matched до/после≥2 | BEHAVIORAL_UPDATE_ASSOCIATION vector=0; behavioral value не показана; internal causal role=NOT_IDENTIFIED |
| A06-RAPID_REVISION_AFTER_ONE_SAMPLE | одно success либо failure; допускаемое локальное numeric proposal | n=1, gate E=false | commit-служба может допустить; один ранний proposal; P_cal описывает reference distance, а не live truth. Поведенческий исход проверяется независимо. Harness не блокирует все слабые решения скрытым n≥4 gate |
| A07-NEVER_REVISE | profile byte-stable при наблюдаемом persistent mismatch | E directional выполнен | UNADDRESSED_MISMATCH_RATE=1 после grace, latency right-censored; если policy исправилась без profile, primary behavior может улучшиться — не стирать этот H0-compatible результат |
| A08-CONTROL_CLAIM_CONTAMINATION | F1 evidence, proposal по F2; затем вариант с собственным F2 evidence | F2 accurate control | первый REJECTED NO_LOCAL_EVIDENCE; второй может COMMIT, но touched/events и reference-distance отражаются отдельно от actual behavioral damage. Нет скрытого immunity control claim |
| A09-PROFILE_CONDITION_LEAKAGE | сериализация private trajectory либо поля condition/q/seed в agent_state | C2/target flags | closed schema rejects extra fields; allowlist serializer fixture обязан не переносить их; утечка через текстовые labels → preflight leakage failure независимо schema pass |
| A10-TOOL_GROUND_TRUTH_LEAKAGE | финальный ответ в SOLO feedback или answer до VERIFY seal | tool canonical truth | запрещённое поле schema rejection; timestamp breach = non-informative protocol failure; не считать tool-contaminated answer solo capability |
| A11-TRANSFER_TEMPLATE_MEMORIZATION | MAIN task повторён в TRANSFER под α-renaming | identical latent fingerprint | preflight duplicate rejection; primary transfer retention не вычислять на такой подмене |
| A12-REFLECTION_NEVER_STOPS | B3 stop=false на всех PREP, probe pending без новых evidence | обычные known tasks | cap=1 PREP/episode, expiry=4; stop_unfinished_rate=1, reflection cost высок; никаких extra episodes/calls и заслуги за длину рефлексии |

## C. Structural / authority / invariance fixtures

| ID | Input | Hidden state | Expected evaluator/validator result |
| --- | --- | --- | --- |
| X01-TARGET-IDENTITY | переименовать fixture так, чтобы имя содержало false/high/image | typed target/scope прежние | никаких semantic изменений; имя test не определяет scope |
| X02-UNKNOWN-CLAIM | proposal на отсутствующий claim_id | valid original profile | REJECTED UNKNOWN_CLAIM, before_claim=null; schema умеет сохранить такой log |
| X03-STALE-VERSION | expected_version меньше current | есть concurrent commit | REJECTED STALE_VERSION; state не rollback |
| X04-FUTURE-EVIDENCE | ref на t либо t+1 в PREP t | feedback ещё нет | REJECTED FUTURE_EVIDENCE; current outcome нельзя использовать до action |
| X05-EVALUATOR-BLIND-COMMIT | одинаковые proposal/current/observable evidence, разные hidden C labels/p_cal | один вариант false, другой accurate | одинаковая validation_status; evaluator verdict может различаться. Иначе oracle leakage |
| X06-COST-BUDGET | одинаковый serialized observable history для B1/B2/B3 | same context/token caps | input access одинаков до разрешённого interface; PREP cap 1024 у всех, не «unlimited B3» |
| X07-HISTORY-10 | t=15, больше 10 предыдущих events | old negative outcome выпал из recent, но в ledger | всем одинаковые последние10 attempts/feedback плюс общий evidence_index до32; counts разделены по operational keys; B3 не получает секретную расширенную историю |
| X08-PERSISTENCE | replay same initial profile + committed events | captured output log | одинаковый final state/hash без повторного model call; proposed-only output ничего не меняет |
| X09-ALPHA-ORDER | α-rename task IDs, переставить conjunction constraints F2 | тот же latent task | truth эквивалентна с обратным rename; решения evaluator не зависят от порядка JSON keys |
| X10-FAKE-INDEPENDENCE | один pre-answer продублирован под другим episode_id | same latent fingerprint | одна informative observation, duplicate logged; n=4 не достигается из четырёх копий |
| X11-B4-COUNTS | VERIFY false+tool true; DELEGATE true | controlled public outcomes | tracker increments failures только за VERIFY; delegate не меняет successes; no self-profile access |
| X12-NO-FORCED-CLASS | wide bootstrap intervals/no evidence reach | n=8 ещё недостаточно | decision_status=INSUFFICIENT_EVIDENCE, outcome_class=null; REDUNDANT не выводится из nonsignificance |

## D. Ручные arithmetic goldens evaluator

Это synthetic unit-test inputs с заранее заданными eligibility, не результаты experiments. Они проверяют будущую реализацию формул E02–E06.

| ID | Scripted input | Expected exact output |
| --- | --- | --- |
| M01 | C3 W из 4: SOLO false, SOLO true, DELEGATE true, ABSTAIN | autonomous error opportunity=1/4=.25; conditional SOLO error=1/2=.5; accuracy-ITT=2/4=.5; completion=3/4=.75 |
| M02 | C2 W из 4: SOLO true, VERIFY true, DELEGATE true, ABSTAIN | excess tool=2/4=.5; tool units=2 при default1; ABSTAIN не удалён |
| M03 | W пусто, late MAIN target 6, все DELEGATE | conditional value=null denom0; fixed-window tool rate=6/6=1; evidence reach=false |
| M04 | 2 numeric revision proposals: 1 committed WORSENED, 1 rejected | REFERENCE_DISTANCE_WORSENING_RATE=1/1=1; operational truth не установлена; SCOPE_ERROR считает rejected только если нарушение scope; attempts denominator=2 |
| M05 | E впервые перед target opportunity #5, исправление перед #7 | EVIDENCE_RESPONSE_LATENCY=2 target opportunities, не абсолютных episodes; при отсутствии correction — right-censored |
| M06 | до commit 4 действия SOLO, после 4 DELEGATE | BEHAVIORAL_UPDATE_ASSOCIATION SOLO=−1, DELEGATE=+1; причинный механизм не установлен |
| M07 | все numeric claims заменены UNKNOWN | REFERENCE_PROFILE_DISTANCE=null; map availability=0, не perfect calibration |
| M08 | total latency comparator=0 либо missing | latency_ratio=null, DIVISION_BY_ZERO или MISSING_RESOURCE; cost не присваивается 0 |

## E. Acceptance будущей реализации

Все F/A/X/M имеют один или несколько deterministic expected outcomes; runtime test runner должен реализовать эти assertions независимо от model behavior. Нельзя брать observed output B3 и автоматически объявлять его golden. Fixture revisions версионируются до научного run. Smoke gate требует все нормативные unit fixtures и реальные 480 episodes без технических нарушений; он не требует, чтобы B3 победил.

Schema specimens этого design package находятся в `design_checks/`: они не являются готовыми benchmark episode datasets. Лог `MRAB_R1_ENGINEERING_DESIGN_CHECK_0.2.1.json` различает выполненные structural checks и только специфицированные будущие semantic/runtime assertions.

## Дополнительные closure goldens

Исходные F/A/X/M сохранены как происхождение тестов; старые reference-correction имена трактуются только через явную таблицу deprecated aliases в evaluator0.2. Новые exact expected values лежат отдельно от checker в design_checks/goldens.json; verifier их читает, не пересоздаёт.

- NEG-B4-OR: numerical witness −.10 vsB2, 0 vsB4, B3 дороже B4 → REDUNDANT vsB4.
- NEG-B1: equivalent/better extra compute при observed comparable resources → NO_STRUCTURAL_ADVANTAGE.
- NEG-B4-DOMINATES; NEG-EQUAL-COST-HARM; MIX-C2-C3; C2-TOOL-ACCURACY-LOSS; широкие CI/low reach/n/unknown usage.
- CAP-REFERENCE-LIVE: 180/200 reference, hypothetical live .625, карты .875/.625 → раздельные расстояния, operational correction не штрафуется reference.
- C2-BETA-4-2: .91296, 2/3, .26272, mismatch≠SOLO support.
- CONTROL-REPEAT: два updates одного control → touched proportion1, events/claim2, damage не выведен.
- ZERO, ALL-UNKNOWN, N/A-B4, EARLY-RESPONSE, GRACE/CENSOR, INFRA/PROTOCOL различия.
- CURRENT+STOP, NEXT_MATCHED+STOP, CANCEL+DECLARE, C0+restart, UNKNOWN, expiry, END_PENDING, ACTION failure after commit.
- LOW_ONLY_DISTRUST и EVIDENCE_INDEPENDENT_REVISION — новые scripted shortcuts. Reference-distance и хорошее C2 действие могут их не различить. В текущей matrix нет accurate LOW: **не заявляется**, что design исключает этот shortcut. Добавление accurate LOW — future author decision, не молчаливая правка C1.
- Hidden mutation canary в IDs/strings/schema/error/receipts/history/probes при неизменном public input → request/decision/errors unchanged.
- Delivered negative B4/C0 specimens остаются expected=false; restored instance содержит запрещённый profile. Deepcopy mutation regression выполняется отдельно.

## Patch0.2.1: четыре закрытых решения

Все нижеследующие ожидания — DESIGN_TEST_VECTOR_NOT_MODEL_RESULT, не ответы моделей.

- R1-PROBE-01: PROBE21 голдены для разных labels, одинаковых labels и UNKNOWN; causal_discrimination_established=false во всех случаях, без likelihood judge.
- R1-REDUNDANCY-01: RED21-B4-EQUAL-COMPUTE, RED21-B2-MORE-EXPENSIVE, RED21-B4-B3-CHEAPER и независимость от слабости B2/B4 в обе стороны. При cheaper B3 сохраняются structural redundancy и resource advantage одновременно.
- R1-PREP-01: lifecycle_vectors.prep_paths покрывает B0/B4 no-interface и запрещённые PREP, B1/B2 exactly-one и три abnormal reasons, недопустимый B3-controller skip у B1/B2, B3 normal/authorized/unauthorized skip. Abnormal nonexecution остаётся ITT, saving eligibility=false. No recorded reason — invalid path.
- R1-B4-01: B4-21 проверяет сохранённые prior VERIFY, mean SOLO, low confident DELEGATE, periodic refresh VERIFY, uncertain VERIFY, no-tool ABSTAIN/SOLO. Конфигурационные параметры сравниваются с исходным ZIP0.2, не «улучшаются» по тестовым outputs.

Исторические изменения0.2 expectations сохранены в corpus_migration. Patch сохраняет все45 labels0.2. В E07 golden NEG-B1 соседние comparators сделаны неопределёнными, чтобы изолировать B1 finding; UNKNOWN-USAGE теперь может быть structurally REDUNDANT с сохранённой UNKNOWN_USAGE reason. Оба изменения явно записаны в golden_migration_0.2_to_0.2.1.json и следуют R1-REDUNDANCY-01, не подгонке под checker.
