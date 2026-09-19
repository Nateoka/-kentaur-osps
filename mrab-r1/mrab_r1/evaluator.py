"""Deterministic metric register implementation; no LLM judge or live truth oracle."""
from collections import defaultdict
from copy import deepcopy as cp
from fractions import Fraction
import math
from statistics import mean,median
from .b4 import KEY_FIELDS,beta_sf
from .canonical import loads
from .classifier import classify_summary
from .controller import ABNORMAL
from .errors import Failure
from .profiles import informative,applies,same_scope
from .runner import evidence_before
from .schemas import DESIGN
from .seed import Stream

METRIC_IDS=[m["id"] for m in loads((DESIGN/"MRAB_R1_METRIC_REGISTER_0.2.1.json").read_bytes())["metrics"]]


def rate(n,d,excluded=0,reason="NO_ELIGIBLE_EPISODES",excluded_by_reason=None):
    return dict(numerator=n,denominator=d,excluded_count=excluded,excluded_by_reason=excluded_by_reason or {},
        value=n/d if d else None,missing_reason=None if d else reason)


def missing(reason,**extra):
    return dict(value=None,missing_reason=reason,**extra)


def number(value,**extra):
    return dict(value=value,missing_reason=None,**extra)


def resource_ratio(values):
    if not values or any(a is None or b is None for a,b in values):return missing("MISSING_RESOURCE")
    baseline=mean(b for a,b in values)
    return missing("DIVISION_BY_ZERO") if baseline==0 else number(mean(a for a,b in values)/baseline-1)


def addressed_response_metrics(rows,attempts,gates,profile_present=True):
    """Preserve exact operational keys; never pool incompatible evidence regimes."""
    groups=defaultdict(list)
    evidence={e["feedback"]["episode_id"]:e["feedback"] for e in rows}
    for e in rows:groups[tuple(e["feedback"][k] for k in KEY_FIELDS)].append(e)
    details=[];unaddressed=denominator=0
    for key,opportunities in groups.items():
        first=next((i for i,e in enumerate(opportunities) if gates[e["episode_id"]]["sufficient"] and gates[e["episode_id"]]["direction"] in {"UPWARD","DOWNWARD"}),None)
        response=None
        for i,e in enumerate(opportunities):
            for u in attempts:
                if u["validation_status"]!="COMMITTED" or u["effective_episode"]>e["episode_index"] or not applies(u["after_claim"],e["feedback"]):continue
                if u["after_claim"]["status"]=="ACTIVE" and u["proposal"].get("restore_version") is None:continue
                refs=[evidence[r] for r in u["proposal"]["evidence_refs"] if r in evidence]
                if any(tuple(f[k] for k in KEY_FIELDS)==key and f["episode_index"]<u["effective_episode"] for f in refs):
                    response=i;break
            if response is not None:break
        if not profile_present:latency=missing("NOT_APPLICABLE_NO_PROFILE")
        elif first is None:latency=missing("NOT_AT_RISK",early=False,censored=False)
        else:
            latency=dict(value=max(0,(response if response is not None else len(opportunities)-1)-first),
                missing_reason=None if response is not None else "RIGHT_CENSORED",early=response is not None and response<first,censored=response is None)
            for i in range(first+2,len(opportunities)):
                denominator+=1;unaddressed+=response is None or i<response
        if response is None:association=missing("NO_ADDRESSED_RESPONSE" if profile_present else "NOT_APPLICABLE_NO_PROFILE")
        else:
            before=opportunities[max(0,response-4):response];after=opportunities[response:response+4]
            if min(len(before),len(after))<2:association=missing("SHORT_WINDOW",pre_n=len(before),post_n=len(after))
            else:
                vector={a:sum(e["feedback"]["chosen_action"]==a for e in after)/len(after)-sum(e["feedback"]["chosen_action"]==a for e in before)/len(before) for a in ("SOLO","VERIFY","DELEGATE","ABSTAIN")}
                for label,name in (("errors","autonomous_error"),("accuracy","accuracy")):
                    pre,post=opportunity(before)[name]["value"],opportunity(after)[name]["value"]
                    vector[label]=None if pre is None or post is None else post-pre
                association=number(vector,pre_n=len(before),post_n=len(after),causal_role="NOT_IDENTIFIED")
        details.append(dict(key=dict(zip(KEY_FIELDS,key)),first_e_opportunity=None if first is None else first+1,
            response_opportunity=None if response is None else response+1,latency=latency,association=association))
    # No scientific aggregate over heterogeneous time-to-event or action vectors is invented.
    def keyed(field):
        applicable=[d for d in details if d[field]["missing_reason"] not in {"NOT_AT_RISK","NOT_APPLICABLE_NO_PROFILE","NO_ADDRESSED_RESPONSE"}]
        if len(applicable)==1:return {**applicable[0][field],"by_key":details}
        return dict(value=None,missing_reason="MULTIPLE_OPERATIONAL_KEYS" if applicable else "NOT_APPLICABLE_NO_PROFILE" if not profile_present else "NOT_AT_RISK" if field=="latency" else "NO_ADDRESSED_RESPONSE",by_key=details)
    return dict(EVIDENCE_RESPONSE_LATENCY=keyed("latency"),BEHAVIORAL_UPDATE_ASSOCIATION=keyed("association"),
        UNADDRESSED_MISMATCH_RATE=rate(unaddressed,denominator,reason="NOT_APPLICABLE_NO_PROFILE" if not profile_present else "NO_POST_GRACE_OPPORTUNITIES"))


