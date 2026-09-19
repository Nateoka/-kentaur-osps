from copy import deepcopy as cp
import unittest
from mrab_r1.audit import e07_conflict
from mrab_r1.classifier import classify_summary
from mrab_r1.canonical import loads, canonical
from mrab_r1.controller import Controller, prep_path
from mrab_r1.profiles import ProfileStore, scope_of
from mrab_r1.schemas import DESIGN


def initial_profile():
    corpus = loads((DESIGN/"design_checks/schema_specimens.json").read_bytes())
    return cp(next(x["instance"] for x in corpus["specimens"] if x["specimen_id"] == "profile-two-slots"))


def observation(claim, i=1, success=True, action="SOLO", mode=None):
    return dict(episode_id=f"e:{i}", episode_index=i, scope_id=claim["scope_id"],
        task_family=claim["task_family"], difficulty_scope=claim["difficulty_scope"][0],
        context_condition=claim["context_condition"][0], tool_condition=claim["tool_condition"],
        capability_configuration_ref=claim["capability_configuration_ref"],
        execution_mode=mode or claim["execution_modes"][0], history_class="NONEMPTY",
        chosen_action=action, solo_correct=success if action in {"SOLO", "VERIFY"} else None,
        final_correct=True, tool_used=action in {"VERIFY", "DELEGATE"}, cost_units=1 if action in {"VERIFY", "DELEGATE"} else 0,
        outcome="CORRECT", prep_skip_reason=None)


def proposal(claim, status="REVISED", interval=None, refs=None):
    return dict(proposal_id="proposal:1", claim_id=claim["claim_id"], expected_version=claim["version"],
        new_status=status, new_interval=interval if interval is not None else {"lower": .5, "upper": .7},
        new_scope=scope_of(claim), evidence_refs=refs or ["e:1"], restore_version=None, basis="Observed local outcome")


def b3_record(stop=True, probe="NONE"):
    return dict(record_kind="MATRYOSHKA_REFLEXIVE", relevant_self_claim=None,
        observed_mismatch=dict(description="NONE", evidence_refs=[]), candidate_loci=["UNKNOWN"],
        probe_needed=probe != "NONE", probe_type=probe, probe_predictions=[],
        profile_update_status="NO_CHANGE", proposed_new_interval=None, proposed_new_scope=None,
        action="VERIFY", confidence="UNSPECIFIED", stop_reflection=stop, proposal=None, cancel_pending_probe=False)


