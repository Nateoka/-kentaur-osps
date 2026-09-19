"""SEARCH/CONFIRM engine, usable offline with explicitly scripted providers."""
from copy import deepcopy as cp
from math import factorial,comb,fsum
from .b4 import beta_sf
from .calls import EpisodeCalls
from .config import OfflineTokenizer,freeze
from .errors import Failure
from .manifest import FAMILIES
from .profiles import ProfileStore
from .controller import Controller
from .b4 import Tracker
from .prompts import Prompts
from .state import history_state
from .answers import normalize_answer
from .tasks import verify_task,generate_symbolic,generate_grid
from .canonical import semantic_sha,integer_dsl_bytes,raw_sha
from .seed import Stream
from .surface import relabel,render
from .generator_options import resolve_options


def beta_quantile(q,a,b):
    # Integer-Beta CDF is a binomial tail; fsum avoids Fraction growth during
    # quantile search. Live evidence gates still use exact rational arithmetic.
    n=a+b-1;coefficients=[(j,comb(n,j)) for j in range(a,n+1)]
    low,high=0.,1.
    for _ in range(60):
        mid=(low+high)/2
        cdf=fsum(c*mid**j*(1-mid)**(n-j) for j,c in coefficients)
        if cdf<q:low=mid
        else:high=mid
    return (low+high)/2


def calibration_plan(config):
    families=[]
    for n in config["generator_options"]["symbolic_sizes"]:
        for length in config["generator_options"]["symbolic_lengths"]:
            families.append(dict(family="SYMBOLIC_PIPELINE",difficulty=dict(n=n,length=length)))
    grid=sorted([(factorial(n)**k,n,k) for n in config["generator_options"]["grid_sizes"] for k in config["generator_options"]["grid_properties"] if factorial(n)**k<=config["generator_options"]["max_grid_assignments"]])
    families += [dict(family="RULE_GRID",difficulty=dict(n=n,k=k)) for _,n,k in grid]
    return dict(status="PLAN_ONLY_NOT_EXECUTED",search_n=40,confirm_n=200,candidate_order=families,
        cells=[dict(architecture=a,family=f,band=b,confirm_n=200) for a in ("B0","B1","B2","B3","B4") for f in FAMILIES for b in ("HIGH","MID")],
        confirm_measurements=4000,confirm_primary_calls=6400,tools_allowed=False,profile_allowed=False,
        history_allowed=False,forced_action="SOLO",independent_confirmation_required=True)


def confirmation_gate(counts,config):
    """counts has all 20 cells and the actual common resolved tuple identity."""
    expected={(a,f,b) for a in ("B0","B1","B2","B3","B4") for f in FAMILIES for b in ("HIGH","MID")}
    if {(r["architecture"],r["family"],r["band"]) for r in counts}!=expected or len(counts)!=20:
        raise Failure("CALIBRATION_NOT_FEASIBLE","INCOMPLETE_CONFIRMATION_MATRIX")
    output=[]
    for row in counts:
        n,s=row["n"],row["successes"]
        if type(n) is not int or n!=200 or type(s) is not int or not 0<=s<=n:
            raise Failure("CALIBRATION_NOT_FEASIBLE","INVALID_CONFIRMATION_COUNTS")
        mean=(s+1)/(n+2);low=beta_quantile(.025,1+s,1+n-s);high=beta_quantile(.975,1+s,1+n-s)
        band=config["calibration_bands"][row["band"]]
        if not band["lower"]<=mean<=band["upper"] or high-low>.16:
            raise Failure("CALIBRATION_NOT_FEASIBLE","BAND_OR_INTERVAL_WIDTH_FAILED")
        output.append(dict(**cp(row),posterior_mean=mean,interval=[low,high]))
    for family in FAMILIES:
        for band in ("HIGH","MID"):
            if len({r["tuple_sha256"] for r in counts if r["family"]==family and r["band"]==band})!=1:
                raise Failure("CALIBRATION_NOT_FEASIBLE","DIFFICULTY_NOT_COMMON_ACROSS_ARCHITECTURES")
    return dict(status="FEASIBLE_FOR_SUPPLIED_COUNTS",cells=output,
        result_kind="CALLER_MUST_DISTINGUISH_SCRIPTED_FROM_EMPIRICAL")


