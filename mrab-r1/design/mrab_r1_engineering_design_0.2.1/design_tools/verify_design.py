"""Read-only verification of DELIVERED bytes; output must be outside package.

No builder imports, no regenerated expected fixtures, no network, no model.
Python -B recommended. Each check has a bounded evidence payload and provenance.
"""
import argparse,hashlib,json,sys,zipfile,math
from pathlib import Path
from copy import deepcopy as cp
from fractions import Fraction

def encode(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
def digest(data):return hashlib.sha256(data).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():digest(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def main(root,output,dependencies):
    root=root.resolve();output=output.resolve()
    if output==root or root in output.parents:raise ValueError('Verifier output must be outside verified package')
    if output.exists():raise FileExistsError('Refuse to overwrite previous verification evidence')
    if dependencies:sys.path.insert(0,str(dependencies.resolve()))
    from jsonschema import Draft202012Validator
    from referencing import Registry,Resource
    from contract_checks import (classify_summary,beta_sf_integer,evidence_gate,freeze_errors,check_update_vector,trace_vector,
        bundle_public_schema,request_vector,private_record_request_vector,canonical,seed_preimage,tiny_solution_anchored_key,rate,operational_rows,usage_vector,opportunity_metrics,response_latency,
        probe_scope_vector,prep_path_vector,strong_b4_vector,b4_policy_change_vector,STRUCTURALLY_MORE_COMPLEX)
    before=inventory(root);checks=[];captures={};output.mkdir(parents=True)
    def record(id,ok,evidence,level='EXECUTED'):
        checks.append(dict(id=id,status=('PASS' if ok else 'FAIL') if level=='EXECUTED' else level,evidence=evidence))
    def read(path):return json.loads((root/path).read_bytes())
    schemas={p.name:json.loads(p.read_bytes()) for p in sorted((root/'schemas').glob('*.json'))}
    registry=Registry().with_resources([(s['$id'],Resource.from_contents(s)) for s in schemas.values()])
    def validation(address,value):
        name,_,fragment=address.partition('#');schema=schemas[name]
        target={'$ref':schema['$id']+('#'+fragment if fragment else '')}
        return list(Draft202012Validator(target,registry=registry).iter_errors(value))
    for name,s in schemas.items():
        Draft202012Validator.check_schema(s)
        refs=[]
        def walk(x):
            if isinstance(x,dict):
                if '$ref' in x:
                    registry.resolver(s['$id']).lookup(x['$ref']);refs.append(x['$ref'])
                for v in x.values():walk(v)
            elif isinstance(x,list):
                for v in x:walk(v)
        walk(s);record('SCHEMA:'+name,True,dict(metaschema='Draft202012',resolved_refs=len(refs)))
    corpus=read('design_checks/schema_specimens.json');items=corpus['specimens'];byid={r['specimen_id']:r for r in items}
    for row in items:
        errors=validation(row['schema'],row['instance']);valid=not errors
        record('CORPUS:'+row['specimen_id'],valid==row['expected_schema_valid'],dict(expected=row['expected_schema_valid'],actual=valid,
            errors=[dict(path='/'+('/'.join(map(str,e.absolute_path))),message=e.message[:240]) for e in errors[:3]]))
    record('CORPUS:unique-ids',len(byid)==len(items),len(items))
    # Reproduce delivered 0.1 failure without importing its mutating audit script.
    with zipfile.ZipFile(root/'references/MRAB_R1_Engineering_Design_Package_0.1.zip') as z:
        prefix='mrab_r1_engineering_design_0.1/'
        oldschemas=[json.loads(z.read(n)) for n in z.namelist() if n.startswith(prefix+'schemas/') and n.endswith('.json')]
        oldreg=Registry().with_resources([(s['$id'],Resource.from_contents(s)) for s in oldschemas]);olds={s['$id'].rsplit('/',1)[-1]:s for s in oldschemas}
        oldrows=json.loads(z.read(prefix+'design_checks/schema_specimens.json'))['specimens'];mismatches=[]
        for r in oldrows:
            name,_,frag=r['schema'].partition('#');address=olds[name]['$id']+('#'+frag if frag else '')
            if Draft202012Validator({'$ref':address},registry=oldreg).is_valid(r['instance'])!=r['expected_schema_valid']:mismatches.append(r['specimen_id'])
        oldcode=z.read(prefix+'design_tools/audit_design.py').decode('utf-8')
    record('A01:old-delivered-40-of-42',sorted(mismatches)==['private-no-profile-B4','private-no-profile-C0'],dict(original_matches=len(oldrows)-len(mismatches),total=len(oldrows),mismatches=mismatches))
    record('A01:original-alias-cause','instance=value' in oldcode and 'bad.update' in oldcode,dict(source='references/original ZIP/design_tools/audit_design.py',inspection='Source tokens plus reproduced serialized mismatch; not execution of original builder'))
    # Inspect and execute only the isolated deepcopy registration AST, NOT builder.
    import ast
    tree=ast.parse((root/'design_tools/build_design_vectors.py').read_text(encoding='utf-8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='register')
    env={'cp':cp,'KIND':'DESIGN_TEST_VECTOR_NOT_MODEL_RESULT'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'isolated_register','exec'),env)
    source={'nested':{'profile':1}};rows=[];env['register'](rows,'mutation','schema',source,False);source['nested']['profile']=None
    record('A01:deepcopy-registration',rows[0]['instance']['nested']['profile']==1,rows)
    fields=[]
    def fieldwalk(name,x,path='#'):
        if isinstance(x,dict):
            if x.get('type')=='object':
                for key,v in x.get('properties',{}).items():
                    if 'description' in v:fields.append((name,path+'/properties/'+key,v['description']))
            for k,v in x.items():fieldwalk(name,v,path+'/'+k)
        elif isinstance(x,list):
            for i,v in enumerate(x):fieldwalk(name,v,path+'/'+str(i))
    for name,s in schemas.items():fieldwalk(name.removesuffix('.schema.json'),s)
    dictionary=(root/'MRAB_R1_FIELD_DICTIONARY.md').read_text(encoding='utf-8')
    actual=[line for line in dictionary.splitlines() if line.startswith('| r1_')]
    expected=[f'| {name} | `{path}` | {desc.replace("|","/")} |' for name,path,desc in sorted(fields)]
    record('SCHEMA:dictionary-exact',actual==expected,dict(expected_fields=len(expected),actual_fields=len(actual)))
    defs=schemas['r1_config.schema.json']['$defs']
    record('SCHEMA:reserved-enums',defs['architecture']['enum']==['B0','B1','B2','B3','B4','B5'] and defs['profile_condition']['enum']==['C0','C1','C2','C3','C4'],dict(architectures=defs['architecture']['enum'],conditions=defs['profile_condition']['enum']))
    record('SCHEMA:version-identity',len(schemas)==5 and all('/r1/0.2.1/' in s['$id'] for s in schemas.values()),{k:s['$id'] for k,s in schemas.items()})
    gold=read('design_checks/goldens.json')
    for g in gold['summary_cases']:
        got=classify_summary(g['input']);found=all(any(f['comparator']==need['comparator'] and f['kind']==need['kind'] for f in got['comparator_findings']) for need in g['required_findings'])
        reason=g['required_reason'];ok=got['outcome_class']==g['expected_outcome'] and found and (not reason or any(reason in s for s in got['uncertainty_reasons']))
        forbidden=any(any(f['comparator']==bad['comparator'] and f['kind']==bad['kind'] for f in got['comparator_findings']) for bad in g.get('forbidden_findings',[]))
        record('E07:'+g['id'],ok and not forbidden,dict(expected=g['expected_outcome'],actual=got,forbidden_finding_present=forbidden))
    for g in gold['probe_scope_cases']:
        got=probe_scope_vector(g['loci'],g['labels'])
        record('PROBE21:'+g['id'],got['causal_discrimination_established']==g['expected_causal'] and got['probe_construct']=='BOUNDED_EVIDENCE_PROBE',got)
    for g in read('design_checks/lifecycle_vectors.json')['prep_paths']:
        got=prep_path_vector(**g['input']);record('PREP21:'+g['id'],all(got[k]==v for k,v in g['expected'].items()),dict(input=g['input'],expected=g['expected'],actual=got))
    for g in gold['b4_policy_cases']:
        got=strong_b4_vector(**g['input']);record('B4-21:'+g['id'],got==g['expected'],dict(input=g['input'],expected=g['expected'],actual=got))
    beta=gold['beta_4_2'];got=dict(above_point_four=float(beta_sf_integer(Fraction(2,5),4,2)),mean=4/6,above_point_eight=float(beta_sf_integer(Fraction(4,5),4,2)))
    record('BETA:4-2',got==beta,got)
    gate=evidence_gate(3,1,Fraction(1,4),Fraction(2,5));record('BETA:mismatch-not-solo',gate['mismatch'] and not gate['solo_support'],gate)
    first=next(n for n in range(1,33) if evidence_gate(n,0,Fraction(1,4),Fraction(2,5))['solo_support'])
    reach=dict(first_all_success_support_n=first,smoke_main_family_opportunities=8//2,pilot_main_family_opportunities=24//2,pilot_post_support_opportunities=max(0,12-first),pilot_post_support_after_grace=max(0,12-first-2))
    record('FINITE:gate-reach',reach==gold['finite_gate'],reach)
    counts=dict(smoke_trajectories=4*5*2,smoke_episodes=4*5*2*(8+4),pilot_trajectories=4*5*8,pilot_episodes=4*5*8*(24+8),confirmation_measurements=5*2*2*200,confirmation_calls=(2+3*2)*2*2*200)
    record('COUNTS:matrix-and-calibration',counts==gold['counts'],counts)
    smoke_normal=dict(B0=96,B1=192,B2=192,B3_min=96,B3_max=192,B4_min=0,B4_max=96)
    record('COUNTS21:mandatory-prep-normal',4*2*12*6==576 and 4*8*32*6==6144 and 4*2*12*8==768 and 4*8*32*8==8192,
        dict(smoke_normal_min=576,smoke_normal_max=768,pilot_normal_min=6144,pilot_normal_max=8192,smoke_by_arm=smoke_normal,excludes='repairs, abnormal calls/nonexecutions, calibration'))
    smoke=[];pilot=[]
    for t in range(1,33):
        # Explicit long all-success scripted trajectory, one exact operational key
        # per family; no claim that models or changing histories realize it.
        family='F1' if t%2 else 'F2';previous=(t-1)//2
        g=evidence_gate(previous,0,Fraction(1,4),Fraction(2,5));r=dict(episode=t,family=family,prior_n=previous,main=t<=24,sufficient=g['mismatch'],solo_support=g['solo_support'])
        pilot.append(r)
        if t<=8:smoke.append(r)
    captures['long_scripted_trace.json']=dict(artifact='DESIGN_TEST_VECTOR_NOT_MODEL_RESULT',episodes=pilot)
    record('FINITE:long-trace-not-smoke',not any(r['sufficient'] for r in smoke) and [r['episode'] for r in pilot if r['main'] and r['solo_support']]==[21,22,23,24],dict(smoke_post_e=0,pilot_post_support=[r['episode'] for r in pilot if r['main'] and r['solo_support']]))
    cal=Fraction(181,202);maps=[Fraction(7,8),Fraction(5,8)];ref=[float(abs(m-cal)) for m in maps];live=[float(abs(m-Fraction(5,8))) for m in maps]
    record('CAPABILITY:reference-live-counterexample',ref[0]<ref[1] and live[1]<live[0],dict(reference_180_of_200_posterior_mean=float(cal),hypothetical_live=.625,reference_distances=ref,live_distances=live,label='DESIGN_TEST_VECTOR_NOT_MODEL_RESULT'))
    for tr in read('design_checks/lifecycle_vectors.json')['traces']:
        got=trace_vector(tr['events']);positions=[];start=0
        for event in tr['required']:
            try:index=got['log'].index(event,start);positions.append(index);start=index+1
            except ValueError:break
        record('TRACE:'+tr['id'],len(positions)==len(tr['required']) and got['latched']==tr['latched'],got)
    # Exact family/mode partition and addressability outside the recent10 window.
    feedback=cp(byid['episode-structural-only']['instance']['feedback']);rows=[]
    for i in range(1,15):
        r=cp(feedback);r.update(episode_id='e:'+str(i),episode_index=i);rows.append(r)
    context=cp(feedback);rows[3]['execution_mode']='PREP_SKIPPED';rows[5]['history_class']='EMPTY';rows[6]['chosen_action']='DELEGATE';rows[6]['solo_correct']=None
    retained=operational_rows(rows,context,15)
    record('EVIDENCE:operational-partition',len(retained)==11 and retained[0]['episode_id']=='e:1',dict(retained=[r['episode_id'] for r in retained],recent10=[r['episode_id'] for r in rows[-10:]],evidence_index_count=len(rows)))
    profile=cp(byid['profile-two-slots']['instance']);claim=profile['claims'][0];scopekeys=['scope_id','task_family','difficulty_scope','context_condition','tool_condition','capability_configuration_ref','execution_modes']
    def proposal(p,status='REVISED'):
        c=p['claims'][0]
        return dict(proposal_id='proposal:1',claim_id=c['claim_id'],expected_version=c['version'],new_status=status,new_interval={'lower':.55,'upper':.70},new_scope={k:cp(c[k]) for k in scopekeys},evidence_refs=['e:1'],restore_version=None,basis='Authored scoped evidence')
    evidence=[dict(rows[0],informative=True)];prop=proposal(profile)
    accepted=check_update_vector(profile,prop,'B3',15,evidence,[]);same=check_update_vector(profile,prop,'B2',15,evidence,[])
    record('COMMIT:common-atomic',accepted==same and accepted['status']=='COMMITTED' and accepted['profile']['version']==2 and accepted['profile']['claims'][0]['version']==3 and not validation('r1_self_profile.schema.json#/$defs/update_event',accepted['event']),accepted)
    for id,change,actor,ev in [
        ('readonly-B1',{},'B1',evidence),('readonly-B0',{},'B0',evidence),('stale',{'expected_version':9},'B3',evidence),
        ('future',{'evidence_refs':['future']},'B3',evidence),('foreign-family',{'claim_id':profile['claims'][1]['claim_id']},'B3',evidence),
        ('unknown-claim',{'claim_id':'missing'},'B3',evidence)]:
        p=cp(prop);p.update(change);got=check_update_vector(profile,p,actor,15,ev,[])
        record('COMMIT:reject-'+id,got['status']=='REJECTED' and got['profile']==profile and not validation('r1_self_profile.schema.json#/$defs/update_event',got['event']),got)
    p=cp(prop);p['new_scope']['capability_configuration_ref']='different';got=check_update_vector(profile,p,'B3',15,evidence,[])
    record('COMMIT:no-configuration-relabel',got['status']=='REJECTED',got['codes'])
    p=cp(prop);p['new_scope']['scope_id']='renamed:scope';got=check_update_vector(profile,p,'B3',15,evidence,[])
    record('COMMIT:scope-address-immutable',got['status']=='REJECTED' and 'SCOPE_VIOLATION' in got['codes'],got['codes'])
    broad=cp(profile);broad['claims'][0]['execution_modes']=['PREP_EXECUTED','PREP_SKIPPED'];p=proposal(broad,'NARROWED');p['new_scope']['execution_modes']=['PREP_EXECUTED'];p['new_interval']=cp(claim['estimated_success_interval'])
    narrow=check_update_vector(broad,p,'B3',15,evidence,[]);restore=proposal(narrow['profile'],'ACTIVE');restore.update(restore_version=1,new_interval=cp(claim['estimated_success_interval']),new_scope={k:cp(claim[k]) for k in scopekeys})
    restored=check_update_vector(narrow['profile'],restore,'B3',16,evidence,[claim]);record('COMMIT:narrow-and-restore',narrow['status']==restored['status']=='COMMITTED' and restored['profile']['claims'][0]['execution_modes']==claim['execution_modes'],dict(narrow=narrow,restore=restored))
    p=proposal(profile,'UNKNOWN');p['new_interval']=None;unknown=check_update_vector(profile,p,'B3',15,evidence,[])
    p=proposal(unknown['profile'],'REVISED');back=check_update_vector(unknown['profile'],p,'B3',16,evidence,[claim]);record('COMMIT:unknown-return',unknown['status']==back['status']=='COMMITTED' and back['stages'][0]['status']=='QUESTIONED' and back['stages'][0]['estimated_success_interval'] is not None,back)
    replay=cp(profile)
    for e in [accepted['event']]:
        replay['version']=e['profile_version_after'];replay['claims']=[cp(e['after_claim']) if c['claim_id']==e['after_claim']['claim_id'] else c for c in replay['claims']]
    record('COMMIT:replay',canonical(replay)==canonical(accepted['profile']),dict(replayed_sha256=digest(canonical(replay)),expected_sha256=digest(canonical(accepted['profile']))))
    # Real assembled design request contents retained, including repair branch.
    state=cp(byid['episode-structural-only']['instance']['agent_input']);state['evidence_index']=[dict(episode_id=r['episode_id'],feedback=r) for r in rows]
    public_schema=bundle_public_schema(schemas,'r1_reflexive_record.schema.json','/$defs/b3')
    hidden1=dict(profile_condition='C2',ground_truth='SECRET_CANARY_A',ids='SECRET_CANARY_A',prompt='SECRET_CANARY_A',schema='SECRET_CANARY_A',history='SECRET_CANARY_A',pending='SECRET_CANARY_A')
    hidden2={k:'SECRET_CANARY_B' for k in hidden1}
    req1=request_vector(state,'Test public interface',public_schema,hidden1,prep=byid['b3']['instance'],receipt=accepted['event']);req2=request_vector(state,'Test public interface',public_schema,hidden2,prep=byid['b3']['instance'],receipt=accepted['event'])
    repair=dict(invalid_output='{invalid',errors=[dict(code='TYPE',path='/action',private_detail='SECRET_CANARY_A')]);err1=request_vector(state,'Repair public schema',public_schema,hidden1,repair=repair);repair['errors'][0]['private_detail']='SECRET_CANARY_B';err2=request_vector(state,'Repair public schema',public_schema,hidden2,repair=repair)
    captures['request_capture.json']=dict(artifact='DESIGN_TEST_VECTOR_NOT_MODEL_RESULT',request=req1,repair=err1,request_sha256=digest(canonical(req1)))
    record('LEAK:request-noninterference',canonical(req1)==canonical(req2) and canonical(err1)==canonical(err2) and b'SECRET_CANARY' not in canonical([req1,err1]),dict(request_sha256=digest(canonical(req1)),repair_sha256=digest(canonical(err1)),limit='Test builder, NOT future runtime'))
    record('LEAK:committer-blind',check_update_vector(profile,prop,'B3',15,evidence,[])==accepted,dict(hidden_metadata_not_in_committer_signature=True,limit='Bounded pure function only'))
    changed=cp(state);changed['trajectory_id']='different:public';changedreq=request_vector(changed,'Test public interface',public_schema,hidden1)
    record('LEAK:public-mutation-sensitive',canonical(changedreq)!=canonical(request_vector(state,'Test public interface',public_schema,hidden1)),dict(positive_control='Public input changes request'))
    record('LEAK:answer-free-output-schema',all(token not in canonical(public_schema).decode('utf-8') for token in ['ground_truth','profile_condition','calibration_cells','posterior_wrong_before']),dict(bundle_bytes=len(canonical(public_schema))))
    private=cp(byid['episode-structural-only']['instance']);private['agent_input']=state;private['update_event']=accepted['event']
    req=private_record_request_vector(private,'Public ACTION',schemas)
    private['evaluator_private']={k:'HIDDEN_MUTATION_CANARY' for k in private['evaluator_private']}
    private['final_answer']='HIDDEN_MUTATION_CANARY';private['feedback']['ground_truth']='HIDDEN_MUTATION_CANARY';private['private_prompt']='HIDDEN_MUTATION_CANARY'
    req2=private_record_request_vector(private,'Public ACTION',schemas)
    captures['private_projection_request.json']=req
    record('LEAK:private-allowlist-payload',canonical(req)==canonical(req2) and b'HIDDEN_MUTATION_CANARY' not in canonical(req2),dict(bytes=len(canonical(req)),receipt_keys=sorted(req['receipt']),boundary='Exact authored private-episode projection; future adapter not executed'))
    config=read('r1_config.default.json');record('FREEZE:template',freeze_errors(config)==['TEMPLATE_NOT_RUNNABLE'],freeze_errors(config))
    frozen=cp(config);frozen['configuration_status']='FROZEN';errs=freeze_errors(frozen)
    record('FREEZE:reject-placeholders',any('architecture_prompt_sha256/B3' in e for e in errs) and any('runtime_identity/' in e for e in errs),errs)
    content={};counter=[0]
    def resolved(x,path=''):
        if isinstance(x,dict):return {k:resolved(v,path+'/'+k) for k,v in x.items()}
        if isinstance(x,list):return [resolved(v,path+'/'+str(i)) for i,v in enumerate(x)]
        if isinstance(x,str) and ('sha256' in path):
            data=('DESIGN_COMPONENT_'+path).encode();h=digest(data);content[h]=data;return h
        if isinstance(x,str) and 'CONFIGURE' in x:return 'design:component'
        return x
    complete=resolved(frozen);complete['design_decisions']['probe_claim']='BOUNDED_EVIDENCE_PROBE'
    h=next(iter(content));complete['selected_difficulty_tuples']=[dict(family=f,band=b,scope_id='scope:'+str(i),tuple_sha256=h) for i,(f,b) in enumerate([('SYMBOLIC_PIPELINE','HIGH'),('SYMBOLIC_PIPELINE','MID'),('RULE_GRID','HIGH'),('RULE_GRID','MID')])]
    # Positive preflight only proves these presence/hash gates, never run readiness.
    record('FREEZE:resolved-synthetic-presence',freeze_errors(complete,content)==[],dict(errors=freeze_errors(complete,content),not_runtime_ready=True,choice_is_fixture_only=True))
    tampered=cp(content);tampered[h]=b'changed';record('FREEZE:wrong-resolved-bytes',bool(freeze_errors(complete,tampered)),freeze_errors(complete,tampered))
    timeout=byid['timeout-retains-call']['instance'];u=usage_vector([timeout]);record('USAGE:timeout-no-zero',u['call_count']==1 and u['exact_tokens'] is None and u['reflection_tokens'] is None and not u['errors'],u)
    badtimeout=cp(timeout);badtimeout['output_tokens']=0;u=usage_vector([badtimeout]);record('USAGE:unavailable-no-fake-zero','UNAVAILABLE_NOT_NULL:output_tokens' in u['errors'],u)
    c=cp(timeout);c.update(response_status='RETURNED',input_tokens=100,output_tokens=40,reasoning_tokens=10,cached_tokens=30,latency_ms=3,monetary_cost=1,output_includes_reasoning=True)
    c['usage_availability']={k:'OBSERVED' for k in c['usage_availability']};c['usage_reason']={k:'' for k in c['usage_reason']};r=cp(c);r.update(phase='REPAIR',repair_of='PREP')
    u=usage_vector([c,r]);record('USAGE:no-double-count',u['exact_tokens']==280 and u['reflection_tokens']==280,u)
    c['output_includes_reasoning']=False;u=usage_vector([c]);record('USAGE:reasoning-excluded-output',u['exact_tokens']==150,u)
    rowsm=[dict(action=a,solo_correct=s,final_correct=f,outcome=o) for a,s,f,o in [('SOLO',False,False,'INCORRECT'),('SOLO',True,True,'CORRECT'),('DELEGATE',None,True,'CORRECT'),('ABSTAIN',None,None,'ABSTAINED')]]
    m=opportunity_metrics(rowsm);record('METRIC:four-outcomes',m['autonomous_error']['value']==.25 and m['accuracy']['value']==.5 and m['completion']['value']==.75,m)
    abnormal_rows=[dict(action=None,solo_correct=None,final_correct=None,outcome=reason if reason!='EXPLICIT_NONEXECUTION' else 'PROTOCOL_FAILURE',prep_skip_reason=reason) for reason in ['PROTOCOL_FAILURE','INFRA_FAILURE','EXPLICIT_NONEXECUTION']]
    m=opportunity_metrics(abnormal_rows);record('PREP21:abnormal-remains-ITT',m['accuracy']['denominator']==3 and m['accuracy']['value']==0 and m['excluded_infra']==0,m)
    record('METRIC:zero',rate(0,0)['value'] is None,rate(0,0))
    control_events=['claim:b','claim:b'];record('METRIC:control-repeat',len(set(control_events))/1==1 and len(control_events)/1==2,dict(touched_proportion=1,events_per_claim=2,damage=None,damage_reason='NOT_INFERRED_FROM_COUNT'))
    early=response_latency(5,3,12);censored=response_latency(5,None,12);record('METRIC:early-censor-grace',early['value']==0 and early['early'] and censored['value']==7 and censored['post_grace_denominator']==6,dict(early=early,censored=censored,never=response_latency(None,None,12)))
    for id,reason in [('ALL_UNKNOWN','NO_NUMERIC_APPLICABLE_CLAIMS'),('B4','NOT_APPLICABLE_NO_PROFILE'),('OPERATIONAL_TRUTH','OPERATIONAL_TRUTH_NOT_IDENTIFIED')]:
        value=rate(0,0,reason);record('METRIC:'+id,value['value'] is None and value['missing_reason']==reason,value)
    # Anti-gaming witnesses: disclose blind spot, do not claim identification.
    profiles=[.875,.325,.875];low_only=['QUESTION' if x<.4 else 'KEEP' for x in profiles]
    no_evidence_revision=['REVISE' for _ in profiles]
    record('GAMING:LOW_ONLY_DISTRUST',low_only==['KEEP','QUESTION','KEEP'],dict(actions=low_only,matrix_has_accurate_low=False,identified_as_genuine_revision=False,limitation='Current C1 not expanded'))
    record('GAMING:EVIDENCE_INDEPENDENT_REVISION',len(set(no_evidence_revision))==1,dict(attempts=no_evidence_revision,admissibility_with_empty_evidence=check_update_vector(profile,prop,'B3',15,[],[])['status'],is_sufficient_evidence_of_learning=False))
    record('PROBE:labels-not-discrimination',True,dict(assessment='MANUAL_CONCEPTUAL_COUNTEREXAMPLE',scope_authority='R1-PROBE-01',contrasting_labels_without_likelihood='NOT_IDENTIFIED',bernoulli_06_vs_09_same_support=['SUCCESS','FAILURE'],likelihood_ratio_one_success=.9/.6),level='MANUAL_REVIEW')
    # Domain-separated seeds and tiny exact-group metamorphism, NOT generator.
    streams=['TASK','TASK_ID','FAMILY_ORDER','SURFACE','PROFILE','MODEL','BOOTSTRAP'];seeds=[digest(seed_preimage('v02','seed','MAIN','block',s,1)) for s in streams]
    splitseeds=[digest(seed_preimage('v02','seed',s,'block','TASK',1)) for s in ['CALIBRATION_SEARCH','CALIBRATION_CONFIRM','MAIN','TRANSFER']]
    record('GEN:seed-domains',len(set(seeds))==7 and len(set(splitseeds))==4 and seed_preimage('v02','seed','MAIN','block','TASK',1,architecture='B2')==seed_preimage('v02','seed','MAIN','block','TASK',1,architecture='B3') and seed_preimage('v02','seed','MAIN','block','TASK',1)!=seed_preimage('v02','seed','MAIN','block','TASK',1,attempt=1),dict(streams=dict(zip(streams,seeds)),splits=splitseeds))
    spec=dict(entities=['a','b'],properties=[dict(property_id='p',values=['x','y'])],constraints=[dict(kind='EQ',atom=dict(entity='a',property='p',value='x'))]);solution={'a':{'p':'x'},'b':{'p':'y'}}
    renamed=dict(entities=['b2','a2'],properties=[dict(property_id='q',values=['v','u'])],constraints=[dict(kind='EQ',atom=dict(entity='a2',property='q',value='u'))]);sol2={'a2':{'q':'u'},'b2':{'q':'v'}}
    key=tiny_solution_anchored_key(spec,solution);key2=tiny_solution_anchored_key(renamed,sol2)
    record('GEN:F2-tiny-alpha',key==key2,dict(key_sha256=digest(key),n=2,k=1,production_solver_executed=False))
    s=cp(spec);s['properties'].append(dict(property_id='q',values=['u','v']));sol={'a':{'p':'x','q':'u'},'b':{'p':'y','q':'v'}}
    ax=dict(entity='a',property='p',value='x');au=dict(entity='a',property='q',value='u');bu=dict(entity='b',property='q',value='u')
    s['constraints'] += [dict(kind='EQ',atom=au),dict(kind='NEQ',atom=dict(entity='a',property='p',value='y')),dict(kind='XOR',left=ax,right=bu),dict(kind='IMPLIES',left=ax,right=au)]
    normalized=tiny_solution_anchored_key(s,sol);permuted=cp(s);permuted['properties'].reverse();permuted['constraints'].reverse()
    xor=next(c for c in permuted['constraints'] if c['kind']=='XOR');xor['left'],xor['right']=xor['right'],xor['left']
    invariant=tiny_solution_anchored_key(permuted,sol);reversed_implies=cp(s);imp=reversed_implies['constraints'][-1];imp['left'],imp['right']=imp['right'],imp['left']
    reversekey=tiny_solution_anchored_key(reversed_implies,sol)
    record('GEN:F2-order-XOR-not-IMPLIES',normalized==invariant and normalized!=reversekey,dict(original=digest(normalized),permuted=digest(invariant),reversed_implies=digest(reversekey),n=2,k=2))
    record('GEN:F2-complexity',math.factorial(5)*math.factorial(3)==720 and math.factorial(5)**4*math.factorial(3)==1244160000,dict(new_candidates=720,old_candidates=1244160000,solver_assignment_cap=math.factorial(5)**3))
    vector=[1,2,3];rotate=lambda v:v[-1:]+v[:-1];swap=lambda v:[v[1],v[0],v[2]]
    shift2=lambda v:v[-2:]+v[:-2]
    record('GEN:F1-noncommuting-permutation',rotate(swap(vector))!=swap(rotate(vector)) and rotate(shift2(vector))==shift2(rotate(vector)),dict(rotate_swap=rotate(swap(vector)),swap_rotate=swap(rotate(vector)),allowed_group='cyclic rotations only',cyclic_witness=rotate(shift2(vector))))
    for file,body in captures.items():(output/file).write_bytes(encode(body))
    # Registries/manifests are checked when assembled; missing ones fail acceptance.
    required=['MRAB_R1_SPEC_0.2.1.md','MRAB_R1_TASK_GENERATOR_CONTRACT_0.2.1.md','MRAB_R1_EVALUATOR_CONTRACT_0.2.1.md','MRAB_R1_FIXTURE_PLAN_0.2.1.md','MRAB_R1_SMOKE_RUN_PLAN_0.2.1.md','MRAB_R1_TRACEABILITY_MATRIX_0.2.1.md','MRAB_R1_WORK_SUMMARY.md','MRAB_R1_DECISION_REGISTER_0.2.1.json','MRAB_R1_FINDING_DISPOSITIONS_0.2.1.json','MRAB_R1_METRIC_REGISTER_0.2.1.json']
    record('DELIVERY:required-documents',all((root/p).is_file() for p in required),dict(missing=[p for p in required if not (root/p).is_file()]))
    open_decisions=[]
    if (root/'MRAB_R1_DECISION_REGISTER_0.2.1.json').exists():
        decisions=read('MRAB_R1_DECISION_REGISTER_0.2.1.json');open_decisions=[r['id'] for r in decisions['decisions'] if r['classification']=='AUTHOR_DECISION_REQUIRED' and r['status']=='OPEN']
        decision_by_id={r['id']:r for r in decisions['decisions']}
        record('CLOSURE21:four-author-decisions',all(decision_by_id.get(k,{}).get('status')=='ACCEPTED' for k in ['R1-PROBE-01','R1-REDUNDANCY-01','R1-PREP-01','R1-B4-01']),{k:decision_by_id.get(k,{}).get('status') for k in ['R1-PROBE-01','R1-REDUNDANCY-01','R1-PREP-01','R1-B4-01']})
        record('CLOSURE21:OD-02',decision_by_id.get('OD-02',{}).get('closed_by')=='R1-PROBE-01' and decision_by_id['OD-02']['status']=='CLOSED' and not open_decisions,dict(od02=decision_by_id.get('OD-02'),open=open_decisions))
        with zipfile.ZipFile(root/'references/MRAB_R1_Engineering_Design_Package_0.2.zip') as z:
            oldconfig=json.loads(z.read('mrab_r1_engineering_design_0.2/r1_config.default.json'))
            olddecisions=json.loads(z.read('mrab_r1_engineering_design_0.2/MRAB_R1_DECISION_REGISTER_0.2.json'))
        oldcap=next(r for r in olddecisions['decisions'] if r['id']=='R1-CAPABILITY-01')
        record('CLOSURE21:capability-unchanged',decision_by_id['R1-CAPABILITY-01']['decision']==oldcap['decision'] and config['design_decisions']['capability_estimand']==oldconfig['design_decisions']['capability_estimand'],dict(decision='R1-CAPABILITY-01',unchanged=True))
        b4fields=['solo_threshold','tracker_prior_alpha','tracker_prior_beta','tracker_refresh','tracker_min_informative','tracker_uncertain_mass_low','tracker_uncertain_mass_high']
        record('B4-21:strong-policy-preserved',all(config['policy'][k]==oldconfig['policy'][k] for k in b4fields) and config['b4_policy_version']=='STRONG_TRACKER_POLICY_0.2',dict(version=config['b4_policy_version'],parameters={k:config['policy'][k] for k in b4fields}))
        changed=cp(config);changed['policy']['tracker_refresh']=2
        mutation=b4_policy_change_vector(config,changed,results_seen=True)
        record('B4-21:no-post-result-silent-tuning',not mutation['allowed'] and mutation['reason']=='NEW_EXPERIMENTAL_PROTOCOL_REQUIRED',mutation)
        record('CLOSURE21:matrix-unchanged',all(config[k]==oldconfig[k] for k in ['architectures','profile_conditions','trajectories_per_cell','main_episodes','transfer_episodes']),dict(architectures=config['architectures'],conditions=config['profile_conditions'],new_baselines=False))
        b4episode=cp(byid['episode-structural-only']['instance']);b4state=b4episode['agent_input']
        b4state.update(current_profile=None,profile_history=[],history_anchors=[],reflexive_state=None,tracker_state=[],capability_configuration=cp(config['capability_configurations']['B4']))
        b4episode.update(action_input_profile=None,prep_record=None,update_event=None)
        b4episode['execution_context'].update(execution_mode='NO_PREP_INTERFACE',prep_call_count=0,prep_skip_reason=None)
        b4request=private_record_request_vector(b4episode,'Fixed tracker action SOLO; solve task only',schemas)
        record('B4-21:no-rich-self-model-payload',b4request['state']['current_profile'] is None and b4request['state']['reflexive_state'] is None and b4request['prep'] is None and b4request['receipt'] is None and b'candidate_loci' not in canonical(b4request),
            dict(output_schema='action_record only',false_profile=False,b3_prep=False,b3_stop_state=False,b3_update_protocol=False,limit='Authored request builder, not runtime'))
        record('RED21:fixed-structural-relation',STRUCTURALLY_MORE_COMPLEX=={'B2':True,'B4':True} and config['structural_relations']=={'B3_more_complex_than_B2':True,'B3_more_complex_than_B4':True},dict(relation=STRUCTURALLY_MORE_COMPLEX,complexity_score_created=False))
    if (root/'MRAB_R1_FINDING_DISPOSITIONS_0.2.1.json').exists():
        findings=read('MRAB_R1_FINDING_DISPOSITIONS_0.2.1.json');ids={r['id'] for r in findings['findings']}
        record('DELIVERY:A01-A16-coverage',ids=={'A'+str(i).zfill(2) for i in range(1,17)},sorted(ids))
    if (root/'MRAB_R1_METRIC_REGISTER_0.2.1.json').exists():
        metrics=read('MRAB_R1_METRIC_REGISTER_0.2.1.json')['metrics'];required_fields={'id','unit','scope','window','numerator','denominator','formula','exclusions','missingness','comparator','reason_codes','input_pointers','verification'}
        with zipfile.ZipFile(root/'references/MRAB_R1_Engineering_Design_Package_0.2.zip') as z:oldmetrics=json.loads(z.read('mrab_r1_engineering_design_0.2/MRAB_R1_METRIC_REGISTER_0.2.json'))['metrics']
        record('CLOSURE21:no-new-metrics',{m['id'] for m in metrics}=={m['id'] for m in oldmetrics},dict(metric_count=len(metrics),new_metrics=[]))
        record('METRIC:register-contract',all(required_fields<=set(r) for r in metrics),dict(metrics=len(metrics),missing={r['id']:sorted(required_fields-set(r)) for r in metrics if not required_fields<=set(r)}))
        badptr=[];totalptr=0
        for metric in metrics:
            for pointer in metric['input_pointers']:
                totalptr+=1;file,_,fragment=pointer.partition('#')
                try:
                    node=schemas[Path(file).name]
                    for key in fragment.strip('/').split('/'):
                        if key:node=node[key.replace('~1','/').replace('~0','~')]
                except (KeyError,TypeError):badptr.append(dict(metric=metric['id'],pointer=pointer))
        record('METRIC:input-pointers',not badptr,dict(resolved=totalptr-len(badptr),bad=badptr))
    sources=read('MRAB_R1_SOURCE_REGISTER.json');source_results=[]
    for r in sources['sources']:
        p=root/r['path'];source_results.append(dict(id=r['id'],matches=p.is_file() and digest(p.read_bytes())==r['sha256']))
    record('SOURCE:hashes',all(r['matches'] for r in source_results),source_results)
    record('SOURCE:original-register-match',sources.get('original_request_matches') is True and all(r.get('original_hash_matches') is True for r in sources['sources'] if r.get('original_register_sha256')),
        dict(original_request_matches=sources.get('original_request_matches'),canonical_matches={r['id']:r['original_hash_matches'] for r in sources['sources'] if r.get('original_register_sha256')}))
    import re
    active_md=[p for p in root.glob('*.md') if p.name!='CHANGELOG_0.1_TO_0.2.md']
    stale=[]
    patterns=[r'OD-02 / AUTHOR_DECISION_REQUIRED',r'OD-02[^\n]{0,80}оста[её]тся[^\n]{0,30}откры',r'до OD-02',r'Опциональный PREP call B1/B2/B3',r'optional PREP',r'EQUIVALENT и B3 дороже X',r'\b\d+\s+PASS[,;]?\s*\d*\s*FAIL']
    for p in active_md:
        body=p.read_text(encoding='utf-8')
        for pattern in patterns:
            if re.search(pattern,body):stale.append(dict(file=p.name,pattern=pattern))
    record('DOC21:no-stale-normative-fragments',not stale,dict(scanned=len(active_md),stale=stale,limit='Lexical regression plus separate MANUAL_REVIEW, not proof by keywords'))
    summary=(root/'MRAB_R1_WORK_SUMMARY.md').read_text(encoding='utf-8')
    record('DOC21:actual-final-report-reference','MRAB_R1_FINAL_VERIFICATION_0.2.1.json' in summary and not re.search(r'\b\d+\s+PASS',summary),dict(summary_uses_final_report=True,no_hardcoded_count=True))
    if (root/'CHANGED_FILES_0.2_TO_0.2.1.json').exists():
        changes=read('CHANGED_FILES_0.2_TO_0.2.1.json');change_ok=True
        with zipfile.ZipFile(root/'references/MRAB_R1_Engineering_Design_Package_0.2.zip') as z:oldbytes={n.split('/',1)[1]:z.read(n) for n in z.namelist()}
        covered=set(changes['unchanged_files'])
        for name in changes['unchanged_files']:
            change_ok=change_ok and (root/name).read_bytes()==oldbytes[name]
        for entry in changes['entries']:
            name=entry['path'];prior=entry['previous_path']
            if prior:change_ok=change_ok and digest(oldbytes[prior])==entry['old_sha256']
            if name:
                covered.add(name)
                if entry['new_sha256']:change_ok=change_ok and digest((root/name).read_bytes())==entry['new_sha256']
        record('DELIVERY21:changed-file-list',change_ok and covered==set(inventory(root)),dict(entries=len(changes['entries']),unchanged=len(changes['unchanged_files']),full_member_coverage=covered==set(inventory(root))))
    manifest=root/'CONTENT_MANIFEST.json'
    if manifest.exists():
        entries=read('CONTENT_MANIFEST.json')['files'];expected_names={r['path'] for r in entries};actual_names=set(inventory(root))-{'CONTENT_MANIFEST.json'}
        record('DELIVERY:content-manifest',expected_names==actual_names and len(entries)==len(expected_names) and all((root/r['path']).is_file() and digest((root/r['path']).read_bytes())==r['sha256'] and (root/r['path']).stat().st_size==r['bytes'] for r in entries),dict(entries=len(entries),exact_inventory=expected_names==actual_names))
        core=['MRAB_R1_SPEC_0.2.1.md',*['schemas/r1_'+n+'.schema.json' for n in ['config','self_profile','episode_record','reflexive_record','trajectory']],
            'MRAB_R1_TASK_GENERATOR_CONTRACT_0.2.1.md','MRAB_R1_EVALUATOR_CONTRACT_0.2.1.md','MRAB_R1_FIXTURE_PLAN_0.2.1.md','MRAB_R1_SMOKE_RUN_PLAN_0.2.1.md','MRAB_R1_TRACEABILITY_MATRIX_0.2.1.md','MRAB_R1_ENGINEERING_DESIGN_CHECK_0.2.1.json','MRAB_R1_WORK_SUMMARY.md']
        record('DELIVERY:all13',len(core)==13 and all((root/p).is_file() for p in core),dict(required_core=core))
    record('READONLY:input-byte-identity',before==inventory(root),dict(files=len(before),unchanged=before==inventory(root)))
    failures=[r['id'] for r in checks if r['status']=='FAIL'];readiness='DESIGN_REPAIR_REQUIRED' if failures else 'DESIGN_REVIEW_REQUIRED' if open_decisions else 'IMPLEMENTATION_READY_DESIGN_ONLY'
    report=dict(artifact='MRAB_R1_ENGINEERING_DESIGN_CHECK_0.2.1',result_kind='DESIGN_TEST_VECTOR_NOT_MODEL_RESULT',readiness=readiness,
        verification_stage='SEALED_FRESH_EXTRACTION' if manifest.exists() else 'PRE_SEAL',
        executed_pass=sum(r['status']=='PASS' for r in checks),executed_fail=len(failures),failures=failures,open_decisions=open_decisions,checks=checks,
        input_hashes=before,model_calls=0,calibration_runs=0,smoke_runs=0,pilot_runs=0,production_runtime_created=False,
        specified_only=['Full generator/solver dual execution','Provider adapter non-interference','Bootstrap from real trajectories','Run manifests with actual model identities','Power/real evidence reach'],
        outside_r1=['Strong likelihood-based causal discrimination construct','Causal external self-model role and internal mechanism'],
        evidence_files=[dict(path=file,sha256=digest((output/file).read_bytes())) for file in captures])
    (output/'MRAB_R1_ENGINEERING_DESIGN_CHECK_0.2.1.json').write_bytes(encode(report))
    print(json.dumps({k:report[k] for k in ['readiness','executed_pass','executed_fail','failures','open_decisions','model_calls']},ensure_ascii=False))
    return bool(failures)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--dependencies',type=Path);a=p.parse_args();sys.exit(main(a.package,a.output,a.dependencies))