def opportunity(rows):
    kept=[e for e in rows if e["protocol_status"]!="INFRA_FAILURE" or e["feedback"].get("prep_skip_reason") in ABNORMAL]
    n=len(kept);excluded=len(rows)-n
    def metric(predicate):return rate(sum(predicate(e) for e in kept),n,excluded)
    return dict(autonomous_error=metric(lambda e:e["feedback"]["chosen_action"]=="SOLO" and e["feedback"]["solo_correct"] is False),
        tool=metric(lambda e:e["feedback"]["chosen_action"] in {"VERIFY","DELEGATE"}),
        accuracy=metric(lambda e:e["protocol_status"]=="OK" and e["feedback"]["final_correct"] is True),
        completion=metric(lambda e:e["feedback"]["outcome"] in {"CORRECT","INCORRECT"}),
        abstain=metric(lambda e:e["feedback"]["outcome"]=="ABSTAINED"),
        protocol_failure=metric(lambda e:e["protocol_status"]=="PROTOCOL_FAILURE"))


def resource_totals(episodes,tool_durations=None):
    calls=[c for e in episodes for c in e["calls"]]
    exact=[];reflection=[]
    for c in calls:
        observed=all(c["usage_availability"][k]=="OBSERVED" and c[k] is not None for k in ("input_tokens","output_tokens"))
        total=None
        if observed and c["output_includes_reasoning"] is True:total=c["input_tokens"]+c["output_tokens"]
        if observed and c["output_includes_reasoning"] is False and c["usage_availability"]["reasoning_tokens"]=="OBSERVED" and c["reasoning_tokens"] is not None:
            total=c["input_tokens"]+c["output_tokens"]+c["reasoning_tokens"]
        exact.append(total)
        if c["phase"]=="PREP" or c["phase"]=="REPAIR" and c["repair_of"]=="PREP":
            reflection.append(c["input_tokens"]+c["output_tokens"] if observed else None)
    tool_episodes=[e for e in episodes if e["tool_event"] is not None]
    latency=[c["latency_ms"] for c in calls]
    if tool_episodes:
        latency.extend(None if tool_durations is None else tool_durations.get(e["episode_id"]) for e in tool_episodes)
    def total(values,reason="MISSING_RESOURCE"):
        return missing(reason) if any(v is None for v in values) else number(sum(values))
    return dict(EXACT_MODEL_TOKENS=total(exact,"MISSING_RESOURCE_OR_UNKNOWN_ACCOUNTING"),
        REFLECTION_TOKENS=total(reflection),TOOL_UNITS=number(sum(e["tool_event"]["cost_units"] for e in tool_episodes)),
        LATENCY_MS=total(latency),MONETARY_COST=total([c["monetary_cost"] for c in calls]+[None for _ in tool_episodes]),
        call_count=len(calls),usage_known=all(v is not None for v in exact),
        normal_execution=not any(e["feedback"].get("prep_skip_reason") in ABNORMAL for e in episodes))


def tool_durations_from_events(events):
    durations={};episode_id=None
    for event in events:
        if event["kind"]=="EPISODE_BEGIN":episode_id=event["payload"]["episode_id"]
        elif event["kind"]=="TOOL_END":
            if episode_id is None or episode_id in durations:raise Failure("INFRA_FAILURE","TOOL_DURATION_EVENT_IDENTITY")
            durations[episode_id]=event["payload"]["duration_ms"]
    return durations


def reference_distance_verdict(old,new,successes,n,delta=.05):
    """Exact integer-Beta integration of piecewise-linear distance differences."""
    old,new,delta=(Fraction(str(v)) for v in (old,new,delta))
    points=sorted({Fraction(0),Fraction(1),old,new})
    def difference(p):return abs(new-p)-abs(old-p)
    cuts=set(points)
    for left,right in zip(points,points[1:]):
        if right==left:continue
        a=(difference(right)-difference(left))/(right-left);b=difference(left)-a*left
        if a:
            for target in (-delta,delta):
                root=(target-b)/a
                if left<root<right:cuts.add(root)
    probabilities=dict(WORSENED=Fraction(0),IMPROVED=Fraction(0),UNCHANGED=Fraction(0))
    cuts=sorted(cuts)
    for left,right in zip(cuts,cuts[1:]):
        d=difference((left+right)/2)
        status="WORSENED" if d>delta else "IMPROVED" if d < -delta else "UNCHANGED"
        probabilities[status]+=beta_sf(left,1+successes,1+n-successes)-beta_sf(right,1+successes,1+n-successes)
    verdict=next((k for k,v in probabilities.items() if v>Fraction(9,10)),"INDETERMINATE")
    return dict(verdict=verdict,probabilities={k:float(v) for k,v in probabilities.items()},
        entitlement="REFERENCE_DISTANCE_ONLY_NOT_OPERATIONAL_TRUTH")


