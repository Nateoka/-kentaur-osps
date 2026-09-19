"""Durable trajectory execution with safe-boundary resume and no hidden session."""
from copy import deepcopy as cp
from fractions import Fraction
import time
from . import RUNTIME_VERSION,PROTOCOL_REVISION
from .canonical import canonical,loads,raw_sha,semantic_sha,integer_dsl_bytes
from .config import OfflineTokenizer,freeze
from .controller import Controller,prep_path,ABNORMAL
from .profiles import ProfileStore,applies,informative
from .b4 import Tracker,beta_sf
from .calls import EpisodeCalls
from .prompts import Prompts
from .schemas import Schemas
from .state import history_state,key_for
from .storage import EventStore,read_events
from .errors import Failure
from .tasks import verify_task
from .seed import Stream
from .answers import normalize_answer
from .tool_dispatch import execute_sealed_tool


def evidence_before(feedbacks,key,interval):
    rows=[f for f in feedbacks if informative(f) and all(f[k]==key[k] for k in key if k!="scope_id")]
    s=sum(f["solo_correct"] for f in rows);f=len(rows)-s
    if interval is None:return dict(sufficient=False,direction="NOT_APPLICABLE",wrong=None,solo_support=False,n=len(rows))
    upward=beta_sf(str(interval["upper"]),1+s,1+f);downward=1-beta_sf(str(interval["lower"]),1+s,1+f)
    sufficient=len(rows)>=4 and upward+downward>Fraction(9,10)
    return dict(sufficient=sufficient,direction="UPWARD" if sufficient and upward>Fraction(9,10) else "DOWNWARD" if sufficient and downward>Fraction(9,10) else "UNRESOLVED",
        wrong=float(upward+downward),solo_support=len(rows)>=4 and beta_sf(".8",1+s,1+f)>Fraction(9,10),n=len(rows))


