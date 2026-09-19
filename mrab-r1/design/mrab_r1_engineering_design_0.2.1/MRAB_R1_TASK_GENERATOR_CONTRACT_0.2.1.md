# MRAB-R1 — Task Generator Contract 0.2.1

Это спецификация, не реализация генератора/interpreter/solver. Все ENGINEERING DEFAULT настраиваются до calibration; ни одного model run в данном проходе.

## G01. Общий envelope и deterministic seed

Input future generator: benchmark_version=0.1, protocol_revision=R1_0.1_DESIGN_PATCH_0.2.1, family, difficulty tuple, split (CALIBRATION_SEARCH/CALIBRATION_CONFIRM/MAIN/TRANSFER), master seed, block_id, item_index, generation_attempt. Output private: task_view, canonical_ground_truth, latent_fingerprint, surface_template_id, generation_log. В model payload входит только task_view: task_id, task_family, scope_id, difficulty_scope, context_condition, spec. Hidden metadata запрещены в instruction, task_id и spec.

`task_id` = первые 24 hex от SHA-256 domain-separated TASK_ID seed (не человекочитаемый split/condition). `scope_id`/difficulty_scope — непрозрачные идентификаторы опубликованных capability scopes; они не содержат слова HIGH/MID. Они стабильны между main/transfer.

Единый preimage для каждого digest: UTF-8 компактный JSON array ["MRAB-R1", protocol_revision, master_seed, split, block_id, stream, item_index, generation_attempt, counter, architecture_or_null, phase_or_null]. Все строки ASCII identifiers; integers nonnegative; без NaN/duplicate keys. architecture и phase заполняются только для MODEL, иначе null. SHA-256 каждого preimage даёт очередной digest, counter=0,1,…; uint32 big-endian, rejection x<floor(2^32/m)*m, randint=a+x mod m, Fisher–Yates descending. Это заменяет две несогласованные pipe-string формулы 0.1; старые streams нельзя выдавать за новые.

TASK, TASK_ID, FAMILY_ORDER, SURFACE, PROFILE, MODEL, BOOTSTRAP имеют разные domain labels. Architecture ID отсутствует в task seed matched block, присутствует в model-sampling seed. Condition находится только в private block_id, никогда в task text. Generation retries используют attempt, не тихо двигают поток соседних items. Максимум 1000 attempts на item: иначе GENERATION_FAILURE, не подмена scope более лёгкой задачей.

