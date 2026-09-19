"""Minimal lawful public-state capacity witness; no model invocation."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mrab_r1.prompts import Prompts
from mrab_r1.schemas import Schemas
from mrab_r1.config import OfflineTokenizer
from mrab_r1.surface import render


def witness():
    feedbacks=[]
    for i in range(1,32):
        family="SYMBOLIC_PIPELINE" if i%2 else "RULE_GRID"
        feedbacks.append(dict(episode_id="abcdefghijklmnopqrstuvwxyzABCDE"[i-1],episode_index=i,
            task_family=family,scope_id="s" if i%2 else "r",difficulty_scope="d",context_condition="x",
            chosen_action="SOLO",solo_correct=True,final_correct=True,tool_used=False,cost_units=0,
            outcome="CORRECT",prep_skip_reason=None,capability_configuration_ref="c",
            execution_mode="NO_PREP_INTERFACE",history_class="EMPTY" if i==1 else "NONEMPTY",tool_condition="SOLO_NO_TOOL"))
    task=dict(task_id="q",task_family="RULE_GRID",scope_id="r",difficulty_scope="d",context_condition="x",
        spec=dict(family="RULE_GRID",entities=["a","b"],properties=[dict(property_id="p",values=["u","v"])],constraints=[dict(kind="EQ",atom=dict(entity="a",property="p",value="u"))]),
        surface_text="placeholder")
    task["surface_text"]=render(task["spec"],"C")
    ledger=[]
    for scope,hclass in [("s","EMPTY"),("s","NONEMPTY"),("r","NONEMPTY")]:
        rows=[f for f in feedbacks if f["scope_id"]==scope and f["history_class"]==hclass]
        ledger.append(dict(scope_id=scope,n=len(rows),successes=len(rows),capability_configuration_ref="c",
            execution_mode="NO_PREP_INTERFACE",history_class=hclass,difficulty_scope="d",context_condition="x",tool_condition="SOLO_NO_TOOL"))
    state=dict(trajectory_id="t",episode_index=32,task_view=task,current_profile=None,profile_history=[],
        recent_episode_history=feedbacks[-10:],evidence_ledger=ledger,cumulative_cost=0,reflection_cost=0,
        tracker_state=None,reflexive_state=None,capability_configuration=dict(configuration_id="c",architecture_policy_id="p",
            execution_modes=["NO_PREP_INTERFACE"],history_policy="PUBLIC_BOUNDED_WITH_COMMON_EVIDENCE_INDEX_V02",prep_policy="NONE"),
        current_execution_mode="NO_PREP_INTERFACE",history_anchors=[],evidence_index=[dict(episode_id=f["episode_id"],feedback=f) for f in feedbacks])
    registry=Schemas();registry.validate(state,registry.ref("trajectory","agent_state"))
    request=Prompts().request("ACTION","B0",state)
    limit=Schemas(storage_patch=False).resolve(registry.ref("episode_record","call_usage"))["properties"]["request_bytes"]["maxLength"]
    return dict(kind="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT",architecture="B0",condition="C0",episode_index=32,
        public_state_schema_valid=True,request_characters=len(request.decode()),request_bytes=len(request),
        request_record_character_limit=limit,test_tokenizer_count=OfflineTokenizer().count(request),
        configured_input_token_cap=16384,exceeds_record_schema=len(request.decode())>limit,
        runtime_storage_patch="R1-STORAGE-REQUEST-01",runtime_request_character_cap=None,
        note="Short IDs, no profile/anchors/PREP; normal mandatory history and evidence index. Byte-quarter tokenizer only an offline witness, not a real model tokenizer.",
        state=state,request_utf8=request.decode())


if __name__=="__main__":
    data=witness()
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in data.items() if k not in {"state","request_utf8"}},indent=2))
