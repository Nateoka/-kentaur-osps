import json
import unittest
from mrab_r1.calibration import CalibrationEngine,beta_quantile
from mrab_r1.b4 import beta_sf
from mrab_r1.config import template
from mrab_r1.provider import FakeProvider
from mrab_r1.tasks import generate_symbolic,verify_task
from mrab_r1.surface import render
from tests.test_runtime_contracts import b3_record
from tests.test_runner import scripted_response


class CalibrationTests(unittest.TestCase):
    def test_quantile_matches_exact_integer_beta_cdf(self):
        for a,b in [(181,21),(125,77),(1,201),(201,1)]:
            for q in (.025,.975):
                value=beta_quantile(q,a,b)
                self.assertAlmostEqual(float(1-beta_sf(value,a,b)),q,places=11)

    def test_reset_measurements_all_architectures_no_tools_history_profile(self):
        config=template();spec=generate_symbolic("cal-test","CALIBRATION_SEARCH","b",0,n=3,length=8)["spec"]
        view=dict(task_id="opaque",task_family="SYMBOLIC_PIPELINE",scope_id="scope:s",difficulty_scope="d:s",context_condition="ctx:0",spec=spec,surface_text=render(spec,"A"))
        item=dict(task_view=view,ground_truth=verify_task(spec))
        for arch in ("B0","B1","B2","B3","B4"):
            with self.subTest(architecture=arch):
                script=[]
                for i in range(2):
                    if arch in {"B1","B2","B3"}:
                        prep=b3_record(True) if arch=="B3" else dict(record_kind="EXTRA_COMPUTE" if arch=="B1" else "GENERIC_CRITIC",memo="Check.",recommended_action="SOLO",confidence="UNSPECIFIED")
                        if arch=="B2":prep["proposal"]=None
                        script.append(scripted_response(prep,len(script)))
                    script.append(scripted_response(dict(action="SOLO",solo_answer=item["ground_truth"],confidence="UNSPECIFIED"),len(script)))
                provider=FakeProvider(script);events=[]
                engine=CalibrationEngine(config,provider,lambda k,p:events.append((k,p)))
                for i in range(2):
                    record=engine.measurement(item,arch,i)
                    self.assertTrue(record["solo_correct"]);self.assertEqual(record["tool_events"],[])
                self.assertEqual(len(provider.captures),4 if arch in {"B1","B2","B3"} else 2)
                for capture in provider.captures:
                    request=json.loads(bytes.fromhex(capture["request_hex"]));state=request["agent_state"]
                    self.assertIsNone(state["current_profile"]);self.assertEqual(state["recent_episode_history"],[])
                    self.assertEqual(state["evidence_index"],[])
                    self.assertEqual(state["profile_history"],[])


if __name__=="__main__":unittest.main()
