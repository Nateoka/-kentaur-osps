"""Allowlist state construction from public observations and own commit events."""
from copy import deepcopy as cp
from .b4 import KEY_FIELDS
from .profiles import informative
from .errors import Failure


def key_for(task_view,configuration,mode,has_history):
    return dict(task_family=task_view["task_family"],scope_id=task_view["scope_id"],
        difficulty_scope=task_view["difficulty_scope"],context_condition=task_view["context_condition"],
        tool_condition="SOLO_NO_TOOL",capability_configuration_ref=configuration["configuration_id"],
        execution_mode=mode,history_class="NONEMPTY" if has_history else "EMPTY")


def history_state(trajectory_id,index,task_view,profile_store,feedbacks,configuration,
                  mode,architecture,controller,tracker,all_calls,tool_units):
    if len(feedbacks)>32 or len(profile_store.attempts)>32:
        raise Failure("CONFIGURATION_FAILURE","PUBLIC_HISTORY_OVERFLOW")
    ledger={}
    for f in feedbacks:
        if not informative(f):continue
        key=tuple(f[k] for k in KEY_FIELDS)
        entry=ledger.setdefault(key,{k:cp(f[k]) for k in ("scope_id","difficulty_scope","context_condition","tool_condition","capability_configuration_ref","execution_mode","history_class")})
        entry["n"]=entry.get("n",0)+1;entry["successes"]=entry.get("successes",0)+int(f["solo_correct"])
    reflection=[c for c in all_calls if c["phase"]=="PREP" or c["phase"]=="REPAIR" and c["repair_of"]=="PREP"]
    reflection_cost=None if any(c["input_tokens"] is None or c["output_tokens"] is None for c in reflection) else sum(c["input_tokens"]+c["output_tokens"] for c in reflection)
    tracker_state=None
    if architecture=="B4":
        tracker_state=[]
        for key,counts in sorted(tracker.cells.items()):
            fields=dict(zip(KEY_FIELDS,key));fields.pop("task_family")
            # scope_id is explicit in feedback/task addresses, not inferred from a condition.
            scope=next((f["scope_id"] for f in feedbacks if tuple(f[k] for k in KEY_FIELDS)==key),task_view["scope_id"])
            tracker_state.append(dict(scope_id=scope,**fields,successes=counts["successes"],failures=counts["failures"],
                opportunities=counts["opportunity"],alpha=1+counts["successes"],beta=1+counts["failures"]))
    return dict(trajectory_id=trajectory_id,episode_index=index,task_view=cp(task_view),
        current_profile=cp(profile_store.current),profile_history=cp(profile_store.attempts[-10:]),
        recent_episode_history=cp(feedbacks[-10:]),evidence_ledger=list(ledger.values()),
        cumulative_cost=tool_units,reflection_cost=reflection_cost,tracker_state=tracker_state,
        reflexive_state=controller.public_state() if architecture=="B3" else None,
        capability_configuration=cp(configuration),current_execution_mode=mode,
        history_anchors=profile_store.anchors(),evidence_index=[dict(episode_id=f["episode_id"],feedback=cp(f)) for f in feedbacks])