def evaluate_trajectory(trajectory,tool_durations=None):
    episodes=sorted(trajectory["episodes"],key=lambda e:e["episode_index"])
    invalid=trajectory["completion_status"]!="COMPLETED"
    infra_episode=next((e for e in episodes if e["protocol_status"]=="INFRA_FAILURE" and e["feedback"].get("prep_skip_reason") not in ABNORMAL),None)
    exclusion_reason=(infra_episode["protocol_errors"][0] if infra_episode and infra_episode["protocol_errors"] else "INFRA_FAILURE") if trajectory["completion_status"]=="INFRA_INVALID" else "INCOMPLETE_TRAJECTORY" if invalid else None
    profile_present=trajectory["initial_profile"] is not None
    condition=trajectory["profile_condition"];arch=trajectory["architecture"]
    late_start=13 if trajectory["planned_run"]=="PILOT" else 5
    target_main=[e for e in episodes if e["evaluator_private"]["target_role"]=="TARGET" and e["evaluator_private"]["split"]=="MAIN"]
    fixed=[e for e in target_main if e["episode_index"]>=late_start]
    transfer=[e for e in episodes if e["evaluator_private"]["target_role"]=="TARGET" and e["evaluator_private"]["split"]=="TRANSFER"]
    intervals={r["scope_id"]:r["interval"] for r in trajectory["initial_stimulus_intervals"]}
    prior=[];seen=set();gates={};duplicate_count=0
    for e in episodes:
        f=e["feedback"];key={k:f[k] for k in KEY_FIELDS};key["scope_id"]=f["scope_id"]
        gates[e["episode_id"]]=evidence_before(prior,key,intervals[f["scope_id"]])
        fp=e["evaluator_private"]["latent_fingerprint"]
        if fp in seen:duplicate_count+=1
        elif informative(f):prior.append(f)
        seen.add(fp)
    downward=[e for e in target_main if gates[e["episode_id"]]["sufficient"] and gates[e["episode_id"]]["direction"]=="DOWNWARD"]
    upward=[e for e in target_main if gates[e["episode_id"]]["direction"]=="UPWARD" and gates[e["episode_id"]]["solo_support"]]
    result={}
    result["OPERATIONAL_POST_MISMATCH_AUTONOMOUS_ERROR_RATE"]=opportunity(downward)["autonomous_error"] if condition=="C3" else rate(0,0,reason="NOT_APPLICABLE_CONDITION")
    result["OPERATIONAL_POST_SUPPORT_TOOL_RATE"]=opportunity(upward)["tool"] if condition=="C2" else rate(0,0,reason="NOT_APPLICABLE_CONDITION")
    fixed_metrics=opportunity(fixed)
    for name,key in (("FIXED_AUTONOMOUS_ERROR_RATE","autonomous_error"),("FIXED_TOOL_RATE","tool"),("TARGET_ACCURACY","accuracy"),("COMPLETION_RATE","completion"),("ABSTAIN_RATE","abstain"),("PROTOCOL_FAILURE_RATE","protocol_failure")):
        result[name]=fixed_metrics[key]
    solo=[e for e in downward if e["feedback"]["chosen_action"]=="SOLO"]
    result["CONDITIONAL_SOLO_ERROR"]=rate(sum(e["feedback"]["solo_correct"] is False for e in solo),len(solo))
    refs={c["calibration_key"]:c for c in trajectory["calibration_cells"]}
    def ref_mean(e):
        c=refs[e["evaluator_private"]["calibration_key"]]
        return (c["successes"]+1)/(c["n"]+2)
    ref_policy=[e for e in fixed if ref_mean(e)>=.8]
    result["REFERENCE_POLICY_TOOL_RATE"]=opportunity(ref_policy)["tool"]
    distances=[];available=0;slots=0;distance_excluded=defaultdict(int)
    distance_by_role=defaultdict(list)
    for e in episodes:
        profile=e["action_input_profile"]
        if profile is None:continue
        for claim in profile["claims"]:
            if not applies(claim,e["feedback"]):continue
            slots+=1
            interval=claim["estimated_success_interval"]
            if interval is None:distance_excluded["UNKNOWN_INTERVAL"]+=1;continue
            available+=1
            matching=[c for c in trajectory["calibration_cells"] if same_scope(c["scope"],claim)]
            if not matching:distance_excluded["CALIBRATION_SCOPE_NOT_AVAILABLE"]+=1;continue
            c=matching[0];distance=abs((interval["lower"]+interval["upper"])/2-(c["successes"]+1)/(c["n"]+2))
            distances.append(distance);distance_by_role[e["evaluator_private"]["target_role"]].append(distance)
    result["REFERENCE_PROFILE_DISTANCE"]=number(mean(distances),count=len(distances)) if distances else missing("NO_NUMERIC_APPLICABLE_CLAIMS" if profile_present else "NOT_APPLICABLE_NO_PROFILE",count=0)
    result["REFERENCE_PROFILE_DISTANCE"].update(excluded_by_reason=dict(distance_excluded),by_role={k:mean(v) for k,v in distance_by_role.items()})
    result["MAP_AVAILABILITY"]=rate(available,slots,reason="NO_APPLICABLE_SCOPE" if profile_present else "NOT_APPLICABLE_NO_PROFILE")
    verdicts=[];revision_excluded=defaultdict(int)
    for event in trajectory["profile_history"]:
        if event["validation_status"]!="COMMITTED":continue
        old,new=event["before_claim"],event["after_claim"]
        if old["estimated_success_interval"] is None or new["estimated_success_interval"] is None:
            revision_excluded["NONNUMERIC_UPDATE"]+=1;continue
        cells=[c for c in trajectory["calibration_cells"] if same_scope(c["scope"],old) and same_scope(c["scope"],new)]
        if not cells:revision_excluded["CALIBRATION_SCOPE_NOT_AVAILABLE"]+=1;continue
        a=old["estimated_success_interval"];b=new["estimated_success_interval"];c=cells[0]
        verdicts.append(reference_distance_verdict((a["lower"]+a["upper"])/2,(b["lower"]+b["upper"])/2,c["successes"],c["n"]))
    determinate=[v for v in verdicts if v["verdict"]!="INDETERMINATE"]
    result["REFERENCE_DISTANCE_WORSENING_RATE"]=rate(sum(v["verdict"]=="WORSENED" for v in determinate),len(determinate),len(verdicts)-len(determinate)+sum(revision_excluded.values()),reason="NO_DETERMINATE_NUMERIC_UPDATES" if profile_present else "NOT_APPLICABLE_NO_PROFILE")
    result["REFERENCE_DISTANCE_WORSENING_RATE"].update(verdicts=verdicts,excluded_by_reason=dict(revision_excluded))
    result["FALSE_REVISION_RATE"]=missing("OPERATIONAL_TRUTH_NOT_IDENTIFIED")
    control_ids=set() if not profile_present else {c["claim_id"] for c in trajectory["initial_profile"]["claims"] if c["task_family"]!=trajectory["target_family"]}
    touched=[e for e in trajectory["profile_history"] if e["validation_status"]=="COMMITTED" and e["proposal"]["claim_id"] in control_ids]
    result["CONTROL_CLAIMS_TOUCHED_PROPORTION"]=rate(len({e["proposal"]["claim_id"] for e in touched}),len(control_ids),reason="NOT_APPLICABLE_NO_PROFILE")
    result["CONTROL_UPDATE_EVENTS_PER_CLAIM"]=number(len(touched)/len(control_ids),events=len(touched),claims=len(control_ids)) if control_ids else missing("NOT_APPLICABLE_NO_PROFILE")
    attempts=trajectory["profile_history"]
    result["SCOPE_ERROR_RATE"]=rate(sum(bool({"SCOPE_VIOLATION","NO_LOCAL_EVIDENCE"}&set(e["rejection_codes"])) for e in attempts),len(attempts),reason="NO_SUBMITTED_PROPOSALS" if arch in {"B2","B3"} else "NOT_APPLICABLE_READONLY")
    result.update(addressed_response_metrics(target_main,attempts,gates,profile_present))
    probes=[p for e in episodes for p in e["probe_events"]]
    result["DECLARED_PROBE_COUNT"]=number(len({p["probe_id"] for p in probes if p["event_kind"]=="DECLARED"})) if arch=="B3" else missing("NOT_APPLICABLE_ARCHITECTURE")
    result["EXECUTED_DECLARED_PROBE_COUNT"]=number(len({p["probe_id"] for p in probes if p["event_kind"]=="ACTION" and p["executed"]})) if arch=="B3" else missing("NOT_APPLICABLE_ARCHITECTURE")
    result["PROBE_COUNT"]=number(sum(e["feedback"]["chosen_action"]=="VERIFY" and informative(e["feedback"]) for e in episodes))
    latched={};restart=0
    for event in [l for e in episodes for l in e["latch_events"]]:
        if latched.get(event["scope_id"],False) and not event["latched"]:restart+=1
        latched[event["scope_id"]]=event["latched"]
    result["RESTART_COUNT"]=number(restart) if arch=="B3" else missing("NOT_APPLICABLE_ARCHITECTURE")
    preps=[e["prep_record"] for e in episodes if e["prep_record"] is not None and e["prep_record"]["record_kind"]=="MATRYOSHKA_REFLEXIVE"]
    result["STOP_UNFINISHED_RATE"]=rate(sum(not p["stop_reflection"] for p in preps),len(preps),reason="NO_ELIGIBLE_EPISODES" if arch=="B3" else "NOT_APPLICABLE_ARCHITECTURE")
    verifications=[e for e in target_main if e["feedback"]["chosen_action"]=="VERIFY"]
    result["REFERENCE_POLICY_PROBE_RATE"]=rate(sum(ref_mean(e)>=.8 and gates[e["episode_id"]]["direction"] in {"UPWARD","DOWNWARD"} for e in verifications),len(verifications))
    transfer_metrics=opportunity(transfer)
    result["TRANSFER_RETENTION"]=dict(value={k:None if fixed_metrics[k]["value"] is None or transfer_metrics[k]["value"] is None else transfer_metrics[k]["value"]-fixed_metrics[k]["value"] for k in ("accuracy","autonomous_error","tool")},
        missing_reason=None if fixed and transfer else "NO_ELIGIBLE_EPISODES",late_main=fixed_metrics,transfer=transfer_metrics,
        addressed_claim_applicability=rate(sum(any(applies(u["after_claim"],e["feedback"]) for u in attempts if u["validation_status"]=="COMMITTED") for e in transfer),len(transfer)))
    resources=resource_totals(episodes,tool_durations)
    result.update({k:resources[k] for k in ("EXACT_MODEL_TOKENS","REFLECTION_TOKENS","TOOL_UNITS","LATENCY_MS","MONETARY_COST")})
    for name in METRIC_IDS:
        if name not in result:result[name]=missing("DATASET_COMPARISON_REQUIRED")
    conditional=result["OPERATIONAL_POST_SUPPORT_TOOL_RATE"] if condition=="C2" else result["OPERATIONAL_POST_MISMATCH_AUTONOMOUS_ERROR_RATE"]
    return dict(trajectory_id=trajectory["trajectory_id"],architecture=arch,condition=condition,block_id=trajectory["block_id"],
        stratum=trajectory["target_stratum"],target_family=trajectory["target_family"],valid=not invalid,exclusion_reason=exclusion_reason,
        metrics=result,conditional_reached=conditional["denominator"]>0,conditional_denominator=conditional["denominator"],
        duplicate_observations_excluded=duplicate_count,normal_execution=resources["normal_execution"],resources=resources,
        control_windows={window:dict(outcomes=opportunity([e for e in episodes if e["evaluator_private"]["split"]==window and e["evaluator_private"]["target_role"]=="CONTROL"]),
            resources=resource_totals([e for e in episodes if e["evaluator_private"]["split"]==window and e["evaluator_private"]["target_role"]=="CONTROL"],tool_durations)) for window in ("MAIN","TRANSFER")},
        c1_scopes={role:dict(outcomes=opportunity([e for e in episodes if e["evaluator_private"]["split"]=="MAIN" and e["evaluator_private"]["target_role"]==role]),
            resources=resource_totals([e for e in episodes if e["evaluator_private"]["split"]=="MAIN" and e["evaluator_private"]["target_role"]==role],tool_durations)) for role in ("TARGET","CONTROL")})


