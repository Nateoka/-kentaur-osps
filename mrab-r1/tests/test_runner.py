from copy import deepcopy as cp
import json
from pathlib import Path
import tempfile
import unittest
from mrab_r1.config import template
from mrab_r1.manifest import build_manifest,FAMILIES
from mrab_r1.provider import FakeProvider,ProviderResponse,ReplayProvider
from mrab_r1.runner import TrajectoryRunner
from mrab_r1.canonical import integer_dsl_bytes,semantic_sha
from mrab_r1.schemas import Schemas
from tests.test_runtime_contracts import b3_record
from mrab_r1.invariants import verify_trajectory
from mrab_r1.b4 import Tracker
from mrab_r1.state import key_for
from tests.test_runtime_contracts import proposal
from mrab_r1.evaluator import evaluate_trajectory


def scripted_response(value,index):
    return ProviderResponse(json.dumps(value,separators=(',',':')).encode(),f"fake:{index}",str(index),str(index),
        input_tokens=100,output_tokens=40,cached_tokens=0,reasoning_tokens=None,latency_ms=1)


def reference_cells(config,plan):
    cells=[]
    for family,address in plan["scope_by_family"].items():
        band=plan["target_stratum"] if family==plan["target_family"] else "HIGH"
        cells.append(dict(calibration_key="reference:"+address["scope_id"],architecture=plan["architecture"],band=band,
            scope=dict(scope_id=address["scope_id"],task_family=family,difficulty_scope=[address["difficulty_scope"]],
                context_condition=[address["context_condition"]],tool_condition="SOLO_NO_TOOL",
                capability_configuration_ref=config["capability_configurations"][plan["architecture"]]["configuration_id"],
                execution_modes=config["capability_configurations"][plan["architecture"]]["execution_modes"]),
            successes=180 if band=="HIGH" else 124,n=200,dataset_hash="a"*64))
    return cells


