"""Recheck maximum F2 sample and both captured 32-episode traces on current code."""
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mrab_r1.canonical import loads,semantic_sha,raw_sha
from mrab_r1.config import template
from mrab_r1.tasks import generate_grid,verify_task
from mrab_r1.replay import replay_trajectory
from mrab_r1.evaluator import evaluate_trajectory
from mrab_r1.audit import e07_conflict


def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def main():
    tick=time.perf_counter();item=generate_grid("performance","MAIN","maximum",0,n=5,k=3,max_attempts=5)
    assert verify_task(item["spec"])==item["canonical_ground_truth"]
    performance=dict(status="PASS_SINGLE_SAMPLE_NOT_WORST_CASE_BOUND",n=5,k=3,assignment_space=1728000,
        alpha_certificates_upper_bound=720,seconds=time.perf_counter()-tick,clues=len(item["spec"]["constraints"]),
        fingerprint=item["latent_fingerprint"],sample=item)
    dump(ROOT/"verification/F2_MAX_SAMPLE_CURRENT.json",performance)
    dump(ROOT/"verification/E07_CONFLICT_REPRODUCTION.json",e07_conflict())
    source_hashes={p.name:raw_sha(p.read_bytes()) for p in (ROOT/"mrab_r1").glob("*.py")}
    for directory in ("long_trace_01","long_trace_compound"):
        folder=ROOT/"verification"/directory;original=loads((folder/"SCRIPTED_32_TRAJECTORY.json").read_bytes())
        manifest=loads((folder/"PILOT_PLAN_FIXTURE.json").read_bytes());captures=loads((folder/"SCRIPTED_32_CAPTURES.json").read_bytes())
        target=folder/"CURRENT_RUNTIME_REPLAY_EVENTS.jsonl"
        if target.exists():raise RuntimeError("Current replay proof already exists; do not overwrite")
        replay=replay_trajectory(template(),manifest,original["trajectory_id"],captures,target,original["calibration_cells"],original)
        expected=evaluate_trajectory(original)
        assert replay["evaluation_sha256"]==semantic_sha(expected)
        result=dict(status="PASS",source_hashes=source_hashes,episodes=32,trajectory_sha256=replay["trajectory_sha256"],
            replay_trajectory_sha256=replay["trajectory_sha256"],replay_evaluation_sha256=replay["evaluation_sha256"],
            captured_calls=len(captures),real_model_calls=0,real_calibration_runs=0,real_smoke_runs=0,real_pilot_runs=0,
            schema_and_invariants=replay["invariants"])
        dump(folder/"CURRENT_RUNTIME_REPLAY_REPORT.json",result)
        print(json.dumps(dict(trace=directory,status="PASS",calls=len(captures))),flush=True)
    print(json.dumps(dict(status="PASS",f2_max_seconds=performance["seconds"])),flush=True)


if __name__=="__main__":main()
