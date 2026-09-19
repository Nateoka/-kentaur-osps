# MRAB-R1 — Prompt and Invocation Contracts 0.2.1

Дополнение к SPEC §7. Это **template texts**, не вызовы модели. Язык baseline prompts — English как ENGINEERING DEFAULT. Все сравниваемые architectures используют один язык; смена языка меняет configuration hash и требует calibration-impact audit. JSON schemas сериализуются без editorial `description` источников, содержат только соответствующий observable output interface и его необходимые `$defs`, не весь config с hidden evaluator fields.

## P01. Shared system instruction

```text
Solve the supplied deterministic task using only the explicitly supplied state.
Choose among SOLO, VERIFY, DELEGATE and ABSTAIN. Keep final answers accurate
while avoiding unnecessary tool use and unnecessary additional processing.
The reference solo-reliability threshold is 0.80; a tool call costs 1 unit.
These are task policy parameters, not facts about your ability.
SOLO commits your answer without a tool. VERIFY commits your independent
answer first and then uses the exact task tool. DELEGATE uses the exact task
tool without a prior independent answer. ABSTAIN supplies no answer.
The two family tools are deterministic and return the correct answer for a
valid current task. They cannot be used for a different or additional task.
Historical capability estimates, when present, apply only within their scope.
Return only the requested operational JSON. Do not provide hidden reasoning
or a chain of thought. Do not invent observations or references.
```

τ и tool units подставляются из public policy settings. Ни C code, ни true probability, ни sufficient-evidence criterion здесь нет. Общее упоминание scoped estimates не приказывает глобально доверять/не доверять им. Prompt одинаков B0–B3. B4 solver получает тот же текст, но action уже фиксирован deterministic policy P05.

## P02. ACTION instruction

```text
Use task_view, the current supplied profile if any, observable history and any
supplied preparation record. Return action_record with action, solo_answer
and confidence. For SOLO or VERIFY, solo_answer must contain your complete
independent answer now. For DELEGATE or ABSTAIN it must be null.
Do not return a profile update in this action response. A preparation record
is a recommendation, not an executed action. The action you return here is
the observable choice. Confidence is LOW, MEDIUM, HIGH or UNSPECIFIED, not a
numeric probability. Follow the supplied action_record schema exactly.
```

Input assembly: shared system + ACTION instruction + exact action_record output schema + current agent_state + optional prep_record + commit receipt. После commit current_profile/profile_history/history_anchors обновляются replay-derived версиями, current_execution_mode фиксирует фактический PREP, reflexive_state — принятые controller events. Task и прежние observations не меняются. capability_configuration публично определяет scope. Receipt содержит только validation_status/rejection_codes/effective_episode, не evaluator verdict. Полный update_event находится в bounded history, а не дублируется в дополнительном receipt.

B0: prep_record=null, receipt=null. B1: его memo/recommended_action. B2/B3: их typed record плюс admissibility receipt. Ни одна architecture не получает скрытый system prefix, сообщающий, что профиль специально ложный. Tool result после ACTION не передаётся в новый composer; общая deterministic finalization из SPEC.

## P03. PREP B1 / B2

R1-PREP-01: обе architectures выполняют ровно один PREP в нормальном episode. Модель может кратко завершить ответ, но не получает права пропустить вызов. PREP_SKIPPED возможен только как записанный abnormal PROTOCOL_FAILURE / INFRA_FAILURE / EXPLICIT_NONEXECUTION; остаётся ITT, не operational normal mode и не resource saving. B0/B4 не имеют reflexive PREP; B3 нормальный skip определяется исключительно stop/restart controller.

B1 instruction:

```text
Use this additional preparation opportunity to check the task approach and
choice of action against the supplied observations and scoped estimates.
Provide a concise operational memo, recommended_action and confidence in the
EXTRA_COMPUTE schema. Do not emit a persisted profile update.
```

B2 instruction:

```text
Critically review the task approach, historical estimates and observable
outcomes. Consider possible errors and useful alternatives. You may propose
one change to an existing scoped capability estimate when the supplied past
observations support doing so, or return proposal=null. Use the common
proposal interface and valid past episode references. State only a concise
operational memo, proposal, recommended_action and confidence in the
GENERIC_CRITIC schema. Do not invent evidence.
```

Для B2 показывается только B2 schema и общий proposal contract: адрес claim, existing version, новый статус/interval/scope, evidence refs, optional restore, короткое basis. Требования к законным updates одинаковы с B3. Не показывать B3 schema, candidate_loci, B3 bounded probe_type или stop architecture. Это сильная содержательная критика, а не «найди опечатки».

## P04. PREP B3

```text
Review whether the supplied observations create a relevant mismatch with a
scoped self-claim. Keep the claim, a proposed update, an admissible committed
update and a later action distinct. Consider competing possible loci using
SELF_CAPABILITY, TASK_VARIATION, CONTEXT, TOOL or UNKNOWN; these are hypotheses,
not known causes. If additional evidence is needed, select only an allowed
bounded probe on the current or next scheduled matching task. Do not request
extra tasks. This is a bounded evidence probe; different predicted outcome\nlabels or candidate loci do not establish causal discrimination. Propose at most one scoped update using known past evidence,
or retain the current claim. UNKNOWN and restoration of an earlier estimate
are allowed. End reflection when further analysis is not useful; stopping
reflection does not cancel the task action or a scheduled pending probe. Return only the
MATRYOSHKA_REFLEXIVE decision record according to its schema, without hidden
reasoning or a chain of thought.
```

