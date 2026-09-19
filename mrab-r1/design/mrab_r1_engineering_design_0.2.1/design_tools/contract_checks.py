"""DESIGN_TEST_VECTOR_NOT_MODEL_RESULT.

Pure, bounded contract checks for authored vectors. This is NOT a benchmark
evaluator, committer, runner, solver, generator, calibration or model adapter.
No model calls, hidden reasoning or statistical fitting from experiment data.
"""
from copy import deepcopy as cp
from fractions import Fraction
from math import comb
import hashlib,json,itertools

POLICY=dict(eq=.05,accuracy=.02,c1=.05,resource=.20,min_pairs=6,min_reach=.50,reach_gap=.25,gain=.05)
# R1-REDUNDANCY-01: predeclared relation, NOT an estimated complexity score.
STRUCTURALLY_MORE_COMPLEX={'B2':True,'B4':True}
ABNORMAL_PREP_REASONS={'PROTOCOL_FAILURE','INFRA_FAILURE','EXPLICIT_NONEXECUTION'}
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
def sha(value):return hashlib.sha256(canonical(value)).hexdigest()


def beta_sf_integer(x,a,b):
    """Exact rational survival function for positive integer shapes only."""
    x=Fraction(x);n=a+b-1
    return sum(Fraction(comb(n,k))*x**k*(1-x)**(n-k) for k in range(a))


def evidence_gate(successes,failures,lower,upper,tau=Fraction(4,5)):
    n=successes+failures;a=1+successes;b=1+failures
    up=beta_sf_integer(Fraction(upper),a,b);down=1-beta_sf_integer(Fraction(lower),a,b)
    solo=beta_sf_integer(tau,a,b)
    return dict(n=n,upward=float(up),downward=float(down),wrong_band=float(up+down),
        mismatch=n>=4 and up+down>Fraction(9,10),solo_support=n>=4 and solo>Fraction(9,10),
        probability_above_tau=float(solo),posterior_mean=a/(a+b))


def rate(numerator,denominator,reason='NO_ELIGIBLE_EPISODES'):
    return dict(value=numerator/denominator if denominator else None,numerator=numerator,
        denominator=denominator,missing_reason=None if denominator else reason)

def operational_rows(rows,context,before):
    """Bounded evidence-filter witness; caller supplies public feedback only."""
    keys=['task_family','difficulty_scope','context_condition','tool_condition','capability_configuration_ref','execution_mode','history_class']
    return [cp(r) for r in rows if r['episode_index']<before and r.get('solo_correct') is not None
        and r.get('chosen_action') in ['SOLO','VERIFY'] and r.get('outcome')!='INFRA_FAILURE'
        and all(r[k]==context[k] for k in keys)]

def usage_vector(calls):
    """Small resource arithmetic check: missingness never becomes zero."""
    totals=[];reflection=[];errors=[]
    for c in calls:
        for k,a in c['usage_availability'].items():
            if a=='UNAVAILABLE' and c[k] is not None:errors.append('UNAVAILABLE_NOT_NULL:'+k)
            if a!='UNAVAILABLE' and c[k] is None:errors.append('COUNT_NOT_PRESENT:'+k)
            if a!='OBSERVED' and not c['usage_reason'][k]:errors.append('MISSING_USAGE_REASON:'+k)
        exact=all(c['usage_availability'][k]=='OBSERVED' for k in ['input_tokens','output_tokens'])
        value=None
        if exact and c['output_includes_reasoning'] is True:value=c['input_tokens']+c['output_tokens']
        if exact and c['output_includes_reasoning'] is False and c['usage_availability']['reasoning_tokens']=='OBSERVED':value=c['input_tokens']+c['output_tokens']+c['reasoning_tokens']
        totals.append(value)
        if c['phase']=='PREP' or c['phase']=='REPAIR' and c['repair_of']=='PREP':
            reflection.append(c['input_tokens']+c['output_tokens'] if exact else None)
    return dict(call_count=len(calls),exact_tokens=None if None in totals else sum(totals),
        reflection_tokens=None if None in reflection else sum(reflection),errors=errors)

