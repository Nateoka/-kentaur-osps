"""Addressed design amendments over the preserved 0.1 schema builder.

Only static schema construction; no model, generator, solver or benchmark runtime.
"""
from copy import deepcopy as cp

BASE='https://mrab.example.invalid/r1/0.2.1/'
def ref(file,name):return {'$ref':BASE+file+'.schema.json#/$defs/'+name}
def obj(props,description):return dict(type='object',properties=props,required=list(props),additionalProperties=False,description=description)
def fld(value,description):return {**cp(value),'description':description}
def arr(value,maximum=128):return dict(type='array',items=value,maxItems=maximum)
def en(*values):return dict(type='string',enum=list(values))
def null(value):return {'anyOf':[value,{'type':'null'}]}
ID={'type':'string','pattern':'^[a-zA-Z0-9_:.-]{1,96}$'}
SHA={'type':'string','pattern':'^[0-9a-f]{64}$'}
INT={'type':'integer','minimum':0}
NUM={'type':'number','minimum':0}
TEXT={'type':'string','maxLength':20000}
def add(target,key,value,description):
    target['properties'][key]=fld(value,description)
    if key not in target['required']:target['required'].append(key)


def amend(schemas):
    c,p,e,r,t=(schemas['r1_'+n] for n in ('config','self_profile','episode_record','reflexive_record','trajectory'))
    d=c['$defs'];component=obj({'identity':fld(ID,'Versioned component identity; TEMPLATE may use CONFIGURE.'),
        'sha256':fld(SHA,'Actual component bytes hash. FROZEN rejects placeholders/zero hashes and requires content resolution.')},'Immutable component identity, not a claim of execution.')
    d['runtime_identity']=obj({k:fld(component,'Pinned '+k+' implementation/content.') for k in
        ['provider_adapter','tokenizer','parser','canonicalizer','prompt_bundle','output_schema_bundle','symbolic_tool','grid_tool']},
        'Missing runtime identities in 0.1; private configuration only.')
    add(c,'contract_version',{'const':'0.2.1'},'Data contract/package revision; benchmark matrix identity stays 0.1.')
    add(c,'protocol_revision',{'const':'R1_0.1_DESIGN_PATCH_0.2.1'},'Changed controller/evaluation protocol; not comparable under the old protocol hash.')
    c['properties']['benchmark_version']['description']='Matrix/family R1 0.1 identity, distinct from contract 0.2.1.'
    add(c,'runtime_identity',ref('r1_config','runtime_identity'),'Pinned runtime identity; TEMPLATE is not executable.')
    add(c,'compute_settings',obj({'reasoning_mode':fld(TEXT,'Provider setting or explicit UNAVAILABLE.'),
        'reasoning_budget':fld(null(INT),'Configured limit when observable; null is not zero.'),
        'usage_accounting':fld(en('OUTPUT_INCLUDES_REASONING','OUTPUT_EXCLUDES_REASONING','UNKNOWN'),'Avoid double counting provider token categories.'),
        'prep_interface':fld({'const':'PREP_THEN_ACTION_BUNDLE'},'Explicit baseline variant, not draft-then-critic equivalence.')},'Compute/context settings, not an intelligence score.'),'Compute settings included in freeze.')
    add(c,'selected_difficulty_tuples',arr(obj({'family':fld(d['family'],'Family.'),'band':fld(en('HIGH','MID'),'Private reference band.'),
        'scope_id':fld(ID,'Opaque public scope.'),'tuple_sha256':fld(SHA,'Canonical selected tuple content hash; content must resolve in manifest.')},'Selected tuple identity.'),4),
        'Empty for TEMPLATE; FROZEN requires exactly four resolved tuples and independent calibration gate later.')
    add(c,'design_decisions',obj({'capability_estimand':fld(en('OPERATIONAL_SELF_MODEL_REFERENCE_ANCHORED'),
        'R1-CAPABILITY-01 accepted author decision; p_reference is not ground truth of p_operational(t).'),
        'probe_claim':fld({'const':'BOUNDED_EVIDENCE_PROBE'},
        'R1-PROBE-01 accepted: OD-02 closed; labels cannot establish causal discrimination.')},'Accepted research scope; stronger causal experiment remains outside R1.'),'Author-scoped decisions.')
    add(c,'structural_relations',obj({'B3_more_complex_than_B2':fld({'const':True},'Predeclared R1-REDUNDANCY-01 relation, not a score.'),
        'B3_more_complex_than_B4':fld({'const':True},'Predeclared R1-REDUNDANCY-01 relation, not a score.')},'No computed complexity metric.'),'Structural redundancy basis.')
    add(c,'b4_policy_version',{'const':'STRONG_TRACKER_POLICY_0.2'},'R1-B4-01 intentionally retains strengthened0.2 simple baseline; freeze parameters before run.')
    add(c,'ordering_policy',{'const':'STRICT_ALTERNATION_COUNTERBALANCED'},'Versioned engineering default; change requires new protocol identity.')
    add(c,'transfer_scope',{'const':'SURFACE_CONTEXT_REDUNDANCY'},'Unchanged DSL; no new parsing/skill claim.')
    d['capability_configuration']=obj({'configuration_id':fld(ID,'Opaque public configuration identity, never a condition code.'),
        'architecture_policy_id':fld(ID,'Versioned public actor policy interface; no hidden treatment label.'),
        'history_policy':fld({'const':'PUBLIC_BOUNDED_WITH_COMMON_EVIDENCE_INDEX_V02'},'Same history access; content is recorded per episode, not assumed constant.'),
        'prep_policy':fld(en('NONE','EXACTLY_ONE','AT_MOST_ONE_WITH_CONTROLLER'),'R1-PREP-01: B1/B2 exactly one; B3 controller only normal skip; B0/B4 none.'),
        'execution_modes':fld(arr(en('PREP_EXECUTED','PREP_SKIPPED','NO_PREP_INTERFACE'),3),'Declared permitted execution modes; narrowing is set inclusion.')},
        'Public capability configuration scope; reference measurement reset mode is separately logged.')
    add(c,'capability_configurations',obj({k:fld(ref('r1_config','capability_configuration'),'Public configuration for '+k)
        for k in ['B0','B1','B2','B3','B4']},'Private treatment-to-public-configuration map.'),'Configurations addressed by claims, R1-CAPABILITY-01.')
    for b in ['B0','B1','B2','B3','B4']:
        policy='NONE' if b in ['B0','B4'] else 'EXACTLY_ONE' if b in ['B1','B2'] else 'AT_MOST_ONE_WITH_CONTROLLER'
        modes=['NO_PREP_INTERFACE'] if b in ['B0','B4'] else ['PREP_EXECUTED'] if b in ['B1','B2'] else ['PREP_EXECUTED','PREP_SKIPPED']
        c['properties']['capability_configurations']['properties'][b]['allOf']=[{'properties':{'prep_policy':{'const':policy},'execution_modes':{'const':modes}}}]
    add(d['scope'],'capability_configuration_ref',ID,'Addressed policy configuration; not a universal capability statement.')
    add(d['scope'],'execution_modes',arr(en('PREP_EXECUTED','PREP_SKIPPED','NO_PREP_INTERFACE'),3),'Nonempty permitted modes; operation NARROWED may only remove modes.')
    d['scope']['properties']['execution_modes']['minItems']=1
    d['scope']['properties']['execution_modes']['uniqueItems']=True
    for key in ['capability_configuration_ref','execution_modes']:
        add(p['$defs']['claim'],key,d['scope']['properties'][key],d['scope']['properties'][key]['description'])
    add(c,'evaluation_policy',obj({
        'equivalence_margin':fld(NUM,'Default 0.05 absolute rate difference; CI must fit entirely.'),
        'target_accuracy_loss_margin':fld(NUM,'Default 0.02 absolute loss in C2/C3; evaluation policy, not universal Uместность.'),
        'c1_accuracy_loss_margin':fld(NUM,'Default 0.05 per scope.'),
        'resource_ratio_margin':fld(NUM,'Default 0.20 each measured resource; no scalar utility.'),
        'minimum_reach':fld(NUM,'Default 0.50; conditional comparison eligibility only.'),
        'maximum_reach_difference':fld(NUM,'Default 0.25; differences remain reported.'),
        'minimum_gain':fld(NUM,'Default 0.05 primary point advantage.')},'E07 explicit policy thresholds; CI gates use planned trajectory contrasts.'),'Predeclared evaluation policy.')
    # Call records retain accepted attempts even when the provider returns no usage.
    call=e['$defs']['call_usage']
    for key in ['input_tokens','output_tokens']:
        call['properties'][key]=fld(null(INT),'Observed/estimated count or null; availability and reason are explicit per category.')
    call['properties']['output_sha256']=fld(null(SHA),'Null if no public response bytes, never a fabricated empty response hash.')
    call['properties']['visible_output']=fld(null(TEXT),'Captured final-channel output, including malformed JSON; null when unavailable. No hidden reasoning.')
    add(call,'request_bytes',TEXT,'Exact sent public UTF-8 request string. input_sha256 hashes these recoverable bytes.')
    add(call,'response_status',en('RETURNED','TIMEOUT','CANCELLED','TRANSPORT_FAILURE'),'Accepted call remains in the log on failure.')
    add(call,'usage_availability',obj({k:fld(en('OBSERVED','ESTIMATED','UNAVAILABLE'),'Availability of '+k+'; UNAVAILABLE requires null, ESTIMATED requires method.')
        for k in ['input_tokens','output_tokens','reasoning_tokens','cached_tokens','latency_ms','monetary_cost']},'Category-specific availability; do not coerce missingness to zero.'),'Availability per resource.')
    add(call,'usage_reason',obj({k:fld(TEXT,'Reason/estimation method; empty only for observed values.') for k in
        ['input_tokens','output_tokens','reasoning_tokens','cached_tokens','latency_ms','monetary_cost']},'Reasons retained after timeout.'),'Usage provenance.')
    add(call,'output_includes_reasoning',null({'type':'boolean'}),'Provider accounting contract; null prevents an exact token total.')
    # Ordered multiple probe/latch events instead of one lossy per-episode slot.
    probe=e['$defs']['probe_event']
    add(probe,'probe_id',null(ID),'Stable declaration address; null only for NONE.')
    add(probe,'event_kind',en('NONE','DECLARED','CANCELLED','ACTION','FEEDBACK','EXPIRED','END_PENDING'),'One event in ordered probe_events; stopping PREP does not cancel.')
    add(probe,'sequence',INT,'Total order shared with commit/call/tool/seal events.')
    add(probe,'reason',TEXT,'Explicit cancellation/expiry/action mismatch reason, no evaluator truth.')
    e['properties'].pop('probe_event');e['required'].remove('probe_event')
    add(e,'probe_events',arr(ref('r1_episode_record','probe_event'),16),'Append-only events; replacement records CANCELLED then DECLARED.')
    d['latch_event']=obj({'scope_id':fld(ID,'Use public task scope also in C0; never a numeric fake claim.'),
        'sequence':fld(INT,'Shared event sequence.'),'latched':fld({'type':'boolean'},'New latch state.'),
        'reason':fld(en('STOP_DECLARED','NEW_SCOPE','CONTEXT_CHANGED','TOOL_AVAILABILITY_CHANGED','SURPRISE','NEW_EVIDENCE','PROBE_RETURNED','PROBE_EXPIRED','PROBE_CANCELLED'),
        'Observable controller trigger, not evaluator E or proof of internal self-regulation.')},'Controller transition record.')
    add(e,'latch_events',arr(ref('r1_config','latch_event'),16),'Latch transitions separate from probe lifecycle.')
    add(e,'termination_reason',en('CONTINUE','STOP_DECLARED','WAITING_FEEDBACK','PROTOCOL_FAILURE','INFRA_FAILURE','END_PENDING','END_NO_PENDING'),
        'Deterministic episode/controller termination reason. Final trajectory state derivable by order.')
    d['execution_context']=obj({'capability_configuration_ref':fld(ID,'Addressed configuration from the current claim/policy.'),
        'execution_mode':fld(en('PREP_EXECUTED','PREP_SKIPPED','NO_PREP_INTERFACE'),'Actual PREP occurrence, not its ceiling.'),
        'history_class':fld(en('EMPTY','NONEMPTY'),'Coarse comparability class; equal class does not establish stationary capability.'),
        'public_state_sha256':fld(SHA,'Exact ACTION-visible state hash before answer; no hidden fields.'),
        'prep_record_sha256':fld(null(SHA),'Actual prep record hash or null when absent.'),
        'history_policy_id':fld({'const':'PUBLIC_BOUNDED_WITH_COMMON_EVIDENCE_INDEX_V02'},'Pinned common observability policy.')},
        'Public operational mode provenance; p_operational(t) is not measured by this record.')
    add(e,'execution_context',ref('r1_config','execution_context'),'State immediately before ACTION; operational evidence partition key derives from this record.')
    add(d['execution_context'],'prep_skip_reason',null(en('B3_STOP_CONTROLLER','PROTOCOL_FAILURE','INFRA_FAILURE','EXPLICIT_NONEXECUTION')),
        'Required non-null for PREP_SKIPPED; null for PREP_EXECUTED/NO_PREP_INTERFACE. Abnormal nonexecution remains ITT, not architecture savings.')
    add(d['execution_context'],'prep_call_count',{'type':'integer','minimum':0,'maximum':1},'Accepted primary PREP calls; repair attempts remain separately logged. Skipped=0, executed=1.')
    d['execution_context']['allOf']=[
        {'if':{'properties':{'execution_mode':{'const':'PREP_SKIPPED'}}},'then':{'properties':{'prep_skip_reason':{'type':'string'},'prep_call_count':{'const':0}}},'else':{'properties':{'prep_skip_reason':{'type':'null'}}}},
        {'if':{'properties':{'execution_mode':{'const':'PREP_EXECUTED'}}},'then':{'properties':{'prep_call_count':{'const':1}}}},
        {'if':{'properties':{'execution_mode':{'const':'NO_PREP_INTERFACE'}}},'then':{'properties':{'prep_call_count':{'const':0}}}}]
    add(e['$defs']['feedback'],'prep_skip_reason',d['execution_context']['properties']['prep_skip_reason'],'Public abnormal/normal skip provenance, no hidden evaluator inference.')
    add(t['$defs']['agent_state'],'capability_configuration',ref('r1_config','capability_configuration'),'Public definition of the referenced capability configuration, without B/C labels.')
    add(t['$defs']['agent_state'],'current_execution_mode',null(en('PREP_EXECUTED','PREP_SKIPPED','NO_PREP_INTERFACE')),'Null before PREP decision, exact actual mode in ACTION payload; actual request bytes preserve both states.')
    for owner in [e['$defs']['feedback'],t['$defs']['ledger_entry'],d['tracker_state']]:
        for key in ['capability_configuration_ref','execution_mode','history_class']:
            add(owner,key,d['execution_context']['properties'][key],'Public operational partition: '+key+'. Counts are never pooled silently across keys.')
    add(e['$defs']['feedback'],'episode_index',{'type':'integer','minimum':1,'maximum':32},'Past index, needed for admissibility without hidden schedule.')
    add(e['$defs']['feedback'],'tool_condition',d['scope']['properties']['tool_condition'],'Observable tool availability for exact scope matching.')
    for owner in [t['$defs']['ledger_entry'],d['tracker_state']]:
        for key in ['difficulty_scope','context_condition','tool_condition']:
            value=ID if key!='tool_condition' else d['scope']['properties'][key]
            add(owner,key,value,'Exact public partition field; no family-only pooling.')
    update=p['$defs']['update_event']
    add(update,'sequence',{'type':'integer','minimum':1},'Unique order within episode; before ACTION, shared with calls/probes/tools.')
    add(update,'profile_version_before',{'type':'integer','minimum':1},'Snapshot version before attempt.')
    add(update,'profile_version_after',{'type':'integer','minimum':1},'Unchanged on reject; +1 on atomic commit.')
    add(update,'stage_snapshots',arr(ref('r1_self_profile','claim'),2),'Exact intermediate claim snapshots; no partial stage becomes externally committed.')
    for owner in [e,t,p]:
        add(owner,'contract_version',{'const':'0.2.1'},'Serialization contract revision, distinct from benchmark identity.')
    for key in ['equivalence_margin','target_accuracy_loss_margin','c1_accuracy_loss_margin','minimum_reach','maximum_reach_difference','minimum_gain']:
        c['properties']['evaluation_policy']['properties'][key]['maximum']=1
    c['properties']['calibration_plan']['properties']['difficulty_contract_version']={'const':'G02_G03_0.2.1','description':'Versioned canonicalization contract.'}
    for key in ['evidence_ledger','tracker_state','reflexive_state']:
        # Exact mode/context partitions can exceed the former family-only cap20.
        field=t['$defs']['agent_state']['properties'][key]
        if 'maxItems' in field:field['maxItems']=128
        for branch in field.get('anyOf',[]):
            if 'maxItems' in branch:branch['maxItems']=128
    stop=t['$defs']['stop_state'];stop['properties']['scope_id']=fld(ID,'Public task scope; C0 uses scope without a numeric claim. No accidental global latch.')
    # Lossless bounded history: show last attempts, plus explicit derived anchors,
    # all sourced from the same public log and offered to B0-B3 equally.
    t['$defs']['agent_state']['properties']['profile_history']['description']='Last history_window attempts, COMMITTED and REJECTED; full immutable private log retained.'
    d['history_anchor']=obj({'claim_id':fld(ID,'Existing slot.'),'version':fld({'type':'integer','minimum':1},'Historical committed claim version.'),
        'claim':fld(ref('r1_self_profile','claim'),'Exact old public snapshot; not evaluator interpretation.'),
        'reason':fld(en('LAST_NUMERIC','SCOPE_PARENT','RESTORE_REQUEST'),'Why this bounded anchor is present.')},'Derived snapshot, not a new canonical self-model object.')
    add(t['$defs']['agent_state'],'history_anchors',arr(ref('r1_config','history_anchor'),8),'Public derivation: last numeric and scope-parent snapshots per claim; bounded, same access B0-B3.')
    d['evidence_index_entry']=obj({'episode_id':fld(ID,'Past observable episode ref.'),'feedback':fld(ref('r1_episode_record','feedback'),'No correct answer or private metadata.')},'Addressable public feedback retained beyond recent window.')
    add(t['$defs']['agent_state'],'evidence_index',arr(ref('r1_config','evidence_index_entry'),32),'All past public feedback refs, at most 32; equal information access, not B3-only memory.')
    for owner in [t,t['$defs']['agent_state']]:
        owner['properties']['reflection_cost']=fld(null(INT),'Observed public PREP+PREP-repair input/output tokens; null when any required count unavailable, not zero.')
    seeds=t['properties']['seed_metadata'];add(seeds,'TASK_ID',SHA,'Separate opaque public task-ID stream, same preimage fields as G01.')
    # R1-PROBE-01: bounded evidence bookkeeping; strong likelihood construct
    # outside R1, not a pending requirement of this patch.
    b3=r['$defs']['b3'];b3['properties']['stop_reflection']['description']='Latch future PREP; does not cancel ACTION or a pending scheduled probe.'
    b3['properties']['probe_predictions']['description']='Prospective annotations only; same labels or UNKNOWN allowed. No schema inference of discrimination.'
    b3['allOf'][0]['then']['properties']={'probe_type':{'not':{'const':'NONE'}}}
    add(b3,'cancel_pending_probe',{'type':'boolean'},'Explicit cancellation, processed before any new declaration; false does not cancel on stop.')
    probe['allOf'][0]['else']['properties']['predictions']={'minItems':0}
    return schemas