class RuntimeContractTests(unittest.TestCase):
    def test_R1_E07_HARM_01_counterproductive_missing(self):
        summary = e07_conflict()["input"]
        source = loads((DESIGN/"design_checks/goldens.json").read_bytes())
        summary = cp(next(x["input"] for x in source["summary_cases"] if x["id"] == "WIDE-CI"))
        # Exact new author example: safe accuracy/completion, harmful fixed C2.
        row = summary["comparators"]["B2"]["C2"]
        row.update(n_pairs=8, accuracy_loss=[-.01, .01], completion_loss=[-.01, .01], fixed_ci=[.07, .11], primary_ci=None, point=None, reach=None)
        result = classify_summary(summary)
        self.assertEqual(result["outcome_class"], "COUNTERPRODUCTIVE")
        self.assertTrue(any(f["kind"] == "HARM" and f["comparator"] == "B2" and "C2" in f["conditions"] for f in result["comparator_findings"]))
        self.assertIn("B2:C2:MISSING_CI", result["uncertainty_reasons"])
        self.assertIn("B2:C2:LOW_OR_DIFFERENTIAL_REACH", result["uncertainty_reasons"])

    def test_R1_E07_HARM_01_mixed_missing(self):
        summary = e07_conflict()["input"]
        summary["comparators"]["B4"]["C2"].update(n_pairs=8, accuracy_loss=[-.01,.01], completion_loss=[-.01,.01], fixed_ci=[-.12,-.08], primary_ci=[-.12,-.08], point=-.1, reach=[1,1])
        result = classify_summary(summary)
        self.assertEqual(result["outcome_class"], "MIXED_TRADEOFF")
        self.assertIn("B2:C3:MISSING_CI", result["uncertainty_reasons"])
        self.assertTrue({"HARM", "BENEFIT"} <= {f["kind"] for f in result["comparator_findings"]})

    def test_all_19_goldens_runtime(self):
        for case in loads((DESIGN/"design_checks/goldens.json").read_bytes())["summary_cases"]:
            with self.subTest(id=case["id"]):
                result = classify_summary(case["input"])
                self.assertEqual(result["outcome_class"], case["expected_outcome"])
                for f in case.get("required_findings", []):
                    self.assertTrue(any(all(x.get(k) == v for k,v in f.items()) for x in result["comparator_findings"]))

    def test_PREP_24_paths(self):
        for case in loads((DESIGN/"design_checks/lifecycle_vectors.json").read_bytes())["prep_paths"]:
            with self.subTest(id=case["id"]):
                result = prep_path(**case["input"])
                for k,v in case["expected"].items():
                    self.assertEqual(result[k], v)

    def test_shared_committer_one_sample_allowed(self):
        initial = initial_profile()
        claim = initial["claims"][0]
        results = []
        for actor in ("B2", "B3"):
            store = ProfileStore(initial)
            event = store.commit(proposal(claim), actor, 2, [observation(claim)], 1)
            self.assertEqual(event["validation_status"], "COMMITTED")
            self.assertEqual(event["transition_path"], ["ACTIVE", "QUESTIONED", "REVISED"])
            self.assertEqual(event["after_claim"]["version"], 3)
            results.append(canonical(store.current))
        self.assertEqual(*results)

    def test_commit_rejections_and_local_control(self):
        p = initial_profile()
        c, other = p["claims"]
        cases = []
        stale = proposal(c); stale["expected_version"] = 9; cases.append((stale, "STALE_VERSION"))
        unknown = proposal(c); unknown["claim_id"] = "missing"; cases.append((unknown, "UNKNOWN_CLAIM"))
        future = proposal(c, refs=["e:2"]); cases.append((future, "FUTURE_EVIDENCE"))
        control = proposal(other); cases.append((control, "NO_LOCAL_EVIDENCE"))
        wide = proposal(c); wide["new_scope"]["difficulty_scope"].append("new"); cases.append((wide, "SCOPE_VIOLATION"))
        for prop, reason in cases:
            with self.subTest(reason=reason):
                store = ProfileStore(p)
                event = store.commit(prop, "B3", 2, [observation(c)], 1)
                self.assertIn(reason, event["rejection_codes"])
                self.assertEqual(store.current, p)
        store = ProfileStore(p)
        self.assertEqual(store.commit(proposal(other), "B2", 2, [observation(other)], 1)["validation_status"], "COMMITTED")

    def test_unknown_return_and_restore(self):
        p = initial_profile(); store = ProfileStore(p); c = p["claims"][0]
        q = proposal(c, "UNKNOWN"); q["new_interval"] = None
        self.assertEqual(store.commit(q, "B3", 2, [observation(c)], 1)["validation_status"], "COMMITTED")
        current = store.current["claims"][0]
        q = proposal(current, "REVISED", {"lower":.6,"upper":.8})
        event = store.commit(q, "B3", 3, [observation(c)], 2)
        self.assertEqual(event["stage_snapshots"][0]["status"], "QUESTIONED")
        self.assertIsNotNone(event["stage_snapshots"][0]["estimated_success_interval"])
        self.assertEqual(event["validation_status"], "COMMITTED")

    def test_controller_current_stop_not_cancel_action(self):
        counter = iter(range(1,100)); ctl = Controller(lambda:next(counter))
        key = observation(initial_profile()["claims"][0]); key["execution_mode"] = "PREP_EXECUTED"
        self.assertTrue(ctl.begin(1,key))
        ctl.accept_prep(b3_record(True,"VERIFY_CURRENT"),1,key,[])
        self.assertTrue(ctl.action(1,key,"VERIFY"))
        ctl.feedback(1,key,key,None,True)
        self.assertEqual([e["event_kind"] for e in ctl.probe_events],["DECLARED","ACTION","FEEDBACK"])
        self.assertFalse(ctl.states[key["scope_id"]]["latched"])

    def test_controller_C0_two_observations_restart(self):
        counter = iter(range(1,100)); ctl = Controller(lambda:next(counter))
        key = observation(initial_profile()["claims"][0]); key["execution_mode"] = "PREP_EXECUTED"
        ctl.begin(1,key); ctl.accept_prep(b3_record(),1,key,[])
        ctl.feedback(1,key,key,None)
        key["execution_mode"] = "PREP_SKIPPED"
        self.assertFalse(ctl.begin(2,key))
        ctl.feedback(2,key,key,None)
        self.assertTrue(ctl.begin(3,key))