def opportunity_metrics(rows):
    """Four hand-authored outcome rows only; not a trajectory evaluator."""
    kept=[r for r in rows if r['outcome']!='INFRA_FAILURE' or r.get('prep_skip_reason') in ABNORMAL_PREP_REASONS];n=len(kept)
    return dict(autonomous_error=rate(sum(r['action']=='SOLO' and r['solo_correct'] is False for r in kept),n),
        tools=rate(sum(r['action'] in ['VERIFY','DELEGATE'] for r in kept),n),
        accuracy=rate(sum(r['final_correct'] is True for r in kept),n),
        completion=rate(sum(r['outcome'] in ['CORRECT','INCORRECT'] for r in kept),n),
        excluded_infra=len(rows)-n)

def response_latency(first_e,response,last_opportunity,grace=2):
    if first_e is None:return dict(value=None,reason='NOT_AT_RISK',early=False,censored=False,post_grace_denominator=0)
    return dict(value=max(0,(response if response is not None else last_opportunity)-first_e),reason=None if response is not None else 'RIGHT_CENSORED',
        early=response is not None and response<first_e,censored=response is None,post_grace_denominator=max(0,last_opportunity-first_e+1-grace))


def classify_summary(summary,policy=None):
    """E07 logic ONLY: accepts preregistered synthetic CI summaries, not episodes.

    Every negative/comparator finding is retained before overall classification.
    No nonsignificance=>equivalence, no common score, no inferred model results.
    """
    p=policy or POLICY;findings=[];reasons=[];by={};guard=summary.get('c1',{})
    def valid(ci):return isinstance(ci,list) and len(ci)==2 and ci[0]<=ci[1]
    def eq(ci,m):return valid(ci) and -m<=ci[0] and ci[1]<=m
    def worse(ci,m):return valid(ci) and ci[0]>m
    def better(ci,m=0):return valid(ci) and ci[1]<-m
    def add(against,kind,detail):findings.append(dict(comparator=against,kind=kind,reason=detail))
    c1_safe=all(valid(guard.get(s)) and guard[s][1]<=p['c1'] for s in ['target_accuracy_loss','control_accuracy_loss'])
    c1_harm=any(worse(guard.get(s),p['c1']) for s in ['target_accuracy_loss','control_accuracy_loss'])
    c1_resource_known=all(valid(ci) for ci in guard.get('resource_ratios',{}).values()) and bool(guard.get('resource_ratios'))
    c1_resource_ok=c1_resource_known and all(ci[1]<=p['resource'] for ci in guard['resource_ratios'].values())
    # Predeclared compensating C1 gain is accuracy, never mere completion.
    compensated=all(better(guard.get(s),p['c1']) for s in ['target_accuracy_loss','control_accuracy_loss'])
    c1_safe=c1_safe and (c1_resource_ok or compensated)
    if c1_harm:add('B0/B2:C1','HARM','Accuracy loss exceeds C1 margin; extra cost is not required')
    for comparator in ['B1','B2','B4']:
        data=summary.get('comparators',{}).get(comparator)
        if not data:reasons.append(comparator+':MISSING_COMPARATOR');continue
        costs=data.get('resource_ratios',{})
        known_usage=data.get('usage_known') is True and bool(costs) and all(valid(v) for v in costs.values())
        normal_comparison=data.get('normal_execution_comparison',True)
        comparable=known_usage and normal_comparison and all(eq(v,p['resource']) for v in costs.values())
        more_costly=known_usage and normal_comparison and any(worse(v,p['resource']) for v in costs.values()) and not any(better(v,p['resource']) for v in costs.values())
        less_costly=known_usage and normal_comparison and any(better(v,p['resource']) for v in costs.values()) and not any(worse(v,p['resource']) for v in costs.values())
        resource_advantage=less_costly and data.get('resource_advantage_eligible',True)
        benefit=[];harm=[];equiv=[];eligible=True
        for condition in ['C2','C3']:
            row=data.get(condition,{})
            if row.get('n_pairs',0)<p['min_pairs']:
                reasons.append(comparator+':'+condition+':LOW_PAIRED_N');eligible=False;continue
            accuracy=row.get('accuracy_loss');completion=row.get('completion_loss')
            fixed=row.get('fixed_ci');primary=row.get('primary_ci')
            if not all(valid(x) for x in [accuracy,completion,fixed,primary]):
                reasons.append(comparator+':'+condition+':MISSING_CI');eligible=False;continue
            # Fixed-window definite harm survives differential post-E reach.
            if worse(accuracy,p['accuracy']) or worse(fixed,p['eq']):harm.append(condition)
            reach=row.get('reach')
            reached=isinstance(reach,list) and len(reach)==2 and min(reach)>=p['min_reach'] and abs(reach[0]-reach[1])<=p['reach_gap']
            if not reached:
                reasons.append(comparator+':'+condition+':LOW_OR_DIFFERENTIAL_REACH');eligible=False;continue
            if better(primary) and better(fixed) and row.get('point',0)<=-p['gain'] and accuracy[1]<=p['accuracy'] and completion[1]<=p['eq']:
                benefit.append(condition)
            equiv.append(eq(primary,p['eq']) and eq(fixed,p['eq']) and eq(accuracy,p['accuracy']) and eq(completion,p['eq']))
        equivalent=eligible and len(equiv)==2 and all(equiv)
        by[comparator]=dict(benefit=benefit,harm=harm,equivalent=equivalent,more_costly=more_costly,
            comparable=comparable,eligible=eligible,usage_known=known_usage)
        if harm:add(comparator,'HARM',','.join(harm)+' definite adverse outcome; does not require increased cost')
        if benefit:add(comparator,'BENEFIT',','.join(benefit)+' with accuracy/completion guards')
        if equivalent and comparator in {'B2','B4'} and (STRUCTURALLY_MORE_COMPLEX[comparator] or more_costly):
            add(comparator,'REDUNDANT','R1-REDUNDANCY-01: EQUIVALENT AND (structurally more complex OR materially more expensive)')
            if STRUCTURALLY_MORE_COMPLEX[comparator]:add(comparator,'REDUNDANT_BY_STRUCTURE','Predeclared B3 > '+comparator+' structural relation, not a score')
            if more_costly:add(comparator,'REDUNDANT_BY_COST','Materially greater observed resource cost')
        if resource_advantage:add(comparator,'RESOURCE_ADVANTAGE_B3','Material observed resource advantage with no opposing material resource loss; retained alongside structural redundancy')
        if comparator=='B1' and comparable and (equivalent or harm):
            add(comparator,'NO_STRUCTURAL_ADVANTAGE','Extra compute is sufficient/effective at comparable observed resources')
        if not known_usage:reasons.append(comparator+':UNKNOWN_USAGE')
        if not normal_comparison:reasons.append(comparator+':RESOURCE_COMPARISON_NONEXECUTION')
    harms=[f for f in findings if f['kind']=='HARM'];benefits=[f for f in findings if f['kind']=='BENEFIT']
    redundant=[f for f in findings if f['kind']=='REDUNDANT' and f['comparator'] in {'B2','B4'}]
    no_structure=[f for f in findings if f['kind']=='NO_STRUCTURAL_ADVANTAGE']
    if harms and benefits:outcome='MIXED_TRADEOFF'
    elif harms:outcome='COUNTERPRODUCTIVE'
    elif redundant:outcome='REDUNDANT'
    elif no_structure:outcome='NO_STRUCTURAL_ADVANTAGE'
    elif (c1_safe and all(k in by and by[k]['eligible'] and by[k]['usage_known'] for k in ['B1','B2','B4'])
        and len(by['B2']['benefit'])==2 and by['B4']['benefit'] and by['B1']['benefit'] and by['B1']['comparable']):outcome='PROMISING'
    else:outcome=None
    if outcome is None and not reasons:reasons.append('CI_OR_GUARD_UNRESOLVED')
    return dict(decision_status='CLASSIFIABLE' if outcome else 'INSUFFICIENT_EVIDENCE',outcome_class=outcome,
        comparator_findings=findings,uncertainty_reasons=reasons,unit='TRAJECTORY',result_kind='DESIGN_TEST_VECTOR_NOT_MODEL_RESULT')


