"""G02/G03 independent-task primitives. No model, profile or evaluator access."""
from copy import deepcopy
from itertools import permutations, product
from math import factorial
from functools import lru_cache
from .canonical import integer_dsl_bytes, raw_sha
from .errors import Failure
from .schemas import Schemas
from .seed import Stream


@lru_cache(maxsize=1)
def _schemas():
    # Immutable contract registry, never contains trajectory or provider state.
    return Schemas()


def symbolic(spec, max_abs=1000000):
    _schemas().validate(spec, _schemas().ref("config", "symbolic_spec"), "GENERATION_FAILURE")
    if any(type(x) is not int for x in spec["initial"]) or any(type(v) is not int for op in spec["operations"] for key, v in op.items() if key != "op"):
        raise Failure("GENERATION_FAILURE", "EXACT_INTEGER_REQUIRED")
    v = list(spec["initial"])
    n = len(v)
    for op in spec["operations"]:
        kind = op["op"]
        if any(op[key] >= n for key in ("index", "left", "right") if key in op):
            raise Failure("GENERATION_FAILURE", "INDEX_OUT_OF_BOUNDS")
        if kind == "ADD":
            v[op["index"]] += op["value"]
        elif kind == "MULTIPLY":
            v[op["index"]] *= op["value"]
        elif kind == "MOD":
            v[op["index"]] %= op["modulus"]
        elif kind == "SWAP":
            i, j = op["left"], op["right"]
            if i == j:
                raise Failure("GENERATION_FAILURE", "IDENTICAL_SWAP_INDICES")
            v[i], v[j] = v[j], v[i]
        elif kind == "ROTATE":
            k = op["steps"]
            if not 0 < abs(k) < n:
                raise Failure("GENERATION_FAILURE", "ROTATION_OUT_OF_BOUNDS")
            v = [v[(j - k) % n] for j in range(n)]
        if max(abs(x) for x in v) > max_abs:
            raise Failure("GENERATION_FAILURE", "INTERMEDIATE_LIMIT")
    return {"family": "SYMBOLIC_PIPELINE", "result": v}


def validate_generated_symbolic(spec, max_abs=1000000):
    answer = symbolic(spec, max_abs)
    ops = spec["operations"]
    if len(ops) >= 2 and len({x["op"] for x in ops}) < 2:
        raise Failure("GENERATION_FAILURE", "INSUFFICIENT_OPERATION_VARIETY")
    if answer["result"] == spec["initial"]:
        raise Failure("GENERATION_FAILURE", "UNCHANGED_FINAL_VECTOR")
    for a, b in zip(ops, ops[1:]):
        if a["op"] != b["op"]:
            continue
        kind = a["op"]
        cancel = (kind == "SWAP" and {a["left"], a["right"]} == {b["left"], b["right"]}) or (kind == "ROTATE" and a["steps"] == -b["steps"]) or (kind == "ADD" and a["index"] == b["index"] and a["value"] == -b["value"])
        if cancel:
            raise Failure("GENERATION_FAILURE", "ADJACENT_CANCELLATION")
    return answer


def generate_symbolic(master_seed, split, block_id, item_index, n=3, length=4,
                      weights=None, max_abs=1000000, max_attempts=1000, start_attempt=0):
    if type(start_attempt) is not int or not 0<=start_attempt<1000:
        raise Failure("CONFIGURATION_FAILURE", "INVALID_GENERATION_ATTEMPT")
    if not (2 <= n <= 8 and 1 <= length <= 40 and 1 <= max_attempts <= 1000):
        raise Failure("CONFIGURATION_FAILURE", "INVALID_SYMBOLIC_DIFFICULTY")
    weights = weights or dict(ADD=1, MULTIPLY=1, SWAP=1, ROTATE=1, MOD=1)
    if set(weights) != {"ADD", "MULTIPLY", "SWAP", "ROTATE", "MOD"}:
        raise Failure("CONFIGURATION_FAILURE", "INVALID_OPERATION_WEIGHTS")
    rejected = []
    for attempt in range(start_attempt, min(1000, start_attempt+max_attempts)):
        r = Stream(master_seed, split, block_id, "TASK", item_index, attempt)
        spec = dict(family="SYMBOLIC_PIPELINE", initial=[r.randint(-20, 20) for _ in range(n)], operations=[])
        for _ in range(length):
            kind = r.weighted(weights)
            if kind in {"ADD", "MULTIPLY", "MOD"}:
                op = dict(op=kind, index=r.randint(0, n-1))
                if kind == "MOD":
                    op["modulus"] = r.randint(2, 11)
                else:
                    values = [x for x in range(-9, 10) if x] if kind == "ADD" else [-3, -2, -1, 2, 3]
                    op["value"] = values[r.randint(0, len(values)-1)]
            elif kind == "SWAP":
                i = r.randint(0, n-1)
                j = r.randint(0, n-2)
                op = dict(op=kind, left=i, right=j + (j >= i))
            else:
                choices = [x for x in range(-(n-1), n) if x]
                op = dict(op=kind, steps=choices[r.randint(0, len(choices)-1)])
            spec["operations"].append(op)
        try:
            answer = validate_generated_symbolic(spec, max_abs)
        except Failure as failure:
            rejected.append(dict(attempt=attempt, reason=failure.code))
            continue
        return dict(spec=spec, canonical_ground_truth=answer,
                    latent_fingerprint=raw_sha(integer_dsl_bytes(spec)),
                    task_id=Stream(master_seed, split, block_id, "TASK_ID", item_index, attempt).digest().hex()[:24],
                    generation_attempt=attempt, rejected_attempts=rejected)
    raise Failure("GENERATION_FAILURE", "ATTEMPTS_EXHAUSTED")


