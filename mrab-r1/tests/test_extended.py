from copy import deepcopy as cp
import unittest
from mrab_r1.schemas import Schemas
from mrab_r1.errors import Failure
from mrab_r1.profiles import ProfileStore,scope_of
from mrab_r1.runner import evidence_before
from mrab_r1.evaluator import addressed_response_metrics,resource_ratio,bootstrap_pairs
from mrab_r1.seed import Stream
from mrab_r1.answers import normalize_answer
from mrab_r1.tasks import verify_task
from mrab_r1.calibration import confirmation_gate
from mrab_r1.config import template,freeze
from tests.test_runtime_contracts import initial_profile,observation,proposal
from tools.check_request_capacity import witness


class ExtendedTests(unittest.TestCase):
    def test_storage_patch_exact_single_removal_and_witness(self):
        patched=Schemas();source=Schemas(False);expected=cp(source.docs)
        del expected[source.ref("episode_record")]["$defs"]["call_usage"]["properties"]["request_bytes"]["maxLength"]
        self.assertEqual(patched.docs,expected)
        data=witness();self.assertGreater(data["request_characters"],20000)
        self.assertLess(data["test_tokenizer_count"],16384)

    def test_F06_C1_preserve_and_F07_F08_gates(self):
        claim=initial_profile()["claims"][0];key=observation(claim)
        key={k:v for k,v in key.items() if k in (*scope_of(claim).keys(),"execution_mode","history_class")}
        for success,interval,expected in [(True,{"lower":.8,"upper":.95},False),(True,{"lower":.25,"upper":.4},True),(False,{"lower":.8,"upper":.95},True)]:
            rows=[observation(claim,i,success) for i in range(1,5)]
            gate=evidence_before(rows,key,interval)
            self.assertEqual(gate["sufficient"],expected)
            if expected:self.assertEqual(gate["direction"],"UPWARD" if success else "DOWNWARD")
        gate=evidence_before([observation(claim,i) for i in range(1,5)],key,{"lower":.8,"upper":.95})
        self.assertAlmostEqual(gate["wrong"],.5538990625)

    def test_I22_earliest_gates_use_only_previous_observations(self):
        from mrab_r1.b4 import KEY_FIELDS
        claim=initial_profile()["claims"][0];f=observation(claim)
        key={k:f[k] for k in (*KEY_FIELDS,"scope_id")};past=[]
        for n in range(11):
            gate=evidence_before(past,key,{"lower":.25,"upper":.4})
            self.assertEqual(gate["n"],n)
            self.assertEqual(gate["sufficient"],n>=4)
            self.assertEqual(gate["solo_support"],n>=10)
            past.append(observation(claim,n+1))

    def test_F09_rollback_versions_history_monotone(self):
        p=initial_profile();store=ProfileStore(p);c=p["claims"][0];f=observation(c)
        event=store.commit(proposal(c),"B2",2,[f],1)
        revised=event["after_claim"]
        restore=proposal(revised,"ACTIVE",c["estimated_success_interval"]);restore["restore_version"]=1
        restored=store.commit(restore,"B2",3,[f],2)
        self.assertEqual(restored["validation_status"],"COMMITTED")
        self.assertEqual(restored["after_claim"]["estimated_success_interval"],c["estimated_success_interval"])
        self.assertEqual(restored["after_claim"]["version"],5);self.assertEqual(len(store.attempts),2)

    def test_F10_scope_strict_subset_and_X03_stale(self):
        p=initial_profile();c=p["claims"][0];c["difficulty_scope"]=["d1","d2"];f=observation(c)
        store=ProfileStore(p);prop=proposal(c,"NARROWED",c["estimated_success_interval"])
        prop["new_scope"]["difficulty_scope"]=["d1"]
        event=store.commit(prop,"B3",2,[f],1)
        self.assertEqual(event["validation_status"],"COMMITTED")
        self.assertEqual(event["after_claim"]["difficulty_scope"],["d1"])
        stale=store.commit(prop,"B3",3,[f],2)
        self.assertIn("STALE_VERSION",stale["rejection_codes"])

    def test_A04_X02_X04_reject_not_mutate(self):
        p=initial_profile();c=p["claims"][0];f=observation(c)
        for code,mutate in [("UNKNOWN_CLAIM",lambda x:x.update(claim_id="absent")),("FUTURE_EVIDENCE",lambda x:x.update(evidence_refs=["e:2"])),("SCOPE_VIOLATION",lambda x:x["new_scope"].update(scope_id="new"))]:
            with self.subTest(code=code):
                store=ProfileStore(p);prop=proposal(c);mutate(prop)
                event=store.commit(prop,"B3",2,[f],1)
                self.assertIn(code,event["rejection_codes"]);self.assertEqual(store.current,p)
                if code=="UNKNOWN_CLAIM":self.assertIsNone(event["before_claim"])

    def test_X05_hidden_blind_and_X01_label_blind(self):
        p=initial_profile();c=p["claims"][0];f=observation(c)
        outputs=[]
        for hidden in ({"condition":"C1","truth":.9},{"condition":"C3","truth":.2}):
            # There is no hidden argument to the production commit service.
            outputs.append(ProfileStore(p).commit(proposal(c),"B3",2,[f],1))
        self.assertEqual(outputs[0],outputs[1])
        self.assertEqual(outputs[0]["validation_status"],"COMMITTED")

    def test_answer_full_order_normalization_and_duplicate_rejection(self):
        spec=dict(family="RULE_GRID",entities=["a","b"],properties=[dict(property_id="p",values=["u","v"])],constraints=[dict(kind="EQ",atom=dict(entity="a",property="p",value="v"))])
        answer=verify_task(spec);reversed_answer=cp(answer);reversed_answer["result"].reverse()
        self.assertEqual(normalize_answer(spec,reversed_answer),answer)
        bad=cp(answer);bad["result"][1]=cp(bad["result"][0])
        with self.assertRaises(Failure):normalize_answer(spec,bad)

    def test_M08_missing_zero_distinct(self):
        self.assertEqual(resource_ratio([(1,0)])["missing_reason"],"DIVISION_BY_ZERO")
        self.assertEqual(resource_ratio([(1,None)])["missing_reason"],"MISSING_RESOURCE")
        self.assertEqual(resource_ratio([(2,4)])["value"],-.5)

    def test_F18_template_reserved_not_runnable(self):
        with self.assertRaises(Failure):freeze(template(),{})
        config=template();config["architectures"].append("B5")
        with self.assertRaises(Failure):freeze(config,{})

    def test_confirmation_20_cells_and_failure_no_retune(self):
        rows=[dict(architecture=a,family=f,band=b,n=200,successes=180 if b=="HIGH" else 124,tuple_sha256="a"*64) for a in ("B0","B1","B2","B3","B4") for f in ("SYMBOLIC_PIPELINE","RULE_GRID") for b in ("HIGH","MID")]
        self.assertEqual(len(confirmation_gate(rows,template())["cells"]),20)
        rows[0]["successes"]=0
        with self.assertRaises(Failure) as caught:confirmation_gate(rows,template())
        self.assertEqual(caught.exception.kind,"CALIBRATION_NOT_FEASIBLE")

    def test_conditional_endpoint_five_pairs_cannot_gain_ci(self):
        pairs=[(dict(condition="C2",stratum="HIGH",target_family="SYMBOLIC_PIPELINE"),{}) for _ in range(5)]
        result=bootstrap_pairs(pairs,Stream("s","MAIN","b","BOOTSTRAP"),lambda _:0,100)
        self.assertIsNone(result["ci"]);self.assertEqual(result["reason"],"LOW_PAIRED_N")