def probe_scope_vector(candidate_loci,predicted_labels):
    """Normative entitlement witness, no causal judge or likelihood model."""
    return dict(probe_construct='BOUNDED_EVIDENCE_PROBE',annotations_recorded=len(predicted_labels),
        labels_differ=len(set(predicted_labels))>1,loci_differ=len(set(candidate_loci))>1,
        causal_discrimination_established=False,reason='R1_PROBE_01_LABELS_DO_NOT_ESTABLISH_CAUSAL_DISCRIMINATION')


def prep_path_vector(architecture,mode,prep_calls,skip_reason=None,controller_authorized=False):
    """Finite authored path check only; not a controller or runtime scheduler."""
    errors=[];abnormal=skip_reason in ABNORMAL_PREP_REASONS
    if architecture in {'B0','B4'}:
        if prep_calls!=0 or mode!='NO_PREP_INTERFACE' or skip_reason is not None:errors.append('PREP_FORBIDDEN')
    elif architecture in {'B1','B2'}:
        if mode=='PREP_EXECUTED' and prep_calls==1 and skip_reason is None:pass
        elif mode=='PREP_SKIPPED' and prep_calls==0 and abnormal:pass
        else:errors.append('MANDATORY_PREP_NOT_EXECUTED_OR_INVALID_REASON')
    elif architecture=='B3':
        if mode=='PREP_EXECUTED' and prep_calls==1 and skip_reason is None:pass
        elif mode=='PREP_SKIPPED' and prep_calls==0 and skip_reason=='B3_STOP_CONTROLLER' and controller_authorized:pass
        elif mode=='PREP_SKIPPED' and prep_calls==0 and abnormal:pass
        else:errors.append('B3_SKIP_REQUIRES_CONTROLLER_OR_ABNORMAL_REASON')
    else:errors.append('UNKNOWN_ARCHITECTURE')
    return dict(valid=not errors,errors=errors,normal=not abnormal and not errors,itt_included=not errors,
        architecture_saving_eligible=not errors and not abnormal,
        operational_evidence_eligible=not errors and not abnormal,
        abnormal_reason=skip_reason if abnormal else None)