def grid_validate(spec):
    schemas = _schemas()
    schemas.validate(spec, schemas.ref("config", "grid_spec"), "GENERATION_FAILURE")
    entities = spec["entities"]
    props = {p["property_id"]: p["values"] for p in spec["properties"]}
    n, k = len(entities), len(props)
    if k != len(spec["properties"]) or any(len(v) != n for v in props.values()) or factorial(n)**k > 2000000:
        raise Failure("GENERATION_FAILURE", "INVALID_GRID_DIMENSIONS")
    for clause in spec["constraints"]:
        for atom in ([clause["atom"]] if "atom" in clause else [clause["left"], clause["right"]]):
            if atom["entity"] not in entities or atom["property"] not in props or atom["value"] not in props[atom["property"]]:
                raise Failure("GENERATION_FAILURE", "UNKNOWN_GRID_ATOM")
    return entities, props


def _possible(clause, assigned, positions):
    def atom(a):
        values = assigned.get(a["property"])
        return None if values is None else values[positions[a["entity"]]] == a["value"]
    kind = clause["kind"]
    if kind in {"EQ", "NEQ"}:
        x = atom(clause["atom"])
        return x is None or (x if kind == "EQ" else not x)
    a, b = atom(clause["left"]), atom(clause["right"])
    if kind == "IMPLIES":
        return not (a is True and b is False)
    return a is None or b is None or a != b


def grid_solutions(spec, limit=2):
    """Exact property-permutation CSP. Prunes only logically impossible prefixes.

    At limit=2 two witnesses prove ambiguity; unique requires exhaustive search
    of every remaining consistent branch. No timeout is recast as uniqueness.
    """
    entities, props = grid_validate(spec)
    positions = {e: i for i, e in enumerate(entities)}
    prop_order = sorted(props)
    choices = {p: list(permutations(props[p])) for p in prop_order}
    found, assignment = [], {}
    def search(depth):
        if limit is not None and len(found) >= limit:
            return
        if depth == len(prop_order):
            found.append(deepcopy(assignment))
            return
        p = prop_order[depth]
        for values in choices[p]:
            assignment[p] = values
            if all(_possible(c, assignment, positions) for c in spec["constraints"]):
                search(depth + 1)
            if limit is not None and len(found) >= limit:
                break
        assignment.pop(p, None)
    search(0)
    return found


def solve_grid(spec):
    solutions = grid_solutions(spec)
    if not solutions:
        raise Failure("UNSAT_TASK", "NO_SOLUTION")
    if len(solutions) != 1:
        raise Failure("AMBIGUOUS_TASK", "MULTIPLE_SOLUTIONS")
    solution = solutions[0]
    pos = {e: i for i, e in enumerate(spec["entities"])}
    return dict(family="RULE_GRID", result=[dict(entity_id=e,
        assignments=[dict(property_id=p, value_id=solution[p][pos[e]]) for p in sorted(solution)]) for e in sorted(pos)])


def alpha_fingerprint(spec):
    """G07 exact full group, at most n! * k! certificates, not value n!^k."""
    answer = solve_grid(spec)
    owners = {(a["property_id"], a["value_id"]): row["entity_id"] for row in answer["result"] for a in row["assignments"]}
    certificates = []
    for entities in permutations(spec["entities"]):
        eidx = {e: i for i, e in enumerate(entities)}
        for properties in permutations(p["property_id"] for p in spec["properties"]):
            pidx = {p: i for i, p in enumerate(properties)}
            def atom(a):
                return [eidx[a["entity"]], pidx[a["property"]], eidx[owners[a["property"], a["value"]]]]
            clauses = []
            for c in spec["constraints"]:
                if "atom" in c:
                    clauses.append([c["kind"], atom(c["atom"])])
                else:
                    operands = [atom(c["left"]), atom(c["right"])]
                    if c["kind"] == "XOR":
                        operands.sort()
                    clauses.append([c["kind"], *operands])
            certificate = integer_dsl_bytes([len(entities), len(properties), sorted(clauses)])
            certificates.append(certificate)
    return raw_sha(min(certificates))