class CalibrationEngine:
    def __init__(self,config,provider,event_sink,tokenizer=None,enable_real_provider=False,content=None,pre_lock=None):
        self.config,self.provider,self.sink=cp(config),provider,event_sink
        self.tokenizer=tokenizer or OfflineTokenizer();self.prompts=Prompts();self.sequence=0
        if provider.kind not in {"FAKE","REPLAY"}:
            if not enable_real_provider:raise Failure("CONFIGURATION_FAILURE","REAL_CALIBRATION_DISABLED")
            if pre_lock is not None:
                from .config import verify_calibration_lock
                verify_calibration_lock(pre_lock,config)
            else:freeze(config,content or {})
            if tokenizer is None:raise Failure("CONFIGURATION_FAILURE","REAL_TOKENIZER_REQUIRED")
            from .identity import verify_frozen_implementation
            verify_frozen_implementation(config,provider,tokenizer)

    def next_sequence(self):
        self.sequence+=1
        return self.sequence

    def measurement(self,item,architecture,index,phase="SEARCH",block_id="calibration"):
        """item is sealed task_view/ground_truth supplied by split-isolated generator."""
        config=cp(self.config["capability_configurations"][architecture])
        if verify_task(item["task_view"]["spec"])!=item["ground_truth"]:
            raise Failure("INFRA_FAILURE","CALIBRATION_TASK_TRUTH_MISMATCH")
        if self.tokenizer.count(integer_dsl_bytes(item["task_view"]))>4096:
            raise Failure("CONFIGURATION_FAILURE","CALIBRATION_TASK_PAYLOAD_OVERFLOW")
        mode="PREP_EXECUTED" if architecture in {"B1","B2","B3"} else "NO_PREP_INTERFACE"
        profile=ProfileStore(None)
        state=history_state(f"measurement:{index}",1,item["task_view"],profile,[],config,None,
            architecture,Controller(self.next_sequence),Tracker(),[],0)
        calls=EpisodeCalls(self.provider,self.prompts,self.config,self.tokenizer,architecture,f"cal:{block_id}:{architecture}:{index}",self.next_sequence,self.sink,
            dict(split="CALIBRATION_"+phase,block_id=block_id,item_index=index))
        prep=None;answer=None;failure=None
        try:
            if architecture in {"B1","B2","B3"}:
                prep=calls.structured(self.prompts.request("PREP",architecture,state,calibration=True),"PREP")
                if prep.get("proposal") is not None:
                    raise Failure("PROTOCOL_FAILURE","CALIBRATION_PROFILE_UPDATE_DISABLED")
            state["current_execution_mode"]=mode
            answer=calls.structured(self.prompts.request("ACTION",architecture,state,prep,fixed_action="SOLO" if architecture=="B4" else None,calibration=True),"ACTION","SOLO")
            answer["solo_answer"]=normalize_answer(item["task_view"]["spec"],answer["solo_answer"])
        except Failure as error:
            failure=error.as_dict()
            if error.kind in {"INFRA_FAILURE","CONFIGURATION_FAILURE"}:
                self.sink("CALIBRATION_FAILURE",failure)
                raise
        record=dict(measurement_id=f"measurement:{block_id}:{architecture}:{index}",architecture=architecture,phase=phase,block_id=block_id,item_index=index,
            task_id=item["task_view"]["task_id"],solo_correct=answer is not None and answer["solo_answer"]==item["ground_truth"],
            calls=calls.calls,failure=failure,profile=None,history=[],commits=[],tool_events=[],
            artifact_kind="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT" if self.provider.kind in {"FAKE","REPLAY"} else "REFERENCE_CALIBRATION_MEASUREMENT")
        self.sink("CALIBRATION_MEASUREMENT",record)
        return record

    def measure_cell(self,items,architecture,phase,block_id="calibration"):
        expected=40 if phase=="SEARCH" else 200 if phase=="CONFIRM" else None
        if expected is None or len(items)!=expected:raise Failure("CONFIGURATION_FAILURE","CALIBRATION_CELL_SIZE")
        rows=[self.measurement(item,architecture,i,phase,block_id) for i,item in enumerate(items)]
        return dict(n=len(rows),successes=sum(r["solo_correct"] for r in rows),measurements=rows)