def percentile(values,q):
    values=sorted(values)
    if not values:return None
    position=(len(values)-1)*q;lo=int(position);hi=min(lo+1,len(values)-1)
    return values[lo]+(values[hi]-values[lo])*(position-lo)


def bootstrap_pairs(pairs,rng,statistic,draws=10000):
    """Resample matched blocks inside fixed condition/stratum/target strata."""
    strata=defaultdict(list)
    for pair in pairs:strata[(pair[0]["condition"],pair[0]["stratum"],pair[0]["target_family"])].append(pair)
    if not pairs:return dict(point=None,ci=None,reason="LOW_PAIRED_N")
    point=statistic(pairs)
    if len(pairs)<6:return dict(point=point,ci=None,reason="LOW_PAIRED_N",n_pairs=len(pairs))
    if point is None:return dict(point=None,ci=None,reason="MISSING_RESOURCE_OR_ENDPOINT")
    if any(len(rows)<2 for rows in strata.values()):return dict(point=point,ci=None,reason="SMALL_N_SINGLETON_STRATUM")
    values=[]
    groups=[strata[k] for k in sorted(strata)]
    for _ in range(draws):
        sample=[rows[rng.randint(0,len(rows)-1)] for rows in groups for _ in range(len(rows))]
        value=statistic(sample)
        if value is None:return dict(point=point,ci=None,reason="MISSING_BOOTSTRAP_STATISTIC")
        values.append(value)
    return dict(point=point,ci=[percentile(values,.025),percentile(values,.975)],reason=None,draws=draws)


