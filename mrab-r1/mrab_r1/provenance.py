"""Verified capture boundary. Hash chains prove consistency, not human authenticity.

The external event-head / artifact hashes must be retained by the run custodian.
No editable loose call record, sidecar, or 'validated: true' flag is authoritative.
"""
from copy import deepcopy as cp
import math
from .canonical import semantic_sha, raw_sha
from .errors import Failure
from .storage import read_events
from .seed import Stream

TEST_VECTOR="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT"


def require(ok, code):
    if not ok:raise Failure("INFRA_FAILURE",code)


def verify_calls(events, calls, config, *, architecture, split, block_id, item_index):
    requests={};responses={};usages={}
    for event in events:
        kind,p=event["kind"],event["payload"]
        target={"CALL_REQUEST":requests,"CALL_RESPONSE":responses,"CALL_USAGE":usages}.get(kind)
        if target is not None:
            require(p["call_id"] not in target,"DUPLICATE_CAPTURE_CALL")
            target[p["call_id"]]=p
    require(len(calls)==len(usages) and {c["call_id"] for c in calls}==set(usages),"CALL_USAGE_SET_MISMATCH")
    # A pre-accept adapter failure may have a request but no usage. It cannot
    # silently supply fabricated resource measurements.
    rejected={e["payload"]["call_id"] for e in events if e["kind"]=="CALL_NOT_ACCEPTED"}
    require(set(requests)==set(usages)|rejected and set(responses)==set(usages),"UNPAIRED_CALL_CAPTURE")
    for call in calls:
        cid=call["call_id"];request=requests[cid];response=responses[cid]
        require(call==usages[cid],"CALL_USAGE_CHAIN_MISMATCH")
        require(response.get("resource_observations")=={k:call[k] for k in ("input_tokens","output_tokens","reasoning_tokens","cached_tokens","latency_ms")},"CALL_RESOURCE_RESPONSE_MISMATCH")
        raw=bytes.fromhex(request["request_hex"])
        require(raw==call["request_bytes"].encode("utf-8") and raw_sha(raw)==request["request_sha256"]==call["input_sha256"],"CALL_REQUEST_BYTES_MISMATCH")
        output=None if response["raw_hex"] is None else bytes.fromhex(response["raw_hex"])
        require((None if output is None else raw_sha(output))==call["output_sha256"],"CALL_OUTPUT_BYTES_MISMATCH")
        if call["visible_output"] is not None:
            require(output==call["visible_output"].encode("utf-8"),"VISIBLE_OUTPUT_MISMATCH")
        require(call["model_revision"]==config["model_configuration"]["model_revision"],"CALL_MODEL_IDENTITY")
        rng=Stream(config["master_seed"],split,block_id,"MODEL",item_index,
                   architecture=architecture,phase=call["phase"])
        cc=request["call_config"]
        require(cc["seed_digest"]==rng.digest().hex() and cc["sampling_seed"]==rng.randint(0,2**32-1),"CALL_SEED_PROVENANCE")
        require(cc["phase"]==call["phase"] and cc["repair_of"]==call["repair_of"],"CALL_PHASE_PROVENANCE")
        cap=config["budgets"]["repair_output_tokens" if call["phase"]=="REPAIR" else "prep_output_tokens" if call["phase"]=="PREP" else "action_output_tokens"]
        require(cc["max_output_tokens"]==cap and cc["timeout_seconds"]==config["timeouts"]["model_call_seconds"] and cc["temperature"]==config["model_configuration"]["temperature"] and cc["top_p"]==config["model_configuration"]["top_p"],"CALL_CONFIGURATION_DRIFT")


def collect_trajectory(trajectory, event_path, manifest, config, artifact,
                       calibration_events, *, scientific=True):
    from .calibration_artifact import verify_artifact
    verify_artifact(artifact,config,calibration_events,scientific=scientific)
    return _collect_trajectory(trajectory,event_path,manifest,config,artifact,scientific=scientific)


