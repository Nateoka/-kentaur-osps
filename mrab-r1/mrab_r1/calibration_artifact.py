"""Runtime-only CalibrationArtifact; no changes to frozen source schemas."""
from copy import deepcopy as cp
from .canonical import semantic_sha,raw_sha,integer_dsl_bytes
from .errors import Failure
from .storage import read_events,decode_events
from pathlib import Path
from .config import verify_calibration_lock
from .provenance import require,TEST_VECTOR,provider_identity,verify_calls

# Cache ONLY a successful proof over exact byte digest + exact artifact/config
# identities. Re-read and hash bytes on every call, never trust path/mtime or a
# caller-supplied validation flag. Bounded; no provider data retained here.
_verified={}


def scope_for(config,architecture,family,band,difficulty):
    selected=next(r for r in config["selected_difficulty_tuples"] if (r["family"],r["band"])==(family,band))
    digest=raw_sha(integer_dsl_bytes([family,difficulty]))[:16]
    capability=config["capability_configurations"][architecture]
    return dict(scope_id=selected["scope_id"],task_family=family,difficulty_scope=["d:"+digest],
        context_condition=["ctx:0"],tool_condition="SOLO_NO_TOOL",
        capability_configuration_ref=capability["configuration_id"],execution_modes=cp(capability["execution_modes"]))


def _artifact_structure(artifact,config):
    from .calibration import confirmation_gate
    p=artifact["payload"]
    require(semantic_sha(p)==artifact["sha256"],"CALIBRATION_ARTIFACT_HASH_MISMATCH")
    require(p["config_sha256"]==semantic_sha(config),"CALIBRATION_CONFIG_IDENTITY")
    verify_calibration_lock(p["pre_calibration_lock"],config,final=True)
    require(p["runtime_identity"]==config["runtime_identity"] and p["provider_identity"]==provider_identity(config),"CALIBRATION_COMPONENT_IDENTITY")
    require(p["selected_tuples"]==config["selected_difficulty_tuples"],"CALIBRATION_TUPLE_IDENTITY")
    require(p["gate_status"]=="PASS","CALIBRATION_NOT_FEASIBLE")
    gate=confirmation_gate(p["confirmation_cells"],config)
    require(gate["status"]=="FEASIBLE_FOR_SUPPLIED_COUNTS","CALIBRATION_GATE_MISMATCH")
    manifests=p["confirmation_manifests"]
    require(len(manifests)==4 and len({(m["family"],m["band"]) for m in manifests})==4,"CONFIRMATION_MANIFEST_CARDINALITY")
    require(len({m["dataset_hash"] for m in manifests})==4,"CONFIRMATION_DATASET_NOT_UNIQUE")
    for cell in p["confirmation_cells"]:
        selected=next(s for s in p["selected_tuples"] if (s["family"],s["band"])==(cell["family"],cell["band"]))
        manifest=next(m for m in manifests if (m["family"],m["band"])==(cell["family"],cell["band"]))
        require(cell["tuple_sha256"]==selected["tuple_sha256"]==manifest["tuple_sha256"]==semantic_sha(manifest["difficulty"]),"REFERENCE_TUPLE_MISMATCH")
        require(selected["scope_id"]=="scope:"+raw_sha(integer_dsl_bytes([cell["family"],manifest["difficulty"]]))[:16],"REFERENCE_DATASET_SCOPE_IDENTITY")
        require(cell["dataset_hash"]==manifest["dataset_hash"],"REFERENCE_DATASET_MISMATCH")
        require(cell["scope"]==scope_for(config,cell["architecture"],cell["family"],cell["band"],manifest["difficulty"]),"REFERENCE_SCOPE_OR_CAPABILITY_MISMATCH")
    return p


