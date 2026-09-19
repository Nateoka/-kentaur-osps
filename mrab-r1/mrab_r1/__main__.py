"""Explicit offline CLI. No built-in real-provider adapter or implicit network use."""
import argparse
import json
from pathlib import Path
import sys
from .canonical import loads
from .errors import Failure


def read(path):return loads(Path(path).read_bytes())


def output(value,path=None):
    data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8")
    if path:
        with Path(path).open("xb") as stream:stream.write(data)
    else:sys.stdout.buffer.write(data)


def main():
    parser=argparse.ArgumentParser(description="MRAB-R1 Runtime 0.1.1 — offline by default")
    parser.add_argument("--output",help="New JSON output path; existing files are not overwritten")
    sub=parser.add_subparsers(dest="command",required=True)
    design=sub.add_parser("verify-design-contract");design.add_argument("--zip",required=True)
    sub.add_parser("reproduce-design-conflict")
    verification=sub.add_parser("verify-runtime");verification.add_argument("--manifest-plans",action="store_true")
    freeze=sub.add_parser("freeze-config");freeze.add_argument("config");freeze.add_argument("--content-dir",required=True)
    verify=sub.add_parser("verify-task");verify.add_argument("path")
    generator=sub.add_parser("generate-task")
    for name in ("family","seed","split","block"):generator.add_argument("--"+name,required=True)
    generator.add_argument("--item",type=int,required=True);generator.add_argument("--n",type=int,default=3)
    generator.add_argument("--k",type=int,default=1);generator.add_argument("--length",type=int,default=4)
    plan=sub.add_parser("calibration-plan");plan.add_argument("config")
    manifest=sub.add_parser("build-manifest");manifest.add_argument("config");manifest.add_argument("tuples")
    manifest.add_argument("--run",choices=["SMOKE","PILOT"]);manifest.add_argument("--offline-fixture",action="store_true")
    manifest.add_argument("--content-dir");manifest.add_argument("--fingerprint-ledger")
    for command in ("run-trajectory","replay-trajectory"):
        run=sub.add_parser(command);run.add_argument("config");run.add_argument("manifest")
        run.add_argument("--trajectory-id",required=True);run.add_argument("--reference-cells",required=True)
        run.add_argument("--events",required=True);run.add_argument("--offline-script" if command=="run-trajectory" else "--captures",required=True)
        if command=="replay-trajectory":run.add_argument("--expected");run.add_argument("--tool-durations")
    for name in ("evaluate","collect-run"):
        evaluate=sub.add_parser(name);evaluate.add_argument("trajectories");evaluate.add_argument("--seed")
        evaluate.add_argument("--mode",choices=["SCIENTIFIC","DESIGN_TEST_VECTOR_NOT_MODEL_RESULT"],default="SCIENTIFIC")
        evaluate.add_argument("--resource-sidecar");evaluate.add_argument("--manifest");evaluate.add_argument("--config")
        evaluate.add_argument("--event-logs",help="JSON map trajectory_id -> event-log path")
        evaluate.add_argument("--calibration-artifact");evaluate.add_argument("--calibration-events")
    verify_trajectory=sub.add_parser("verify-trajectory");verify_trajectory.add_argument("trajectory");verify_trajectory.add_argument("--manifest");verify_trajectory.add_argument("--config")
    args=parser.parse_args()
    def content(directory):return {p.name:p.read_bytes() for p in Path(directory).iterdir() if p.is_file()} if directory else {}
    try:
        if args.command=="reproduce-design-conflict":
            from .audit import e07_conflict
            result=e07_conflict()
        elif args.command=="verify-design-contract":
            from .verification import verify_design
            result=verify_design(args.zip)
        elif args.command=="verify-runtime":
            from .verification import verify_runtime
            result=verify_runtime(args.manifest_plans)
        elif args.command=="freeze-config":
            from .config import freeze
            result=freeze(read(args.config),content(args.content_dir))
        elif args.command=="verify-task":
            from .tasks import verify_task
            result=verify_task(read(args.path))
        elif args.command=="generate-task":
            from .tasks import generate_symbolic,generate_grid
            common=dict(master_seed=args.seed,split=args.split,block_id=args.block,item_index=args.item,n=args.n)
            if args.family=="SYMBOLIC_PIPELINE":result=generate_symbolic(**common,length=args.length)
            elif args.family=="RULE_GRID":result=generate_grid(**common,k=args.k)
            else:raise Failure("CONFIGURATION_FAILURE","UNKNOWN_TASK_FAMILY")
        elif args.command=="calibration-plan":
            from .calibration import calibration_plan
            result=calibration_plan(read(args.config))
        elif args.command=="build-manifest":
            from .manifest import build_manifest,verify_manifest
            config=read(args.config);tuples={(r["family"],r["band"]):r["difficulty"] for r in read(args.tuples)}
            result=build_manifest(config,tuples,args.run,read(args.fingerprint_ledger) if args.fingerprint_ledger else None,args.offline_fixture,content(args.content_dir))
            verify_manifest(result,config)
        elif args.command=="run-trajectory":
            from .provider import FakeProvider,ProviderResponse
            from .runner import TrajectoryRunner
            from .invariants import enforce_trajectory
            from .evaluator import tool_durations_from_events
            responses=[]
            for row in read(args.offline_script):
                row=dict(row);row["raw_bytes"]=None if row["raw_hex"] is None else bytes.fromhex(row["raw_hex"]);del row["raw_hex"]
                responses.append(ProviderResponse(**row))
            provider=FakeProvider(responses);config=read(args.config);manifest=read(args.manifest)
            runner=TrajectoryRunner(config,manifest,args.trajectory_id,provider,args.events,read(args.reference_cells))
            trajectory=runner.run()
            result=dict(trajectory=trajectory,captures=provider.captures,invariants=enforce_trajectory(trajectory,manifest,config if config["configuration_status"]=="FROZEN" else None),
                artifact_kind="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT",real_model_calls=0,network_calls=0,tool_durations=tool_durations_from_events(runner.store.events))
        elif args.command=="replay-trajectory":
            from .replay import replay_trajectory
            result=replay_trajectory(read(args.config),read(args.manifest),args.trajectory_id,read(args.captures),args.events,
                read(args.reference_cells),read(args.expected) if args.expected else None,recorded_tool_durations=read(args.tool_durations) if args.tool_durations else None)
        elif args.command=="verify-trajectory":
            from .invariants import verify_trajectory
            result=verify_trajectory(read(args.trajectory),read(args.manifest) if args.manifest else None,read(args.config) if args.config else None)
        else:
            from .evaluator import evaluate_dataset
            if args.mode=="SCIENTIFIC" or args.command=="collect-run":
                if not all((args.manifest,args.config,args.event_logs,args.calibration_artifact,args.calibration_events)):
                    raise Failure("INFRA_FAILURE","MANDATORY_SCIENTIFIC_PROVENANCE_MISSING")
                if args.seed is not None:raise Failure("INFRA_FAILURE","ARBITRARY_SCIENTIFIC_BOOTSTRAP_SEED_FORBIDDEN")
            if args.command=="collect-run":
                from .provenance import collect_run_bundle
                result=collect_run_bundle(read(args.trajectories),read(args.event_logs),read(args.manifest),read(args.config),read(args.calibration_artifact),args.calibration_events,scientific=args.mode=="SCIENTIFIC")
                if args.resource_sidecar and read(args.resource_sidecar)!=result["payload"]["tool_durations"]:
                    raise Failure("INFRA_FAILURE","UNBOUND_RESOURCE_SIDECAR")
            else:
                result=evaluate_dataset(read(args.trajectories),args.seed,tool_durations=read(args.resource_sidecar) if args.resource_sidecar else None,
                    planned_manifest=read(args.manifest) if args.manifest else None,frozen_config=read(args.config) if args.config else None,
                    event_logs=read(args.event_logs) if args.event_logs else None,calibration_artifact=read(args.calibration_artifact) if args.calibration_artifact else None,
                    calibration_events=args.calibration_events,mode=args.mode)
        output(result,args.output)
        return 2 if isinstance(result,dict) and result.get("status")=="FAIL" else 0
    except Failure as error:
        output(error.as_dict());return 2
    except (OSError,KeyError,TypeError,ValueError) as error:
        output(dict(kind="CONFIGURATION_FAILURE",code="CLI_INPUT_OR_OUTPUT_ERROR",error_type=type(error).__name__));return 2


if __name__=="__main__":sys.exit(main())
