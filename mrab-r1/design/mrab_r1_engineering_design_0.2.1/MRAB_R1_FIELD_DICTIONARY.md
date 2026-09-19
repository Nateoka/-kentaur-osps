# MRAB-R1 — точный словарь полей

Сгенерирован из пяти schemas; schema JSON Pointer — единственный адрес определения. `$ref` переиспользует определение, а не создаёт иной смысл. Межобъектные ограничения I01–I24 заданы в SPEC. Полные private records запрещены в agent payload.

| Schema | JSON Pointer | Значение |
| --- | --- | --- |
| r1_config | `#/$defs/action_record/properties/action` | Выбранный реальный action. |
| r1_config | `#/$defs/action_record/properties/confidence` | Категориальный self-report, не probability. |
| r1_config | `#/$defs/action_record/properties/solo_answer` | Обязателен для SOLO/VERIFY; null для DELEGATE/ABSTAIN. |
| r1_config | `#/$defs/answer/oneOf/0/properties/family` | Тип ответа. |
| r1_config | `#/$defs/answer/oneOf/0/properties/result` | Конечный вектор длины n. |
| r1_config | `#/$defs/answer/oneOf/1/properties/family` | Тип ответа. |
| r1_config | `#/$defs/answer/oneOf/1/properties/result` | Полное решение grid; exact bijection и полнота по G03. |
| r1_config | `#/$defs/answer/oneOf/1/properties/result/items/properties/assignments` | Все properties, sorted by property_id. |
| r1_config | `#/$defs/answer/oneOf/1/properties/result/items/properties/assignments/items/properties/property_id` | Property ID. |
| r1_config | `#/$defs/answer/oneOf/1/properties/result/items/properties/assignments/items/properties/value_id` | Выбранное значение. |
| r1_config | `#/$defs/answer/oneOf/1/properties/result/items/properties/entity_id` | Entity ID строки. |
| r1_config | `#/$defs/atom/properties/entity` | Entity ID из spec.entities. |
| r1_config | `#/$defs/atom/properties/property` | Property ID из spec.properties. |
| r1_config | `#/$defs/atom/properties/value` | Value ID именно указанного property. |
| r1_config | `#/$defs/calibration_cell/properties/architecture` | Калибруемая configuration architecture. |
| r1_config | `#/$defs/calibration_cell/properties/band` | Hidden admitted stratum. |
| r1_config | `#/$defs/calibration_cell/properties/calibration_key` | Private key architecture/family/difficulty/context scope. |
| r1_config | `#/$defs/calibration_cell/properties/dataset_hash` | Hash independent confirmation manifest. |
| r1_config | `#/$defs/calibration_cell/properties/n` | Число holdout items, successes≤n. |
| r1_config | `#/$defs/calibration_cell/properties/scope` | Scope измерения. |
| r1_config | `#/$defs/calibration_cell/properties/successes` | Empirical holdout solo successes. |
| r1_config | `#/$defs/capability_configuration/properties/architecture_policy_id` | Versioned public actor policy interface; no hidden treatment label. |
| r1_config | `#/$defs/capability_configuration/properties/configuration_id` | Opaque public configuration identity, never a condition code. |
| r1_config | `#/$defs/capability_configuration/properties/execution_modes` | Declared permitted execution modes; narrowing is set inclusion. |
| r1_config | `#/$defs/capability_configuration/properties/history_policy` | Same history access; content is recorded per episode, not assumed constant. |
| r1_config | `#/$defs/capability_configuration/properties/prep_policy` | R1-PREP-01: B1/B2 exactly one; B3 controller only normal skip; B0/B4 none. |
| r1_config | `#/$defs/constraint/oneOf/0/properties/atom` | Проверяемый atom. |
| r1_config | `#/$defs/constraint/oneOf/0/properties/kind` | Тип логического constraint. |
| r1_config | `#/$defs/constraint/oneOf/1/properties/atom` | Проверяемый atom. |
| r1_config | `#/$defs/constraint/oneOf/1/properties/kind` | Тип логического constraint. |
| r1_config | `#/$defs/constraint/oneOf/2/properties/kind` | Тип логического constraint. |
| r1_config | `#/$defs/constraint/oneOf/2/properties/left` | Левый atom. |
| r1_config | `#/$defs/constraint/oneOf/2/properties/right` | Правый atom. |
| r1_config | `#/$defs/constraint/oneOf/3/properties/kind` | Тип логического constraint. |
| r1_config | `#/$defs/constraint/oneOf/3/properties/left` | Левый atom. |
| r1_config | `#/$defs/constraint/oneOf/3/properties/right` | Правый atom. |
| r1_config | `#/$defs/evidence_index_entry/properties/episode_id` | Past observable episode ref. |
| r1_config | `#/$defs/evidence_index_entry/properties/feedback` | No correct answer or private metadata. |
| r1_config | `#/$defs/execution_context/properties/capability_configuration_ref` | Addressed configuration from the current claim/policy. |
| r1_config | `#/$defs/execution_context/properties/execution_mode` | Actual PREP occurrence, not its ceiling. |
| r1_config | `#/$defs/execution_context/properties/history_class` | Coarse comparability class; equal class does not establish stationary capability. |
| r1_config | `#/$defs/execution_context/properties/history_policy_id` | Pinned common observability policy. |
| r1_config | `#/$defs/execution_context/properties/prep_call_count` | Accepted primary PREP calls; repair attempts remain separately logged. Skipped=0, executed=1. |
| r1_config | `#/$defs/execution_context/properties/prep_record_sha256` | Actual prep record hash or null when absent. |
| r1_config | `#/$defs/execution_context/properties/prep_skip_reason` | Required non-null for PREP_SKIPPED; null for PREP_EXECUTED/NO_PREP_INTERFACE. Abnormal nonexecution remains ITT, not architecture savings. |
| r1_config | `#/$defs/execution_context/properties/public_state_sha256` | Exact ACTION-visible state hash before answer; no hidden fields. |
| r1_config | `#/$defs/grid_spec/properties/constraints` | Конъюнкция ограничений; уникальность решения проверяет solver. |
| r1_config | `#/$defs/grid_spec/properties/entities` | Уникальные entity IDs. |
| r1_config | `#/$defs/grid_spec/properties/family` | Discriminator DSL. |
| r1_config | `#/$defs/grid_spec/properties/properties` | Properties с уникальными IDs. |
| r1_config | `#/$defs/grid_spec/properties/properties/items/properties/property_id` | Уникальный property ID. |
| r1_config | `#/$defs/grid_spec/properties/properties/items/properties/values` | Values; число равно числу entities по G03. |
| r1_config | `#/$defs/history_anchor/properties/claim` | Exact old public snapshot; not evaluator interpretation. |
| r1_config | `#/$defs/history_anchor/properties/claim_id` | Existing slot. |
| r1_config | `#/$defs/history_anchor/properties/reason` | Why this bounded anchor is present. |
| r1_config | `#/$defs/history_anchor/properties/version` | Historical committed claim version. |
| r1_config | `#/$defs/interval/properties/lower` | Нижняя граница probability claim, не confidence interval. |
| r1_config | `#/$defs/interval/properties/upper` | Верхняя граница; I04 дополнительно требует lower≤upper. |
| r1_config | `#/$defs/latch_event/properties/latched` | New latch state. |
| r1_config | `#/$defs/latch_event/properties/reason` | Observable controller trigger, not evaluator E or proof of internal self-regulation. |
| r1_config | `#/$defs/latch_event/properties/scope_id` | Use public task scope also in C0; never a numeric fake claim. |
| r1_config | `#/$defs/latch_event/properties/sequence` | Shared event sequence. |
| r1_config | `#/$defs/operation/oneOf/0/properties/index` | Изменяемая координата, zero-based. |
| r1_config | `#/$defs/operation/oneOf/0/properties/op` | Операция F1. |
| r1_config | `#/$defs/operation/oneOf/0/properties/value` | Ненулевое слагаемое. |
| r1_config | `#/$defs/operation/oneOf/1/properties/index` | Изменяемая координата. |
| r1_config | `#/$defs/operation/oneOf/1/properties/op` | Операция F1. |
| r1_config | `#/$defs/operation/oneOf/1/properties/value` | Множитель, исключены 0 и 1. |
| r1_config | `#/$defs/operation/oneOf/2/properties/left` | Первая координата. |
| r1_config | `#/$defs/operation/oneOf/2/properties/op` | Операция F1. |
| r1_config | `#/$defs/operation/oneOf/2/properties/right` | Вторая координата; distinct от left по G02. |
| r1_config | `#/$defs/operation/oneOf/3/properties/op` | Операция F1. |
| r1_config | `#/$defs/operation/oneOf/3/properties/steps` | Right shift; абсолютное значение меньше n по G02. |
| r1_config | `#/$defs/operation/oneOf/4/properties/index` | Изменяемая координата. |
| r1_config | `#/$defs/operation/oneOf/4/properties/modulus` | Положительный modulus, результат Euclidean remainder. |
| r1_config | `#/$defs/operation/oneOf/4/properties/op` | Операция F1. |
| r1_config | `#/$defs/probe_prediction/properties/if_not_observed` | Судьба гипотезы при несовпадении, не автоматический profile commit. |
| r1_config | `#/$defs/probe_prediction/properties/locus` | Одна из заранее заявленных альтернатив. |
| r1_config | `#/$defs/probe_prediction/properties/observable_pattern` | Предсказанное публичное различие; это не hidden mechanism. |
| r1_config | `#/$defs/runtime_identity/properties/canonicalizer` | Pinned canonicalizer implementation/content. |
| r1_config | `#/$defs/runtime_identity/properties/canonicalizer/properties/identity` | Versioned component identity; TEMPLATE may use CONFIGURE. |
| r1_config | `#/$defs/runtime_identity/properties/canonicalizer/properties/sha256` | Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution. |
| r1_config | `#/$defs/runtime_identity/properties/grid_tool` | Pinned grid_tool implementation/content. |
| r1_config | `#/$defs/runtime_identity/properties/grid_tool/properties/identity` | Versioned component identity; TEMPLATE may use CONFIGURE. |
| r1_config | `#/$defs/runtime_identity/properties/grid_tool/properties/sha256` | Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution. |
| r1_config | `#/$defs/runtime_identity/properties/output_schema_bundle` | Pinned output_schema_bundle implementation/content. |
| r1_config | `#/$defs/runtime_identity/properties/output_schema_bundle/properties/identity` | Versioned component identity; TEMPLATE may use CONFIGURE. |
| r1_config | `#/$defs/runtime_identity/properties/output_schema_bundle/properties/sha256` | Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution. |
| r1_config | `#/$defs/runtime_identity/properties/parser` | Pinned parser implementation/content. |
| r1_config | `#/$defs/runtime_identity/properties/parser/properties/identity` | Versioned component identity; TEMPLATE may use CONFIGURE. |
| r1_config | `#/$defs/runtime_identity/properties/parser/properties/sha256` | Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution. |
| r1_config | `#/$defs/runtime_identity/properties/prompt_bundle` | Pinned prompt_bundle implementation/content. |
| r1_config | `#/$defs/runtime_identity/properties/prompt_bundle/properties/identity` | Versioned component identity; TEMPLATE may use CONFIGURE. |
| r1_config | `#/$defs/runtime_identity/properties/prompt_bundle/properties/sha256` | Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution. |
| r1_config | `#/$defs/runtime_identity/properties/provider_adapter` | Pinned provider_adapter implementation/content. |
| r1_config | `#/$defs/runtime_identity/properties/provider_adapter/properties/identity` | Versioned component identity; TEMPLATE may use CONFIGURE. |
| r1_config | `#/$defs/runtime_identity/properties/provider_adapter/properties/sha256` | Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution. |
| r1_config | `#/$defs/runtime_identity/properties/symbolic_tool` | Pinned symbolic_tool implementation/content. |
| r1_config | `#/$defs/runtime_identity/properties/symbolic_tool/properties/identity` | Versioned component identity; TEMPLATE may use CONFIGURE. |
| r1_config | `#/$defs/runtime_identity/properties/symbolic_tool/properties/sha256` | Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution. |
| r1_config | `#/$defs/runtime_identity/properties/tokenizer` | Pinned tokenizer implementation/content. |
| r1_config | `#/$defs/runtime_identity/properties/tokenizer/properties/identity` | Versioned component identity; TEMPLATE may use CONFIGURE. |
| r1_config | `#/$defs/runtime_identity/properties/tokenizer/properties/sha256` | Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution. |
| r1_config | `#/$defs/scope/properties/capability_configuration_ref` | Addressed policy configuration; not a universal capability statement. |
| r1_config | `#/$defs/scope/properties/context_condition` | Непустое множество применимых public context IDs. |
| r1_config | `#/$defs/scope/properties/difficulty_scope` | Допустимые difficulty IDs из sealed configuration. |
| r1_config | `#/$defs/scope/properties/execution_modes` | Nonempty permitted modes; operation NARROWED may only remove modes. |
| r1_config | `#/$defs/scope/properties/scope_id` | Непрозрачный идентификатор области; не HIGH/MID label. |
| r1_config | `#/$defs/scope/properties/task_family` | Семейство capability, не evaluator target role. |
| r1_config | `#/$defs/scope/properties/tool_condition` | Capability относится к самостоятельному решению без инструмента. |
| r1_config | `#/$defs/symbolic_spec/properties/family` | Discriminator DSL. |
| r1_config | `#/$defs/symbolic_spec/properties/initial` | Начальный вектор. |
| r1_config | `#/$defs/symbolic_spec/properties/operations` | Упорядоченная программа. |
| r1_config | `#/$defs/task_view/properties/context_condition` | Видимое условие контекста. |
| r1_config | `#/$defs/task_view/properties/difficulty_scope` | ID текущего difficulty tuple. |
| r1_config | `#/$defs/task_view/properties/scope_id` | Видимый scope ID для локального claim. |
| r1_config | `#/$defs/task_view/properties/spec` | Полный DSL, без ground truth. |
| r1_config | `#/$defs/task_view/properties/surface_text` | Answer-free deterministic rendering текущего DSL. |
| r1_config | `#/$defs/task_view/properties/task_family` | Видимое family. |
| r1_config | `#/$defs/task_view/properties/task_id` | Opaque ID, без split/condition/band. |
| r1_config | `#/$defs/tracker_state/properties/alpha` | 1+successes; numeric equality по I21. |
| r1_config | `#/$defs/tracker_state/properties/beta` | 1+failures; numeric equality по I21. |
| r1_config | `#/$defs/tracker_state/properties/capability_configuration_ref` | Public operational partition: capability_configuration_ref. Counts are never pooled silently across keys. |
| r1_config | `#/$defs/tracker_state/properties/context_condition` | Exact public partition field; no family-only pooling. |
| r1_config | `#/$defs/tracker_state/properties/difficulty_scope` | Exact public partition field; no family-only pooling. |
| r1_config | `#/$defs/tracker_state/properties/execution_mode` | Public operational partition: execution_mode. Counts are never pooled silently across keys. |
| r1_config | `#/$defs/tracker_state/properties/failures` | Число unique informative failure. |
| r1_config | `#/$defs/tracker_state/properties/history_class` | Public operational partition: history_class. Counts are never pooled silently across keys. |
| r1_config | `#/$defs/tracker_state/properties/opportunities` | Все opportunities scope, включая DELEGATE. |
| r1_config | `#/$defs/tracker_state/properties/scope_id` | Observable tracked scope. |
| r1_config | `#/$defs/tracker_state/properties/successes` | Число уникальных informative success. |
| r1_config | `#/$defs/tracker_state/properties/tool_condition` | Exact public partition field; no family-only pooling. |
| r1_config | `#/properties/analysis_windows` | Анализ не подбирается после observed result. |
| r1_config | `#/properties/analysis_windows/properties/interval_mass` | ENGINEERING DEFAULT .95 bootstrap/calibration uncertainty interval. |
| r1_config | `#/properties/analysis_windows/properties/min_each_side` | ENGINEERING DEFAULT 2, не больше заданных окон. |
| r1_config | `#/properties/analysis_windows/properties/min_paired_trajectories` | ENGINEERING DEFAULT 6 для primary classification. |
| r1_config | `#/properties/analysis_windows/properties/post_update_opportunities` | ENGINEERING DEFAULT 4. |
| r1_config | `#/properties/analysis_windows/properties/pre_update_opportunities` | ENGINEERING DEFAULT 4. |
| r1_config | `#/properties/architectures` | Фиксированная ordered матрица. |
| r1_config | `#/properties/b4_policy_version` | R1-B4-01 intentionally retains strengthened0.2 simple baseline; freeze parameters before run. |
| r1_config | `#/properties/benchmark_version` | Matrix/family R1 0.1 identity, distinct from contract 0.2.1. |
| r1_config | `#/properties/budgets` | Budget fairness settings. |
| r1_config | `#/properties/budgets/properties/action_output_tokens` | ENGINEERING DEFAULT 1024. |
| r1_config | `#/properties/budgets/properties/max_input_tokens` | ENGINEERING DEFAULT 16384, overflow fails config. |
| r1_config | `#/properties/budgets/properties/max_prep_calls` | Нет неограниченного reflexive loop. |
| r1_config | `#/properties/budgets/properties/max_repairs_per_episode` | Общий лимит на episode, не по каждому call. |
| r1_config | `#/properties/budgets/properties/max_tools_per_episode` | Нельзя покупать дополнительные evidence items. |
| r1_config | `#/properties/budgets/properties/prep_output_tokens` | ENGINEERING DEFAULT 1024 for B1/B2/B3. |
| r1_config | `#/properties/budgets/properties/repair_output_tokens` | ENGINEERING DEFAULT 512. |
| r1_config | `#/properties/calibration_bands` | Configurable target bands; common difficulty gate обязателен. |
| r1_config | `#/properties/calibration_bands/properties/HIGH` | ENGINEERING DEFAULT [.80,.95]. |
| r1_config | `#/properties/calibration_bands/properties/MID` | ENGINEERING DEFAULT [.55,.70]. |
| r1_config | `#/properties/calibration_plan` | Calibration preflight plan. |
| r1_config | `#/properties/calibration_plan/properties/confirm_n` | ENGINEERING DEFAULT 200 independent holdout. |
| r1_config | `#/properties/calibration_plan/properties/difficulty_contract_version` | Versioned canonicalization contract. |
| r1_config | `#/properties/calibration_plan/properties/max_interval_width` | ENGINEERING DEFAULT 0.16 at 95%. |
| r1_config | `#/properties/calibration_plan/properties/search_n` | ENGINEERING DEFAULT 40 per candidate. |
| r1_config | `#/properties/capability_configurations` | Configurations addressed by claims, R1-CAPABILITY-01. |
| r1_config | `#/properties/capability_configurations/properties/B0` | Public configuration for B0 |
| r1_config | `#/properties/capability_configurations/properties/B1` | Public configuration for B1 |
| r1_config | `#/properties/capability_configurations/properties/B2` | Public configuration for B2 |
| r1_config | `#/properties/capability_configurations/properties/B3` | Public configuration for B3 |
| r1_config | `#/properties/capability_configurations/properties/B4` | Public configuration for B4 |
| r1_config | `#/properties/compute_settings` | Compute settings included in freeze. |
| r1_config | `#/properties/compute_settings/properties/prep_interface` | Explicit baseline variant, not draft-then-critic equivalence. |
| r1_config | `#/properties/compute_settings/properties/reasoning_budget` | Configured limit when observable; null is not zero. |
| r1_config | `#/properties/compute_settings/properties/reasoning_mode` | Provider setting or explicit UNAVAILABLE. |
| r1_config | `#/properties/compute_settings/properties/usage_accounting` | Avoid double counting provider token categories. |
| r1_config | `#/properties/configuration_status` | TEMPLATE не допускает model execution. |
| r1_config | `#/properties/contract_version` | Data contract/package revision; benchmark matrix identity stays 0.1. |
| r1_config | `#/properties/cost_currency` | Одна валюта resource ledger; default UNSPECIFIED требует monetary_cost=null. |
| r1_config | `#/properties/design_decisions` | Author-scoped decisions. |
| r1_config | `#/properties/design_decisions/properties/capability_estimand` | R1-CAPABILITY-01 accepted author decision; p_reference is not ground truth of p_operational(t). |
| r1_config | `#/properties/design_decisions/properties/probe_claim` | R1-PROBE-01 accepted: OD-02 closed; labels cannot establish causal discrimination. |
| r1_config | `#/properties/evaluation_policy` | Predeclared evaluation policy. |
| r1_config | `#/properties/evaluation_policy/properties/c1_accuracy_loss_margin` | Default 0.05 per scope. |
| r1_config | `#/properties/evaluation_policy/properties/equivalence_margin` | Default 0.05 absolute rate difference; CI must fit entirely. |
| r1_config | `#/properties/evaluation_policy/properties/maximum_reach_difference` | Default 0.25; differences remain reported. |
| r1_config | `#/properties/evaluation_policy/properties/minimum_gain` | Default 0.05 primary point advantage. |
| r1_config | `#/properties/evaluation_policy/properties/minimum_reach` | Default 0.50; conditional comparison eligibility only. |
| r1_config | `#/properties/evaluation_policy/properties/resource_ratio_margin` | Default 0.20 each measured resource; no scalar utility. |
| r1_config | `#/properties/evaluation_policy/properties/target_accuracy_loss_margin` | Default 0.02 absolute loss in C2/C3; evaluation policy, not universal Uместность. |
| r1_config | `#/properties/evaluator` | Evaluator-only settings. |
| r1_config | `#/properties/evaluator/properties/behavioral_margin` | ENGINEERING DEFAULT δ=0.05. |
| r1_config | `#/properties/evaluator/properties/bootstrap_draws` | ENGINEERING DEFAULT 10000 trajectory-block samples. |
| r1_config | `#/properties/evaluator/properties/grace_target_opportunities` | ENGINEERING DEFAULT 2. |
| r1_config | `#/properties/evaluator/properties/min_informative` | ENGINEERING DEFAULT 4, hidden от агента. |
| r1_config | `#/properties/evaluator/properties/prior_alpha` | ENGINEERING DEFAULT 1. |
| r1_config | `#/properties/evaluator/properties/prior_beta` | ENGINEERING DEFAULT 1. |
| r1_config | `#/properties/evaluator/properties/resource_margin` | ENGINEERING DEFAULT 0.20 относительного роста. |
| r1_config | `#/properties/evaluator/properties/wrong_band_probability` | ENGINEERING DEFAULT 0.90 strict greater-than. |
| r1_config | `#/properties/generator_options` | Generator design settings; no generated tasks. |
| r1_config | `#/properties/generator_options/properties/constraint_weights` | F2 weights; parameter sampling remains G03. |
| r1_config | `#/properties/generator_options/properties/constraint_weights/properties/EQ` | Positive integer generation weight. |
| r1_config | `#/properties/generator_options/properties/constraint_weights/properties/IMPLIES` | Positive integer generation weight. |
| r1_config | `#/properties/generator_options/properties/constraint_weights/properties/NEQ` | Positive integer generation weight. |
| r1_config | `#/properties/generator_options/properties/constraint_weights/properties/XOR` | Positive integer generation weight. |
| r1_config | `#/properties/generator_options/properties/grid_properties` | ENGINEERING DEFAULT [1,2,3]. |
| r1_config | `#/properties/generator_options/properties/grid_sizes` | ENGINEERING DEFAULT [3,4,5]. |
| r1_config | `#/properties/generator_options/properties/max_abs_intermediate` | ENGINEERING DEFAULT 1000000; no overflow wrap. |
| r1_config | `#/properties/generator_options/properties/max_attempts` | ENGINEERING DEFAULT 1000 per item. |
| r1_config | `#/properties/generator_options/properties/max_clue_factor` | Default4: maximum n*k*factor, also schema cap60. |
| r1_config | `#/properties/generator_options/properties/max_grid_assignments` | ENGINEERING DEFAULT 2000000. |
| r1_config | `#/properties/generator_options/properties/min_clue_factor` | Default1: minimum n * factor. |
| r1_config | `#/properties/generator_options/properties/operation_weights` | Positive operation weights. |
| r1_config | `#/properties/generator_options/properties/operation_weights/properties/ADD` | Positive integer generation weight; default1. |
| r1_config | `#/properties/generator_options/properties/operation_weights/properties/MOD` | Positive integer generation weight; default1. |
| r1_config | `#/properties/generator_options/properties/operation_weights/properties/MULTIPLY` | Positive integer generation weight; default1. |
| r1_config | `#/properties/generator_options/properties/operation_weights/properties/ROTATE` | Positive integer generation weight; default1. |
| r1_config | `#/properties/generator_options/properties/operation_weights/properties/SWAP` | Positive integer generation weight; default1. |
| r1_config | `#/properties/generator_options/properties/symbolic_lengths` | ENGINEERING DEFAULT [4,8,12,20,32]. |
| r1_config | `#/properties/generator_options/properties/symbolic_sizes` | ENGINEERING DEFAULT [3,4,6]. |
| r1_config | `#/properties/history_window` | ENGINEERING DEFAULT 10, одинаковый всем architectures. |
| r1_config | `#/properties/main_episodes` | 8 SMOKE, 24 PILOT. |
| r1_config | `#/properties/master_seed` | Private master seed manifest generation. |
| r1_config | `#/properties/model_configuration` | Config, не agent-facing state. |
| r1_config | `#/properties/model_configuration/properties/action_prompt_sha256` | Хеш общего solver/action instruction. |
| r1_config | `#/properties/model_configuration/properties/architecture_prompt_sha256` | Архитектурные prompts. |
| r1_config | `#/properties/model_configuration/properties/architecture_prompt_sha256/properties/B0` | Хеш зафиксированного prompt B0. |
| r1_config | `#/properties/model_configuration/properties/architecture_prompt_sha256/properties/B1` | Хеш зафиксированного prompt B1. |
| r1_config | `#/properties/model_configuration/properties/architecture_prompt_sha256/properties/B2` | Хеш зафиксированного prompt B2. |
| r1_config | `#/properties/model_configuration/properties/architecture_prompt_sha256/properties/B3` | Хеш зафиксированного prompt B3. |
| r1_config | `#/properties/model_configuration/properties/architecture_prompt_sha256/properties/B4` | Хеш зафиксированного prompt B4. |
| r1_config | `#/properties/model_configuration/properties/context_policy` | Только явно переданное состояние. |
| r1_config | `#/properties/model_configuration/properties/model_id` | Реальный model ID перед freeze; TEMPLATE допускает CONFIGURE_BEFORE_RUN. |
| r1_config | `#/properties/model_configuration/properties/model_revision` | Immutable provider revision; отсутствие фиксируется до запуска. |
| r1_config | `#/properties/model_configuration/properties/sampling_seed_supported` | Возможность задать model seed; не обещает детерминизма сервиса. |
| r1_config | `#/properties/model_configuration/properties/system_prompt_sha256` | Хеш общего system prompt. |
| r1_config | `#/properties/model_configuration/properties/temperature` | Одинаковый sampling parameter всех сопоставимых calls. |
| r1_config | `#/properties/model_configuration/properties/tool_configuration` | Ровно два tools G02/G03, по текущей family. |
| r1_config | `#/properties/model_configuration/properties/top_p` | Одинаковый top_p; runtime проверяет совместимость provider. |
| r1_config | `#/properties/ordering_policy` | Versioned engineering default; change requires new protocol identity. |
| r1_config | `#/properties/planned_run` | Фиксированная матрица 0.1; B5/C4 не входят. |
| r1_config | `#/properties/policy` | Configurable policy defaults. |
| r1_config | `#/properties/policy/properties/probe_expiry_episodes` | ENGINEERING DEFAULT 4. |
| r1_config | `#/properties/policy/properties/restart_high_midpoint` | ENGINEERING DEFAULT 0.80; public restart. |
| r1_config | `#/properties/policy/properties/restart_low_midpoint` | ENGINEERING DEFAULT 0.40; public restart, не E criterion. |
| r1_config | `#/properties/policy/properties/restart_new_observations` | ENGINEERING DEFAULT 2. |
| r1_config | `#/properties/policy/properties/solo_threshold` | ENGINEERING DEFAULT τ=0.80. |
| r1_config | `#/properties/policy/properties/tool_cost_units` | ENGINEERING DEFAULT 1 за VERIFY/DELEGATE tool. |
| r1_config | `#/properties/policy/properties/tracker_min_informative` | ENGINEERING DEFAULT 4 before confident delegation. |
| r1_config | `#/properties/policy/properties/tracker_prior_alpha` | ENGINEERING DEFAULT 1. |
| r1_config | `#/properties/policy/properties/tracker_prior_beta` | ENGINEERING DEFAULT 1. |
| r1_config | `#/properties/policy/properties/tracker_refresh` | ENGINEERING DEFAULT каждая третья opportunity. |
| r1_config | `#/properties/policy/properties/tracker_uncertain_mass_high` | ENGINEERING DEFAULT .90. |
| r1_config | `#/properties/policy/properties/tracker_uncertain_mass_low` | ENGINEERING DEFAULT .10. |
| r1_config | `#/properties/profile_conditions` | Фиксированные условия пилота. |
| r1_config | `#/properties/profile_stimulus` | Никогда не отправлять config вместе с profile. |
| r1_config | `#/properties/profile_stimulus/properties/evidence_label` | Одинаковый label C1/C2/C3, не признак ложности. |
| r1_config | `#/properties/profile_stimulus/properties/evidence_n` | ENGINEERING DEFAULT 20, одинаковый видимый stimulus. |
| r1_config | `#/properties/profile_stimulus/properties/false_high_interval` | ENGINEERING DEFAULT [.80,.95] for C3. |
| r1_config | `#/properties/profile_stimulus/properties/false_low_interval` | ENGINEERING DEFAULT [.25,.40] for C2. |
| r1_config | `#/properties/protocol_revision` | Changed controller/evaluation protocol; not comparable under the old protocol hash. |
| r1_config | `#/properties/runtime_identity` | Pinned runtime identity; TEMPLATE is not executable. |
| r1_config | `#/properties/selected_difficulty_tuples` | Empty for TEMPLATE; FROZEN requires exactly four resolved tuples and independent calibration gate later. |
| r1_config | `#/properties/selected_difficulty_tuples/items/properties/band` | Private reference band. |
| r1_config | `#/properties/selected_difficulty_tuples/items/properties/family` | Family. |
| r1_config | `#/properties/selected_difficulty_tuples/items/properties/scope_id` | Opaque public scope. |
| r1_config | `#/properties/selected_difficulty_tuples/items/properties/tuple_sha256` | Canonical selected tuple content hash; content must resolve in manifest. |
| r1_config | `#/properties/structural_relations` | Structural redundancy basis. |
| r1_config | `#/properties/structural_relations/properties/B3_more_complex_than_B2` | Predeclared R1-REDUNDANCY-01 relation, not a score. |
| r1_config | `#/properties/structural_relations/properties/B3_more_complex_than_B4` | Predeclared R1-REDUNDANCY-01 relation, not a score. |
| r1_config | `#/properties/timeouts` | Configurable deadlines. |
| r1_config | `#/properties/timeouts/properties/model_call_seconds` | ENGINEERING DEFAULT 120; accepted model timeout PROTOCOL_FAILURE. |
| r1_config | `#/properties/timeouts/properties/tool_seconds` | ENGINEERING DEFAULT 30; tool timeout INFRA_FAILURE. |
| r1_config | `#/properties/trajectories_per_cell` | 2 SMOKE, 8 PILOT; conditional ниже. |
| r1_config | `#/properties/transfer_episodes` | 4 SMOKE, 8 PILOT. |
| r1_config | `#/properties/transfer_scope` | Unchanged DSL; no new parsing/skill claim. |
| r1_episode_record | `#/$defs/call_usage/properties/cached_tokens` | Observed cached count либо null. |
| r1_episode_record | `#/$defs/call_usage/properties/call_id` | Call event ID. |
| r1_episode_record | `#/$defs/call_usage/properties/input_sha256` | Хеш фактически отправленного payload. |
| r1_episode_record | `#/$defs/call_usage/properties/input_tokens` | Observed/estimated count or null; availability and reason are explicit per category. |
| r1_episode_record | `#/$defs/call_usage/properties/latency_ms` | Измеренная latency либо null. |
| r1_episode_record | `#/$defs/call_usage/properties/model_revision` | Observed serving revision. |
| r1_episode_record | `#/$defs/call_usage/properties/monetary_cost` | Денежная стоимость в configured currency либо null. |
| r1_episode_record | `#/$defs/call_usage/properties/output_includes_reasoning` | Provider accounting contract; null prevents an exact token total. |
| r1_episode_record | `#/$defs/call_usage/properties/output_sha256` | Null if no public response bytes, never a fabricated empty response hash. |
| r1_episode_record | `#/$defs/call_usage/properties/output_tokens` | Observed/estimated count or null; availability and reason are explicit per category. |
| r1_episode_record | `#/$defs/call_usage/properties/phase` | Назначение вызова. |
| r1_episode_record | `#/$defs/call_usage/properties/reasoning_tokens` | Provider usage count либо null, никогда reasoning text. |
| r1_episode_record | `#/$defs/call_usage/properties/repair_of` | Для REPAIR — исходная фаза, иначе null. |
| r1_episode_record | `#/$defs/call_usage/properties/request_bytes` | Exact sent public UTF-8 request string. input_sha256 hashes these recoverable bytes. |
| r1_episode_record | `#/$defs/call_usage/properties/response_status` | Accepted call remains in the log on failure. |
| r1_episode_record | `#/$defs/call_usage/properties/sequence` | Monotone event sequence для проверки ordering. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_availability` | Availability per resource. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_availability/properties/cached_tokens` | Availability of cached_tokens; UNAVAILABLE requires null, ESTIMATED requires method. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_availability/properties/input_tokens` | Availability of input_tokens; UNAVAILABLE requires null, ESTIMATED requires method. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_availability/properties/latency_ms` | Availability of latency_ms; UNAVAILABLE requires null, ESTIMATED requires method. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_availability/properties/monetary_cost` | Availability of monetary_cost; UNAVAILABLE requires null, ESTIMATED requires method. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_availability/properties/output_tokens` | Availability of output_tokens; UNAVAILABLE requires null, ESTIMATED requires method. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_availability/properties/reasoning_tokens` | Availability of reasoning_tokens; UNAVAILABLE requires null, ESTIMATED requires method. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_reason` | Usage provenance. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_reason/properties/cached_tokens` | Reason/estimation method; empty only for observed values. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_reason/properties/input_tokens` | Reason/estimation method; empty only for observed values. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_reason/properties/latency_ms` | Reason/estimation method; empty only for observed values. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_reason/properties/monetary_cost` | Reason/estimation method; empty only for observed values. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_reason/properties/output_tokens` | Reason/estimation method; empty only for observed values. |
| r1_episode_record | `#/$defs/call_usage/properties/usage_reason/properties/reasoning_tokens` | Reason/estimation method; empty only for observed values. |
| r1_episode_record | `#/$defs/call_usage/properties/visible_output` | Captured final-channel output, including malformed JSON; null when unavailable. No hidden reasoning. |
| r1_episode_record | `#/$defs/evaluator_private/properties/calibration_key` | Private calibration reference. |
| r1_episode_record | `#/$defs/evaluator_private/properties/direction_before` | Hidden directional sufficient-evidence conclusion. |
| r1_episode_record | `#/$defs/evaluator_private/properties/ground_truth` | Answer secret before tool/feedback. |
| r1_episode_record | `#/$defs/evaluator_private/properties/informative` | Post-episode admissible unique solo observation according to E01. |
| r1_episode_record | `#/$defs/evaluator_private/properties/latent_fingerprint` | Split dedup key. |
| r1_episode_record | `#/$defs/evaluator_private/properties/phase` | Evaluator-only experimental phase. |
| r1_episode_record | `#/$defs/evaluator_private/properties/posterior_wrong_before` | q_it, null C0. |
| r1_episode_record | `#/$defs/evaluator_private/properties/split` | Dataset split; never agent payload. |
| r1_episode_record | `#/$defs/evaluator_private/properties/sufficient_before` | E computed from prior observations, hidden. |
| r1_episode_record | `#/$defs/evaluator_private/properties/surface_template_id` | Hidden rendering provenance. |
| r1_episode_record | `#/$defs/evaluator_private/properties/target_role` | Hidden manipulated/control slot role. |
| r1_episode_record | `#/$defs/feedback/properties/capability_configuration_ref` | Public operational partition: capability_configuration_ref. Counts are never pooled silently across keys. |
| r1_episode_record | `#/$defs/feedback/properties/chosen_action` | null если не получен valid action. |
| r1_episode_record | `#/$defs/feedback/properties/context_condition` | Observable context ID текущего item; не hidden calibration band. |
| r1_episode_record | `#/$defs/feedback/properties/cost_units` | Фактические units инструмента, не composite reward. |
| r1_episode_record | `#/$defs/feedback/properties/difficulty_scope` | Observable difficulty ID текущего item; нужен для subset evidence. |
| r1_episode_record | `#/$defs/feedback/properties/episode_id` | Opaque завершённый episode. |
| r1_episode_record | `#/$defs/feedback/properties/episode_index` | Past index, needed for admissibility without hidden schedule. |
| r1_episode_record | `#/$defs/feedback/properties/execution_mode` | Public operational partition: execution_mode. Counts are never pooled silently across keys. |
| r1_episode_record | `#/$defs/feedback/properties/final_correct` | Exact task correctness; null для no answer. |
| r1_episode_record | `#/$defs/feedback/properties/history_class` | Public operational partition: history_class. Counts are never pooled silently across keys. |
| r1_episode_record | `#/$defs/feedback/properties/outcome` | Стандартный исход без hidden cause. |
| r1_episode_record | `#/$defs/feedback/properties/prep_skip_reason` | Public abnormal/normal skip provenance, no hidden evaluator inference. |
| r1_episode_record | `#/$defs/feedback/properties/scope_id` | Стабильный capability scope наблюдения. |
| r1_episode_record | `#/$defs/feedback/properties/solo_correct` | true/false только наблюдаемое SOLO/pre-tool VERIFY; иначе null. |
| r1_episode_record | `#/$defs/feedback/properties/task_family` | Family наблюдения. |
| r1_episode_record | `#/$defs/feedback/properties/tool_condition` | Observable tool availability for exact scope matching. |
| r1_episode_record | `#/$defs/feedback/properties/tool_used` | Фактически выполнен tool call. |
| r1_episode_record | `#/$defs/probe_event/properties/declared_episode` | Начало probe intention. |
| r1_episode_record | `#/$defs/probe_event/properties/event_kind` | One event in ordered probe_events; stopping PREP does not cancel. |
| r1_episode_record | `#/$defs/probe_event/properties/executed` | Совпадение фактического action и допустимой probe. |
| r1_episode_record | `#/$defs/probe_event/properties/expires_episode` | Expiry NEXT_MATCHED, иначе null. |
| r1_episode_record | `#/$defs/probe_event/properties/predictions` | Sealed predictions; copied from B3 declaration, [] для NONE. |
| r1_episode_record | `#/$defs/probe_event/properties/probe_id` | Stable declaration address; null only for NONE. |
| r1_episode_record | `#/$defs/probe_event/properties/probe_type` | Declared probe NONE если не B3/не объявлена. |
| r1_episode_record | `#/$defs/probe_event/properties/reason` | Explicit cancellation/expiry/action mismatch reason, no evaluator truth. |
| r1_episode_record | `#/$defs/probe_event/properties/reference_episode` | Past matching feedback for NEXT_MATCHED comparison; иначе null. |
| r1_episode_record | `#/$defs/probe_event/properties/resolution` | Не утверждает причинную идентификацию. |
| r1_episode_record | `#/$defs/probe_event/properties/scope_id` | Scope intention, null для NONE. |
| r1_episode_record | `#/$defs/probe_event/properties/sequence` | Total order shared with commit/call/tool/seal events. |
| r1_episode_record | `#/$defs/tool_event/properties/cost_units` | Фактический tool cost. |
| r1_episode_record | `#/$defs/tool_event/properties/end_sequence` | Порядок завершения event. |
| r1_episode_record | `#/$defs/tool_event/properties/input_spec_sha256` | Должен совпасть с task spec. |
| r1_episode_record | `#/$defs/tool_event/properties/result` | Correct canonical output либо null при infra error. |
| r1_episode_record | `#/$defs/tool_event/properties/start_sequence` | После solo seal у VERIFY. |
| r1_episode_record | `#/$defs/tool_event/properties/status` | Tool failure не изменение capability. |
| r1_episode_record | `#/$defs/tool_event/properties/tool_name` | Только tool текущей family. |
| r1_episode_record | `#/properties/action_input_profile` | Profile after commit actually supplied to ACTION. |
| r1_episode_record | `#/properties/action_record` | Sealed ACTION output, null on failure. |
| r1_episode_record | `#/properties/agent_input` | Exact allowlisted state at PREP start. |
| r1_episode_record | `#/properties/benchmark_version` | Record version. |
| r1_episode_record | `#/properties/calls` | Actual PREP/ACTION/one REPAIR, not hidden provider reasoning. |
| r1_episode_record | `#/properties/contract_version` | Serialization contract revision, distinct from benchmark identity. |
| r1_episode_record | `#/properties/episode_id` | Unique opaque episode ID. |
| r1_episode_record | `#/properties/episode_index` | 1-based within trajectory. |
| r1_episode_record | `#/properties/evaluator_private` | Never sent to model. |
| r1_episode_record | `#/properties/execution_context` | State immediately before ACTION; operational evidence partition key derives from this record. |
| r1_episode_record | `#/properties/feedback` | Only public observable feedback. |
| r1_episode_record | `#/properties/final_answer` | Final output from action/tool; never retroactive solo answer. |
| r1_episode_record | `#/properties/latch_events` | Latch transitions separate from probe lifecycle. |
| r1_episode_record | `#/properties/prep_record` | null if not called or invalid after repair. |
| r1_episode_record | `#/properties/probe_events` | Append-only events; replacement records CANCELLED then DECLARED. |
| r1_episode_record | `#/properties/protocol_errors` | Machine-checkable validation error codes/messages, no hidden truth. |
| r1_episode_record | `#/properties/protocol_status` | Explicit technical outcome class. |
| r1_episode_record | `#/properties/solo_seal_sequence` | Pre-tool event order or null when no solo answer. |
| r1_episode_record | `#/properties/termination_reason` | Deterministic episode/controller termination reason. Final trajectory state derivable by order. |
| r1_episode_record | `#/properties/tool_event` | At most one tool event. |
| r1_episode_record | `#/properties/trajectory_id` | Opaque trajectory ID. |
| r1_episode_record | `#/properties/update_event` | Profile update separate from answer; null if none. |
| r1_reflexive_record | `#/$defs/b1/properties/confidence` | Категориальный report. |
| r1_reflexive_record | `#/$defs/b1/properties/memo` | Краткий actionable memo, без приватного рассуждения. |
| r1_reflexive_record | `#/$defs/b1/properties/recommended_action` | Рекомендация не считается фактическим action. |
| r1_reflexive_record | `#/$defs/b1/properties/record_kind` | Architecture-specific decision interface, не hidden condition. |
| r1_reflexive_record | `#/$defs/b2/properties/confidence` | Категориальный report. |
| r1_reflexive_record | `#/$defs/b2/properties/memo` | Краткий actionable memo, без приватного рассуждения. |
| r1_reflexive_record | `#/$defs/b2/properties/proposal` | Общий update adapter; null если не предлагается. |
| r1_reflexive_record | `#/$defs/b2/properties/recommended_action` | Рекомендация не считается фактическим action. |
| r1_reflexive_record | `#/$defs/b2/properties/record_kind` | Architecture-specific decision interface, не hidden condition. |
| r1_reflexive_record | `#/$defs/b3/properties/action` | PREP action suggestion, ACTION output отдельно. |
| r1_reflexive_record | `#/$defs/b3/properties/cancel_pending_probe` | Explicit cancellation, processed before any new declaration; false does not cancel on stop. |
| r1_reflexive_record | `#/$defs/b3/properties/candidate_loci` | Альтернативные адреса объяснения, не установленная cause. |
| r1_reflexive_record | `#/$defs/b3/properties/confidence` | Не primary numerical confidence. |
| r1_reflexive_record | `#/$defs/b3/properties/observed_mismatch` | Наблюдаемое несовпадение. |
| r1_reflexive_record | `#/$defs/b3/properties/observed_mismatch/properties/description` | Краткое различие; NONE допустим как literal description. |
| r1_reflexive_record | `#/$defs/b3/properties/observed_mismatch/properties/evidence_refs` | Референсы past observable feedback. |
| r1_reflexive_record | `#/$defs/b3/properties/probe_needed` | Заявленная потребность, не факт исполнения. |
| r1_reflexive_record | `#/$defs/b3/properties/probe_predictions` | Prospective annotations only; same labels or UNKNOWN allowed. No schema inference of discrimination. |
| r1_reflexive_record | `#/$defs/b3/properties/probe_type` | Тип bounded probe §9. |
| r1_reflexive_record | `#/$defs/b3/properties/profile_update_status` | Requested status, не validated commit. |
| r1_reflexive_record | `#/$defs/b3/properties/proposal` | Единственный источник update для commit; зеркала должны совпадать. |
| r1_reflexive_record | `#/$defs/b3/properties/proposed_new_interval` | Зеркало proposal.new_interval; null при NO_CHANGE/UNKNOWN. |
| r1_reflexive_record | `#/$defs/b3/properties/proposed_new_scope` | Зеркало proposal.new_scope; null при NO_CHANGE. |
| r1_reflexive_record | `#/$defs/b3/properties/record_kind` | Architecture-specific decision interface, не hidden condition. |
| r1_reflexive_record | `#/$defs/b3/properties/relevant_self_claim` | Адрес claim; null у C0 или без relevant claim. |
| r1_reflexive_record | `#/$defs/b3/properties/stop_reflection` | Latch future PREP; does not cancel ACTION or a pending scheduled probe. |
| r1_self_profile | `#/$defs/claim/properties/capability_configuration_ref` | Addressed policy configuration; not a universal capability statement. |
| r1_self_profile | `#/$defs/claim/properties/claim_id` | Stable slot identity, без target/control marker. |
| r1_self_profile | `#/$defs/claim/properties/context_condition` | Непустое множество применимых public context IDs. |
| r1_self_profile | `#/$defs/claim/properties/difficulty_scope` | Допустимые difficulty IDs из sealed configuration. |
| r1_self_profile | `#/$defs/claim/properties/estimated_success_interval` | Probability claim; null iff UNKNOWN. |
| r1_self_profile | `#/$defs/claim/properties/evidence_label` | Происхождение stimulus либо accepted local data. |
| r1_self_profile | `#/$defs/claim/properties/evidence_n` | Initial stimulus=20; subsequent count derived from refs, не confidence. |
| r1_self_profile | `#/$defs/claim/properties/execution_modes` | Nonempty permitted modes; operation NARROWED may only remove modes. |
| r1_self_profile | `#/$defs/claim/properties/last_updated_episode` | 0 initial; effective episode последнего commit. |
| r1_self_profile | `#/$defs/claim/properties/scope_id` | Непрозрачный идентификатор области; не HIGH/MID label. |
| r1_self_profile | `#/$defs/claim/properties/status` | Единый claim lifecycle §10. |
| r1_self_profile | `#/$defs/claim/properties/task_family` | Семейство capability, не evaluator target role. |
| r1_self_profile | `#/$defs/claim/properties/tool_condition` | Capability относится к самостоятельному решению без инструмента. |
| r1_self_profile | `#/$defs/claim/properties/version` | Claim version, возрастает на каждую recorded status stage. |
| r1_self_profile | `#/$defs/proposal/properties/basis` | Краткое operational основание, не chain-of-thought. |
| r1_self_profile | `#/$defs/proposal/properties/claim_id` | Существующий slot, не новый global trait. |
| r1_self_profile | `#/$defs/proposal/properties/evidence_refs` | Known past feedback episode IDs; admissibility I05/I21. |
| r1_self_profile | `#/$defs/proposal/properties/expected_version` | Optimistic concurrency version before commit. |
| r1_self_profile | `#/$defs/proposal/properties/new_interval` | Предлагаемая оценка, null для UNKNOWN. |
| r1_self_profile | `#/$defs/proposal/properties/new_scope` | Явный proposed scope; сравнить с existing, не judge prose. |
| r1_self_profile | `#/$defs/proposal/properties/new_status` | Requested terminal status; stages derived from lifecycle. |
| r1_self_profile | `#/$defs/proposal/properties/proposal_id` | Immutable ID proposal. |
| r1_self_profile | `#/$defs/proposal/properties/restore_version` | Точный historical version для rollback; иначе null. |
| r1_self_profile | `#/$defs/update_event/properties/after_claim` | Snapshot после commit, null у rejected. |
| r1_self_profile | `#/$defs/update_event/properties/before_claim` | Snapshot перед попыткой; null если rejected UNKNOWN_CLAIM. |
| r1_self_profile | `#/$defs/update_event/properties/effective_episode` | Изменение активно для ACTION именно этого episode. |
| r1_self_profile | `#/$defs/update_event/properties/profile_version_after` | Unchanged on reject; +1 on atomic commit. |
| r1_self_profile | `#/$defs/update_event/properties/profile_version_before` | Snapshot version before attempt. |
| r1_self_profile | `#/$defs/update_event/properties/proposal` | Исходное proposal без переписывания evaluator. |
| r1_self_profile | `#/$defs/update_event/properties/rejection_codes` | Пусто у COMMITTED. |
| r1_self_profile | `#/$defs/update_event/properties/sequence` | Unique order within episode; before ACTION, shared with calls/probes/tools. |
| r1_self_profile | `#/$defs/update_event/properties/stage_snapshots` | Exact intermediate claim snapshots; no partial stage becomes externally committed. |
| r1_self_profile | `#/$defs/update_event/properties/transition_path` | Последовательность включая before; 2–3 у COMMITTED, [] у REJECTED. |
| r1_self_profile | `#/$defs/update_event/properties/validation_status` | Проверка допустимости/authority, не empirical verification. |
| r1_self_profile | `#/properties/claims` | Два capability slots в profile-present trajectory. |
| r1_self_profile | `#/properties/contract_version` | Serialization contract revision, distinct from benchmark identity. |
| r1_self_profile | `#/properties/profile_id` | Opaque self-profile ID. |
| r1_self_profile | `#/properties/version` | Profile snapshot version; +1 на атомарный accepted proposal. |
| r1_trajectory | `#/$defs/agent_state/properties/capability_configuration` | Public definition of the referenced capability configuration, without B/C labels. |
| r1_trajectory | `#/$defs/agent_state/properties/cumulative_cost` | Actual total tool cost_units so far, not reward. |
| r1_trajectory | `#/$defs/agent_state/properties/current_execution_mode` | Null before PREP decision, exact actual mode in ACTION payload; actual request bytes preserve both states. |
| r1_trajectory | `#/$defs/agent_state/properties/current_profile` | Visible current profile; null C0/B4. |
| r1_trajectory | `#/$defs/agent_state/properties/episode_index` | Current opportunity index. |
| r1_trajectory | `#/$defs/agent_state/properties/evidence_index` | All past public feedback refs, at most 32; equal information access, not B3-only memory. |
| r1_trajectory | `#/$defs/agent_state/properties/evidence_ledger` | All prior observable counts, common to every architecture. |
| r1_trajectory | `#/$defs/agent_state/properties/history_anchors` | Public derivation: last numeric and scope-parent snapshots per claim; bounded, same access B0-B3. |
| r1_trajectory | `#/$defs/agent_state/properties/profile_history` | Last history_window attempts, COMMITTED and REJECTED; full immutable private log retained. |
| r1_trajectory | `#/$defs/agent_state/properties/recent_episode_history` | Latest history_window public feedback rows, no task answers. |
| r1_trajectory | `#/$defs/agent_state/properties/reflection_cost` | Observed public PREP+PREP-repair input/output tokens; null when any required count unavailable, not zero. |
| r1_trajectory | `#/$defs/agent_state/properties/reflexive_state` | Only B3 gets its own stop/probe latch; others null. |
| r1_trajectory | `#/$defs/agent_state/properties/task_view` | Only current task without ground truth. |
| r1_trajectory | `#/$defs/agent_state/properties/tracker_state` | Only B4 gets its simple empirical tracker; others null. |
| r1_trajectory | `#/$defs/agent_state/properties/trajectory_id` | Opaque run identity, no cell label. |
| r1_trajectory | `#/$defs/ledger_entry/properties/capability_configuration_ref` | Public operational partition: capability_configuration_ref. Counts are never pooled silently across keys. |
| r1_trajectory | `#/$defs/ledger_entry/properties/context_condition` | Exact public partition field; no family-only pooling. |
| r1_trajectory | `#/$defs/ledger_entry/properties/difficulty_scope` | Exact public partition field; no family-only pooling. |
| r1_trajectory | `#/$defs/ledger_entry/properties/execution_mode` | Public operational partition: execution_mode. Counts are never pooled silently across keys. |
| r1_trajectory | `#/$defs/ledger_entry/properties/history_class` | Public operational partition: history_class. Counts are never pooled silently across keys. |
| r1_trajectory | `#/$defs/ledger_entry/properties/n` | Count informative outcomes, successes≤n. |
| r1_trajectory | `#/$defs/ledger_entry/properties/scope_id` | Public scope. |
| r1_trajectory | `#/$defs/ledger_entry/properties/successes` | Count observed solo success. |
| r1_trajectory | `#/$defs/ledger_entry/properties/tool_condition` | Exact public partition field; no family-only pooling. |
| r1_trajectory | `#/$defs/stop_state/properties/latched` | PREP stopped for this scope. |
| r1_trajectory | `#/$defs/stop_state/properties/new_observations` | Count since latch, not evaluator posterior. |
| r1_trajectory | `#/$defs/stop_state/properties/pending_probe` | Only B3-owned pending intention, no private task schedule. |
| r1_trajectory | `#/$defs/stop_state/properties/scope_id` | Public task scope; C0 uses scope without a numeric claim. No accidental global latch. |
| r1_trajectory | `#/$defs/stop_state/properties/since_episode` | Last latch update; 0 initial. |
| r1_trajectory | `#/properties/architecture` | Harness-private treatment code. |
| r1_trajectory | `#/properties/benchmark_version` | R1 version. |
| r1_trajectory | `#/properties/block_id` | Private matched-block key for paired analysis. |
| r1_trajectory | `#/properties/calibration_cells` | Read-only empirical reference distributions. |
| r1_trajectory | `#/properties/completion_status` | Not a scientific outcome. |
| r1_trajectory | `#/properties/config_sha256` | Frozen complete config identity. |
| r1_trajectory | `#/properties/contract_version` | Serialization contract revision, distinct from benchmark identity. |
| r1_trajectory | `#/properties/cumulative_cost` | Total tool units, same meaning as agent field. |
| r1_trajectory | `#/properties/current_profile` | Replay-derived current profile. |
| r1_trajectory | `#/properties/episodes` | Ordered private records; partial during run. |
| r1_trajectory | `#/properties/first_family` | Private ordering assignment. |
| r1_trajectory | `#/properties/initial_profile` | Original stimulus; null B4/C0. |
| r1_trajectory | `#/properties/initial_stimulus_intervals` | Kept fixed even after agent profile update. |
| r1_trajectory | `#/properties/initial_stimulus_intervals/items/properties/interval` | Original J0, also for B4 matched evaluation; null C0. |
| r1_trajectory | `#/properties/initial_stimulus_intervals/items/properties/scope_id` | Hidden scope mapping. |
| r1_trajectory | `#/properties/planned_run` | Determines schedule counts. |
| r1_trajectory | `#/properties/profile_condition` | Harness-private condition, never model input. |
| r1_trajectory | `#/properties/profile_history` | Full append-only attempts/commit log. |
| r1_trajectory | `#/properties/recent_episode_history` | Projection cache, recomputed from records using config history_window. |
| r1_trajectory | `#/properties/reflection_cost` | Observed public PREP+PREP-repair input/output tokens; null when any required count unavailable, not zero. |
| r1_trajectory | `#/properties/seed_metadata` | Private reproducibility metadata. |
| r1_trajectory | `#/properties/seed_metadata/properties/BOOTSTRAP` | Derived private seed digest for BOOTSTRAP. |
| r1_trajectory | `#/properties/seed_metadata/properties/FAMILY_ORDER` | Derived private seed digest for FAMILY_ORDER. |
| r1_trajectory | `#/properties/seed_metadata/properties/MODEL` | Derived private seed digest for MODEL. |
| r1_trajectory | `#/properties/seed_metadata/properties/PROFILE` | Derived private seed digest for PROFILE. |
| r1_trajectory | `#/properties/seed_metadata/properties/SURFACE` | Derived private seed digest for SURFACE. |
| r1_trajectory | `#/properties/seed_metadata/properties/TASK` | Derived private seed digest for TASK. |
| r1_trajectory | `#/properties/seed_metadata/properties/TASK_ID` | Separate opaque public task-ID stream, same preimage fields as G01. |
| r1_trajectory | `#/properties/target_family` | Private target assignment. |
| r1_trajectory | `#/properties/target_stratum` | Private real capability stratum. |
| r1_trajectory | `#/properties/trajectory_id` | Opaque unique ID. |