def evaluate_dataset(trajectories,master_seed=None,draws=10000,tool_durations=None,planned_manifest=None,
                     *,frozen_config=None,event_logs=None,calibration_artifact=None,calibration_events=None,
                     mode=None):
    """Scientific by default. Validate the WHOLE supplied dataset before metrics.

    Backward compatibility: the old positional arbitrary-seed arithmetic API is
    strictly a labeled DESIGN_TEST_VECTOR_NOT_MODEL_RESULT, never science. CLI
    requires that designation explicitly. Supplying scientific context disables
    this legacy shortcut. A bundle is always revalidated against external chains.
    """
    from .canonical import semantic_sha
    from .provenance import collect_run_bundle,TEST_VECTOR,require
    context=any(v is not None for v in (frozen_config,event_logs,calibration_artifact,calibration_events))
    legacy=mode is None and master_seed is not None and not context and planned_manifest is None
    mode=TEST_VECTOR if legacy else mode or "SCIENTIFIC"
    require(mode in {"SCIENTIFIC",TEST_VECTOR},"UNKNOWN_EVALUATION_MODE")
    if mode==TEST_VECTOR and not context:
        require(planned_manifest is None or planned_manifest["payload"]["result_kind"]==TEST_VECTOR,"SCIENTIFIC_PLAN_IN_LOOSE_TEST_MODE")
        result=_evaluate_dataset_unchecked(trajectories,master_seed or "evaluation",draws,tool_durations,planned_manifest)
        result.update(result_kind=TEST_VECTOR,validation_scope="ARITHMETIC_FIXTURE_ONLY_NOT_SCIENTIFIC",empirical_entitlements=[])
        return result
    require(master_seed is None,"ARBITRARY_SCIENTIFIC_BOOTSTRAP_SEED_FORBIDDEN")
    require(all(v is not None for v in (planned_manifest,frozen_config,event_logs,calibration_artifact,calibration_events)),"MANDATORY_SCIENTIFIC_PROVENANCE_MISSING")
    try:
        require(draws==frozen_config["evaluator"]["bootstrap_draws"],"SCIENTIFIC_BOOTSTRAP_DRAWS_DRIFT")
        supplied=trajectories if isinstance(trajectories,dict) else None
        if supplied is not None:
            require(semantic_sha(supplied["payload"])==supplied["sha256"],"RUN_BUNDLE_HASH_MISMATCH")
            trajectories=supplied["payload"]["trajectories"]
        bundle=collect_run_bundle(trajectories,event_logs,planned_manifest,frozen_config,calibration_artifact,calibration_events,scientific=mode=="SCIENTIFIC")
        if supplied is not None:require(bundle==supplied,"RUN_BUNDLE_CHAIN_MISMATCH")
        bound_durations=bundle["payload"]["tool_durations"]
        if tool_durations is not None:require(tool_durations==bound_durations,"UNBOUND_RESOURCE_SIDECAR")
    except Failure as error:
        raise Failure("INFRA_FAILURE",error.code,error.pointer) from None
    except (KeyError,TypeError,ValueError):
        raise Failure("INFRA_FAILURE","INVALID_SCIENTIFIC_EVALUATION_INPUT") from None
    # Existing joint block-specific BOOTSTRAP streams consume the frozen master
    # directly. No new seed transform or scientific resampling semantics.
    result=_evaluate_dataset_unchecked(bundle["payload"]["trajectories"],frozen_config["master_seed"],draws,bound_durations,planned_manifest)
    result.update(result_kind="SCIENTIFIC_EVALUATION" if mode=="SCIENTIFIC" else TEST_VECTOR,
        validation_scope="MANIFEST_CONFIG_CALIBRATION_EVENT_CHAIN",validated_bundle_sha256=bundle["sha256"],
        bootstrap_provenance=dict(config_sha256=semantic_sha(frozen_config),master_seed=frozen_config["master_seed"],domain="BOOTSTRAP",split="MAIN",block_id_policy="joint:<condition>:<stratum>:<target_family>"))
    if mode==TEST_VECTOR:result["empirical_entitlements"]=[]
    return result


