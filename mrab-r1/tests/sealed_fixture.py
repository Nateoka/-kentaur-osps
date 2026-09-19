"""Synthetic, hand-authored captures. ZERO provider invocations, not calibration.

Exercises the complete 20 x 200 evidence boundary with actual generated tasks.
No model, SEARCH call, CONFIRM call, smoke or pilot is executed here.
"""
from copy import deepcopy as cp
import json,os,subprocess
from pathlib import Path
from mrab_r1.canonical import canonical,semantic_sha,raw_sha,loads,integer_dsl_bytes
from mrab_r1.calibration import calibration_items
from mrab_r1.calibration_artifact import scope_for,seal_artifact
from mrab_r1.config import pre_calibration_lock,freeze
from mrab_r1.seed import Stream
from mrab_r1.storage import EventStore
from mrab_r1.prompts import Prompts
from mrab_r1.state import history_state
from mrab_r1.profiles import ProfileStore
from mrab_r1.controller import Controller
from mrab_r1.b4 import Tracker
from mrab_r1.provenance import TEST_VECTOR
from tests.test_freeze import frozen_fixture
from tests.test_runtime_contracts import b3_record


def chain(path,events):
    encoded=json.dumps(events,ensure_ascii=False,separators=(',',':')).encode()
    result=subprocess.run([os.environ['MRAB_JCS_NODE'],str(Path(__file__).with_name('chain_fixture.cjs'))],input=encoded,capture_output=True,check=True,timeout=60)
    Path(path).write_bytes(result.stdout)


def configured():
    config,content=frozen_fixture()
    config['generator_options'].update(symbolic_sizes=[3],symbolic_lengths=[8,12],grid_sizes=[3,4],grid_properties=[2])
    tuples={(f,b):dict(n=3,length=8 if b=='HIGH' else 12) if f=='SYMBOLIC_PIPELINE' else dict(n=3 if b=='HIGH' else 4,k=2)
        for f in ('SYMBOLIC_PIPELINE','RULE_GRID') for b in ('HIGH','MID')}
    config['selected_difficulty_tuples']=[]
    for (family,band),difficulty in sorted(tuples.items()):
        raw=canonical(difficulty);digest=raw_sha(raw);content[digest]=raw
        config['selected_difficulty_tuples'].append(dict(family=family,band=band,scope_id='scope:'+raw_sha(integer_dsl_bytes([family,difficulty]))[:16],tuple_sha256=digest))
    return config,content,tuples


