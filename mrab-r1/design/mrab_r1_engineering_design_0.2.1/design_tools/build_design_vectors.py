"""Explicit0.2 ->0.2.1 authored vector migration, never called by verifier.

Expectations are author-prescribed, not inferred from checker output.
No runtime, model, generator or solver implementation.
"""
import argparse,json,zipfile
from pathlib import Path
from copy import deepcopy as cp

KIND='DESIGN_TEST_VECTOR_NOT_MODEL_RESULT'
def write(root,name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def register(rows,identity,schema,value,valid,note='R1 patch021 authored vector'):
    rows.append(dict(specimen_id=identity,schema=schema,instance=cp(value),expected_schema_valid=valid,classification=KIND,revision_note=note))

def migrate(x):
    if isinstance(x,list):return [migrate(v) for v in x]
    if not isinstance(x,dict):return x
    x={k:migrate(v) for k,v in x.items()}
    if 'contract_version' in x:x['contract_version']='0.2.1'
    if 'protocol_revision' in x:x['protocol_revision']='R1_0.1_DESIGN_PATCH_0.2.1'
    if 'prep_policy' in x:
        x['prep_policy']={'OPTIONAL_ONE':'EXACTLY_ONE','OPTIONAL_ONE_WITH_LATCH':'AT_MOST_ONE_WITH_CONTROLLER'}.get(x['prep_policy'],x['prep_policy'])
        if x['prep_policy']=='EXACTLY_ONE':x['execution_modes']=['PREP_EXECUTED']
    if 'calibration_plan' in x:
        x['calibration_plan']['difficulty_contract_version']='G02_G03_0.2.1'
        x['design_decisions']['probe_claim']='BOUNDED_EVIDENCE_PROBE'
        x['structural_relations']={'B3_more_complex_than_B2':True,'B3_more_complex_than_B4':True}
        x['b4_policy_version']='STRONG_TRACKER_POLICY_0.2'
    if 'history_policy_id' in x and 'execution_mode' in x:
        x.update(prep_skip_reason=None if x['execution_mode']!='PREP_SKIPPED' else 'B3_STOP_CONTROLLER',
            prep_call_count=1 if x['execution_mode']=='PREP_EXECUTED' else 0)
    if 'chosen_action' in x and 'outcome' in x:x['prep_skip_reason']=None
    return x

def new_summary_cases(base):
    cases=[]
    def uncertain(x,b):
        for c in ['C2','C3']:x['comparators'][b][c]['primary_ci']=[-.4,.4]
    def add(id,comparator,cost,findings,other_weak=False):
        x=cp(base);other='B2' if comparator=='B4' else 'B4'
        uncertain(x,'B1')
        if other_weak:
            for c in ['C2','C3']:
                x['comparators'][other][c].update(primary_ci=[-.12,-.08],fixed_ci=[-.12,-.08],point=-.10)
        else:uncertain(x,other)
        x['comparators'][comparator]['resource_ratios']['tokens']=cost
        cases.append(dict(id=id,input=x,expected_outcome='REDUNDANT',required_findings=[dict(comparator=comparator,kind=k) for k in findings],required_reason=None,
            authority='R1-REDUNDANCY-01'))
    add('RED21-B4-EQUAL-COMPUTE','B4',[-.05,.05],['REDUNDANT','REDUNDANT_BY_STRUCTURE'])
    add('RED21-B2-MORE-EXPENSIVE','B2',[.3,.4],['REDUNDANT','REDUNDANT_BY_COST'])
    add('RED21-B4-B3-CHEAPER','B4',[-.4,-.3],['REDUNDANT','REDUNDANT_BY_STRUCTURE','RESOURCE_ADVANTAGE_B3'])
    add('RED21-WEAK-B2-INDEPENDENT','B4',[-.05,.05],['REDUNDANT'],True)
    add('RED21-WEAK-B4-INDEPENDENT','B2',[-.05,.05],['REDUNDANT'],True)
    x=cp(cases[2]);x['id']='RED21-NONEXECUTION-NOT-SAVING';x['input']['comparators']['B4']['resource_advantage_eligible']=False
    x['required_findings']=[dict(comparator='B4',kind='REDUNDANT_BY_STRUCTURE')];x['forbidden_findings']=[dict(comparator='B4',kind='RESOURCE_ADVANTAGE_B3')];cases.append(x)
    return cases

def prep_vectors():
    rows=[]
    def add(id,b,mode,calls,reason=None,controller=False,valid=True,normal=True):
        rows.append(dict(id=id,input=dict(architecture=b,mode=mode,prep_calls=calls,skip_reason=reason,controller_authorized=controller),
            expected=dict(valid=valid,normal=normal and valid,itt_included=valid,architecture_saving_eligible=normal and valid,operational_evidence_eligible=normal and valid)))
    for b in ['B0','B4']:
        add(b+'-NORMAL-NO-PREP',b,'NO_PREP_INTERFACE',0)
        add(b+'-FORBIDDEN-PREP',b,'PREP_EXECUTED',1,valid=False)
    for b in ['B1','B2']:
        add(b+'-NORMAL-EXACTLY-ONE',b,'PREP_EXECUTED',1)
        add(b+'-UNRECORDED-SKIP',b,'PREP_SKIPPED',0,valid=False)
        add(b+'-CONTROLLER-NOT-ALLOWED',b,'PREP_SKIPPED',0,'B3_STOP_CONTROLLER',True,valid=False)
        add(b+'-TWO-PREP-FORBIDDEN',b,'PREP_EXECUTED',2,valid=False)
        for reason in ['PROTOCOL_FAILURE','INFRA_FAILURE','EXPLICIT_NONEXECUTION']:
            add(b+'-ABNORMAL-'+reason,b,'PREP_SKIPPED',0,reason,normal=False)
    add('B3-NORMAL-PREP','B3','PREP_EXECUTED',1)
    add('B3-NORMAL-CONTROLLER-SKIP','B3','PREP_SKIPPED',0,'B3_STOP_CONTROLLER',True)
    add('B3-UNAUTHORIZED-SKIP','B3','PREP_SKIPPED',0,'B3_STOP_CONTROLLER',False,valid=False)
    add('B3-UNRECORDED-SKIP','B3','PREP_SKIPPED',0,valid=False)
    add('B3-TWO-PREP-FORBIDDEN','B3','PREP_EXECUTED',2,valid=False)
    add('B3-ABNORMAL-NONEXECUTION','B3','PREP_SKIPPED',0,'EXPLICIT_NONEXECUTION',normal=False)
    return rows

def main(original,output):
    root=output.resolve();root.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(original) as z:
        prefix='mrab_r1_engineering_design_0.2/'
        read=lambda n:json.loads(z.read(prefix+n))
        corpus=read('design_checks/schema_specimens.json')
        config=read('r1_config.default.json')
        gold=read('design_checks/goldens.json')
        traces=read('design_checks/lifecycle_vectors.json')
        oldmigration=read('design_checks/corpus_migration.json')
    rows=[]
    for row in corpus['specimens']:
        register(rows,row['specimen_id'],row['schema'],migrate(row['instance']),row['expected_schema_valid'],
            '0.2 expectation retained; required021 fields migrated; R1-PROBE-01 confirms bounded evidence scope')
    config=migrate(config);write(root,'r1_config.default.json',config)
    bad=cp(config);bad['capability_configurations']['B1']['execution_modes'].append('PREP_SKIPPED')
    register(rows,'B1-config-reject-normal-skip','r1_config.schema.json',bad,False)
    bad=cp(config);bad['capability_configurations']['B2']['prep_policy']='AT_MOST_ONE_WITH_CONTROLLER'
    register(rows,'B2-config-reject-controller-policy','r1_config.schema.json',bad,False)
    bad=cp(config);bad['structural_relations']['B3_more_complex_than_B4']=False
    register(rows,'predeclared-structure-not-configurable-score','r1_config.schema.json',bad,False)
    ctx=next(r['instance']['execution_context'] for r in rows if r['specimen_id']=='episode-structural-only')
    for label,reason in [('normal-b3','B3_STOP_CONTROLLER'),('abnormal-protocol','PROTOCOL_FAILURE'),('abnormal-infra','INFRA_FAILURE'),('abnormal-explicit','EXPLICIT_NONEXECUTION')]:
        x=cp(ctx);x.update(execution_mode='PREP_SKIPPED',prep_call_count=0,prep_skip_reason=reason)
        register(rows,'execution-context-'+label,'r1_config.schema.json#/$defs/execution_context',x,True)
    x=cp(ctx);x.update(execution_mode='PREP_SKIPPED',prep_call_count=0,prep_skip_reason=None)
    register(rows,'execution-context-skip-needs-reason','r1_config.schema.json#/$defs/execution_context',x,False)
    write(root,'design_checks/schema_specimens.json',dict(artifact=KIND,benchmark_runs=0,specimens=rows))
    write(root,'design_checks/corpus_migration.json',dict(base='0.2',base_migration_history=oldmigration,patch_rule='All45 original0.2 labels retained, explicit new specimens appended; R1-PROBE-01 closes former draft scope.'))
    oldbase=cp(next(g['input'] for g in gold['summary_cases'] if g['id']=='NEG-B1'))
    migrated=[]
    for g in gold['summary_cases']:
        if g['id']=='NEG-B1':
            for b in ['B2','B4']:
                for c in ['C2','C3']:g['input']['comparators'][b][c]['primary_ci']=[-.4,.4]
            migrated.append(dict(id=g['id'],reason='Isolate B1 equivalence without newly-authorized structural redundancy vs B2/B4. Expected B1 finding/outcome retained.',authority='R1-REDUNDANCY-01'))
        if g['id']=='UNKNOWN-USAGE':
            g['expected_outcome']='REDUNDANT'
            g['required_findings']=[dict(comparator='B4',kind='REDUNDANT_BY_STRUCTURE')]
            migrated.append(dict(id=g['id'],old_expected=None,new_expected='REDUNDANT',reason='Unknown usage remains a reason but cannot cancel established structural redundancy.',authority='R1-REDUNDANCY-01'))
    gold['summary_cases']+=new_summary_cases(oldbase)
    gold['probe_scope_cases']=[
        dict(id='LABELS-DIFFER-NOT-CAUSAL',loci=['SELF_CAPABILITY','TASK_VARIATION'],labels=['FAILURE','SUCCESS'],expected_causal=False),
        dict(id='LABELS-SAME-NOT-CAUSAL',loci=['SELF_CAPABILITY','TASK_VARIATION'],labels=['SUCCESS','SUCCESS'],expected_causal=False),
        dict(id='UNKNOWN-NO-FORCED-PREDICTION',loci=['UNKNOWN'],labels=[],expected_causal=False)]
    gold['b4_policy_cases']=[
        dict(id='PRIOR-VERIFY',input=dict(successes=0,failures=0,opportunity=1),expected='VERIFY'),
        dict(id='MEAN-SOLO',input=dict(successes=9,failures=1,opportunity=11),expected='SOLO'),
        dict(id='LOW-CONFIDENT-DELEGATE',input=dict(successes=0,failures=4,opportunity=5),expected='DELEGATE'),
        dict(id='PERIODIC-REFRESH-VERIFY',input=dict(successes=0,failures=4,opportunity=6),expected='VERIFY'),
        dict(id='UNCERTAIN-VERIFY',input=dict(successes=5,failures=1,opportunity=7),expected='VERIFY'),
        dict(id='NO-TOOL-ABSTAIN',input=dict(successes=0,failures=0,opportunity=1,tool_available=False),expected='ABSTAIN'),
        dict(id='NO-TOOL-SOLO',input=dict(successes=9,failures=1,opportunity=11,tool_available=False),expected='SOLO')]
    write(root,'design_checks/goldens.json',gold)
    write(root,'design_checks/golden_migration_0.2_to_0.2.1.json',migrated)
    traces['prep_paths']=prep_vectors();traces['authority']='R1-PREP-01'
    write(root,'design_checks/lifecycle_vectors.json',traces)
    print(json.dumps(dict(specimens=len(rows),summary_goldens=len(gold['summary_cases']),prep_paths=len(traces['prep_paths']),probe_goldens=len(gold['probe_scope_cases']),b4_goldens=len(gold['b4_policy_cases']),model_calls=0)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.original,a.output)