def scripts(manifest,plan,action="SOLO"):
    records=[];tracker=Tracker()
    for index,task_id in enumerate(plan["task_ids"]):
        arch=plan["architecture"]
        if arch=="B4":
            private=manifest["payload"]["tasks"][task_id]["record"]
            key=key_for(private["task_view"],template()["capability_configurations"][arch],"NO_PREP_INTERFACE",index>0)
            action=tracker.opportunity(key)
            tracker.observe(key,private["latent_fingerprint"],action,True if action in {"SOLO","VERIFY"} else None,action=="VERIFY","OK")
            if action in {"DELEGATE","ABSTAIN"}:continue
        if arch in {"B1","B2","B3"}:
            prep=b3_record(False) if arch=="B3" else dict(record_kind="EXTRA_COMPUTE" if arch=="B1" else "GENERIC_CRITIC",memo="Check task.",recommended_action=action,confidence="UNSPECIFIED")
            if arch=="B2":prep["proposal"]=None
            records.append(scripted_response(prep,len(records)))
        answer=manifest["payload"]["tasks"][task_id]["record"]["ground_truth"]
        records.append(scripted_response(dict(action=action,solo_answer=answer if action in {"SOLO","VERIFY"} else None,confidence="UNSPECIFIED"),len(records)))
    return records


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=template()
        cls.tuples={(f,b):({'n':3,'length':8} if f=='SYMBOLIC_PIPELINE' else {'n':4,'k':2}) for f in FAMILIES for b in ['HIGH','MID']}
        cls.manifest=build_manifest(cls.config,cls.tuples,offline_fixture=True)

    def plan(self,architecture):
        return next(t for t in self.manifest["payload"]["trajectories"] if t["architecture"]==architecture and t["condition"]=="C1")

    def run_plan(self,arch,td,action="SOLO",stop_after=2,provider=None,path="events.jsonl"):
        p=self.plan(arch);provider=provider or FakeProvider(scripts(self.manifest,p,action))
        runner=TrajectoryRunner(self.config,self.manifest,p["trajectory_id"],provider,Path(td)/path,reference_cells(self.config,p))
        result=runner.run(stop_after)
        self.assertEqual(verify_trajectory(result,self.manifest)["failures"],[])
        return result,provider

    def test_B0_real_episode_record(self):
        with tempfile.TemporaryDirectory() as td:
            result,provider=self.run_plan("B0",td)
            self.assertEqual(len(result["episodes"]),2)
            self.assertTrue(all(e["feedback"]["final_correct"] for e in result["episodes"]))
            self.assertEqual(result["current_profile"],result["initial_profile"])
            self.assertEqual(len(provider.captures),2)

    def test_B1_B2_exact_one_prep(self):
        for arch in ("B1","B2"):
            with self.subTest(arch=arch),tempfile.TemporaryDirectory() as td:
                result,provider=self.run_plan(arch,td)
                self.assertEqual(len(provider.captures),4)
                self.assertTrue(all(e["execution_context"]["prep_call_count"]==1 for e in result["episodes"]))

    def test_B3_declaration_free_normal_episode(self):
        with tempfile.TemporaryDirectory() as td:
            result,provider=self.run_plan("B3",td)
            self.assertEqual(len(provider.captures),4)
            self.assertTrue(all(e["protocol_status"]=="OK" for e in result["episodes"]))

    def test_VERIFY_seal_then_tool(self):
        with tempfile.TemporaryDirectory() as td:
            result,_=self.run_plan("B0",td,action="VERIFY")
            for episode in result["episodes"]:
                self.assertLess(episode["solo_seal_sequence"],episode["tool_event"]["start_sequence"])
                self.assertTrue(episode["feedback"]["tool_used"])
                self.assertEqual(len(episode["calls"]),1)

    def test_DELEGATE_does_not_supply_solo_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            result,_=self.run_plan("B0",td,action="DELEGATE")
            for e in result["episodes"]:
                self.assertIsNone(e["feedback"]["solo_correct"])
                self.assertFalse(e["evaluator_private"]["informative"])
                self.assertTrue(e["feedback"]["final_correct"])

    def test_ABSTAIN_null_answer_and_no_tool(self):
        with tempfile.TemporaryDirectory() as td:
            result,_=self.run_plan("B0",td,action="ABSTAIN")
            for e in result["episodes"]:
                self.assertIsNone(e["final_answer"])
                self.assertIsNone(e["tool_event"])
                self.assertIsNone(e["feedback"]["final_correct"])

    def test_resume_at_safe_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            first,provider=self.run_plan("B0",td,stop_after=1)
            second,_=self.run_plan("B0",td,stop_after=2,provider=provider)
            self.assertEqual(first["episodes"][0],second["episodes"][0])
            self.assertEqual(len(provider.captures),2)

    def test_full_scripted_B0_trajectory_and_replay(self):
        with tempfile.TemporaryDirectory() as td:
            result,provider=self.run_plan("B0",td,stop_after=None)
            self.assertEqual(result["completion_status"],"COMPLETED")
            self.assertEqual(len(result["episodes"]),12)
            replay=ReplayProvider(provider.captures)
            repeated,_=self.run_plan("B0",td,stop_after=None,provider=replay,path="replay.jsonl")
            replay.assert_consumed()
            self.assertEqual(semantic_sha(result),semantic_sha(repeated))

    def test_B4_full_strong_tracker_no_profile(self):
        with tempfile.TemporaryDirectory() as td:
            result,provider=self.run_plan("B4",td,stop_after=None)
            self.assertEqual(result["completion_status"],"COMPLETED")
            self.assertTrue(all(e["prep_record"] is None and e["action_input_profile"] is None for e in result["episodes"]))
            self.assertEqual(result["episodes"][0]["action_record"]["action"],"VERIFY")

    def test_F14_repair_sees_no_fresh_context(self):
        with tempfile.TemporaryDirectory() as td:
            base=scripts(self.manifest,self.plan("B1"));prep=json.loads(base[0].raw_bytes)
            provider=FakeProvider([scripted_response(dict(wrapped=prep),0),scripted_response(prep,1),*base[1:]])
            result,_=self.run_plan("B1",td,stop_after=1,provider=provider)
            episode=result["episodes"][0]
            self.assertEqual([c["phase"] for c in episode["calls"]],["PREP","REPAIR","ACTION"])
            repair=json.loads(provider.captures[1]["request_hex"] and bytes.fromhex(provider.captures[1]["request_hex"]))
            self.assertEqual(set(repair),{"system","invalid_output","validation_errors","output_schema"})

    def test_F15_second_invalid_no_second_repair(self):
        with tempfile.TemporaryDirectory() as td:
            prep=json.loads(scripts(self.manifest,self.plan("B1"))[0].raw_bytes)
            provider=FakeProvider([scripted_response(dict(wrapped=prep),0),scripted_response(prep,1),scripted_response(dict(bad=True),2)])
            result,_=self.run_plan("B1",td,stop_after=1,provider=provider)
            self.assertEqual(result["episodes"][0]["protocol_status"],"PROTOCOL_FAILURE")
            self.assertEqual(len(provider.captures),3)

    def test_accepted_PREP_timeout_counts_one_no_free_skip(self):
        with tempfile.TemporaryDirectory() as td:
            provider=FakeProvider([ProviderResponse(None,"timeout","0","1",status="TIMEOUT")])
            result,_=self.run_plan("B2",td,stop_after=1,provider=provider)
            e=result["episodes"][0]
            self.assertEqual(e["execution_context"]["prep_call_count"],1)
            self.assertEqual(e["protocol_status"],"PROTOCOL_FAILURE")
            self.assertIsNone(e["feedback"]["final_correct"])

    def test_tool_exception_is_infra_not_agent_error(self):
        with tempfile.TemporaryDirectory() as td:
            plan=self.plan("B0");provider=FakeProvider(scripts(self.manifest,plan,"VERIFY"))
            def failed(_):raise RuntimeError("private text must not leak")
            result=TrajectoryRunner(self.config,self.manifest,plan["trajectory_id"],provider,Path(td)/"events.jsonl",reference_cells(self.config,plan),tool_executor=failed).run()
            self.assertEqual(result["completion_status"],"INFRA_INVALID")
            self.assertIsNone(result["episodes"][0]["feedback"]["solo_correct"])
            self.assertEqual(verify_trajectory(result,self.manifest)["failures"],[])

    def custom_profile_run(self,td,unknown_both=False,fail_after_commit=False,stale_repeat=False):
        plan=self.plan("B2");provider=FakeProvider([])
        runner=TrajectoryRunner(self.config,self.manifest,plan["trajectory_id"],provider,Path(td)/"events.jsonl",reference_cells(self.config,plan))
        records=[];previous_proposal=None
        for i,task_id in enumerate(plan["task_ids"],1):
            prep=dict(record_kind="GENERIC_CRITIC",memo="Local observation.",recommended_action="SOLO",confidence="UNSPECIFIED",proposal=None)
            if i==2 or unknown_both and i==3:
                previous=self.manifest["payload"]["tasks"][plan["task_ids"][i-2]]["record"]["task_view"]
                claim=next(c for c in runner.initial_profile["claims"] if c["task_family"]==previous["task_family"])
                prop=proposal(claim,"UNKNOWN" if unknown_both else "REVISED",refs=[f"{plan['trajectory_id']}:{i-1}"])
                if unknown_both:prop["new_interval"]=None
                prep["proposal"]=prop
                previous_proposal=cp(prop)
            if i==3 and stale_repeat:prep["proposal"]=cp(previous_proposal)
            records.append(scripted_response(prep,len(records)))
            if i==2 and fail_after_commit:
                records.extend([scripted_response(dict(invalid=True),len(records)),scripted_response(dict(invalid=True),len(records)+1)])
            else:
                truth=self.manifest["payload"]["tasks"][task_id]["record"]["ground_truth"]
                records.append(scripted_response(dict(action="SOLO",solo_answer=truth,confidence="UNSPECIFIED"),len(records)))
        provider.responses=tuple(records)
        result=runner.run()
        self.assertEqual(verify_trajectory(result,self.manifest)["failures"],[])
        return result,provider

    def test_commit_survives_failed_ACTION_and_replay(self):
        with tempfile.TemporaryDirectory() as td:
            result,provider=self.custom_profile_run(td,fail_after_commit=True)
            e=result["episodes"][1]
            self.assertEqual(e["update_event"]["validation_status"],"COMMITTED")
            self.assertEqual(e["protocol_status"],"PROTOCOL_FAILURE")
            self.assertEqual(result["episodes"][2]["agent_input"]["current_profile"],e["action_input_profile"])
            self.assertNotEqual(result["current_profile"],result["initial_profile"])
            from mrab_r1.replay import replay_trajectory
            p=self.plan("B2")
            repeated=replay_trajectory(self.config,self.manifest,p["trajectory_id"],provider.captures,Path(td)/"replay.jsonl",reference_cells(self.config,p),result)
            self.assertEqual(repeated["trajectory_sha256"],semantic_sha(result))

    def test_A01_A03_M07_all_UNKNOWN_not_perfect_calibration(self):
        with tempfile.TemporaryDirectory() as td:
            result,_=self.custom_profile_run(td,unknown_both=True)
            self.assertTrue(all(c["status"]=="UNKNOWN" and c["estimated_success_interval"] is None for c in result["current_profile"]["claims"]))
            # Explicit descriptive slice of already logged all-UNKNOWN states;
            # not a replacement benchmark trajectory or inferential sample.
            descriptive=cp(result);descriptive["episodes"]=descriptive["episodes"][3:]
            report=evaluate_trajectory(descriptive)
            self.assertIsNone(report["metrics"]["REFERENCE_PROFILE_DISTANCE"]["value"])
            self.assertEqual(report["metrics"]["MAP_AVAILABILITY"]["value"],0)
            self.assertEqual(report["metrics"]["CONTROL_CLAIMS_TOUCHED_PROPORTION"]["value"],1)

    def test_A09_hidden_canaries_leave_B4_requests_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            plan=self.plan("B4");base=FakeProvider(scripts(self.manifest,plan))
            original=TrajectoryRunner(self.config,self.manifest,plan["trajectory_id"],base,Path(td)/"base.jsonl",reference_cells(self.config,plan)).run(2)
            changed=cp(self.manifest);selected=next(p for p in changed["payload"]["trajectories"] if p["trajectory_id"]==plan["trajectory_id"])
            selected["condition"]="C3" # No visible profile in B4: same public stimulus.
            selected["private_canaries"]={field:"CANARY_HIDDEN_"+field for field in ("ids","labels","strings","schemas","errors","profile_metadata","history","probes","receipts")}
            for task in changed["payload"]["tasks"].values():
                task["record"]["private_canaries"]=cp(selected["private_canaries"])
                from mrab_r1.canonical import raw_sha
                task["sha256"]=raw_sha(integer_dsl_bytes(task["record"]))
            changed["sha256"]=semantic_sha(changed["payload"])
            cells=reference_cells(self.config,plan)
            for c in cells:c["successes"]=3;c["dataset_hash"]="b"*64
            replay=FakeProvider(scripts(changed,selected))
            mutated=TrajectoryRunner(self.config,changed,plan["trajectory_id"],replay,Path(td)/"mutated.jsonl",cells).run(2)
            self.assertEqual([c["request_hex"] for c in base.captures],[c["request_hex"] for c in replay.captures])
            self.assertEqual([e["feedback"] for e in original["episodes"]],[e["feedback"] for e in mutated["episodes"]])
            for captured in replay.captures:self.assertNotIn(b"CANARY_HIDDEN",bytes.fromhex(captured["request_hex"]))

    def test_M04_rejected_attempt_not_numeric_distance_denominator(self):
        with tempfile.TemporaryDirectory() as td:
            result,_=self.custom_profile_run(td,stale_repeat=True)
            self.assertEqual([e["validation_status"] for e in result["profile_history"]],["COMMITTED","REJECTED"])
            report=evaluate_trajectory(result)["metrics"]
            self.assertEqual(report["REFERENCE_DISTANCE_WORSENING_RATE"]["value"],1)
            self.assertEqual(report["REFERENCE_DISTANCE_WORSENING_RATE"]["denominator"],1)
            self.assertEqual(report["SCOPE_ERROR_RATE"]["denominator"],2)
            self.assertEqual(report["SCOPE_ERROR_RATE"]["numerator"],0)

    def test_F12_wrong_VERIFY_remains_informative_failure(self):
        with tempfile.TemporaryDirectory() as td:
            p=self.plan("B0");records=scripts(self.manifest,p,"VERIFY");action=json.loads(records[0].raw_bytes)
            answer=action["solo_answer"]
            if answer["family"]=="SYMBOLIC_PIPELINE":answer["result"][0]+=1
            else:
                a,b=answer["result"][:2]
                a["assignments"][0]["value_id"],b["assignments"][0]["value_id"]=b["assignments"][0]["value_id"],a["assignments"][0]["value_id"]
            records[0]=scripted_response(action,0)
            result,_=self.run_plan("B0",td,stop_after=1,provider=FakeProvider(records))
            e=result["episodes"][0]
            self.assertFalse(e["feedback"]["solo_correct"]);self.assertTrue(e["feedback"]["final_correct"])
            self.assertTrue(e["evaluator_private"]["informative"])


if __name__=="__main__":unittest.main()
