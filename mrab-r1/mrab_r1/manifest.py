"""Sealed task schedules. No model calls or calibration success is implied."""
from copy import deepcopy as cp
from .canonical import canonical, semantic_sha, raw_sha, integer_dsl_bytes
from .errors import Failure
from .seed import Stream
from .tasks import generate_symbolic,generate_grid,verify_task,alpha_fingerprint
from .surface import relabel,render,parse_surface
from .generator_options import resolve_options

FAMILIES=("SYMBOLIC_PIPELINE","RULE_GRID")


def build_manifest(config, tuples, planned_run=None, existing_fingerprints=None, offline_fixture=False,content=None):
    """tuples maps (family, band) -> resolved difficulty objects, explicitly supplied."""
    run=planned_run or config["planned_run"]
    if run not in {"SMOKE","PILOT"}:
        raise Failure("CONFIGURATION_FAILURE","UNSUPPORTED_RUN_PLAN")
    if config["configuration_status"]!="FROZEN" and not offline_fixture:
        raise Failure("CONFIGURATION_FAILURE","FROZEN_CONFIG_REQUIRED")
    if not offline_fixture:
        from .config import freeze
        freeze(config,content or {})
        if run!=config["planned_run"]:raise Failure("CONFIGURATION_FAILURE","PLAN_CONFIG_RUN_MISMATCH")
        for row in config["selected_difficulty_tuples"]:
            if semantic_sha(tuples[row["family"],row["band"]])!=row["tuple_sha256"]:
                raise Failure("CONFIGURATION_FAILURE","SELECTED_TUPLE_HASH_MISMATCH")
    if set(tuples)!={(f,b) for f in FAMILIES for b in ("HIGH","MID")}:
        raise Failure("CONFIGURATION_FAILURE","FOUR_DIFFICULTY_TUPLES_REQUIRED")
    count,main,total=(2,8,12) if run=="SMOKE" else (8,24,32)
    seen=dict(existing_fingerprints or {});tasks={};trajectories=[];blocks=[]
    for condition in ("C0","C1","C2","C3"):
        for replicate in range(count):
            block=f"block:{condition}:{replicate}"
            target=FAMILIES[replicate%2]
            first=FAMILIES[replicate%2 if run=="SMOKE" else (replicate//2)%2]
            band="HIGH" if condition=="C2" else "MID" if condition=="C3" else ("HIGH","MID")[replicate%2 if run=="SMOKE" else replicate//4]
            scope_by_family={}
            for family in FAMILIES:
                difficulty=tuples[family,band if family==target else "HIGH"]
                digest=raw_sha(integer_dsl_bytes([family,difficulty]))[:16]
                selected=next((r for r in config["selected_difficulty_tuples"] if r["family"]==family and r["band"]==(band if family==target else "HIGH")),None)
                scope_by_family[family]=dict(scope_id=selected["scope_id"] if selected and not offline_fixture else "scope:"+digest,difficulty_scope="d:"+digest,context_condition="ctx:0")
            schedule=[]
            for index in range(1,total+1):
                family=first if index%2 else FAMILIES[1-FAMILIES.index(first)]
                split="MAIN" if index<=main else "TRANSFER"
                difficulty=cp(tuples[family,band if family==target else "HIGH"])
                attempt=0;duplicates=[]
                while True:
                    kwargs=dict(master_seed=config["master_seed"],split=split,block_id=block,item_index=index,start_attempt=attempt)
                    options=resolve_options(config,family,difficulty)
                    item=generate_symbolic(**kwargs,**options) if family==FAMILIES[0] else generate_grid(**kwargs,**options)
                    fingerprint=item["latent_fingerprint"]
                    if fingerprint not in seen:break
                    duplicates.append(dict(attempt=item["generation_attempt"],reason="LATENT_DUPLICATE",prior_split=seen[fingerprint]))
                    attempt=item["generation_attempt"]+1
                    if attempt>=1000:raise Failure("GENERATION_FAILURE","DEDUP_ATTEMPTS_EXHAUSTED")
                seen[fingerprint]=split
                rng=Stream(config["master_seed"],split,block,"SURFACE",index,item["generation_attempt"])
                template=("A","B")[rng.randint(0,1)] if split=="MAIN" else ("C","D")[rng.randint(0,1)]
                spec=relabel(item["spec"],rng,split=="TRANSFER")
                surface=render(spec,template)
                if parse_surface(surface)!=spec:raise Failure("INFRA_FAILURE","RENDER_ROUND_TRIP_FAILED")
                if family==FAMILIES[1] and alpha_fingerprint(spec)!=fingerprint:
                    raise Failure("INFRA_FAILURE","ALPHA_RENDER_CHANGED_TASK")
                task_view=dict(task_id=item["task_id"],task_family=family,spec=spec,surface_text=surface,**scope_by_family[family])
                private=dict(task_view=task_view,ground_truth=verify_task(spec),latent_fingerprint=fingerprint,
                    surface_template_id=template,split=split,generation_attempt=item["generation_attempt"],duplicate_rejections=duplicates,
                    phase=("SMOKE_MAIN" if split=="MAIN" else "SMOKE_TRANSFER") if run=="SMOKE" else "TRANSFER" if split=="TRANSFER" else "INITIAL_EXPOSURE" if index<=6 else "EVIDENCE_ACCUMULATION" if index<=12 else "ADAPTATION",
                    target_role="TARGET" if family==target else "CONTROL")
                seal=raw_sha(integer_dsl_bytes(private));task_ref=item["task_id"]
                if task_ref in tasks:raise Failure("INFRA_FAILURE","TASK_ID_COLLISION")
                tasks[task_ref]=dict(record=private,sha256=seal)
                schedule.append(task_ref)
            blocks.append(block)
            for architecture in ("B0","B1","B2","B3","B4"):
                identity=raw_sha(integer_dsl_bytes(["trajectory",config["master_seed"],block,architecture]))[:24]
                trajectories.append(dict(trajectory_id=identity,block_id=block,architecture=architecture,
                    condition=condition,target_family=target,first_family=first,target_stratum=band,
                    scope_by_family=cp(scope_by_family),task_ids=schedule[:]))
    order=Stream(config["master_seed"],"MAIN","manifest","FAMILY_ORDER").shuffle(trajectories)
    payload=dict(version="0.1",planned_run=run,config_sha256=semantic_sha(config),trajectories=order,tasks=tasks,
        result_kind="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT" if offline_fixture else "SEALED_EXPERIMENT_PLAN_NOT_RESULT",
        expected_trajectories=4*5*count,expected_episodes=4*5*count*total,main_episodes=main,transfer_episodes=total-main)
    return dict(payload=payload,sha256=semantic_sha(payload))


def verify_manifest(manifest, config):
    payload=manifest["payload"]
    if semantic_sha(payload)!=manifest["sha256"] or semantic_sha(config)!=payload["config_sha256"]:
        raise Failure("INFRA_FAILURE","MANIFEST_HASH_MISMATCH")
    if payload["result_kind"]!="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT" and (config["configuration_status"]!="FROZEN" or payload["planned_run"]!=config["planned_run"]):
        raise Failure("INFRA_FAILURE","MANIFEST_FROZEN_RUN_MISMATCH")
    trajectories=payload["trajectories"];tasks=payload["tasks"]
    if len(trajectories)!=payload["expected_trajectories"] or sum(len(t["task_ids"]) for t in trajectories)!=payload["expected_episodes"]:
        raise Failure("INFRA_FAILURE","MANIFEST_COUNT_MISMATCH")
    seen=set()
    ids={t["trajectory_id"] for t in trajectories}
    if len(ids)!=len(trajectories):raise Failure("INFRA_FAILURE","DUPLICATE_TRAJECTORY_ID")
    block_map={}
    for t in trajectories:block_map.setdefault(t["block_id"],[]).append(t)
    expected_blocks=8 if payload["planned_run"]=="SMOKE" else 32
    if len(block_map)!=expected_blocks:raise Failure("INFRA_FAILURE","BLOCK_COUNT_MISMATCH")
    for arms in block_map.values():
        if len(arms)!=5 or {a["architecture"] for a in arms}!={"B0","B1","B2","B3","B4"} or any(a["task_ids"]!=arms[0]["task_ids"] for a in arms):
            raise Failure("INFRA_FAILURE","MATCHED_BLOCK_MISMATCH")
    for key,task in tasks.items():
        private=task["record"]
        if key!=private["task_view"]["task_id"] or raw_sha(integer_dsl_bytes(private))!=task["sha256"]:
            raise Failure("INFRA_FAILURE","TASK_SEAL_MISMATCH")
        if private["latent_fingerprint"] in seen:raise Failure("INFRA_FAILURE","LATENT_DUPLICATE")
        seen.add(private["latent_fingerprint"])
        if verify_task(private["task_view"]["spec"])!=private["ground_truth"]:
            raise Failure("INFRA_FAILURE","GROUND_TRUTH_MISMATCH")
        spec=private["task_view"]["spec"]
        fingerprint=alpha_fingerprint(spec) if spec["family"]==FAMILIES[1] else raw_sha(integer_dsl_bytes(spec))
        if fingerprint!=private["latent_fingerprint"]:raise Failure("INFRA_FAILURE","LATENT_FINGERPRINT_MISMATCH")
        if parse_surface(private["task_view"]["surface_text"])!=spec:raise Failure("INFRA_FAILURE","SURFACE_SPEC_MISMATCH")
    for trajectory in trajectories:
        if len(set(trajectory["task_ids"]))!=len(trajectory["task_ids"]):raise Failure("INFRA_FAILURE","TRAJECTORY_DUPLICATE_ITEM")
        for index,task_id in enumerate(trajectory["task_ids"],1):
            p=tasks[task_id]["record"]
            expected=trajectory["first_family"] if index%2 else FAMILIES[1-FAMILIES.index(trajectory["first_family"])]
            if p["task_view"]["task_family"]!=expected or p["split"]!=("MAIN" if index<=payload["main_episodes"] else "TRANSFER"):
                raise Failure("INFRA_FAILURE","SCHEDULE_MISMATCH")
    return dict(status="PASS",trajectories=len(trajectories),episodes=payload["expected_episodes"],unique_tasks=len(tasks))