def _collect_trajectory(trajectory,event_path,manifest,config,artifact,*,scientific):
    from .invariants import enforce_trajectory
    from .calibration_artifact import materialize_reference_cells
    enforce_trajectory(trajectory,manifest,config)
    events=read_events(event_path)
    require(bool(events) and events[0]["kind"]=="RUN_START","RUN_START_REQUIRED")
    start=events[0]["payload"]
    plan=next(t for t in manifest["payload"]["trajectories"] if t["trajectory_id"]==trajectory["trajectory_id"])
    cells=materialize_reference_cells(artifact,config,plan)
    require(trajectory["calibration_cells"]==cells==start["reference_cells"],"REFERENCE_CELLS_CHAIN_MISMATCH")
    require(start["config_sha256"]==semantic_sha(config) and start["manifest_sha256"]==manifest["sha256"] and start["trajectory_id"]==trajectory["trajectory_id"],"RUN_START_IDENTITY")
    require(start.get("calibration_artifact_sha256")==artifact["sha256"] and start.get("reference_cells_sha256")==semantic_sha(cells),"RUN_CALIBRATION_IDENTITY")
    require(start.get("runtime_identity")==config["runtime_identity"],"RUN_RUNTIME_IDENTITY")
    require(start.get("provider_identity")==provider_identity(config),"RUN_PROVIDER_IDENTITY")
    if scientific:
        require(start.get("result_kind")=="MODEL_RUN" and start.get("provider_kind") not in {None,"FAKE","REPLAY"},"TEST_VECTOR_NOT_SCIENTIFIC_DATA")
        require(manifest["payload"]["result_kind"]=="SEALED_EXPERIMENT_PLAN_NOT_RESULT","TEST_PLAN_NOT_SCIENTIFIC_DATA")
    require(events[-1]["kind"]=="CHECKPOINT","UNSEALED_EPISODE_TAIL")
    checkpoint=events[-1]["payload"]
    require(checkpoint.get("trajectory")==trajectory,"TRAJECTORY_CHECKPOINT_MISMATCH")
    records=[e["payload"] for e in events if e["kind"]=="EPISODE_RECORD"]
    require(records==trajectory["episodes"]==checkpoint["episodes"],"EPISODE_CHAIN_MISMATCH")
    require(checkpoint["all_calls"]==[c for e in records for c in e["calls"]],"CHECKPOINT_CALLS_MISMATCH")
    durations={};current=[];index=0
    for event in events[1:]:
        if event["kind"]=="EPISODE_BEGIN":
            require(not current,"UNFINISHED_EPISODE_CAPTURE")
            current=[event]
        elif current:
            current.append(event)
        if event["kind"]=="EPISODE_RECORD":
            require(bool(current) and index<len(records),"EPISODE_CAPTURE_ORDER")
            record=records[index];index+=1;eid=record["episode_id"]
            require(current[0]["payload"]["episode_id"]==eid,"EPISODE_CAPTURE_IDENTITY")
            verify_calls(current,record["calls"],config,architecture=plan["architecture"],
                split=record["evaluator_private"]["split"],block_id=plan["block_id"],item_index=index-1)
            tool_ends=[e["payload"] for e in current if e["kind"]=="TOOL_END"]
            tool_starts=[e["payload"] for e in current if e["kind"]=="TOOL_START"]
            tool=record["tool_event"]
            require(len(tool_ends)==len(tool_starts)==int(tool is not None),"TOOL_CAPTURE_CARDINALITY")
            if tool is not None:
                end=tool_ends[0];begin=tool_starts[0];duration=end["duration_ms"]
                require(end["tool_event"]==tool and begin["sequence"]==tool["start_sequence"] and begin["spec_sha256"]==tool["input_spec_sha256"],"TOOL_CAPTURE_MISMATCH")
                require(type(duration) in {int,float} and math.isfinite(duration) and duration>=0,"INVALID_TOOL_LATENCY")
                durations[eid]=duration
            if scientific:
                for e in current:
                    if e["kind"]=="CALL_RESPONSE":
                        require(e["payload"]["observed_model_revision"]==config["model_configuration"]["model_revision"],"OBSERVED_MODEL_REVISION_MISMATCH")
            current=[]
        elif not current and event["kind"] in {"CALL_REQUEST","CALL_RESPONSE","CALL_USAGE","TOOL_END"}:
            raise Failure("INFRA_FAILURE","UNSCOPED_CAPTURE_EVENT")
    require(not current,"INCOMPLETE_EPISODE_CAPTURE")
    return dict(trajectory=cp(trajectory),tool_durations=durations,event_head=events[-1]["sha256"],event_count=len(events))


def provider_identity(config):
    return dict(adapter=cp(config["runtime_identity"]["provider_adapter"]),
        model_configuration=cp(config["model_configuration"]),compute_settings=cp(config["compute_settings"]))


def collect_run_bundle(trajectories,event_logs,manifest,config,artifact,calibration_events,*,scientific=True):
    """Re-read chains even when a caller supplies a previously sealed bundle."""
    try:
        from .config import validate_frozen
        from .manifest import verify_manifest
        from .calibration_artifact import verify_artifact
        validate_frozen(config);verify_manifest(manifest,config)
        verify_artifact(artifact,config,calibration_events,scientific=scientific)
        require(len({t["trajectory_id"] for t in trajectories})==len(trajectories),"DUPLICATE_TRAJECTORY")
        require(set(event_logs)=={t["trajectory_id"] for t in trajectories},"EVENT_LOG_SET_MISMATCH")
        rows=[_collect_trajectory(t,event_logs[t["trajectory_id"]],manifest,config,artifact,scientific=scientific) for t in trajectories]
        payload=dict(version="0.1.1",result_kind="VALIDATED_MODEL_RUN_BUNDLE" if scientific else TEST_VECTOR,
            config_sha256=semantic_sha(config),manifest_sha256=manifest["sha256"],calibration_artifact_sha256=artifact["sha256"],
            trajectories=[r["trajectory"] for r in rows],tool_durations={r["trajectory"]["trajectory_id"]:r["tool_durations"] for r in rows},
            event_heads={r["trajectory"]["trajectory_id"]:dict(sha256=r["event_head"],count=r["event_count"]) for r in rows})
        return dict(payload=payload,sha256=semantic_sha(payload))
    except Failure as error:
        raise Failure("INFRA_FAILURE",error.code,error.pointer) from None
    except (OSError,KeyError,IndexError,StopIteration,TypeError,ValueError):
        raise Failure("INFRA_FAILURE","INVALID_RUN_BUNDLE_INPUT") from None