def strong_b4_vector(successes,failures,opportunity,tool_available=True,policy=None):
    """Small deterministic policy truth-table witness, not a deployed router."""
    p=policy or dict(solo_threshold=.8,tracker_prior_alpha=1,tracker_prior_beta=1,tracker_refresh=3,tracker_min_informative=4,tracker_uncertain_mass_low=.1,tracker_uncertain_mass_high=.9)
    a=p['tracker_prior_alpha']+successes;b=p['tracker_prior_beta']+failures
    if int(a)!=a or int(b)!=b:raise ValueError('DESIGN_VECTOR_INTEGER_BETA_ONLY')
    mean=a/(a+b);mass=float(beta_sf_integer(Fraction(str(p['solo_threshold'])),int(a),int(b)))
    if not tool_available:return 'SOLO' if mean>=p['solo_threshold'] else 'ABSTAIN'
    if mean>=p['solo_threshold']:return 'SOLO'
    if successes+failures<p['tracker_min_informative'] or p['tracker_uncertain_mass_low']<=mass<=p['tracker_uncertain_mass_high'] or opportunity%p['tracker_refresh']==0:return 'VERIFY'
    return 'DELEGATE'


def b4_policy_change_vector(before,after,results_seen):
    """Frozen-policy mutation guard witness, not a run manager."""
    keys=['solo_threshold','tracker_prior_alpha','tracker_prior_beta','tracker_refresh','tracker_min_informative','tracker_uncertain_mass_low','tracker_uncertain_mass_high']
    changed=any(before['policy'][k]!=after['policy'][k] for k in keys)
    return dict(changed=changed,allowed=not (changed and results_seen and before['protocol_revision']==after['protocol_revision']),
        reason='NEW_EXPERIMENTAL_PROTOCOL_REQUIRED' if changed and results_seen and before['protocol_revision']==after['protocol_revision'] else None)