def verify_artifact(artifact,config,event_path,*,scientific=True):
    try:
        p=_artifact_structure(artifact,config)
        if scientific:require(p["result_kind"]=="REFERENCE_CALIBRATION","TEST_CALIBRATION_NOT_SCIENTIFIC")
        else:require(p["result_kind"] in {"REFERENCE_CALIBRATION",TEST_VECTOR},"UNKNOWN_CALIBRATION_KIND")
        raw=Path(event_path).read_bytes()
        key=(raw_sha(raw),artifact["sha256"],semantic_sha(config),scientific)
        if key in _verified:return cp(_verified[key])
        events=decode_events(raw)
        require(len(events)>1 and events[-1]["kind"]=="CALIBRATION_ARTIFACT_SEAL" and events[-1]["payload"]==artifact,"CALIBRATION_SEAL_NOT_IN_CHAIN")
        require(events[-2]["sha256"]==p["evidence_head_sha256"],"CALIBRATION_EVIDENCE_HEAD_MISMATCH")
        verify_confirmation_evidence(p,config,events[:-1],scientific=scientific)
        result=dict(status="PASS",sha256=artifact["sha256"],event_head=events[-1]["sha256"])
        if len(_verified)>=8:_verified.clear()
        _verified[key]=cp(result)
        return result
    except Failure as error:
        raise Failure("INFRA_FAILURE",error.code,error.pointer) from None
    except (OSError,KeyError,IndexError,StopIteration,TypeError,ValueError):
        raise Failure("INFRA_FAILURE","INVALID_CALIBRATION_ARTIFACT") from None