def generate_grid(master_seed, split, block_id, item_index, n=3, k=1,
                  weights=None, min_clues=None, max_clues=None, max_attempts=1000, start_attempt=0):
    if type(start_attempt) is not int or not 0<=start_attempt<1000:
        raise Failure("CONFIGURATION_FAILURE", "INVALID_GENERATION_ATTEMPT")
    if not (2 <= n <= 5 and 1 <= k <= 3 and factorial(n)**k <= 2000000):
        raise Failure("CONFIGURATION_FAILURE", "INVALID_GRID_DIFFICULTY")
    if not 1 <= max_attempts <= 1000:
        raise Failure("CONFIGURATION_FAILURE", "INVALID_ATTEMPT_LIMIT")
    min_clues = n if min_clues is None else min_clues
    max_clues = 4*n*k if max_clues is None else max_clues
    if not 0 <= min_clues <= max_clues <= 60:
        raise Failure("CONFIGURATION_FAILURE", "INVALID_CLUE_BOUNDS")
    weights = weights or dict(EQ=1, NEQ=2, IMPLIES=2, XOR=2)
    if set(weights) != {"EQ", "NEQ", "IMPLIES", "XOR"}:
        raise Failure("CONFIGURATION_FAILURE", "INVALID_CONSTRAINT_WEIGHTS")
    rejected = []
    for attempt in range(start_attempt, min(1000, start_attempt+max_attempts)):
        r = Stream(master_seed, split, block_id, "TASK", item_index, attempt)
        entities = [f"e{i}" for i in range(n)]
        props = [dict(property_id=f"a{i}", values=[f"v{j}" for j in range(n)]) for i in range(k)]
        plant = {p["property_id"]: r.shuffle(p["values"]) for p in props}
        positions = {e: i for i, e in enumerate(entities)}
        atoms = [dict(entity=e, property=p["property_id"], value=v) for e in entities for p in props for v in p["values"]]
        pools = {kind: [] for kind in weights}
        for a in atoms:
            kind = "EQ" if plant[a["property"]][positions[a["entity"]]] == a["value"] else "NEQ"
            pools[kind].append(dict(kind=kind, atom=a))
        for i, left in enumerate(atoms):
            for j, right in enumerate(atoms):
                if i == j:
                    continue
                for kind in ("IMPLIES", "XOR"):
                    if kind == "XOR" and j < i:
                        continue
                    clause = dict(kind=kind, left=left, right=right)
                    if not _possible(clause, plant, positions):
                        continue
                    # Different properties are independent; a nontrivial binary
                    # implication/XOR is not tautological across those properties.
                    if left["property"] == right["property"]:
                        p = left["property"]
                        values = next(x["values"] for x in props if x["property_id"] == p)
                        if all(_possible(clause, {p: v}, positions) for v in permutations(values)):
                            continue
                    pools[kind].append(clause)
        pools = {kind: r.shuffle(items) for kind, items in pools.items()}
        spec = dict(family="RULE_GRID", entities=entities, properties=props, constraints=[])
        before_final = None
        exhausted = False
        while True:
            choices = {kind: weights[kind] for kind, items in pools.items() if items}
            if not choices or len(spec["constraints"]) == 60:
                exhausted = True
                break
            clause = pools[r.weighted(choices)].pop()
            if clause["kind"] == "IMPLIES":
                positive = deepcopy(spec)
                positive["constraints"].append(dict(kind="EQ", atom=clause["left"]))
                if not grid_solutions(positive, limit=1):
                    continue  # No currently possible antecedent: expressly forbidden.
            previous = deepcopy(spec)
            spec["constraints"].append(clause)
            solutions = grid_solutions(spec)
            if not solutions:
                raise Failure("GENERATION_FAILURE", "PLANTED_SOLUTION_LOST")
            if len(solutions) == 1:
                before_final = len(grid_solutions(previous, limit=None))
                break
        if exhausted:
            rejected.append(dict(attempt=attempt, reason="CLAUSE_POOL_OR_SCHEMA_BOUND"))
            continue
        # Fixed shuffled deletion order, each remaining constraint tested once.
        for clause in r.shuffle(deepcopy(spec["constraints"])):
            trial = deepcopy(spec)
            trial["constraints"].remove(clause)
            if len(grid_solutions(trial)) == 1:
                spec = trial
        if not min_clues <= len(spec["constraints"]) <= max_clues:
            rejected.append(dict(attempt=attempt, reason="CLUE_BOUNDS"))
            continue
        return dict(spec=spec, canonical_ground_truth=solve_grid(spec),
            latent_fingerprint=alpha_fingerprint(spec),
            task_id=Stream(master_seed, split, block_id, "TASK_ID", item_index, attempt).digest().hex()[:24],
            generation_attempt=attempt, rejected_attempts=rejected,
            private_diagnostics=dict(survivors_before_final=before_final,
                active_implications=sum(c["kind"] == "IMPLIES" for c in spec["constraints"]),
                active_xors=sum(c["kind"] == "XOR" for c in spec["constraints"])))


def verify_task(spec):
    if spec.get("family") == "SYMBOLIC_PIPELINE":
        return symbolic(spec)
    if spec.get("family") == "RULE_GRID":
        return solve_grid(spec)
    raise Failure("GENERATION_FAILURE", "UNSUPPORTED_TASK_FAMILY")
