"""Cross-object checks over completed or partial recorded trajectories.

I16/I17/I23/I24 are collection/tool/evaluator invariants, verified separately;
this validator does not falsely label those as proven by one trajectory.
"""
from copy import deepcopy as cp
from .canonical import canonical,loads,raw_sha,semantic_sha,integer_dsl_bytes
from .schemas import Schemas
from .profiles import ProfileStore,informative
from .errors import Failure
from .controller import prep_path
from .tasks import verify_task


LOCAL_IDS=("I01","I02","I03","I04","I05","I06","I07","I08","I09","I10","I11","I12","I13","I14","I15","I18","I19","I21","I22")


def verify_trajectory(trajectory,manifest=None,config=None):
    # Historic fixture-only two-argument API remains local validation. A scientific
    # plan ALWAYS requires an actual FROZEN config, before any record is inspected.
    if manifest is not None:
        if semantic_sha(manifest["payload"]) != manifest["sha256"]:
            raise Failure("INFRA_FAILURE","MANIFEST_HASH_MISMATCH")
        if config is None and manifest["payload"]["result_kind"] != "DESIGN_TEST_VECTOR_NOT_MODEL_RESULT":
            raise Failure("INFRA_FAILURE","FROZEN_CONFIG_REQUIRED")
        if config is not None:
            from .config import validate_frozen
            from .manifest import verify_manifest
            try:
                validate_frozen(config)
                verify_manifest(manifest,config)
            except Failure as error:
                raise Failure("INFRA_FAILURE",error.code) from None
    elif config is not None:
        raise Failure("INFRA_FAILURE","PLANNED_MANIFEST_REQUIRED")
    try:
        return _verify_trajectory(trajectory,manifest,config)
    except (KeyError,IndexError,StopIteration,TypeError,ValueError):
        raise Failure("INFRA_FAILURE","MALFORMED_TRAJECTORY_PROVENANCE") from None


