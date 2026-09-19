"""One fully scripted 32-episode integration trace, never a pilot model run."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mrab_r1.config import template
from mrab_r1.manifest import build_manifest,verify_manifest,FAMILIES
from mrab_r1.provider import FakeProvider
from mrab_r1.runner import TrajectoryRunner
from mrab_r1.invariants import enforce_trajectory
from mrab_r1.evaluator import evaluate_trajectory
from mrab_r1.replay import replay_trajectory
from mrab_r1.canonical import loads,semantic_sha
from tests.test_runner import reference_cells,scripts
from tests.test_runner import scripted_response
from tests.test_runtime_contracts import b3_record,proposal


def write(path,data):
    with path.open("x",encoding="utf-8") as stream:json.dump(data,stream,ensure_ascii=False,separators=(",",":"))


def main(destination,compound=False):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    config=template();manifest_file=destination/"PILOT_PLAN_FIXTURE.json"
    if manifest_file.exists():manifest=loads(manifest_file.read_bytes())
    elif (ROOT/"verification/long_trace_01/PILOT_PLAN_FIXTURE.json").exists():
        manifest=loads((ROOT/"verification/long_trace_01/PILOT_PLAN_FIXTURE.json").read_bytes());write(manifest_file,manifest)
    else:
        tuples={(f,b):dict(n=3,length=8) if f==FAMILIES[0] else dict(n=4,k=2) for f in FAMILIES for b in ("HIGH","MID")}
        manifest=build_manifest(config,tuples,planned_run="PILOT",offline_fixture=True);write(manifest_file,manifest)
    checked=verify_manifest(manifest,config);print(json.dumps(dict(plan=checked)),flush=True)
    plan=next(t for t in manifest["payload"]["trajectories"] if t["architecture"]=="B3" and t["condition"]=="C2")
    provider=FakeProvider(scripts(manifest,plan));cells=reference_cells(config,plan)
    runner=TrajectoryRunner(config,manifest,plan["trajectory_id"],provider,destination/"SCRIPTED_32_EVENTS.jsonl",cells)
    if compound:
        responses=[]
        for i,task_id in enumerate(plan["task_ids"],1):
            prep=b3_record(False)
            if i in {2,5}:
                earlier=i-1;view=manifest["payload"]["tasks"][plan["task_ids"][earlier-1]]["record"]["task_view"]
                claim=next(c for c in runner.initial_profile["claims"] if c["task_family"]==view["task_family"])
                proposed=proposal(claim,"UNKNOWN",refs=[f"{plan['trajectory_id']}:{earlier}"]);proposed["new_interval"]=None
                prep.update(proposal=proposed,profile_update_status="UNKNOWN",proposed_new_interval=None,
                    proposed_new_scope=proposed["new_scope"],relevant_self_claim=claim["claim_id"])
            responses.append(scripted_response(prep,len(responses)))
            if i==2:
                responses.extend([scripted_response(dict(invalid=True),len(responses)),scripted_response(dict(invalid=True),len(responses)+1)])
            else:
                truth=manifest["payload"]["tasks"][task_id]["record"]["ground_truth"]
                responses.append(scripted_response(dict(action="SOLO",solo_answer=truth,confidence="UNSPECIFIED"),len(responses)))
        provider.responses=tuple(responses)
    result=runner.run()
    if compound:
        assert result["episodes"][1]["update_event"]["validation_status"]=="COMMITTED"
        assert result["episodes"][1]["protocol_status"]=="PROTOCOL_FAILURE"
        assert result["episodes"][2]["agent_input"]["current_profile"]==result["episodes"][1]["action_input_profile"]
        assert all(c["status"]=="UNKNOWN" and c["estimated_success_interval"] is None for c in result["current_profile"]["claims"])
    verified=enforce_trajectory(result,manifest);evaluation=evaluate_trajectory(result)
    write(destination/"SCRIPTED_32_TRAJECTORY.json",result);write(destination/"SCRIPTED_32_CAPTURES.json",provider.captures)
    print(json.dumps(dict(trace=verified,episodes=len(result["episodes"]),calls=len(provider.captures))),flush=True)
    replay=replay_trajectory(config,manifest,plan["trajectory_id"],provider.captures,destination/"SCRIPTED_32_REPLAY_EVENTS.jsonl",cells,result)
    if semantic_sha(evaluation)!=replay["evaluation_sha256"]:raise RuntimeError("Evaluator replay divergence")
    report=dict(status="PASS",artifact_kind="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT",plan=checked,episodes=len(result["episodes"]),
        scenario="COMMIT_ACTION_FAILURE_AND_ALL_UNKNOWN" if compound else "NORMAL_NO_STOP",
        captured_calls=len(provider.captures),trajectory_sha256=semantic_sha(result),evaluation=evaluation,
        replay_trajectory_sha256=replay["trajectory_sha256"],replay_evaluation_sha256=replay["evaluation_sha256"],
        invariants=verified,real_model_calls=0,real_pilot_calls=0)
    write(destination/"SCRIPTED_32_REPORT.json",report)
    print(json.dumps({k:v for k,v in report.items() if k not in {"evaluation","invariants"}}))


if __name__=="__main__":main(sys.argv[1],"--compound" in sys.argv[2:])