def calibration_items(config,family,difficulty,phase,block_id,seen):
    """Shared matched items across arms; global split ledger is updated in place."""
    split="CALIBRATION_"+phase;n_items=40 if phase=="SEARCH" else 200 if phase=="CONFIRM" else None
    if n_items is None:raise Failure("CONFIGURATION_FAILURE","UNKNOWN_CALIBRATION_PHASE")
    digest=raw_sha(integer_dsl_bytes([family,difficulty]))[:16];rows=[]
    for index in range(n_items):
        attempt=0
        while True:
            generator=generate_symbolic if family=="SYMBOLIC_PIPELINE" else generate_grid
            item=generator(config["master_seed"],split,block_id,index,start_attempt=attempt,**resolve_options(config,family,difficulty))
            if item["latent_fingerprint"] not in seen:break
            attempt=item["generation_attempt"]+1
            if attempt>=1000:raise Failure("GENERATION_FAILURE","CALIBRATION_DEDUP_EXHAUSTED")
        seen[item["latent_fingerprint"]]=split
        rng=Stream(config["master_seed"],split,block_id,"SURFACE",index,item["generation_attempt"])
        spec=relabel(item["spec"],rng,False);template=("A","B")[rng.randint(0,1)]
        view=dict(task_id=item["task_id"],task_family=family,spec=spec,surface_text=render(spec,template),
            scope_id="scope:"+digest,difficulty_scope="d:"+digest,context_condition="ctx:0")
        rows.append(dict(task_view=view,ground_truth=verify_task(spec),latent_fingerprint=item["latent_fingerprint"],
            split=split,generation_attempt=item["generation_attempt"]))
    return rows


def search_and_confirm(config,provider_factory,event_sink,*,offline_fixture=False,tokenizer=None,content=None,existing_fingerprints=None):
    """0.1.1: event_sink must be a new EventStore, not an unsealed callback.

    Takes a configured TEMPLATE with *no* selected tuples. Returns the final
    FROZEN config, CAS and sealed calibration artifact. No retry after CONFIRM.
    """
    from .storage import EventStore
    from .config import pre_calibration_lock
    if not isinstance(event_sink,EventStore) or event_sink.events:
        raise Failure("CONFIGURATION_FAILURE","CALIBRATION_REQUIRES_NEW_EVENT_STORE")
    lock=pre_calibration_lock(config,content or {})
    event_sink.append("CALIBRATION_LOCK",lock)
    try:
        return _search_and_confirm(config,provider_factory,event_sink,lock,offline_fixture=offline_fixture,
            tokenizer=tokenizer,content=content,existing_fingerprints=existing_fingerprints)
    except Failure as error:
        event_sink.append("CALIBRATION_TERMINAL_FAILURE",error.as_dict())
        raise