def freeze_errors(config,content=None):
    """Semantic freeze preflight witness, not a provider implementation check."""
    if config['configuration_status']!='FROZEN':return ['TEMPLATE_NOT_RUNNABLE']
    errors=[]
    if content is None:errors.append('CONTENT_MANIFEST_NOT_PROVIDED')
    def walk(x,path='',hash_context=False):
        if isinstance(x,dict):
            for k,v in x.items():
                hashed=hash_context or 'sha256' in k or k.endswith('_hash')
                if hashed and isinstance(v,str):
                    if len(v)!=64 or len(set(v))==1:errors.append('PLACEHOLDER_HASH:'+path+'/'+k)
                    elif content is not None and (v not in content or hashlib.sha256(content[v]).hexdigest()!=v):errors.append('UNRESOLVED_CONTENT:'+path+'/'+k)
                walk(v,path+'/'+k,hashed)
        elif isinstance(x,list):
            for i,v in enumerate(x):walk(v,path+'/'+str(i))
        elif isinstance(x,str) and any(s in x.upper() for s in ['CONFIGURE','PLACEHOLDER','AUTHOR_DECISION_REQUIRED']):errors.append('UNRESOLVED_SETTING:'+path)
    walk(config)
    if len(config.get('selected_difficulty_tuples',[]))!=4:errors.append('MISSING_SELECTED_DIFFICULTY_TUPLES')
    if config.get('design_decisions',{}).get('probe_claim')!='BOUNDED_EVIDENCE_PROBE':errors.append('R1_PROBE_01_SCOPE_MISMATCH')
    return errors


def scoped_subset(after,before):
    return (after['task_family']==before['task_family'] and after['tool_condition']==before['tool_condition']
        and after['capability_configuration_ref']==before['capability_configuration_ref']
        and all(set(after[k])<=set(before[k]) for k in ['difficulty_scope','context_condition','execution_modes']))