class TrajectoryRunner:
    def __init__(self,config,manifest,trajectory_id,provider,event_path,reference_cells=None,
                 tokenizer=None,enable_real_provider=False,content=None,tool_executor=None,
                 calibration_artifact=None,calibration_events=None):
        self.config=cp(config);self.manifest=cp(manifest);self.provider=provider
        self.tokenizer=tokenizer or OfflineTokenizer();self.schemas=Schemas();self.prompts=Prompts()
        if provider.kind not in {"FAKE","REPLAY"}:
            if not enable_real_provider:raise Failure("CONFIGURATION_FAILURE","REAL_PROVIDER_DISABLED")
            freeze(config,content or {})
            if tokenizer is None:raise Failure("CONFIGURATION_FAILURE","REAL_TOKENIZER_REQUIRED")
            from .identity import verify_frozen_implementation
            verify_frozen_implementation(config,provider,tokenizer)
        self.plan=next((cp(t) for t in manifest["payload"]["trajectories"] if t["trajectory_id"]==trajectory_id),None)
        if self.plan is None:raise Failure("CONFIGURATION_FAILURE","UNKNOWN_TRAJECTORY")
        if semantic_sha(manifest["payload"])!=manifest["sha256"] or semantic_sha(config)!=manifest["payload"]["config_sha256"]:
            raise Failure("INFRA_FAILURE","SEALED_MANIFEST_CONFIG_MISMATCH")
        self.architecture=self.plan["architecture"];self.id=trajectory_id
        self.configuration=cp(config["capability_configurations"][self.architecture])
        if tool_executor is not None and provider.kind not in {"FAKE","REPLAY"}:
            raise Failure("CONFIGURATION_FAILURE","CUSTOM_TOOL_ONLY_FOR_OFFLINE_FAILURE_INJECTION")
        self.tool_executor=tool_executor
        real=provider.kind not in {"FAKE","REPLAY"}
        self.calibration_artifact_sha256=None
        if real and reference_cells is not None:
            raise Failure("CONFIGURATION_FAILURE","EXTERNAL_REAL_REFERENCE_CELLS_FORBIDDEN")
        if real and calibration_artifact is None:
            raise Failure("CONFIGURATION_FAILURE","SEALED_CALIBRATION_ARTIFACT_REQUIRED")
        if calibration_artifact is not None:
            from .calibration_artifact import verify_artifact,materialize_reference_cells
            verify_artifact(calibration_artifact,config,calibration_events,scientific=real)
            materialized=materialize_reference_cells(calibration_artifact,config,self.plan)
            if reference_cells is not None and reference_cells!=materialized:
                raise Failure("INFRA_FAILURE","EXTERNAL_REFERENCE_CELLS_MISMATCH")
            reference_cells=materialized
            self.calibration_artifact_sha256=calibration_artifact["sha256"]
        self.reference_cells=cp(reference_cells)
        if reference_cells is None or len(reference_cells)!=2:raise Failure("CONFIGURATION_FAILURE","TWO_REFERENCE_CELLS_REQUIRED")
        self.store=EventStore(event_path);self.sequence=0;self.feedbacks=[];self.episodes=[];self.all_calls=[];self.tool_units=0
        self.profile=ProfileStore(self._initial_profile(),self.sink)
        self.tracker=Tracker();self.controller=Controller(self.next_sequence,self.sink)
        self.initial_profile=cp(self.profile.current);self.initial_intervals=self._stimulus_intervals()
        self.seen=set();self.completion_status="RUNNING"
        if self.store.events:
            try:self._resume()
            except Exception:
                self.store.close()
                raise
        else:
            self.sink("RUN_START",dict(runtime_version=RUNTIME_VERSION,protocol_revision=PROTOCOL_REVISION,
                config_sha256=semantic_sha(config),manifest_sha256=manifest["sha256"],trajectory_id=self.id,
                initial_profile=self.initial_profile,reference_cells=self.reference_cells,
                calibration_artifact_sha256=self.calibration_artifact_sha256,reference_cells_sha256=semantic_sha(self.reference_cells),
                runtime_identity=cp(config["runtime_identity"]),provider_identity=self._provider_identity(),provider_kind=provider.kind,
                result_kind="MODEL_RUN" if real else "DESIGN_TEST_VECTOR_NOT_MODEL_RESULT",
                runtime_patches=["R1-E07-HARM-01",*self.schemas.applied_patches]))

    def next_sequence(self):
        self.sequence+=1
        return self.sequence

    def _provider_identity(self):
        from .provenance import provider_identity
        return provider_identity(self.config)

    def sink(self,kind,payload):
        return self.store.append(kind,payload)

    def _stimulus_intervals(self):
        rows=[]
        for family,address in self.plan["scope_by_family"].items():
            target=family==self.plan["target_family"];condition=self.plan["condition"]
            band=self.plan["target_stratum"] if target else "HIGH"
            interval=cp(self.config["calibration_bands"][band])
            if target and condition=="C2":interval=cp(self.config["profile_stimulus"]["false_low_interval"])
            if target and condition=="C3":interval=cp(self.config["profile_stimulus"]["false_high_interval"])
            rows.append(dict(scope_id=address["scope_id"],interval=None if condition=="C0" else interval))
        return rows

    def _initial_profile(self):
        if self.architecture=="B4" or self.plan["condition"]=="C0":return None
        intervals={r["scope_id"]:r["interval"] for r in self._stimulus_intervals()}
        claims=[]
        for family,address in self.plan["scope_by_family"].items():
            claims.append(dict(claim_id="claim:"+raw_sha(integer_dsl_bytes([self.id,family]))[:12],
                scope_id=address["scope_id"],task_family=family,difficulty_scope=[address["difficulty_scope"]],
                context_condition=[address["context_condition"]],tool_condition="SOLO_NO_TOOL",
                estimated_success_interval=intervals[address["scope_id"]],evidence_label="HISTORICAL_ESTIMATE",evidence_n=20,
                status="ACTIVE",version=1,last_updated_episode=0,
                capability_configuration_ref=self.configuration["configuration_id"],execution_modes=cp(self.configuration["execution_modes"])))
        rng=Stream(self.config["master_seed"],"MAIN",self.plan["block_id"],"PROFILE")
        return dict(profile_id="profile:"+self.id,version=1,claims=rng.shuffle(claims),contract_version="0.2.1")

    def _checkpoint(self):
        value=dict(sequence=self.sequence,feedbacks=self.feedbacks,episodes=self.episodes,all_calls=self.all_calls,
            tool_units=self.tool_units,seen=sorted(self.seen),completion_status=self.completion_status,
            profile_current=self.profile.current,profile_attempts=self.profile.attempts,
            profile_submitted=sorted(self.profile.submitted_episodes),controller_states=self.controller.states,
            controller_signatures={k:list(v) for k,v in self.controller.signatures.items()},controller_pending=self.controller.pending,
            controller_pending_key=self.controller.pending_key,tracker_seen=sorted(self.tracker.seen),
            tracker_cells=[dict(key=list(k),value=v) for k,v in self.tracker.cells.items()],trajectory=self.trajectory())
        self.sink("CHECKPOINT",value)

    def _resume(self):
        start=self.store.events[0]
        if start["kind"]!="RUN_START" or start["payload"]["trajectory_id"]!=self.id or start["payload"]["manifest_sha256"]!=self.manifest["sha256"]:
            raise Failure("INFRA_FAILURE","RESUME_IDENTITY_MISMATCH")
        identity=start["payload"]
        if (identity["config_sha256"]!=semantic_sha(self.config) or identity.get("calibration_artifact_sha256")!=self.calibration_artifact_sha256
                or identity.get("reference_cells_sha256")!=semantic_sha(self.reference_cells) or identity["reference_cells"]!=self.reference_cells
                or identity.get("runtime_identity")!=self.config["runtime_identity"] or identity.get("provider_identity")!=self._provider_identity()):
            raise Failure("INFRA_FAILURE","RESUME_CONFIG_OR_CALIBRATION_IDENTITY_MISMATCH")
        if self.store.events[-1]["kind"]!="CHECKPOINT":
            raise Failure("INFRA_FAILURE","UNSAFE_INCOMPLETE_EPISODE_REQUIRES_REPLAY")
        state=self.store.events[-1]["payload"]
        self.sequence=state["sequence"];self.feedbacks=cp(state["feedbacks"]);self.episodes=cp(state["episodes"])
        self.all_calls=cp(state["all_calls"]);self.tool_units=state["tool_units"];self.seen=set(state["seen"])
        self.completion_status=state["completion_status"];self.profile.current=cp(state["profile_current"])
        self.profile.attempts=cp(state["profile_attempts"]);self.profile.submitted_episodes=set(state["profile_submitted"])
        self.controller.states=cp(state["controller_states"]);self.controller.signatures={k:tuple(v) for k,v in state["controller_signatures"].items()}
        self.controller.pending=cp(state["controller_pending"]);self.controller.pending_key=cp(state["controller_pending_key"])
        self.tracker.seen=set(state["tracker_seen"]);self.tracker.cells={tuple(x["key"]):cp(x["value"]) for x in state["tracker_cells"]}
        if self.profile.current is not None:self.schemas.validate(self.profile.current,self.schemas.ref("self_profile"),"INFRA_FAILURE")

    def _public(self,index,view,mode):
        value=history_state(self.id,index,view,self.profile,self.feedbacks,self.configuration,mode,
            self.architecture,self.controller,self.tracker,self.all_calls,self.tool_units)
        return self.schemas.validate(value,self.schemas.ref("trajectory","agent_state"),"CONFIGURATION_FAILURE")

    def run_episode(self,index):
        entry=self.manifest["payload"]["tasks"][self.plan["task_ids"][index-1]]
        private=cp(entry["record"]);view=private["task_view"]
        if raw_sha(integer_dsl_bytes(private))!=entry["sha256"] or verify_task(view["spec"])!=private["ground_truth"]:
            raise Failure("INFRA_FAILURE","TASK_PREFLIGHT_MISMATCH")
        if private["latent_fingerprint"] in self.seen:raise Failure("INFRA_FAILURE","DUPLICATE_LATENT_ITEM")
        if self.tokenizer.count(integer_dsl_bytes(view))>4096:raise Failure("CONFIGURATION_FAILURE","TASK_PAYLOAD_OVERFLOW")
        episode_id=f"{self.id}:{index}";arch=self.architecture
        mode="NO_PREP_INTERFACE" if arch in {"B0","B4"} else "PREP_EXECUTED"
        key=key_for(view,self.configuration,mode,bool(self.feedbacks));skip_reason=None;prep_count=0
        allowed=True
        if arch=="B3":
            allowed=self.controller.begin(index,key)
            if not allowed:mode="PREP_SKIPPED";skip_reason="B3_STOP_CONTROLLER"
        key["execution_mode"]=mode
        initial_input=self._public(index,view,None)
        self.sink("EPISODE_BEGIN",dict(episode_id=episode_id,index=index,task_sha256=entry["sha256"],public_input_sha256=semantic_sha(initial_input)))
        calls=EpisodeCalls(self.provider,self.prompts,self.config,self.tokenizer,arch,episode_id,self.next_sequence,self.sink,
            dict(split=private["split"],block_id=self.plan["block_id"],item_index=index-1))
        prep=action=update=tool=final=None;solo_seal=None;protocol_status="OK";errors=[];probe_executed=False
        action_profile=cp(self.profile.current);action_state=None
        try:
            if arch in {"B1","B2","B3"} and allowed:
                request=self.prompts.request("PREP",arch,initial_input)
                try:
                    prep=calls.structured(request,"PREP")
                finally:
                    prep_count=sum(c["phase"]=="PREP" and c["response_status"]!="TRANSPORT_FAILURE" for c in calls.calls)
                    if prep_count==0:mode="PREP_SKIPPED";skip_reason="INFRA_FAILURE"
                if arch=="B3":self.controller.accept_prep(prep,index,key,self.feedbacks,defer_stop=True)
                if arch in {"B2","B3"} and prep.get("proposal") is not None:
                    update=self.profile.commit(prep["proposal"],arch,index,self.feedbacks,self.next_sequence())
                if arch=="B3":self.controller.apply_stop(prep,index,key)
            key["execution_mode"]=mode
            if not prep_path(arch,mode,prep_count,skip_reason,not allowed)["normal"]:
                raise Failure("PROTOCOL_FAILURE","ABNORMAL_PREP_NO_ACTION")
            action_profile=cp(self.profile.current)
            fixed=None
            if arch=="B4":fixed=self.tracker.opportunity(key)
            action_state=self._public(index,view,mode)
            receipt=None if update is None else {k:cp(update[k]) for k in ("validation_status","rejection_codes","effective_episode")}
            if arch=="B4" and fixed in {"DELEGATE","ABSTAIN"}:
                action=dict(action=fixed,solo_answer=None,confidence="UNSPECIFIED")
            else:
                action=calls.structured(self.prompts.request("ACTION",arch,action_state,prep,receipt,fixed),"ACTION",fixed)
            choice=action["action"]
            if choice in {"SOLO","VERIFY"}:
                action["solo_answer"]=normalize_answer(view["spec"],action["solo_answer"])
                solo_seal=self.next_sequence()
                self.sink("SOLO_SEAL",dict(sequence=solo_seal,episode_id=episode_id,answer=action["solo_answer"],answer_sha256=semantic_sha(action["solo_answer"])))
            self.sink("ACTION",dict(sequence=self.next_sequence(),record=action))
            if arch=="B3":probe_executed=self.controller.action(index,key,choice)
            if choice in {"VERIFY","DELEGATE"}:
                start=self.next_sequence()
                if choice=="VERIFY" and (solo_seal is None or solo_seal>=start):raise Failure("PROTOCOL_FAILURE","TOOL_BEFORE_SOLO_SEAL")
                spec_bytes=integer_dsl_bytes(view["spec"])
                self.sink("TOOL_START",dict(sequence=start,spec_sha256=raw_sha(spec_bytes)))
                tick=time.perf_counter();tool_failed=False
                try:
                    result=self.tool_executor(loads(spec_bytes)) if self.tool_executor is not None else execute_sealed_tool(loads(spec_bytes),self.config["timeouts"]["tool_seconds"])
                except Exception:
                    result=None;tool_failed=True
                duration=(time.perf_counter()-tick)*1000
                tool=dict(tool_name="run_symbolic_pipeline" if view["task_family"]=="SYMBOLIC_PIPELINE" else "solve_rule_grid",
                    input_spec_sha256=raw_sha(spec_bytes),result=result,status="OK",start_sequence=start,end_sequence=self.next_sequence(),cost_units=1)
                if tool_failed or duration>self.config["timeouts"]["tool_seconds"]*1000 or result!=private["ground_truth"]:
                    tool.update(status="INFRA_FAILURE",result=None)
                self.sink("TOOL_END",dict(tool_event=tool,duration_ms=duration))
                if tool["status"]!="OK":raise Failure("INFRA_FAILURE","TOOL_TIMEOUT_OR_TRUTH_MISMATCH")
                final=cp(result)
            elif choice=="SOLO":final=cp(action["solo_answer"])
        except Failure as failure:
            self.sink("FAILURE",dict(episode_id=episode_id,**failure.as_dict()))
            if failure.kind=="CONFIGURATION_FAILURE":raise
            protocol_status="INFRA_FAILURE" if failure.kind=="INFRA_FAILURE" else "PROTOCOL_FAILURE"
            errors.append(failure.code)
            if arch in {"B1","B2"} and prep_count==0:
                mode="PREP_SKIPPED";skip_reason=protocol_status
            final=None
        action_profile=cp(self.profile.current)
        if action_state is None:action_state=self._public(index,view,mode)
        self.all_calls.extend(calls.calls)
        key["execution_mode"]=mode
        choice=None if action is None else action["action"]
        solo_correct=(action["solo_answer"]==private["ground_truth"]) if protocol_status=="OK" and choice in {"SOLO","VERIFY"} else None
        final_correct=(final==private["ground_truth"]) if protocol_status=="OK" and final is not None else None
        feedback=dict(episode_id=episode_id,episode_index=index,**key,chosen_action=choice,solo_correct=solo_correct,final_correct=final_correct,
            tool_used=tool is not None,cost_units=0 if tool is None else tool["cost_units"],
            outcome=protocol_status if protocol_status!="OK" else "ABSTAINED" if choice=="ABSTAIN" else "CORRECT" if final_correct else "INCORRECT",prep_skip_reason=skip_reason)
        interval=next(x["interval"] for x in self.initial_intervals if x["scope_id"]==key["scope_id"])
        gate=evidence_before(self.feedbacks,key,interval)
        applicable=None if self.profile.current is None else next((c for c in self.profile.current["claims"] if applies(c,key)),None)
        last_numeric=None if applicable is None else next((a["claim"] for a in self.profile.anchors() if a["reason"]=="LAST_NUMERIC" and a["claim_id"]==applicable["claim_id"] and applies(a["claim"],key)),None)
        if arch=="B3":self.controller.feedback(index,key,feedback,applicable,probe_executed,last_numeric)
        if arch=="B4":self.tracker.observe(key,private["latent_fingerprint"],choice,solo_correct,solo_seal is not None and tool is not None and solo_seal<tool["start_sequence"],protocol_status)
        termination="CONTINUE" if protocol_status=="OK" else protocol_status
        if index==len(self.plan["task_ids"]):termination=self.controller.finish() if arch=="B3" else "END_NO_PENDING"
        cell=next(c for c in self.reference_cells if c["scope"]["scope_id"]==view["scope_id"])
        record=dict(benchmark_version="0.1",contract_version="0.2.1",trajectory_id=self.id,episode_id=episode_id,episode_index=index,
            agent_input=initial_input,action_input_profile=action_profile,prep_record=prep,action_record=action,solo_seal_sequence=solo_seal,
            final_answer=final,tool_event=tool,update_event=update,feedback=feedback,calls=cp(calls.calls),protocol_status=protocol_status,protocol_errors=errors,
            evaluator_private=dict(phase=private["phase"],target_role=private["target_role"],split=private["split"],latent_fingerprint=private["latent_fingerprint"],
                surface_template_id=private["surface_template_id"],calibration_key=cell["calibration_key"],ground_truth=private["ground_truth"],
                sufficient_before=gate["sufficient"],posterior_wrong_before=gate["wrong"],direction_before=gate["direction"],informative=informative(feedback)),
            probe_events=cp(self.controller.probe_events) if arch=="B3" else [],latch_events=cp(self.controller.latch_events) if arch=="B3" else [],termination_reason=termination,
            execution_context=dict(capability_configuration_ref=key["capability_configuration_ref"],execution_mode=mode,history_class=key["history_class"],
                public_state_sha256=semantic_sha(action_state),prep_record_sha256=None if prep is None else semantic_sha(prep),history_policy_id=self.configuration["history_policy"],prep_skip_reason=skip_reason,prep_call_count=prep_count))
        self.schemas.validate(record,self.schemas.ref("episode_record"),"INFRA_FAILURE")
        self.sink("FEEDBACK",feedback);self.sink("EPISODE_RECORD",record)
        self.feedbacks.append(feedback);self.episodes.append(record);self.tool_units+=feedback["cost_units"];self.seen.add(private["latent_fingerprint"])
        if protocol_status=="INFRA_FAILURE" and skip_reason not in ABNORMAL:self.completion_status="INFRA_INVALID"
        elif index==len(self.plan["task_ids"]):self.completion_status="COMPLETED"
        self._checkpoint()
        return record

    def run(self,stop_after=None):
        try:
            while len(self.episodes)<len(self.plan["task_ids"]) and self.completion_status!="INFRA_INVALID":
                self.run_episode(len(self.episodes)+1)
                if stop_after is not None and len(self.episodes)>=stop_after:break
            return self.trajectory()
        finally:self.store.close()

    def trajectory(self):
        seeds={name:Stream(self.config["master_seed"],"MAIN",self.plan["block_id"],name,
            architecture=self.architecture if name=="MODEL" else None,phase="ACTION" if name=="MODEL" else None).digest().hex()
            for name in ("TASK","FAMILY_ORDER","SURFACE","PROFILE","MODEL","BOOTSTRAP","TASK_ID")}
        reflected=self._public(max(1,len(self.episodes)),self.manifest["payload"]["tasks"][self.plan["task_ids"][0]]["record"]["task_view"],None)["reflection_cost"]
        result=dict(benchmark_version="0.1",contract_version="0.2.1",trajectory_id=self.id,config_sha256=semantic_sha(self.config),
            architecture=self.architecture,profile_condition=self.plan["condition"],planned_run=self.manifest["payload"]["planned_run"],block_id=self.plan["block_id"],
            target_family=self.plan["target_family"],first_family=self.plan["first_family"],target_stratum=self.plan["target_stratum"],seed_metadata=seeds,
            calibration_cells=cp(self.reference_cells),initial_profile=self.initial_profile,current_profile=cp(self.profile.current),profile_history=cp(self.profile.attempts),
            recent_episode_history=cp(self.feedbacks[-10:]),cumulative_cost=self.tool_units,reflection_cost=reflected,episodes=cp(self.episodes),
            completion_status=self.completion_status,initial_stimulus_intervals=cp(self.initial_intervals))
        return self.schemas.validate(result,self.schemas.ref("trajectory"),"INFRA_FAILURE")