def _verify_trajectory(trajectory,manifest=None,config=None):
    from .runner import evidence_before
    registry=Schemas();registry.validate(trajectory,registry.ref("trajectory"),"INFRA_FAILURE")
    failures=[]
    def require(condition,invariant,code,episode=None):
        if not condition:failures.append(dict(invariant_id=invariant,code=code,episode_index=episode))
    arch=trajectory["architecture"];initial=trajectory["initial_profile"]
    require((initial is None)==(arch=="B4" or trajectory["profile_condition"]=="C0"),"I03","INITIAL_PROFILE_PRESENCE")
    if initial:
        require(len(initial["claims"])==2 and len({c["claim_id"] for c in initial["claims"]})==2,"I01","CLAIM_SLOTS")
        for c in initial["claims"]:
            modes={"NO_PREP_INTERFACE"} if arch=="B0" else {"PREP_EXECUTED","PREP_SKIPPED"} if arch=="B3" else {"PREP_EXECUTED"}
            require(set(c["execution_modes"])<=modes,"I03","INITIAL_NORMAL_SCOPE")
    store=ProfileStore(initial);prior=[];seen=set();attempts=[];tool_cost=0
    planned=None if manifest is None else next((t for t in manifest["payload"]["trajectories"] if t["trajectory_id"]==trajectory["trajectory_id"]),None)
    if manifest is not None:require(planned is not None,"I18","PLAN_TRAJECTORY_ABSENT")
    if planned:
        for field in ("trajectory_id","block_id","architecture","target_family","first_family","target_stratum"):
            require(trajectory[field]==planned[field],"I18","PLAN_"+field.upper())
        require(trajectory["profile_condition"]==planned["condition"],"I18","PLAN_PROFILE_CONDITION")
        for field in ("planned_run","config_sha256"):
            require(trajectory[field]==manifest["payload"][field],"I18","PLAN_"+field.upper())
        require(len(trajectory["episodes"])<=len(planned["task_ids"]),"I18","PLAN_EPISODE_OVERFLOW")
        require(trajectory["completion_status"]!="COMPLETED" or len(trajectory["episodes"])==len(planned["task_ids"]),"I18","PLAN_INCOMPLETE_COMPLETION")
        if config is not None:
            from .seed import Stream
            expected_seeds={name:Stream(config["master_seed"],"MAIN",planned["block_id"],name,
                architecture=arch if name=="MODEL" else None,phase="ACTION" if name=="MODEL" else None).digest().hex()
                for name in ("TASK","FAMILY_ORDER","SURFACE","PROFILE","MODEL","BOOTSTRAP","TASK_ID")}
            require(trajectory["seed_metadata"]==expected_seeds,"I18","SEED_PROVENANCE_MISMATCH")
    for index,e in enumerate(trajectory["episodes"],1):
        f=e["feedback"];private=e["evaluator_private"];view=e["agent_input"]["task_view"]
        require(e["episode_index"]==index and f["episode_index"]==index and e["trajectory_id"]==trajectory["trajectory_id"],"I18","EPISODE_IDENTITY",index)
        require(e["agent_input"]["current_profile"]==store.current,"I13","PREP_INPUT_NOT_CURRENT_PROFILE",index)
        if planned:
            expected=manifest["payload"]["tasks"][planned["task_ids"][index-1]]["record"]
            require(view==expected["task_view"] and all(private[k]==expected[k] for k in ("split","phase","target_role","latent_fingerprint","surface_template_id","ground_truth")),"I18","SEALED_SCHEDULE",index)
        u=e["update_event"]
        if u is not None:
            try:
                replayed=store.commit(u["proposal"],arch,index,prior,u["sequence"])
                require(replayed==u,"I06","COMMIT_REPLAY_MISMATCH",index)
                require(replayed["validation_status"]==u["validation_status"],"I07","ADMISSIBILITY_NOT_REPRODUCIBLE",index)
            except Failure as error:require(False,"I06",error.code,index)
            attempts.append(u)
            require(all(r in {f["episode_id"] for f in prior} for r in u["proposal"]["evidence_refs"]) or u["validation_status"]=="REJECTED","I05","COMMITTED_NONPAST_REF",index)
        require(e["action_input_profile"]==store.current,"I13","ACTION_INPUT_NOT_COMMITTED_PROFILE",index)
        if arch in {"B0","B1"}:require(e["action_input_profile"]==initial,"I02","READONLY_PROFILE_MUTATED",index)
        if initial is None:require(e["action_input_profile"] is None,"I02","PROFILE_FORBIDDEN",index)
        for claim in [] if store.current is None else store.current["claims"]:
            interval=claim["estimated_success_interval"]
            require((interval is None)==(claim["status"]=="UNKNOWN") and (interval is None or 0<=interval["lower"]<=interval["upper"]<=1),"I04","INTERVAL_STATUS",index)
        require(e["agent_input"]["recent_episode_history"]==prior[-10:],"I15","HISTORY_WINDOW",index)
        require(e["agent_input"]["evidence_index"]==[dict(episode_id=f["episode_id"],feedback=f) for f in prior],"I15","EVIDENCE_INDEX",index)
        require(not registry.errors(e["agent_input"],registry.ref("trajectory","agent_state")),"I14","PUBLIC_ALLOWLIST",index)
        action=e["action_record"];tool=e["tool_event"];choice=None if action is None else action["action"]
        truth=verify_task(view["spec"])
        require(truth==private["ground_truth"],"I08","SEALED_TRUTH_MISMATCH",index)
        if tool:
            require(tool["input_spec_sha256"]==raw_sha(integer_dsl_bytes(view["spec"])),"I08","TOOL_SPEC_MISMATCH",index)
            require(tool["status"]!="OK" or tool["result"]==truth,"I11","TOOL_RESULT_MISMATCH",index)
            require(choice in {"VERIFY","DELEGATE"},"I10","TOOL_NOT_ALLOWED",index)
        if choice=="VERIFY" and tool:require(e["solo_seal_sequence"] is not None and e["solo_seal_sequence"]<tool["start_sequence"],"I09","PREANSWER_NOT_SEALED_FIRST",index)
        if choice=="SOLO":require(tool is None,"I10","SOLO_TOOL",index)
        if choice in {"ABSTAIN","DELEGATE"}:require(action["solo_answer"] is None and e["solo_seal_sequence"] is None,"I10","FORBIDDEN_SOLO_ANSWER",index)
        if choice=="ABSTAIN":require(tool is None and e["final_answer"] is None,"I10","ABSTAIN_RESULT",index)
        require(f["tool_used"]==(tool is not None) and f["cost_units"]==(0 if tool is None else tool["cost_units"]),"I11","TOOL_ACCOUNTING",index)
        tool_cost+=f["cost_units"]
        repairs=[c for c in e["calls"] if c["phase"]=="REPAIR"]
        require(len(repairs)<=1,"I12","MULTIPLE_REPAIRS",index)
        for call in e["calls"]:
            raw=call["request_bytes"].encode()
            require(raw_sha(raw)==call["input_sha256"],"I19","CALL_INPUT_HASH",index)
            if call["visible_output"] is not None:
                require(raw_sha(call["visible_output"].encode("utf-8"))==call["output_sha256"],"I19","CALL_OUTPUT_HASH",index)
            request=loads(raw)
            if call["phase"]=="REPAIR":require(set(request)=={"system","invalid_output","validation_errors","output_schema"},"I12","REPAIR_NEW_CONTEXT",index)
            else:require(set(request)=={"system","instruction","agent_state","output_schema","prep_record","commit_receipt"} and not registry.errors(request["agent_state"],registry.ref("trajectory","agent_state")),"I14","CALL_ALLOWLIST",index)
            for name,status in call["usage_availability"].items():require(status!="UNAVAILABLE" or call[name] is None,"I19","UNAVAILABLE_NOT_NULL",index)
        context=e["execution_context"]
        path=prep_path(arch,context["execution_mode"],context["prep_call_count"],context["prep_skip_reason"],arch=="B3" and context["prep_skip_reason"]=="B3_STOP_CONTROLLER")
        require(path["valid"],"I18","PREP_PATH",index)
        fingerprint=private["latent_fingerprint"]
        require(fingerprint not in seen,"I21","DUPLICATE_LATENT_OBSERVATION",index);seen.add(fingerprint)
        require(private["informative"]==informative(f) and (choice!="DELEGATE" or f["solo_correct"] is None),"I21","INFORMATIVE_ELIGIBILITY",index)
        key={k:f[k] for k in ("scope_id","task_family","difficulty_scope","context_condition","tool_condition","capability_configuration_ref","execution_mode","history_class")}
        interval=next(r["interval"] for r in trajectory["initial_stimulus_intervals"] if r["scope_id"]==key["scope_id"])
        gate=evidence_before(prior,key,interval)
        require(gate["sufficient"]==private["sufficient_before"] and gate["direction"]==private["direction_before"] and gate["wrong"]==private["posterior_wrong_before"],"I22","EVIDENCE_NOT_T_MINUS_ONE",index)
        prior.append(cp(f))
    require(store.current==trajectory["current_profile"] and attempts==trajectory["profile_history"],"I01","FINAL_PROFILE_REPLAY")
    require(tool_cost==trajectory["cumulative_cost"],"I19","CUMULATIVE_TOOL_COST")
    return dict(status="FAIL" if failures else "PASS",checked_invariants=list(LOCAL_IDS),failures=failures,
        collection_checks_required=["I16","I17","I20","I23","I24"],schema_patches=registry.applied_patches)


def enforce_trajectory(trajectory,manifest=None,config=None):
    result=verify_trajectory(trajectory,manifest,config)
    if result["failures"]:
        first=result["failures"][0]
        raise Failure("INFRA_FAILURE",first["invariant_id"]+":"+first["code"])
    return result