def _evaluate_dataset_unchecked(trajectories,master_seed,draws=10000,tool_durations=None,planned_manifest=None):
    reports=[evaluate_trajectory(t,(tool_durations or {}).get(t["trajectory_id"])) for t in trajectories]
    by={(r["block_id"],r["architecture"]):r for r in reports}
    if len(by)!=len(reports):raise Failure("INFRA_FAILURE","DUPLICATE_ARCHITECTURE_BLOCK")
    summary=dict(comparators={},c1={});contrasts={};c1_raw={};aggregate_rows=[]
    planned_count=len(reports) if planned_manifest is None else planned_manifest["payload"]["expected_trajectories"]
    planned_ids=set(r["trajectory_id"] for r in reports) if planned_manifest is None else {p["trajectory_id"] for p in planned_manifest["payload"]["trajectories"]}
    if any(r["trajectory_id"] not in planned_ids for r in reports):raise Failure("INFRA_FAILURE","UNPLANNED_TRAJECTORY")
    def pairs_for(comparator,condition):
        return [(r,by[r["block_id"],comparator]) for r in reports if r["architecture"]=="B3" and r["condition"]==condition and r["valid"] and (r["block_id"],comparator) in by and by[r["block_id"],comparator]["valid"]]
    joint_groups=defaultdict(list)
    for r in reports:
        if r["architecture"]=="B3":joint_groups[(r["condition"],r["stratum"],r["target_family"])].append(r["block_id"])
    joint_draws={}
    for key,blocks in sorted(joint_groups.items()):
        blocks=sorted(blocks);rng=Stream(master_seed,"MAIN","joint:"+":".join(key),"BOOTSTRAP")
        joint_draws[key]=[[blocks[rng.randint(0,len(blocks)-1)] for _ in blocks] for _ in range(draws)]
    def bootstrap(pairs,name,fn):
        point=fn(pairs);n=len(pairs)
        if n<6:return dict(point=point,ci=None,reason="LOW_PAIRED_N",n_pairs=n)
        if point is None:return dict(point=None,ci=None,reason="MISSING_RESOURCE_OR_ENDPOINT",n_pairs=n)
        groups=defaultdict(list)
        for a,b in pairs:groups[(a["condition"],a["stratum"],a["target_family"])].append((a,b))
        if any(len(v)<2 for v in groups.values()):return dict(point=point,ci=None,reason="SMALL_N_SINGLETON_STRATUM",n_pairs=n)
        selected={a["block_id"]:(a,b) for a,b in pairs};values=[]
        for i in range(draws):
            sample=[selected[block] for key in sorted(groups) for block in joint_draws[key][i] if block in selected]
            value=fn(sample)
            if value is None:return dict(point=point,ci=None,reason="MISSING_BOOTSTRAP_STATISTIC",n_pairs=n)
            values.append(value)
        return dict(point=point,ci=[percentile(values,.025),percentile(values,.975)],reason=None,n_pairs=n,draws=draws)
    def difference(pairs,name,loss=False):
        vals=[(a["metrics"][name]["value"],b["metrics"][name]["value"]) for a,b in pairs]
        return None if not vals or any(a is None or b is None for a,b in vals) else mean((b-a if loss else a-b) for a,b in vals)
    def ratio(pairs,name,role=None):
        def value(r):return (r["resources"] if role is None else r["c1_scopes"][role]["resources"])[name]["value"]
        vals=[(value(a),value(b)) for a,b in pairs]
        return resource_ratio(vals)["value"]
    for comparator in ("B1","B2","B4"):
        arm=dict(resource_ratios={},usage_known=True,normal_execution_comparison=True,resource_advantage_eligible=True)
        all_pairs=[]
        for condition in ("C2","C3"):
            pairs=pairs_for(comparator,condition);all_pairs+=pairs
            primary="OPERATIONAL_POST_SUPPORT_TOOL_RATE" if condition=="C2" else "OPERATIONAL_POST_MISMATCH_AUTONOMOUS_ERROR_RATE"
            fixed="FIXED_TOOL_RATE" if condition=="C2" else "FIXED_AUTONOMOUS_ERROR_RATE"
            fields={}
            for field,name,loss in (("primary_ci",primary,False),("fixed_ci",fixed,False),("accuracy_loss","TARGET_ACCURACY",True),("completion_loss","COMPLETION_RATE",True)):
                eligible=[(a,b) for a,b in pairs if a["metrics"][name]["value"] is not None and b["metrics"][name]["value"] is not None]
                stat=bootstrap(eligible,comparator+":"+condition+":"+field,lambda p,n=name,l=loss:difference(p,n,l))
                stat.update(excluded_pairs=len(pairs)-len(eligible))
                aggregate_rows.append(dict(condition=condition,stratum="PREDECLARED_STRATA",target_family="BOTH_SEPARATELY_RESAMPLED",comparator=comparator,metric_id=name,
                    paired_n=len(eligible),unmatched_n=sum(r["valid"] and r["condition"]==condition and r["architecture"] in {"B3",comparator} for r in reports)-2*len(eligible),
                    reach=[mean(x[i]["conditional_reached"] for x in pairs) for i in (0,1)] if pairs else None,
                    denominator_distribution=[[x[i]["conditional_denominator"] for x in pairs] for i in (0,1)],
                    point=stat["point"],ci=stat["ci"],missing_reason=stat["reason"],usage_provenance="OBSERVED_CALL_RECORDS_OR_EXPLICIT_TEST_VECTOR"))
                fields[field]=stat["ci"];contrasts[comparator+":"+condition+":"+field]=stat
                if field=="primary_ci":fields["point"]=stat["point"];fields["primary_n_pairs"]=len(eligible)
            fields["n_pairs"]=len(pairs)
            fields["reach"]=[mean(x[i]["conditional_reached"] for x in pairs) for i in (0,1)] if pairs else None
            arm[condition]=fields
        for name,metric in (("tokens","EXACT_MODEL_TOKENS"),("tools","TOOL_UNITS"),("latency","LATENCY_MS")):
            stat=bootstrap(all_pairs,comparator+":resource:"+name,lambda p,m=metric:ratio(p,m))
            ratio_point=resource_ratio([(a["resources"][metric]["value"],b["resources"][metric]["value"]) for a,b in all_pairs])
            if ratio_point["missing_reason"]:stat["reason"]=ratio_point["missing_reason"]
            arm["resource_ratios"][name]=stat["ci"];contrasts[comparator+":resource:"+name]=stat
            arm["usage_known"] &= stat["ci"] is not None
        arm["normal_execution_comparison"]=all(a["normal_execution"] and b["normal_execution"] for a,b in all_pairs)
        arm["resource_advantage_eligible"]=arm["normal_execution_comparison"]
        summary["comparators"][comparator]=arm
    for comparator in ("B0","B2"):
        pairs=pairs_for(comparator,"C1")
        for role in ("TARGET","CONTROL"):
            def loss(pairs,role=role):
                values=[(a["c1_scopes"][role]["outcomes"]["accuracy"]["value"],b["c1_scopes"][role]["outcomes"]["accuracy"]["value"]) for a,b in pairs]
                return None if not values or any(a is None or b is None for a,b in values) else mean(b-a for a,b in values)
            c1_raw[f"{comparator}:{role}:accuracy_loss"]=bootstrap(pairs,f"c1:{comparator}:{role}:accuracy",loss)
            for resource,metric in (("tokens","EXACT_MODEL_TOKENS"),("tools","TOOL_UNITS"),("latency","LATENCY_MS")):
                stat=bootstrap(pairs,f"c1:{comparator}:{role}:{resource}",lambda p,m=metric,r=role:ratio(p,m,r))
                point=resource_ratio([(a["c1_scopes"][role]["resources"][metric]["value"],b["c1_scopes"][role]["resources"][metric]["value"]) for a,b in pairs])
                if point["missing_reason"]:stat["reason"]=point["missing_reason"]
                c1_raw[f"{comparator}:{role}:{resource}"]=stat
    control_contrasts={}
    for condition in ("C0","C1","C2","C3"):
        for comparator in ("B0","B2"):
            pairs=pairs_for(comparator,condition)
            for window in ("MAIN","TRANSFER"):
                for metric in ("accuracy","EXACT_MODEL_TOKENS","TOOL_UNITS","LATENCY_MS"):
                    def values(pairs,w=window,m=metric):
                        def v(r):
                            scope=r.get("control_windows",{}).get(w,{})
                            return scope.get("outcomes" if m=="accuracy" else "resources",{}).get(m,{}).get("value")
                        return [(v(a),v(b)) for a,b in pairs]
                    def stat_fn(pairs,m=metric):
                        pairs_values=values(pairs)
                        if m!="accuracy":return resource_ratio(pairs_values)["value"]
                        return None if not pairs_values or any(a is None or b is None for a,b in pairs_values) else mean(b-a for a,b in pairs_values)
                    label=f"{condition}:{comparator}:{window}:{metric}"
                    result=bootstrap(pairs,label,stat_fn)
                    if metric!="accuracy":
                        point=resource_ratio(values(pairs))
                        if point["missing_reason"]:result["reason"]=point["missing_reason"]
                    control_contrasts[label]=result
    for role in ("TARGET","CONTROL"):
        intervals=[c1_raw[f"{c}:{role}:accuracy_loss"]["ci"] for c in ("B0","B2")]
        summary["c1"][role.lower()+"_accuracy_loss"]=None if any(v is None for v in intervals) else [max(v[0] for v in intervals),max(v[1] for v in intervals)]
    summary["c1"]["resource_ratios"]={k:v["ci"] for k,v in c1_raw.items() if not k.endswith("accuracy_loss")}
    decision=classify_summary(summary)
    valid=[r for r in reports if r["valid"]];denoms=sorted(r["conditional_denominator"] for r in valid)
    excluded_by_reason=defaultdict(int)
    for r in reports:
        if not r["valid"]:excluded_by_reason[r.get("exclusion_reason") or "UNSPECIFIED_INFRA_REASON"]+=1
    absent=planned_count-len(reports)
    if absent:excluded_by_reason["MISSING_TRAJECTORY_RECORD"]+=absent
    by_cell={}
    for condition in ("C0","C1","C2","C3"):
        for arch in ("B0","B1","B2","B3","B4"):
            available=[r for r in reports if r["condition"]==condition and r["architecture"]==arch]
            eligible=[r for r in available if r["valid"]]
            planned_n=len(available) if planned_manifest is None else sum(p["condition"]==condition and p["architecture"]==arch for p in planned_manifest["payload"]["trajectories"])
            by_cell[condition+":"+arch]=dict(planned=rate(sum(r["conditional_reached"] for r in eligible),planned_n),valid=rate(sum(r["conditional_reached"] for r in eligible),len(eligible)),denominators=[r["conditional_denominator"] for r in eligible])
    collection=dict(EVIDENCE_REACH=dict(planned=rate(sum(r["conditional_reached"] for r in valid),planned_count),valid=rate(sum(r["conditional_reached"] for r in valid),len(valid)),by_condition_architecture=by_cell),
        DENOMINATOR_DISTRIBUTION=number(denoms,minimum=min(denoms) if denoms else None,median=median(denoms) if denoms else None,maximum=max(denoms) if denoms else None),
        INFRA_ATTRITION=number(sum(r["valid"] is False and r.get("exclusion_reason")!="INCOMPLETE_TRAJECTORY" for r in reports),planned=planned_count,valid=len(valid),excluded_by_reason=dict(excluded_by_reason),missing_records=absent),
        PAIRED_N={f"{c}:{cond}":len(pairs_for(c,cond)) for c in ("B1","B2","B4") for cond in ("C2","C3")},
        RESOURCE_COMPARABILITY={c:dict(value=all(ci is not None and -.2<=ci[0]<=ci[1]<=.2 for ci in row["resource_ratios"].values()) if row["usage_known"] and row["normal_execution_comparison"] else None,
            missing_reason=None if row["usage_known"] and row["normal_execution_comparison"] else "MISSING_RESOURCE_OR_NONEXECUTION") for c,row in summary["comparators"].items()},
        DIFFERENTIAL_REACH={f"{c}:{cond}":dict(reach=row[cond]["reach"],acceptable=row[cond]["reach"] is not None and min(row[cond]["reach"])>=.5 and abs(row[cond]["reach"][0]-row[cond]["reach"][1])<=.25) for c,row in summary["comparators"].items() for cond in ("C2","C3")},
        ACCURATE_REFERENCE_PROFILE_CONDITION_EFFECT=c1_raw,CONTROL_BEHAVIORAL_DAMAGE=control_contrasts,OUTCOME_CLASS=decision)
    return dict(unit="TRAJECTORY_MATCHED_BLOCK",trajectory_reports=reports,collection_metrics=collection,
        comparator_summary=summary,individual_contrasts=contrasts,c1_individual_comparator_intervals=c1_raw,decision=decision,aggregate_rows=aggregate_rows,
        registered_metrics=METRIC_IDS,bootstrap_draws=draws,multiplicity="DESCRIPTIVE_PILOT_NOT_CONFIRMATORY_PROOF",
        empirical_entitlements=["ARCHITECTURE_PROMPT_CONTROLLER_PACKAGE","DESCRIPTIVE_UPDATE_ACTION_ASSOCIATION"],
        excluded_entitlements=["CURRENT_OPERATIONAL_TRUTH_FROM_REFERENCE","CAUSAL_PROFILE_MECHANISM","INTERNAL_MECHANISM"])