def check_update_vector(profile,proposal,actor,episode,evidence,history):
    """One authored transaction vector. Produces no persisted state or calls."""
    after_profile=cp(profile);claim=next((v for v in profile['claims'] if v['claim_id']==proposal['claim_id']),None)
    errors=[];before=cp(claim)
    if actor not in {'B2','B3'}:errors.append('UNAUTHORIZED_ACTOR')
    if claim is None:errors.append('UNKNOWN_CLAIM')
    if claim and proposal['expected_version']!=claim['version']:errors.append('STALE_VERSION')
    known={x['episode_id']:x for x in evidence}
    if any(k not in known or known[k]['episode_index']>=episode for k in proposal['evidence_refs']):errors.append('FUTURE_EVIDENCE')
    if claim:
        scope=proposal['new_scope'];restored=next((x for x in history if x['claim_id']==claim['claim_id'] and x['version']==proposal['restore_version']),None)
        if scope['scope_id']!=claim['scope_id']:errors.append('SCOPE_VIOLATION')
        if not scoped_subset(scope,claim) and not (restored and proposal['new_status']=='ACTIVE' and scoped_subset(scope,restored) and scoped_subset(restored,scope)):errors.append('SCOPE_VIOLATION')
        interval=proposal['new_interval'];status=proposal['new_status']
        if (status=='UNKNOWN')!=(interval is None) or (interval and not 0<=interval['lower']<=interval['upper']<=1):errors.append('INVALID_INTERVAL')
        numerical=interval!=claim['estimated_success_interval'] or not (scoped_subset(scope,claim) and scoped_subset(claim,scope))
        local=[known[k] for k in proposal['evidence_refs'] if k in known and known[k]['episode_index']<episode
            and known[k]['task_family']==scope['task_family'] and known[k]['difficulty_scope'] in scope['difficulty_scope']
            and known[k]['context_condition'] in scope['context_condition']
            and known[k]['tool_condition']==scope['tool_condition']
            and known[k]['capability_configuration_ref']==scope['capability_configuration_ref']
            and known[k]['execution_mode'] in scope['execution_modes']]
        if not local or numerical and not any(x['informative'] for x in local):errors.append('NO_LOCAL_EVIDENCE')
        terminal={'ACTIVE','REVISED','NARROWED','UNKNOWN'}
        path=[claim['status']]
        if claim['status']!='QUESTIONED':path+=['QUESTIONED']
        if status!='QUESTIONED':path+=[status]
        if status==claim['status']=='QUESTIONED' or status not in terminal|{'QUESTIONED'}:errors.append('LIFECYCLE_VIOLATION')
        numeric=next((x for x in reversed(history+[claim]) if x['claim_id']==claim['claim_id'] and x['estimated_success_interval'] is not None),None)
        if claim['status']=='UNKNOWN' and not numeric:errors.append('LIFECYCLE_VIOLATION')
        if status=='ACTIVE':
            expected=(restored or numeric)
            if expected is None or interval!=expected['estimated_success_interval']:errors.append('LIFECYCLE_VIOLATION')
        if status=='QUESTIONED' and interval!=(numeric or claim)['estimated_success_interval']:errors.append('LIFECYCLE_VIOLATION')
        if status=='REVISED' and not (scoped_subset(scope,claim) and scoped_subset(claim,scope)):errors.append('SCOPE_VIOLATION')
        if status=='NARROWED' and (not scoped_subset(scope,claim) or scoped_subset(claim,scope)):errors.append('SCOPE_VIOLATION')
    else:path=[]
    if errors:
        event=dict(proposal=cp(proposal),validation_status='REJECTED',rejection_codes=sorted(set(errors)),transition_path=[],before_claim=before,after_claim=None,effective_episode=episode,
            sequence=2,profile_version_before=profile['version'],profile_version_after=profile['version'],stage_snapshots=[])
        return dict(status='REJECTED',codes=sorted(set(errors)),profile=after_profile,stages=[],event=event)
    stages=[];current=cp(claim)
    for state in path[1:]:
        current['status']=state;current['version']+=1;current['last_updated_episode']=episode
        if state=='QUESTIONED' and current['estimated_success_interval'] is None:current['estimated_success_interval']=cp(numeric['estimated_success_interval'])
        if state==status:current.update(cp(proposal['new_scope']));current['estimated_success_interval']=cp(interval)
        current['evidence_n']=len({x['episode_id'] for x in local if x['informative']})
        current['evidence_label']='OBSERVED_OUTCOMES';stages.append(cp(current))
    after_profile['claims']=[current if x['claim_id']==claim['claim_id'] else x for x in after_profile['claims']];after_profile['version']+=1
    event=dict(proposal=cp(proposal),validation_status='COMMITTED',rejection_codes=[],transition_path=path,before_claim=before,after_claim=current,effective_episode=episode,
        sequence=2,profile_version_before=profile['version'],profile_version_after=after_profile['version'],stage_snapshots=cp(stages))
    return dict(status='COMMITTED',codes=[],profile=after_profile,stages=stages,event=event)


def trace_vector(events):
    """Finite scripted lifecycle trace; no scheduler or model execution."""
    pending=None;latched=False;commit=0;log=[];observations=0
    for ev in events:
        kind=ev['event']
        if kind=='DECLARE':
            if pending:log.append('CANCELLED:'+pending['id'])
            pending=cp(ev);log.append('DECLARED:'+ev['id'])
        elif kind=='CANCEL':
            if pending:log.append('CANCELLED:'+pending['id']);pending=None
            latched=False
        elif kind=='STOP':latched=True;observations=0;log.append('LATCHED')
        elif kind=='PREP':log.append('PREP_SKIPPED' if latched or pending and ev.get('waiting') else 'PREP_EXECUTED')
        elif kind=='COMMIT':commit+=1;log.append('COMMITTED')
        elif kind=='ACTION':
            log.append('ACTION:'+ev['action'])
            if pending and ev.get('matches',True):pending['acted']=True
        elif kind=='FEEDBACK':
            if ev.get('informative'):observations+=1
            if pending and pending.get('acted') and ev.get('informative'):
                log.append('EVIDENCE_RETURNED:'+pending['id']);pending=None;latched=False
            if observations>=2 or ev.get('surprise'):latched=False;log.append('RESTART')
        elif kind=='EXPIRE':
            if pending and ev.get('episode',0)>pending.get('expires',-1):log.append('EXPIRED:'+pending['id']);pending=None;latched=False
        elif kind=='ACTION_PROTOCOL_FAILURE':log.append('PROTOCOL_FAILURE_WITH_COMMIT_'+str(commit))
        elif kind=='END_EPISODE':
            if pending and pending.get('type')=='CURRENT' and not pending.get('acted'):
                log.append('CANCELLED:'+pending['id']+':ACTION_NOT_EXECUTED');pending=None;latched=False
        elif kind=='END':log.append('END_PENDING' if pending else 'END_NO_PENDING')
    return dict(log=log,pending=pending,latched=latched,commits=commit)