def verify_confirmation_evidence(p,config,events,*,scientific):
    from .schemas import Schemas
    from .prompts import Prompts
    registry=Schemas();prompts=Prompts()
    action_refs={a:prompts.schema_ref("ACTION",a) for a in config["architectures"]}
    from .calibration import calibration_plan
    candidates=calibration_plan(config)["candidate_order"]
    def one(kind):
        rows=[(i,e["payload"]) for i,e in enumerate(events) if e["kind"]==kind]
        require(len(rows)==1,"CALIBRATION_LIFECYCLE_"+kind)
        return rows[0]
    li,lock=one("CALIBRATION_LOCK");si,selection=one("CALIBRATION_SEARCH_SELECTION")
    fi,frozen=one("CALIBRATION_FINAL_FROZEN");gi,gate=one("CALIBRATION_CONFIRMATION")
    require(li==0 and li<si<fi<gi==len(events)-1,"CALIBRATION_LIFECYCLE_ORDER")
    require(lock==p["pre_calibration_lock"] and frozen==dict(config=config,config_sha256=semantic_sha(config)),"CALIBRATION_LOCK_CHAIN_MISMATCH")
    require(selection["selected_tuples"]==config["selected_difficulty_tuples"],"SEARCH_SELECTION_MISMATCH")
    require(gate["gate_status"]=="PASS" and gate["cells"]==p["confirmation_cells"],"CONFIRMATION_COUNTS_CHAIN_MISMATCH")
    measurements={};manifests={};pending=[];seen=set()
    for i,event in enumerate(events):
        kind,row=event["kind"],event["payload"]
        if kind=="CALIBRATION_ITEM_MANIFEST":
            block=row["block_id"]
            require(block not in manifests,"CALIBRATION_DUPLICATE_MANIFEST")
            require(semantic_sha(row["items"])==row["sha256"],"CALIBRATION_ITEM_MANIFEST_HASH")
            manifests[block]=row
            expected_n=200 if row["phase"]=="CONFIRM" else 40
            require(len(row["items"])==expected_n,"CALIBRATION_MANIFEST_SIZE")
            require((fi<i<gi) if row["phase"]=="CONFIRM" else (li<i<si),"CALIBRATION_SPLIT_ORDER")
            if row["phase"]=="CONFIRM":
                binding=next(m for m in p["confirmation_manifests"] if block==f"confirm:{m['family']}:{m['band']}")
            else:
                binding=candidates[int(block.split(':')[1])]
            family,difficulty=binding["family"],binding["difficulty"]
            scope_digest=raw_sha(integer_dsl_bytes([family,difficulty]))[:16]
            for item_index,item in enumerate(row["items"]):
                require(item["split"]=="CALIBRATION_"+row["phase"] and item["latent_fingerprint"] not in seen,"CALIBRATION_SPLIT_OR_LATENT_DUPLICATE")
                from .tasks import verify_task,alpha_fingerprint
                spec=item["task_view"]["spec"]
                view=item["task_view"]
                require(view["task_family"]==spec["family"]==family and view["scope_id"]=="scope:"+scope_digest and view["difficulty_scope"]=="d:"+scope_digest and view["context_condition"]=="ctx:0","CALIBRATION_ITEM_SCOPE_OR_FAMILY")
                dimensions=dict(n=len(spec["initial"]),length=len(spec["operations"])) if family=="SYMBOLIC_PIPELINE" else dict(n=len(spec["entities"]),k=len(spec["properties"]))
                require(all(difficulty[k]==v for k,v in dimensions.items()),"CALIBRATION_ITEM_TUPLE_DIMENSIONS")
                from .seed import Stream
                require(view["task_id"]==Stream(config["master_seed"],item["split"],block,"TASK_ID",item_index,item["generation_attempt"]).digest().hex()[:24],"CALIBRATION_ITEM_SEED_PROVENANCE")
                require(verify_task(spec)==item["ground_truth"],"CALIBRATION_GROUND_TRUTH")
                fingerprint=alpha_fingerprint(spec) if spec["family"]=="RULE_GRID" else raw_sha(integer_dsl_bytes(spec))
                require(fingerprint==item["latent_fingerprint"],"CALIBRATION_LATENT_FINGERPRINT")
                seen.add(item["latent_fingerprint"])
        elif kind in {"CALL_REQUEST","CALL_RESPONSE","CALL_USAGE","CALL_NOT_ACCEPTED","OUTPUT_VALIDATION_ERRORS"}:
            pending.append(event)
        elif kind=="CALIBRATION_MEASUREMENT":
            phase,block,arch,index=row["phase"],row["block_id"],row["architecture"],row["item_index"]
            key=(block,arch,index)
            require(key not in measurements and block in manifests,"CALIBRATION_MEASUREMENT_IDENTITY")
            require((fi<i<gi) if phase=="CONFIRM" else (li<i<si),"CALIBRATION_MEASUREMENT_ORDER")
            item=manifests[block]["items"][index]
            require(row["task_id"]==item["task_view"]["task_id"] and row["phase"]==manifests[block]["phase"],"CALIBRATION_MEASUREMENT_ITEM")
            require(row["profile"] is None and row["history"]==row["commits"]==row["tool_events"]==[],"CALIBRATION_RESET_VIOLATION")
            verify_calls(pending,row["calls"],config,architecture=arch,split="CALIBRATION_"+phase,block_id=block,item_index=index)
            require(sum(c["phase"]=="PREP" for c in row["calls"])==int(arch in {"B1","B2","B3"}),"CALIBRATION_PREP_INTERFACE")
            require(sum(c["phase"]=="REPAIR" for c in row["calls"])<=1,"CALIBRATION_REPAIR_BUDGET")
            if scientific:
                require(row["artifact_kind"]=="REFERENCE_CALIBRATION_MEASUREMENT","SCRIPTED_CALIBRATION_MEASUREMENT")
                for e in pending:
                    if e["kind"]=="CALL_RESPONSE":require(e["payload"]["observed_model_revision"]==config["model_configuration"]["model_revision"],"CALIBRATION_MODEL_REVISION")
            # Success count is derived from the captured ACTION (or structural
            # repair) bytes, never from caller-supplied aggregate counts alone.
            from .canonical import loads
            from .answers import normalize_answer
            for call in row["calls"]:
                if call["phase"]=="REPAIR":continue
                request=loads(call["request_bytes"]);state=request["agent_state"]
                require(state["task_view"]==item["task_view"] and state["capability_configuration"]==config["capability_configurations"][arch],"CALIBRATION_REQUEST_IDENTITY")
                require(state["current_profile"] is None and all(state[k]==[] for k in ("recent_episode_history","profile_history","evidence_index","evidence_ledger","history_anchors")),"CALIBRATION_REQUEST_RESET")
                mode=None if call["phase"]=="PREP" else "PREP_EXECUTED" if arch in {"B1","B2","B3"} else "NO_PREP_INTERFACE"
                require(state["current_execution_mode"]==mode,"CALIBRATION_EXECUTION_MODE")
            action_calls=[c for c in row["calls"] if c["phase"]=="ACTION" or c["phase"]=="REPAIR" and c["repair_of"]=="ACTION"]
            correct=False
            if row["failure"] is None:
                require(bool(action_calls),"CALIBRATION_ACTION_MISSING")
                answer=loads(action_calls[-1]["visible_output"])
                registry.validate(answer,action_refs[arch],"INFRA_FAILURE")
                require(answer["action"]=="SOLO","CALIBRATION_NOT_SOLO")
                correct=normalize_answer(item["task_view"]["spec"],answer["solo_answer"],registry)==item["ground_truth"]
            require(row["solo_correct"] is correct,"CALIBRATION_SUCCESS_CAPTURE_MISMATCH")
            measurements[key]=row;pending=[]
    require(not pending,"CALIBRATION_UNCONSUMED_CAPTURES")
    from .calibration import calibration_plan
    selected={};results=iter(selection["search_results"])
    for ci,candidate in enumerate(calibration_plan(config)["candidate_order"]):
        family=candidate["family"]
        if all((family,b) in selected for b in ("HIGH","MID")):continue
        result=next(results);require(result["candidate"]==candidate,"SEARCH_CANDIDATE_ORDER")
        block=f"search:{ci}";counts=[]
        require(block in manifests,"SEARCH_CANDIDATE_MANIFEST_MISSING")
        for arch in config["architectures"]:
            rows=[v for (b,a,_),v in measurements.items() if b==block and a==arch]
            require(len(rows)==40 and {r["item_index"] for r in rows}==set(range(40)),"SEARCH_CELL_N")
            counts.append(dict(architecture=arch,n=40,successes=sum(r["solo_correct"] for r in rows)))
        require(counts==result["counts"],"SEARCH_COUNTS_CHAIN_MISMATCH")
        for band in ("HIGH","MID"):
            bounds=config["calibration_bands"][band]
            if (family,band) not in selected and all(bounds["lower"] <= (r["successes"]+1)/42 <= bounds["upper"] for r in counts):
                selected[family,band]=candidate["difficulty"]
    require(next(results,None) is None and len(selected)==4,"SEARCH_SELECTION_CARDINALITY")
    for row in config["selected_difficulty_tuples"]:
        require(row["tuple_sha256"]==semantic_sha(selected[row["family"],row["band"]]),"SEARCH_FINAL_TUPLE_MISMATCH")
    for cell in p["confirmation_cells"]:
        block=f"confirm:{cell['family']}:{cell['band']}"
        manifest=manifests[block]
        require(manifest["sha256"]==cell["dataset_hash"],"CALIBRATION_DATASET_CHAIN_MISMATCH")
        rows=[v for (b,a,_),v in measurements.items() if b==block and a==cell["architecture"]]
        require(len(rows)==200 and {r["item_index"] for r in rows}==set(range(200)),"CALIBRATION_CONFIRM_N")
        require(sum(r["solo_correct"] for r in rows)==cell["successes"],"CALIBRATION_SUCCESSES_CHAIN_MISMATCH")