def _search_and_confirm(config,provider_factory,event_store,lock,*,offline_fixture=False,tokenizer=None,content=None,existing_fingerprints=None):
    """Explicit engine entry point; never invoked by installation or verification.

    Search: first ordered candidate whose five posterior means lie in a band.
    Confirm: independent items, all 20 means and interval widths must pass.
    No automatic second search after a failed confirmation.
    """
    event_sink=event_store.append
    content=cp(content or {})
    seen=dict(existing_fingerprints or {});selected={};search_results=[]
    for candidate_index,candidate in enumerate(calibration_plan(config)["candidate_order"]):
        family,difficulty=candidate["family"],candidate["difficulty"]
        if all((family,b) in selected for b in ("HIGH","MID")):continue
        block=f"search:{candidate_index}";items=calibration_items(config,family,difficulty,"SEARCH",block,seen);counts=[]
        event_sink("CALIBRATION_ITEM_MANIFEST",dict(block_id=block,phase="SEARCH",sha256=semantic_sha(items),items=items))
        for architecture in ("B0","B1","B2","B3","B4"):
            provider=provider_factory(dict(phase="SEARCH",block_id=block,architecture=architecture,family=family,difficulty=cp(difficulty)))
            if offline_fixture and provider.kind not in {"FAKE","REPLAY"}:raise Failure("CONFIGURATION_FAILURE","REAL_CALIBRATION_DISABLED")
            engine=CalibrationEngine(config,provider,event_sink,tokenizer,not offline_fixture,content,pre_lock=lock)
            result=engine.measure_cell(items,architecture,"SEARCH",block)
            counts.append(dict(architecture=architecture,n=result["n"],successes=result["successes"]))
        search_results.append(dict(candidate=cp(candidate),counts=counts))
        for band in ("HIGH","MID"):
            bounds=config["calibration_bands"][band]
            if (family,band) not in selected and all(bounds["lower"] <= (r["successes"]+1)/(r["n"]+2) <= bounds["upper"] for r in counts):
                selected[family,band]=cp(difficulty)
    if len(selected)!=4:raise Failure("CALIBRATION_NOT_FEASIBLE","NO_COMMON_SEARCH_TUPLES")
    from .canonical import canonical
    from .config import verify_calibration_lock
    from .calibration_artifact import scope_for,seal_artifact
    config=cp(config);config["configuration_status"]="FROZEN"
    for (family,band),difficulty in sorted(selected.items()):
        raw=canonical(difficulty);digest=raw_sha(raw);content[digest]=raw
        scope="scope:"+raw_sha(integer_dsl_bytes([family,difficulty]))[:16]
        config["selected_difficulty_tuples"].append(dict(family=family,band=band,scope_id=scope,tuple_sha256=digest))
    event_sink("CALIBRATION_SEARCH_SELECTION",dict(search_results=search_results,selected_tuples=cp(config["selected_difficulty_tuples"])))
    verify_calibration_lock(lock,config,final=True)
    frozen=freeze(config,content)
    event_sink("CALIBRATION_FINAL_FROZEN",frozen)
    confirmation=[];confirmation_manifests=[]
    for (family,band),difficulty in sorted(selected.items()):
        block=f"confirm:{family}:{band}";items=calibration_items(config,family,difficulty,"CONFIRM",block,seen)
        dataset_hash=semantic_sha(items)
        event_sink("CALIBRATION_ITEM_MANIFEST",dict(block_id=block,phase="CONFIRM",sha256=dataset_hash,items=items))
        confirmation_manifests.append(dict(family=family,band=band,difficulty=cp(difficulty),tuple_sha256=semantic_sha(difficulty),dataset_hash=dataset_hash))
        for architecture in ("B0","B1","B2","B3","B4"):
            provider=provider_factory(dict(phase="CONFIRM",block_id=block,architecture=architecture,family=family,band=band,difficulty=cp(difficulty)))
            if offline_fixture and provider.kind not in {"FAKE","REPLAY"}:raise Failure("CONFIGURATION_FAILURE","REAL_CALIBRATION_DISABLED")
            result=CalibrationEngine(config,provider,event_sink,tokenizer,not offline_fixture,content).measure_cell(items,architecture,"CONFIRM",block)
            confirmation.append(dict(architecture=architecture,family=family,band=band,n=result["n"],successes=result["successes"],
                tuple_sha256=semantic_sha(difficulty),dataset_hash=dataset_hash,scope=scope_for(config,architecture,family,band,difficulty)))
    try:confirmation_gate(confirmation,config)
    except Failure:
        event_sink("CALIBRATION_CONFIRMATION",dict(gate_status="CALIBRATION_NOT_FEASIBLE",cells=confirmation))
        seal_artifact(config,lock,confirmation,confirmation_manifests,event_store,offline_fixture=offline_fixture,gate_status="CALIBRATION_NOT_FEASIBLE")
        raise
    event_sink("CALIBRATION_CONFIRMATION",dict(gate_status="PASS",cells=confirmation))
    artifact=seal_artifact(config,lock,confirmation,confirmation_manifests,event_store,offline_fixture=offline_fixture)
    return dict(config=config,config_sha256=frozen["config_sha256"],artifact=artifact,content=content,fingerprint_ledger=seen)