def calibration_fixture(directory):
    config,content,tuples=configured();pre=cp(config);pre.update(configuration_status='TEMPLATE',selected_difficulty_tuples=[])
    lock=pre_calibration_lock(pre,content);events=[];seen={};cells=[];manifests=[];search_results=[]
    def event(kind,payload):events.append(dict(kind=kind,payload=cp(payload)))
    event('CALIBRATION_LOCK',lock)
    prompts=Prompts();request_templates={};empty_profile=ProfileStore(None)
    def measurements(family,band,difficulty,phase,block):
        items=calibration_items(config,family,difficulty,phase,block,seen)
        digest=semantic_sha(items)
        event('CALIBRATION_ITEM_MANIFEST',dict(block_id=block,phase=phase,sha256=digest,items=items))
        successes=(36 if band=='HIGH' else 25) if phase=='SEARCH' else (180 if band=='HIGH' else 124)
        for arch in config['architectures']:
            prep=b3_record(True) if arch=='B3' else dict(record_kind='EXTRA_COMPUTE' if arch=='B1' else 'GENERIC_CRITIC',memo='Test capture.',recommended_action='SOLO',confidence='UNSPECIFIED')
            if arch=='B2':prep['proposal']=None
            for index,item in enumerate(items):
                state=history_state(f'measurement:{index}',1,item['task_view'],empty_profile,[],config['capability_configurations'][arch],None,arch,Controller(lambda:1),Tracker(),[],0)
                answer=cp(item['ground_truth']);correct=index<successes
                if not correct:
                    if family=='SYMBOLIC_PIPELINE':answer['result'][0]+=1
                    else:
                        a,b=answer['result'][:2];a['assignments'],b['assignments']=b['assignments'],a['assignments']
                action=dict(action='SOLO',solo_answer=answer,confidence='UNSPECIFIED');calls=[]
                for number,(call_phase,value) in enumerate(([('PREP',prep)] if arch in {'B1','B2','B3'} else [])+[('ACTION',action)],1):
                    state['current_execution_mode']=None if call_phase=='PREP' else 'PREP_EXECUTED' if arch in {'B1','B2','B3'} else 'NO_PREP_INTERFACE'
                    template_key=(arch,call_phase)
                    if template_key not in request_templates:
                        request_templates[template_key]=loads(prompts.request(call_phase,arch,state,prep if call_phase=='ACTION' and arch in {'B1','B2','B3'} else None,fixed_action='SOLO' if arch=='B4' else None,calibration=True))
                    request=cp(request_templates[template_key]);request['agent_state']=cp(state)
                    request_bytes=json.dumps(request,separators=(',',':')).encode();output=json.dumps(value,separators=(',',':')).encode()
                    rng=Stream(config['master_seed'],'CALIBRATION_'+phase,block,'MODEL',index,architecture=arch,phase=call_phase)
                    cid=f'cal:{block}:{arch}:{index}:call:{number}'
                    cc=dict(phase=call_phase,repair_of=None,max_output_tokens=1024,timeout_seconds=config['timeouts']['model_call_seconds'],temperature=0,top_p=1,sampling_seed=rng.randint(0,2**32-1),seed_digest=rng.digest().hex())
                    resources=dict(input_tokens=100,output_tokens=40,reasoning_tokens=None,cached_tokens=0,latency_ms=1)
                    usage=dict(call_id=cid,phase=call_phase,repair_of=None,input_sha256=raw_sha(request_bytes),output_sha256=raw_sha(output),visible_output=output.decode(),
                        model_revision=config['model_configuration']['model_revision'],sequence=number,request_bytes=request_bytes.decode(),response_status='RETURNED',output_includes_reasoning=True,monetary_cost=None,**resources)
                    usage['usage_availability']={k:'UNAVAILABLE' if v is None else 'OBSERVED' for k,v in dict(resources,monetary_cost=None).items()}
                    usage['usage_reason']={k:'TEST_VECTOR_UNAVAILABLE' if v is None else '' for k,v in dict(resources,monetary_cost=None).items()}
                    event('CALL_REQUEST',dict(call_id=cid,request_hex=request_bytes.hex(),request_sha256=raw_sha(request_bytes),call_config=cc))
                    event('CALL_RESPONSE',dict(call_id=cid,raw_hex=output.hex(),provider_request_id='SYNTHETIC',started_at='0',ended_at='1',status='OK',error_classification=None,observed_model_revision=None,resource_observations=resources))
                    event('CALL_USAGE',usage);calls.append(usage)
                event('CALIBRATION_MEASUREMENT',dict(measurement_id=f'measurement:{block}:{arch}:{index}',architecture=arch,phase=phase,block_id=block,item_index=index,task_id=item['task_view']['task_id'],solo_correct=correct,calls=calls,failure=None,profile=None,history=[],commits=[],tool_events=[],artifact_kind=TEST_VECTOR))
            if phase=='CONFIRM':cells.append(dict(architecture=arch,family=family,band=band,n=200,successes=successes,tuple_sha256=semantic_sha(difficulty),dataset_hash=digest,scope=scope_for(config,arch,family,band,difficulty)))
        if phase=='CONFIRM':manifests.append(dict(family=family,band=band,difficulty=difficulty,tuple_sha256=semantic_sha(difficulty),dataset_hash=digest))
        else:search_results.append(dict(candidate=dict(family=family,difficulty=difficulty),counts=[dict(architecture=a,n=40,successes=successes) for a in config['architectures']]))
    ordered=[(f,b) for f in ('SYMBOLIC_PIPELINE','RULE_GRID') for b in ('HIGH','MID')]
    for i,(f,b) in enumerate(ordered):measurements(f,b,tuples[f,b],'SEARCH',f'search:{i}')
    event('CALIBRATION_SEARCH_SELECTION',dict(search_results=search_results,selected_tuples=cp(config['selected_difficulty_tuples'])))
    event('CALIBRATION_FINAL_FROZEN',freeze(config,content))
    for (f,b),d in sorted(tuples.items()):measurements(f,b,d,'CONFIRM',f'confirm:{f}:{b}')
    event('CALIBRATION_CONFIRMATION',dict(gate_status='PASS',cells=cells))
    path=Path(directory)/'synthetic_calibration.jsonl';chain(path,events)
    with EventStore(path) as store:artifact=seal_artifact(config,lock,cells,manifests,store,offline_fixture=True)
    return config,content,tuples,artifact,path