def bundle_public_schema(schemas,file,fragment):
    """Small test payload builder: reachable public output schema only."""
    root=schemas[file]
    def resolve(uri):
        name=uri.split('#',1)[0].rsplit('/',1)[-1];node=schemas[name]
        for key in uri.partition('#')[2].strip('/').split('/'):
            if key:node=node[key]
        return node
    def expand(x):
        if isinstance(x,dict):
            if '$ref' in x:return expand(resolve(x['$ref']))
            return {k:expand(v) for k,v in x.items() if k not in {'description','title','$id','$defs'}}
        if isinstance(x,list):return [expand(v) for v in x]
        return x
    node=root
    for key in fragment.strip('/').split('/'):
        if key:node=node[key]
    return expand(node)


def request_vector(public_state,instruction,output_schema,hidden=None,prep=None,receipt=None,repair=None):
    """hidden argument is deliberately not consulted. Captured requests retained."""
    if repair is not None:
        # Error codes/paths supplied by public validation, never private value repr.
        return dict(instruction=instruction,invalid_output=repair['invalid_output'],
            errors=[{'code':x['code'],'path':x['path']} for x in repair['errors']],output_schema=cp(output_schema))
    receipt=None if receipt is None else {k:cp(receipt[k]) for k in ['validation_status','rejection_codes','effective_episode']}
    return dict(instruction=instruction,state=cp(public_state),output_schema=cp(output_schema),prep=cp(prep),receipt=receipt)

def private_record_request_vector(record,instruction,schemas):
    """Test allowlist assembly from an authored private episode, never sent."""
    state=cp(record['agent_input'])
    state['current_profile']=cp(record['action_input_profile'])
    state['current_execution_mode']=record['execution_context']['execution_mode']
    schema=bundle_public_schema(schemas,'r1_config.schema.json','/$defs/action_record')
    return request_vector(state,instruction,schema,prep=record['prep_record'],receipt=record['update_event'])


def seed_preimage(protocol,master,split,block,stream,item,attempt=0,counter=0,architecture=None,phase=None):
    """Contract witness for seed derivation, not random task generation."""
    if stream not in {'TASK','TASK_ID','FAMILY_ORDER','SURFACE','PROFILE','MODEL','BOOTSTRAP'}:raise ValueError('UNKNOWN_STREAM')
    return canonical(['MRAB-R1',protocol,master,split,block,stream,item,attempt,counter,
        architecture if stream=='MODEL' else None,phase if stream=='MODEL' else None])


def tiny_solution_anchored_key(spec,solution):
    """Only n<=3 hand-authored UNIQUE goldens. NOT production canonicalizer/solver.

    Full design uses n!*k! candidates, with each property's value labels fixed
    by the unique solution. Public renderer must never expose that private key.
    """
    entities=spec['entities'];props=spec['properties'];assert len(entities)<=3
    candidates=[]
    for ep in itertools.permutations(entities):
        for pp in itertools.permutations([p['property_id'] for p in props]):
            em={x:'e'+str(i) for i,x in enumerate(ep)};pm={x:'p'+str(i) for i,x in enumerate(pp)}
            vm={(p,solution[e][p]):'v'+str(i) for i,e in enumerate(ep) for p in pp}
            def atom(a):return [em[a['entity']],pm[a['property']],vm[(a['property'],a['value'])]]
            clauses=[]
            for x in spec['constraints']:
                operands=[atom(x['atom'])] if 'atom' in x else [atom(x['left']),atom(x['right'])]
                if x['kind']=='XOR':operands.sort()
                clauses.append([x['kind'],operands])
            candidates.append(canonical([len(ep),len(pp),sorted(clauses)]))
    return min(candidates)
