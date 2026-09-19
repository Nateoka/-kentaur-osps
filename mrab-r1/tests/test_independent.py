"""Independent authored assertions; not model results or a complete runtime suite."""
from copy import deepcopy as cp
from itertools import permutations, product
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from mrab_r1 import DESIGN_SHA256
from mrab_r1.b4 import Tracker, KEY_FIELDS, beta_sf, choose_action
from mrab_r1.canonical import canonical, integer_dsl_bytes, loads, raw_sha, semantic_sha
from mrab_r1.errors import Failure
from mrab_r1.provider import FakeProvider, ProviderResponse, ReplayProvider
from mrab_r1.schemas import BASE, DESIGN, Schemas
from mrab_r1.seed import Stream
from mrab_r1.storage import EventStore, read_events
from mrab_r1.tasks import (alpha_fingerprint, generate_grid, generate_symbolic,
    grid_solutions, solve_grid, symbolic, validate_generated_symbolic)


def fold_reference(spec):
    """Separately written immutable fold, never calls production interpreter."""
    state = tuple(spec["initial"])
    for op in spec["operations"]:
        name = op["op"]
        if name == "ROTATE":
            count = op["steps"] % len(state)
            state = state[-count:] + state[:-count] if count else state
        elif name == "SWAP":
            a, b = op["left"], op["right"]
            state = tuple(state[b] if j == a else state[a] if j == b else x for j, x in enumerate(state))
        else:
            p = op["index"]
            old = state[p]
            if name == "ADD":
                new = old + op["value"]
            elif name == "MULTIPLY":
                new = old * op["value"]
            else:
                new = old - (old // op["modulus"]) * op["modulus"]
            state = state[:p] + (new,) + state[p+1:]
    return list(state)


def exhaustive_grid_reference(spec):
    """Full assignment enumeration + independent Boolean implementation, n<=3."""
    if len(spec["entities"]) > 3:
        raise ValueError("Bounded independent verifier")
    solutions = []
    for choices in product(*(list(permutations(p["values"])) for p in spec["properties"])):
        table = {(entity, prop["property_id"]): values[i] for prop, values in zip(spec["properties"], choices)
                 for i, entity in enumerate(spec["entities"])}
        valid = True
        for clause in spec["constraints"]:
            def truth(a):
                return table[a["entity"], a["property"]] == a["value"]
            kind = clause["kind"]
            if kind == "EQ":
                valid = truth(clause["atom"])
            elif kind == "NEQ":
                valid = not truth(clause["atom"])
            elif kind == "IMPLIES":
                valid = (not truth(clause["left"])) or truth(clause["right"])
            else:
                valid = int(truth(clause["left"])) + int(truth(clause["right"])) == 1
            if not valid:
                break
        if valid:
            solutions.append({p["property_id"]: tuple(table[e, p["property_id"]] for e in spec["entities"]) for p in spec["properties"]})
    return solutions


def sample_grid(n=2, k=1):
    return dict(family="RULE_GRID", entities=[f"e{i}" for i in range(n)],
        properties=[dict(property_id=f"a{j}", values=[f"v{i}" for i in range(n)]) for j in range(k)], constraints=[])


def eq(e, v, p="a0"):
    return dict(kind="EQ", atom=dict(entity=e, property=p, value=v))


class CoreTests(unittest.TestCase):
    def test_strict_json(self):
        invalid = [b'{"a":1,"a":2}', b'NaN', b'Infinity', b'1e999', b'9007199254740993',
                   b'"\\ud800"', b'\xff', b'{} trailing', b'```json\n{}\n```']
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(Failure):
                loads(raw)
        self.assertEqual(loads(b'{"x":null,"b":false}'), {"x": None, "b": False})

    def test_jcs_number_vectors(self):
        # RFC 8785 native ECMAScript representation, not Python repr rounding.
        numbers = [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27, -0.0, 1e-6, 1e-7]
        self.assertEqual(canonical(numbers), b'[333333333.3333333,1e+30,4.5,0.002,1e-27,0,0.000001,1e-7]')

    def test_jcs_utf16_and_numeric_keys(self):
        self.assertEqual(canonical({"2": 2, "10": 10, "1": 1}), b'{"1":1,"10":10,"2":2}')
        self.assertEqual(canonical({"\ue000": 1, "\U0001f600": 2}).decode(), '{"\U0001f600":2,"\ue000":1}')

    def test_jcs_semantic_raw_separation(self):
        a, b = b'{"p":0.80}', b'{ "p": 0.8 }'
        self.assertNotEqual(raw_sha(a), raw_sha(b))
        self.assertEqual(semantic_sha(loads(a)), semantic_sha(loads(b)))

    def test_seed_exact_preimage(self):
        r = Stream("seed", "MAIN", "b", "TASK", 7, 2)
        expected = b'["MRAB-R1","R1_0.1_DESIGN_PATCH_0.2.1","seed","MAIN","b","TASK",7,2,0,null,null]'
        self.assertEqual(r.digest(), hashlib.sha256(expected).digest())

    def test_seed_domains_and_reproducibility(self):
        digests = {Stream("seed", split, "b", stream).digest() for split in ["MAIN", "TRANSFER", "CALIBRATION_SEARCH", "CALIBRATION_CONFIRM"]
                   for stream in ["TASK", "TASK_ID", "FAMILY_ORDER", "SURFACE", "PROFILE", "BOOTSTRAP"]}
        self.assertEqual(len(digests), 24)
        a, b = Stream("s", "MAIN", "b", "TASK"), Stream("s", "MAIN", "b", "TASK")
        self.assertEqual(a.shuffle(range(100)), b.shuffle(range(100)))
        for _ in range(100):
            self.assertTrue(2 <= a.randint(2, 11) <= 11)

    def test_seed_rejection_sampling(self):
        r = Stream("s", "MAIN", "b", "TASK")
        r.words = [2**32-1, 7]
        self.assertEqual(r.randint(0, 9), 7)
        self.assertEqual(r.words, [])

    def test_seed_invalid_domains(self):
        for kwargs in [dict(split="TEST"), dict(stream="SECRET"), dict(architecture="B3"), dict(item_index=-1)]:
            args = dict(master_seed="s", split="MAIN", block_id="b", stream="TASK")
            args.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(Failure):
                Stream(**args)

    def test_fake_replay_bytes_and_metadata(self):
        result = ProviderResponse(b'{}', "fake:1", "t0", "t1", input_tokens=10)
        fake = FakeProvider([result])
        self.assertEqual(fake.invoke(b'{"q":1}', {"phase": "ACTION"}), result)
        replay = ReplayProvider(fake.captures)
        self.assertEqual(replay.invoke(b'{"q":1}', {"phase": "ACTION"}), result)
        replay.assert_consumed()
        self.assertIsNone(result.reasoning_tokens)
        self.assertEqual(fake.network_calls, 0)

    def test_replay_rejects_request_mutation(self):
        fake = FakeProvider([ProviderResponse(None, "f", "0", "1", status="TIMEOUT")])
        fake.invoke(b'{}', {})
        with self.assertRaises(Failure):
            ReplayProvider(fake.captures).invoke(b'{ }', {})

    def test_replay_rejects_response_mutation(self):
        fake = FakeProvider([ProviderResponse(b'{}', "f", "0", "1")])
        fake.invoke(b'{}', {})
        fake.captures[0]["response"]["raw_hex"] = b'[]'.hex()
        with self.assertRaises(Failure):
            ReplayProvider(fake.captures).invoke(b'{}', {})

    def test_store_reopen_and_hash_chain(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"events.jsonl"
            with EventStore(path) as store:
                original = {"p": .8}
                event = store.append("SNAPSHOT", original)
                original["p"] = .1
                self.assertEqual(event["payload"]["p"], .8)
                with self.assertRaises(Failure):
                    EventStore(path)
            with EventStore(path) as store:
                self.assertEqual(store.append("NEXT", {})["sequence"], 2)
            self.assertEqual(len(read_events(path)), 2)

    def test_store_detects_mutation_and_truncation(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"events.jsonl"
            with EventStore(path) as store:
                store.append("A", {"value": 1})
            raw = path.read_bytes()
            path.write_bytes(raw.replace(b'"value":1', b'"value":2'))
            with self.assertRaises(Failure):
                read_events(path)
            path.write_bytes(raw[:-1])
            with self.assertRaises(Failure):
                read_events(path)


class TaskTests(unittest.TestCase):
    def test_F01_hand_vector(self):
        spec = dict(family="SYMBOLIC_PIPELINE", initial=[-3, 4, 1], operations=[
            dict(op="ADD", index=0, value=2), dict(op="MULTIPLY", index=1, value=-2),
            dict(op="SWAP", left=0, right=2), dict(op="ROTATE", steps=1), dict(op="MOD", index=2, modulus=5)])
        self.assertEqual(symbolic(spec)["result"], [-1, 1, 2])
        self.assertEqual(fold_reference(spec), [-1, 1, 2])

    def test_F02_invalid_tasks(self):
        for operation in [dict(op="ADD", index=3, value=1), dict(op="MOD", index=0, modulus=0), dict(op="SWAP", left=1, right=1), dict(op="ROTATE", steps=3)]:
            with self.subTest(operation=operation), self.assertRaises(Failure):
                symbolic(dict(family="SYMBOLIC_PIPELINE", initial=[1, 2, 3], operations=[operation]))
        with self.assertRaises(Failure):
            symbolic(dict(family="SYMBOLIC_PIPELINE", initial=[20, 20], operations=[dict(op="MULTIPLY", index=0, value=3)]*20))

    def test_F1_independent_random_vectors(self):
        for i in range(40):
            item = generate_symbolic("seed", "MAIN", "crosscheck", i, n=2+i%7, length=1+i%40)
            self.assertEqual(item["canonical_ground_truth"]["result"], fold_reference(item["spec"]))

    def test_F1_cancellation_filters(self):
        for ops in [[dict(op="ROTATE", steps=1), dict(op="ROTATE", steps=-1)],
                    [dict(op="ADD", index=0, value=2), dict(op="ADD", index=0, value=-2)],
                    [dict(op="SWAP", left=0, right=1), dict(op="SWAP", left=1, right=0)]]:
            with self.subTest(ops=ops), self.assertRaises(Failure):
                validate_generated_symbolic(dict(family="SYMBOLIC_PIPELINE", initial=[1, 2, 3], operations=ops + [dict(op="MOD", index=0, modulus=5)]))

    def test_F1_final_identity(self):
        with self.assertRaises(Failure) as caught:
            validate_generated_symbolic(dict(family="SYMBOLIC_PIPELINE", initial=[1, 2], operations=[dict(op="MOD", index=0, modulus=5)]))
        self.assertEqual(caught.exception.code, "UNCHANGED_FINAL_VECTOR")

    def test_F1_cyclic_metamorphic(self):
        for i in range(8):
            original = generate_symbolic("s", "MAIN", "m", i, n=5, length=20)["spec"]
            rotated = cp(original)
            rotated["initial"] = original["initial"][-1:] + original["initial"][:-1]
            for op in rotated["operations"]:
                for key in ("index", "left", "right"):
                    if key in op:
                        op[key] = (op[key]+1) % 5
            expected = symbolic(original)["result"]
            self.assertEqual(symbolic(rotated)["result"], expected[-1:] + expected[:-1])

    def test_F1_arbitrary_permutation_not_symmetry(self):
        original = dict(family="SYMBOLIC_PIPELINE", initial=[1, 2, 3], operations=[dict(op="ROTATE", steps=1)])
        renamed = cp(original)
        renamed["initial"] = [2, 1, 3]
        actual = symbolic(renamed)["result"]
        truth = symbolic(original)["result"]
        self.assertNotEqual(actual, [truth[1], truth[0], truth[2]])

    def test_F03_unique(self):
        grid = sample_grid()
        grid["constraints"] = [eq("e0", "v1")]
        self.assertEqual(solve_grid(grid)["result"], [dict(entity_id="e0", assignments=[dict(property_id="a0", value_id="v1")]), dict(entity_id="e1", assignments=[dict(property_id="a0", value_id="v0")])])

    def test_F04_ambiguous(self):
        with self.assertRaises(Failure) as caught:
            solve_grid(sample_grid())
        self.assertEqual(caught.exception.kind, "AMBIGUOUS_TASK")

    def test_F05_unsat(self):
        grid = sample_grid()
        grid["constraints"] = [eq("e0", "v0"), {**eq("e0", "v0"), "kind": "NEQ"}]
        with self.assertRaises(Failure) as caught:
            solve_grid(grid)
        self.assertEqual(caught.exception.kind, "UNSAT_TASK")

    def test_F2_independent_exhaustive_crosscheck(self):
        for n in (2, 3):
            for k in (1, 2, 3):
                grid = sample_grid(n, k)
                atoms = [dict(entity=e, property=p["property_id"], value=v) for e in grid["entities"] for p in grid["properties"] for v in p["values"]]
                cases = [[dict(kind=kind, atom=a)] for kind in ("EQ", "NEQ") for a in atoms]
                cases += [[dict(kind=kind, left=a, right=b)] for kind in ("IMPLIES", "XOR") for a, b in zip(atoms, reversed(atoms))]
                cases += [[], [eq("e0", "v0"), {**eq("e0", "v0"), "kind": "NEQ"}]]
                for constraints in cases:
                    grid["constraints"] = constraints
                    self.assertEqual(grid_solutions(grid, limit=None), exhaustive_grid_reference(grid))

    def test_F2_generator_and_irredundancy(self):
        for i in range(3):
            item = generate_grid("seed", "MAIN", "g", i, n=3, k=2, max_attempts=20)
            grid = item["spec"]
            self.assertEqual(len(exhaustive_grid_reference(grid)), 1)
            for j in range(len(grid["constraints"])):
                reduced = cp(grid)
                reduced["constraints"].pop(j)
                self.assertEqual(len(grid_solutions(reduced)), 2)

    def test_X09_alpha_and_conjunction(self):
        grid = sample_grid(3, 2)
        grid["constraints"] = [eq("e0", "v2", "a0"), eq("e1", "v0", "a0"), eq("e0", "v1", "a1"), eq("e2", "v2", "a1")]
        renamed = cp(grid)
        em = {"e0": "z", "e1": "x", "e2": "y"}
        pm = {"a0": "b", "a1": "a"}
        vm = {"a0": {"v0": "p", "v1": "r", "v2": "q"}, "a1": {"v0": "q", "v1": "p", "v2": "r"}}
        renamed["entities"] = [em[e] for e in reversed(grid["entities"])]
        renamed["properties"] = [dict(property_id=pm[p["property_id"]], values=[vm[p["property_id"]][v] for v in reversed(p["values"])]) for p in reversed(grid["properties"])]
        for clause in renamed["constraints"]:
            a = clause["atom"]
            a.update(entity=em[a["entity"]], value=vm[a["property"]][a["value"]], property=pm[a["property"]])
        renamed["constraints"].reverse()
        self.assertEqual(alpha_fingerprint(grid), alpha_fingerprint(renamed))

    def test_generator_reproducible_and_private_envelope(self):
        a = generate_symbolic("seed", "MAIN", "b", 1)
        self.assertEqual(a, generate_symbolic("seed", "MAIN", "b", 1))
        b = generate_symbolic("seed", "TRANSFER", "b", 1)
        self.assertNotEqual(a["task_id"], b["task_id"])
        self.assertNotIn("split", a["spec"])
        self.assertNotIn("canonical_ground_truth", a["spec"])


class ContractTests(unittest.TestCase):
    def test_all_frozen_schema_specimens(self):
        registry = Schemas()
        corpus = loads((DESIGN/"design_checks/schema_specimens.json").read_bytes())
        for specimen in corpus["specimens"]:
            with self.subTest(id=specimen.get("specimen_id", specimen.get("id"))):
                uri = specimen.get("schema_uri", specimen.get("schema"))
                if not uri.startswith("https://"):
                    uri = BASE + uri
                self.assertEqual(not bool(registry.errors(specimen["instance"], uri)), specimen["expected_schema_valid"])

    def test_five_immutable_schemas(self):
        registry = Schemas()
        self.assertEqual(len(registry.docs), 5)
        config = loads((DESIGN/"r1_config.default.json").read_bytes())
        self.assertEqual(registry.errors(config, registry.ref("config")), [])

    def test_public_reachable_bundles(self):
        registry = Schemas()
        for name in ("b1", "b2", "b3"):
            bundle = registry.public_bundle(registry.ref("reflexive_record", name))
            text = json.dumps(bundle)
            for forbidden in ("calibration_bands", "master_seed", "target_claim", "evaluator_private", '"description": "'):
                self.assertNotIn(forbidden, text)
            if name == "b2":
                self.assertNotIn("candidate_loci", text)
                self.assertNotIn("stop_reflection", text)

    def test_error_sanitization(self):
        registry = Schemas()
        errors = registry.errors({"secret": "PRIVATE_CANARY"}, registry.ref("config", "action_record"))
        self.assertTrue(errors)
        self.assertNotIn("PRIVATE_CANARY", json.dumps(errors))
        self.assertTrue(all(set(e) == {"code", "pointer"} for e in errors))

    def test_external_reference_rejected_offline(self):
        with self.assertRaises(Failure):
            Schemas().public_bundle("https://external.invalid/secret.json")

    def test_B4_21_goldens(self):
        goldens = loads((DESIGN/"design_checks/goldens.json").read_bytes())
        for case in goldens["b4_policy_cases"]:
            with self.subTest(id=case["id"]):
                self.assertEqual(choose_action(**case["input"]), case["expected"])

    def test_X11_B4_counts_and_X10_dedup(self):
        tracker = Tracker()
        key = dict(zip(KEY_FIELDS, ["SYMBOLIC_PIPELINE", "d", "c", "SOLO_NO_TOOL", "configuration:4", "NO_PREP_INTERFACE", "NONEMPTY"]))
        self.assertEqual(tracker.opportunity(key), "VERIFY")
        self.assertTrue(tracker.observe(key, "fp1", "VERIFY", False, seal_precedes_tool=True))
        self.assertFalse(tracker.observe(key, "fp2", "DELEGATE", None))
        self.assertFalse(tracker.observe(key, "fp1", "SOLO", True))
        self.assertFalse(tracker.observe(key, "fp3", "VERIFY", True, seal_precedes_tool=False))
        cell = next(iter(tracker.cells.values()))
        self.assertEqual((cell["successes"], cell["failures"]), (0, 1))
        other = {**key, "history_class": "EMPTY"}
        tracker.opportunity(other)
        self.assertEqual(len(tracker.cells), 2)

    def test_beta_4_2_exact(self):
        self.assertEqual(float(beta_sf("0.4", 4, 2)), .91296)
        self.assertEqual(float(beta_sf("0.8", 4, 2)), .26272)


if __name__ == "__main__":
    unittest.main()