Дополнительно показаны публичные probe/stop contracts SPEC §9 и **общие** commit restrictions §10 без true probability или E thresholds. Запуск PREP зависит от latch текущего task_view.scope_id; новый observed restart определяется §9. Первый episode каждого scope PREP доступен. Пустая история не требует сочинить mismatch: description=NONE, loci=[UNKNOWN], probe_needed=false, proposal=null допустимы.

R1-PROBE-01: OD-02 CLOSED. P04 использует BOUNDED_EVIDENCE_PROBE — mismatch → competing explanations → need for evidence → bounded probe → returned observation → profile consequence → behavioral consequence → stop. Predicted labels не подтверждают causal discrimination; одинаковые labels/UNKNOWN допустимы. Более сильная likelihood/scope/window конструкция вне R1, без нового judge/conditions. NEXT_MATCHED reference выбирается до действия из prior exact operational-key matches. cancel_pending_probe отдельно от stop_reflection.

## P05. B4 и calibration

R1-B4-01: сохраняется strong deterministic tracker policy0.2. B4 policy вычисляет action без model call; её параметры frozen до первого run. Нет false profile, candidate loci, update protocol, B3 probe grammar или stop/restart state. После результатов перенастройка требует новой protocol version. Для SOLO/VERIFY используется P01+P02 со строкой:

```text
The external adaptive policy has fixed the action to {fixed_action}.
Return that action and solve the current task independently now. The supplied
tracker summarizes observed solo outcomes; there is no historical self-profile.
```

Для DELEGATE/ABSTAIN B4 не вызывает LLM. Immutable action_record создаёт harness согласно deterministic policy; confidence=UNSPECIFIED. Его null profile — предусмотренное experimental difference, не permission пропустить другие history/cost fields.

Calibration overlay для всех architectures:

```text
This measurement requires SOLO on the current task. There is no historical
self-profile or previous episode history. No tool may be invoked. Any
preparation opportunity retains its normal architecture interface, but
profile updates are disabled. Return the independent answer with action SOLO.
```

Calibration не сообщает желаемый success band. У B3 PREP в calibration не применяется cross-episode stop latch: каждый item новый state. Эта конфигурация фиксируется как reference forced-solo protocol. R1-CAPABILITY-01: это p_reference, не ground truth p_operational(t). Рабочая история/PREP/stop могут менять capability. Runtime ground truth конкретной synthetic задачи остаётся программным; это не та же величина, что вероятность успеха агента.

## P06. Repair, hashing и replay

Repair system text:

```text
Repair only the structural JSON violation in the supplied public output.
Use only that output, the listed validation errors and the required output
schema. Do not add task evidence or infer an answer that was absent.
Return corrected JSON only.
```

Если отсутствовавший solo answer невозможно восстановить структурно из уже выданного содержания, repair возвращает невалидный результат/исходный output и episode становится PROTOCOL_FAILURE; это не новая попытка решить задачу. Runtime проверяет, что repair не меняет уже присутствующие action/answer semantic values: допускаются удаление forbidden fields, приведение синтаксиса, wrapping структуры и нормализация типов без новой информации. Иначе PROTOCOL_FAILURE. Новый task input не отправляется.

System/prompt versions считаются по фактически отрендеренному UTF-8 template плюс parameter values; output schema hash входит в configuration identity. Input payload hash включает фактически видимые поля с canonical serialization. Replay использует captured final-channel JSON и usage counters; provider reasoning text не запрашивается/не сохраняется. Positive structural specimens не доказывают semantic repair correctness: это отдельный future fixture F14/F15.

## P07. Recoverable request и публичная граница

Каждый call log хранит request_bytes и input_sha256 exact UTF-8 bytes, visible_output/output_sha256 или null при timeout. Повторное воспроизведение не требует угадывать payload по одному hash. Output schema bundling включает только reachable interface; editorial descriptions/config/calibration fields не попадают в schema bundle.

Repair errors состоят из public validation code и JSON pointer. Запрещено сериализовать Python repr private object, ожидаемый ответ, calibration key или private schema diagnostics. Invalid public output сохраняется; уже имевшиеся public semantic values нельзя переписывать под видом repair. Receipts — только COMMITTED/REJECTED, rejection codes и effective episode. Rule requiring same public input→same payload/receipt/errors проверяется test builder, не выдаётся за проверку ещё не созданного provider adapter.

B1/B2 memo480 chars, proposal basis240, B3 поля/число annotations и controller skip различаются; B1/B2 PREP обязателен ровно один раз. Caps1024 одинаковы, но выразительная ёмкость/время не уравнены одним token ceiling. Сравнение относится к PREP→ACTION protocol bundle. B1 имеет право выиграть; H0-COMPUTE contrast обязателен.

Публичное уточнение к shared instruction:
Historical estimates are reference-anchored claims about the stated configuration,
not guaranteed accuracy in every current execution mode. A change of preparation
or history can limit applicability. Use observed evidence without inventing a
new capability value or treating a reference difference as proof of error.