class Scripted32MetricTests(unittest.TestCase):
    def fixture(self,response_at=7,action_change=False):
        claim=initial_profile()["claims"][0];rows=[];gates={}
        for i in range(1,33):
            f=observation(claim,i,success=True,action="DELEGATE" if action_change and i>=response_at else "SOLO")
            e=dict(episode_id=f["episode_id"],episode_index=i,feedback=f,protocol_status="OK")
            rows.append(e);gates[e["episode_id"]]=dict(sufficient=i>=5,direction="UPWARD" if i>=5 else "UNRESOLVED")
        attempts=[] if response_at is None else [dict(validation_status="COMMITTED",effective_episode=response_at,after_claim={**claim,"status":"QUESTIONED"},proposal=dict(evidence_refs=["e:1"],restore_version=None))]
        return rows,attempts,gates

    def test_M05_post_E_response_grace_target_opportunities(self):
        result=addressed_response_metrics(*self.fixture())
        self.assertEqual(result["EVIDENCE_RESPONSE_LATENCY"]["value"],2)
        self.assertFalse(result["EVIDENCE_RESPONSE_LATENCY"]["censored"])
        self.assertEqual(result["UNADDRESSED_MISMATCH_RATE"]["value"],0)

    def test_A07_never_revise_right_censored(self):
        result=addressed_response_metrics(*self.fixture(None))
        self.assertEqual(result["UNADDRESSED_MISMATCH_RATE"]["value"],1)
        self.assertEqual(result["EVIDENCE_RESPONSE_LATENCY"]["value"],27)
        self.assertTrue(result["EVIDENCE_RESPONSE_LATENCY"]["censored"])

    def test_M06_action_vector_and_A05_text_only(self):
        changed=addressed_response_metrics(*self.fixture(7,True))["BEHAVIORAL_UPDATE_ASSOCIATION"]
        self.assertEqual(changed["value"]["SOLO"],-1);self.assertEqual(changed["value"]["DELEGATE"],1)
        self.assertEqual(changed["causal_role"],"NOT_IDENTIFIED")
        unchanged=addressed_response_metrics(*self.fixture())["BEHAVIORAL_UPDATE_ASSOCIATION"]
        self.assertTrue(all(v==0 for v in unchanged["value"].values()))

    def test_early_response_not_negative_time(self):
        result=addressed_response_metrics(*self.fixture(3))
        self.assertEqual(result["EVIDENCE_RESPONSE_LATENCY"]["value"],0)
        self.assertTrue(result["EVIDENCE_RESPONSE_LATENCY"]["early"])

    def test_mode_change_cannot_borrow_old_evidence_response(self):
        rows,attempts,gates=self.fixture()
        for row in rows[16:]:row["feedback"]["execution_mode"]="PREP_SKIPPED"
        results=addressed_response_metrics(rows,attempts,gates)
        skipped=next(d for d in results["EVIDENCE_RESPONSE_LATENCY"]["by_key"] if d["key"]["execution_mode"]=="PREP_SKIPPED")
        self.assertIsNone(skipped["response_opportunity"])
        self.assertEqual(skipped["latency"]["missing_reason"],"RIGHT_CENSORED")


if __name__=="__main__":unittest.main()
