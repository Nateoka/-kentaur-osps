from copy import deepcopy as cp
import unittest
from mrab_r1.evaluator import opportunity,rate,resource_totals,reference_distance_verdict,bootstrap_pairs,evaluate_dataset
from mrab_r1.seed import Stream
from mrab_r1.calibration import calibration_plan,confirmation_gate
from mrab_r1.config import template
from mrab_r1.canonical import loads
from mrab_r1.evaluator import evaluate_trajectory
from pathlib import Path


def row(action,solo,final,status="OK",outcome=None):
    return dict(protocol_status=status,feedback=dict(chosen_action=action,solo_correct=solo,final_correct=final,
        prep_skip_reason=None,outcome=outcome or ("CORRECT" if final else "ABSTAINED" if action=="ABSTAIN" else "INCORRECT")))


class EvaluatorTests(unittest.TestCase):
    def test_M01_four_outcomes(self):
        rows=[row("SOLO",False,False),row("SOLO",True,True),row("DELEGATE",None,True),row("ABSTAIN",None,None)]
        m=opportunity(rows)
        self.assertEqual(m["autonomous_error"]["value"],.25)
        self.assertEqual(m["accuracy"]["value"],.5)
        self.assertEqual(m["completion"]["value"],.75)
        self.assertEqual(rate(1,2)["value"],.5)

    def test_M02_tools_and_zero(self):
        rows=[row("SOLO",True,True),row("VERIFY",True,True),row("DELEGATE",None,True),row("ABSTAIN",None,None)]
        self.assertEqual(opportunity(rows)["tool"]["value"],.5)
        self.assertIsNone(opportunity([])["tool"]["value"])
        self.assertEqual(opportunity([])["tool"]["denominator"],0)

    def test_M03_F16_empty_conditional_retains_fixed_TOOL_ITT(self):
        conditional=opportunity([])["tool"]
        fixed=opportunity([row("DELEGATE",None,True) for _ in range(6)])["tool"]
        self.assertIsNone(conditional["value"]);self.assertEqual(conditional["denominator"],0)
        self.assertEqual(fixed["value"],1);self.assertEqual(fixed["denominator"],6)

    def test_PREP_abnormal_infra_ITT_not_savings(self):
        x=row(None,None,None,"INFRA_FAILURE","INFRA_FAILURE");x["feedback"]["prep_skip_reason"]="INFRA_FAILURE"
        self.assertEqual(opportunity([x])["accuracy"],rate(0,1))
        x["feedback"]["prep_skip_reason"]=None
        self.assertEqual(opportunity([x])["accuracy"]["denominator"],0)

    def test_reference_distance_does_not_measure_live_truth(self):
        result=reference_distance_verdict(.875,.625,180,200)
        self.assertEqual(result["verdict"],"WORSENED")
        self.assertIn("NOT_OPERATIONAL_TRUTH",result["entitlement"])
        unchanged=reference_distance_verdict(.8,.8,180,200)
        self.assertEqual(unchanged["verdict"],"UNCHANGED")

    def test_accounting_no_double_count_and_unknown(self):
        c=dict(phase="PREP",repair_of=None,input_tokens=100,output_tokens=40,reasoning_tokens=10,cached_tokens=20,
            latency_ms=1,monetary_cost=None,output_includes_reasoning=True,
            usage_availability={k:"OBSERVED" for k in ("input_tokens","output_tokens","reasoning_tokens")})
        e=dict(calls=[c],tool_event=None,feedback=dict(prep_skip_reason=None))
        self.assertEqual(resource_totals([e])["EXACT_MODEL_TOKENS"]["value"],140)
        self.assertEqual(resource_totals([e])["REFLECTION_TOKENS"]["value"],140)
        c["output_includes_reasoning"]=False
        self.assertEqual(resource_totals([e])["EXACT_MODEL_TOKENS"]["value"],150)
        c["reasoning_tokens"]=None
        self.assertIsNone(resource_totals([e])["EXACT_MODEL_TOKENS"]["value"])

    def test_seeded_paired_bootstrap(self):
        pairs=[]
        for i in range(8):
            a=dict(condition="C2",stratum="HIGH",target_family="SYMBOLIC_PIPELINE",x=i)
            b={**a,"x":i+1};pairs.append((a,b))
        fn=lambda ps:sum(a["x"]-b["x"] for a,b in ps)/len(ps)
        a=bootstrap_pairs(pairs,Stream("s","MAIN","b","BOOTSTRAP"),fn,200)
        b=bootstrap_pairs(pairs,Stream("s","MAIN","b","BOOTSTRAP"),fn,200)
        self.assertEqual(a,b);self.assertEqual(a["ci"],[-1.,-1.])
        self.assertIsNone(bootstrap_pairs(pairs[:1],Stream("s","MAIN","b","BOOTSTRAP"),fn,200)["ci"])

    def test_plan_4000_6400_no_execution(self):
        p=calibration_plan(template())
        self.assertEqual(len(p["cells"]),20)
        self.assertEqual(p["confirm_measurements"],4000)
        self.assertEqual(p["confirm_primary_calls"],6400)

    def test_A02_A12_32_episode_controlled_arithmetic(self):
        path=Path(__file__).resolve().parents[1]/"verification/long_trace_01/SCRIPTED_32_TRAJECTORY.json"
        source=loads(path.read_bytes())
        # Hand-authored all-VERIFY arithmetic mutation, not a new recorded run.
        # SOLO truth is already explicitly scripted true; changing labels does
        # not grant causal or model-performance entitlement.
        verify=cp(source)
        for e in verify["episodes"]:e["feedback"].update(chosen_action="VERIFY",tool_used=True,cost_units=1)
        report=evaluate_trajectory(verify)["metrics"]
        self.assertEqual(report["OPERATIONAL_POST_SUPPORT_TOOL_RATE"]["value"],1)
        self.assertGreater(report["OPERATIONAL_POST_SUPPORT_TOOL_RATE"]["denominator"],0)
        self.assertEqual(report["STOP_UNFINISHED_RATE"]["value"],1)
        delegate=cp(source)
        for e in delegate["episodes"]:e["feedback"].update(chosen_action="DELEGATE",solo_correct=None,tool_used=True,cost_units=1)
        report=evaluate_trajectory(delegate)["metrics"]
        self.assertIsNone(report["OPERATIONAL_POST_SUPPORT_TOOL_RATE"]["value"])
        self.assertEqual(report["FIXED_TOOL_RATE"]["value"],1)


if __name__=="__main__":unittest.main()