def seal_artifact(config,lock,cells,manifests,event_store,*,offline_fixture=False,gate_status="PASS"):
    payload=dict(version="0.1.1",result_kind=TEST_VECTOR if offline_fixture else "REFERENCE_CALIBRATION",
        config_sha256=semantic_sha(config),pre_calibration_lock=cp(lock),runtime_identity=cp(config["runtime_identity"]),
        provider_identity=provider_identity(config),selected_tuples=cp(config["selected_difficulty_tuples"]),
        confirmation_manifests=cp(manifests),confirmation_cells=cp(cells),gate_status=gate_status,
        evidence_head_sha256=event_store.events[-1]["sha256"])
    artifact=dict(payload=payload,sha256=semantic_sha(payload))
    if gate_status=="PASS":
        _artifact_structure(artifact,config)
        verify_confirmation_evidence(payload,config,event_store.events,scientific=not offline_fixture)
    else:
        require(gate_status=="CALIBRATION_NOT_FEASIBLE" and len(cells)==20,"INVALID_FAILED_CALIBRATION_ARTIFACT")
    event_store.append("CALIBRATION_ARTIFACT_SEAL",artifact)
    return artifact


def materialize_reference_cells(artifact,config,plan):
    p=_artifact_structure(artifact,config);output=[]
    for family,address in plan["scope_by_family"].items():
        band=plan["target_stratum"] if family==plan["target_family"] else "HIGH"
        found=[c for c in p["confirmation_cells"] if (c["architecture"],c["family"],c["band"])==(plan["architecture"],family,band)]
        require(len(found)==1,"REFERENCE_CELL_NOT_UNIQUE")
        cell=found[0];scope=cell["scope"]
        require(scope["scope_id"]==address["scope_id"] and scope["difficulty_scope"]==[address["difficulty_scope"]] and scope["context_condition"]==[address["context_condition"]],"TRAJECTORY_REFERENCE_SCOPE_MISMATCH")
        output.append(dict(calibration_key="reference:"+semantic_sha([artifact["sha256"],plan["architecture"],family,band]),
            architecture=plan["architecture"],band=band,scope=cp(scope),successes=cell["successes"],n=cell["n"],dataset_hash=cell["dataset_hash"]))
    require(len(output)==2 and len({c["calibration_key"] for c in output})==2,"REFERENCE_CARDINALITY")
    return output