Уточнение хешей: описанная компактная сортировка достаточна для task DSL с ASCII keys/IDs и ограниченными integers. Для state/profile/config с probability/cost numbers обязательна канонизация [RFC 8785 JCS](https://www.rfc-editor.org/rfc/rfc8785.html), чтобы .80 и .8 не дали разные semantic hashes. Duplicate keys, non-finite values и непредставимые допустимым числовым форматом значения отклоняются до canonicalization. Точные integer вычисления interpreter от этого не заменяются floating arithmetic. Хеши доставленных файлов/source register — SHA-256 **сырых bytes файла**, не JCS; это другой явно названный слой целостности. Future runtime должен фиксировать canonicalizer version, не изобретать собственное rounding правило после runs.

## G02. F1 SYMBOLIC_PIPELINE

Grammar семантического spec:

```text
spec := {family:"SYMBOLIC_PIPELINE", initial:[integer,...], operations:[operation,...]}
operation := {op:"ADD", index:i, value:c}
           | {op:"MULTIPLY", index:i, value:c}
           | {op:"SWAP", left:i, right:j}
           | {op:"ROTATE", steps:k}
           | {op:"MOD", index:i, modulus:m}
```

Vector length n∈[2,8]; initial integers∈[−20,20]; operations count L∈[1,40]. i,j zero-based within current n; SWAP i≠j. ADD value∈[−9,9]\{0}; MULTIPLY value∈[−3,3]\{0,1}; steps integer [−(n−1),n−1]\{0}; modulus m∈[2,11]. No implicit broadcasting, precedence, overflow wrap or division; length constant. ADD/MULTIPLY/MOD modify one coordinate. SWAP exchanges two. ROTATE uses **right shift**: new[(i+k) mod n]=old[i], mathematical nonnegative modulo. MOD returns unique r with 0≤r<m and old[i]=q*m+r, including negative inputs. Operations execute exactly in listed order, arbitrary precision integer intermediate.

Primary answer = `{family:"SYMBOLIC_PIPELINE", result:[integer,...]}` exactly n integers. No tolerance, no free prose normalization. Tool `run_symbolic_pipeline(spec)` accepts only the active sealed spec, returns that answer; it is deterministic, state-free, has no self-profile/evaluator access.

Generation: choose initial vector uniformly; select operation kinds from configured positive weights normalized via integer cumulative weights (default all 1); draw valid parameters; execute privately to reject invalid/out-of-bound candidates. All intermediates require |x|≤10^6. Operation stack must contain ≥2 distinct op kinds when L≥2. Reject whole sequence if final==initial or two immediately adjacent operations are a syntactic cancelling pair (SWAP same pair; ROTATE k followed −k; ADD c followed −c same coordinate). These validity filters do not guarantee psychological difficulty; calibration does.

Difficulty tuple = n, L, operation_weights, max_abs_intermediate. Search default lexicographic grid n∈{3,4,6}, L∈{4,8,12,20,32}, constant op weights; deterministic candidate order increasing n then L. Select common tuples through calibration, never by experimental success. Record rejected-attempt reasons and final tuple; do not edit outcomes.

Hand-authored contract example (not model result): initial [−3,4,1]; ADD index0 value2 →[−1,4,1]; MULTIPLY index1 value−2 →[−1,−8,1]; SWAP0,2 →[1,−8,−1]; ROTATE1 →[−1,1,−8]; MOD index2 modulus5 →[−1,1,2]. Canonical ground truth [−1,1,2]. Include inverse-rotate and negative-mod fixtures.

## G03. F2 RULE_GRID

Exactly n entities e0…e(n−1), k properties a0…a(k−1), n named values per property. Each property assigns values bijectively to entities. Assignment atom (entity,property,value) is true iff assignment[entity][property]==value. Grammar:

```text
spec := {family:"RULE_GRID", entities:[id,...], properties:[property,...], constraints:[constraint,...]}
property := {property_id:id, values:[id,...]}
atom := {entity:id, property:id, value:id}
constraint := {kind:"EQ", atom:atom}
            | {kind:"NEQ", atom:atom}
            | {kind:"IMPLIES", left:atom, right:atom}
            | {kind:"XOR", left:atom, right:atom}
```

EQ requires atom true; NEQ false; IMPLIES = (not left) or right; XOR exactly one true. No natural-language entailment. Entity/property/value IDs unique in their namespaces; referenced IDs must exist, each property's value set has size n. Primary n∈[2,5], k∈[1,3], candidate search capped at (n!)^k≤2,000,000 assignments. No attributes such as real occupations/astrology/knowledge needed. Plain labels are semantically opaque.

Canonical answer = `{family:"RULE_GRID", result:[{entity_id, assignments:[{property_id,value_id},...]}...]}` with one row per entity and one value for every property. Rows and assignments lexicographically sorted by IDs, exact equality after this *specified* ordering normalization; duplicate rows/keys or omitted values are invalid, never silently repaired by evaluator. Entire assignment is requested, not a subjective explanation.

Construction: sample a planted bijective assignment; enumerate valid EQ/NEQ/IMPLIES/XOR clauses true under it, reject tautologies, duplicate clauses, left==right, and implications with false antecedent under every currently surviving assignment. Sample a clause-type-weighted deterministic order (default EQ:1, NEQ:2, IMPLIES:2, XOR:2). Add clauses until exactly one full assignment survives; then remove redundant clauses in one shuffled order, retaining removal iff uniqueness remains. Accept only when exact configured clue-count bounds satisfied; otherwise retry new planted assignment. Because all clauses hold for planted solution, zero-solution generation is always an error, not an acceptable candidate.

Default search n∈{3,4,5}, k∈{1,2,3}, clue count bounds [n,4*n*k], clause weights fixed. Candidate order increasing (n!)^k then n then k. Difficulty also logs active implication/XOR count and surviving assignments before final clue; these are private diagnostics, not labels about model capability. Runtime may implement complete enumeration or an independently verified exact constraint solver, but must prove satisfiability and uniqueness by finding exactly one solution and proving no second exists. No arbitrary search time limit that calls an unproven unique candidate valid.

Tool `solve_rule_grid(spec)` returns the canonical full assignment iff unique. Ambiguous task (≥2 solutions) → AMBIGUOUS_TASK; unsatisfiable → UNSAT_TASK. They are intentional fixtures but not primary agent episodes. Infrastructure aborts before model invocation and replaces from same seed stream/retry rule, never asks agent to infer a hidden tie-break.

Hand-authored example: e0,e1; a0 values v0,v1; EQ(e0,a0,v1), bijection => e1→v0, unique. Empty constraints at n=2 => two assignments, AMBIGUOUS_TASK. EQ(e0,a0,v0)+NEQ(e0,a0,v0) => UNSAT_TASK. These are specification vectors, not experimental measurements.

## G04. Interpreter/solver trust boundary

Generator answer and tool must be checked independently before release: F1 reference interpreter vs a separately implemented fold interpreter with hand-computed vectors; F2 full enumeration vs solver with exhaustive n≤3 cross-check. Metamorphic tests preserve verified answer under α-renaming and reordered constraint conjunction, and transform F1 answer only under cyclic coordinate rotations with indices relabelled; arbitrary permutations require conjugating ROTATE and are NOT an allowed unchanged-DSL symmetry. Tests are future implementation obligations, not reported as already passing here.

Invalid task, tool mismatch, unsupported op, ambiguous/unsat primary task, seed collision, or hash disagreement = INFRA_FAILURE. Do not count it as agent incompetence or invoke a model judge. Stop affected run, preserve log and rerun under corrected implementation version; do not silently erase hard cases. If an infrastructure failure is known only after invocation, trajectory excluded from inferential dataset with reason and attrition count, not spliced replacement episodes.

## G05. Split isolation and surface transfer

CALIBRATION_SEARCH, CALIBRATION_CONFIRM, MAIN, TRANSFER are disjoint. Latent fingerprint ignores surface words. F1 includes exact normalized initial vector and ordered operations; its optional coordinate symmetry is only the cyclic group commuting with ROTATE. Arbitrary coordinate permutations are not silently allowed. F2 uses the solution-anchored exact group canonicalization below. The private solution/canonical label mapping is never used as a public rendering order. Dedup across splits before any model call; equality of solved answer alone is not leakage and not a duplicate task.

Surface is a deterministic encoding of the *same fully specified DSL*. It never supplies intermediate/final answers. MAIN/CALIBRATION templates A: compact canonical JSON with glossary, B: one operation/constraint per numbered line plus structured spec. TRANSFER templates C: fixed column table, D: fully parenthesized prefix text plus structured spec, with unseen label alphabets. Templates C/D are reserved before calibration. All versions include machine-readable spec, so transfer tests robustness to changed presentation/context redundancy, not an unseen parsing skill. The restricted claim is deliberate: it does not demonstrate general task-family transfer.

Renderer output is checked by an independent parser round-trip to the same spec. Public spec excludes template_id, split, planted assignment, solver trace, generator seed, difficulty band and answer. Prefix labels in transfer cannot encode solution ordering. Slot/entity/value permutations random and independent of answer. Any F1/F2 item repeated with renamed surface in the same trajectory is not an independent observation; primary generation forbids it altogether.

## G06. Required engineering tests and hand-off

Inputs/outputs are typed in config `$defs/task_view`, `$defs/symbolic_spec`, `$defs/grid_spec`, `$defs/answer`; semantic ID/index/bijection/uniqueness constraints additionally governed here. `additionalProperties:false` is necessary but cannot establish solver correctness. No primary episode begins until task validation and unique canonical truth are sealed.

Future preflight must prove: reproducible manifest; known modulo/rotation vectors; invalid index rejection; overflow candidate rejection; grid SAT/UNSAT/AMBIGUOUS distinction; solver equivalence; split fingerprint separation; transfer round-trip; answer-free visible payload. Audit rows G01–G06 map to the fixture plan. No task generator, runner or evaluator runtime is supplied in this design pass.

## G07. Exact F2 alpha-canonicalization без факториального перебора values

Для UNIQUE primary item независимый exact solver уже обязан подтвердить единственное assignment A. Используем его только privately. Перебираем n! entity orders и k! property orders. Для каждой пары orders каноническое имя value в property назначается по индексу entity, которой этот value приписан **единственным A**. Затем переписываем atoms, сохраняем порядок IMPLIES operands, сортируем XOR operands и conjunction clauses; берём лексикографический минимум полученных compact integer/ASCII certificates.

Корректность: уникальное решение эквивариантно допустимому alpha-renaming. При фиксированных orders values уже однозначно сопоставлены с entities через A, поэтому независимые n! value permutations каждой property не надо перебирать. Изоморфные items дают один orbit certificate; равенство certificates реконструирует разрешённое переименование constraints. Используются все исходные симметрии entities/properties/per-property values, не сокращённый sorted-constraints hash.

Меняется **способ выбора canonical representative**, а не equivalence group. Это видимое CONTRACT_CLARIFICATION CC-02; новый canonicalizer version/hash обязателен. Это не прежний lexicographic minimum сырого spec по всей группе, но равенство fingerprint определяет ту же изоморфность.

Стоимость certificate: n!×k!×O((n×k+L) log L). При n=5,k=3: 120×6=720 candidates, до60 constraints. Прежняя наивная группа: 120^4×6=1,244,160,000 labelings; solver assignment bound120^3=1,728,000 — другая величина. Стоимость proof of uniqueness остаётся у solver, не исчезает из budget. Algorithm дан; production canonicalizer/solver, масштабный timing и independent n≤3 solver cross-check NOT_EXECUTED.

Tiny hand-authored tests n≤3 с заранее заданным UNIQUE solution проверяют alpha-renaming, property/value permutation, conjunction/XOR symmetry и неинвариантность IMPLIES reversal. Это design vectors, не готовый solver и не solver-certified arbitrary data. UNSAT/AMBIGUOUS fixtures не используют unique-solution key: primary preflight их отвергает; fingerprint подобных diagnostic items остаётся отдельным scoped контрактом.

Public labels/renderer выбираются независимым SURFACE stream, **не** solution-anchored canonical order: иначе приватный certificate превратится в answer leakage. TASK_ID derived independently from truth, split disjointness uses only private key before model calls.

## Patch0.2.1 scope note

Generator DSL/canonicalization and experimental matrix unchanged by the four author decisions. Only configuration/protocol identity is revised. R1-PREP-01 fixes normal B1/B2 PREP exactly once; independent reference confirmation budget remains4000 measurements /6400 calls before repairs/search. B3 calibration reset protocol and R1-CAPABILITY-01 remain unchanged. This contract is still not a production generator.
