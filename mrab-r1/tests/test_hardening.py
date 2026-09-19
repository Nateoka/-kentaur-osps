from copy import deepcopy as cp
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
from mrab_r1.canonical import semantic_sha,canonical,canonical_many,raw_sha
from mrab_r1.config import pre_calibration_lock,verify_calibration_lock
from mrab_r1.manifest import build_manifest
from mrab_r1.invariants import enforce_trajectory
from mrab_r1.evaluator import evaluate_dataset
from mrab_r1.runner import TrajectoryRunner
from mrab_r1.provider import FakeProvider
from mrab_r1.errors import Failure
from mrab_r1.storage import read_events,EventStore
from mrab_r1.provenance import TEST_VECTOR,collect_run_bundle,verify_calls
from mrab_r1.calibration import CalibrationEngine,search_and_confirm
from mrab_r1.calibration_artifact import verify_artifact,materialize_reference_cells
from tests.test_runner import reference_cells,scripts
from tests.sealed_fixture import configured,calibration_fixture,chain


class HardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.config,cls.content,cls.tuples=configured()
        cls.manifest=build_manifest(cls.config,cls.tuples,content=cls.content)
        cls.plan=next(t for t in cls.manifest['payload']['trajectories'] if t['architecture']=='B0' and t['condition']=='C1')
        cls.path=cls.root/'events.jsonl'
        cls.trajectory=TrajectoryRunner(cls.config,cls.manifest,cls.plan['trajectory_id'],FakeProvider(scripts(cls.manifest,cls.plan,'VERIFY')),cls.path,reference_cells(cls.config,cls.plan)).run(2)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def reject(self,call):
        with self.assertRaises(Failure) as caught:call()
        self.assertEqual(caught.exception.kind,'INFRA_FAILURE')
        return caught.exception.code

    def test_I18_all_planned_identity_mutations(self):
        self.assertEqual(enforce_trajectory(self.trajectory,self.manifest,self.config)['status'],'PASS')
        mutations=dict(profile_condition='C2',block_id='block:other',architecture='B1',target_family='RULE_GRID' if self.plan['target_family']=='SYMBOLIC_PIPELINE' else 'SYMBOLIC_PIPELINE',
            target_stratum='MID' if self.plan['target_stratum']=='HIGH' else 'HIGH',first_family='RULE_GRID' if self.plan['first_family']=='SYMBOLIC_PIPELINE' else 'SYMBOLIC_PIPELINE',
            planned_run='PILOT',config_sha256='b'*64,trajectory_id='unplanned')
        for key,value in mutations.items():
            with self.subTest(mutation=key):
                t=cp(self.trajectory);t[key]=value
                self.reject(lambda:enforce_trajectory(t,self.manifest,self.config))
        for domain in self.trajectory['seed_metadata']:
            with self.subTest(mutation='seed_metadata:'+domain):
                t=cp(self.trajectory);t['seed_metadata'][domain]='a'*64
                self.reject(lambda:enforce_trajectory(t,self.manifest,self.config))

    def test_manifest_hash_config_and_frozen_gate(self):
        from mrab_r1.config import freeze
        with self.assertRaises(Failure):freeze(self.config,None)
        m=cp(self.manifest);m['payload']['planned_run']='PILOT'
        self.reject(lambda:enforce_trajectory(self.trajectory,m,self.config))
        c=cp(self.config);c['master_seed']='another-seed'
        self.reject(lambda:enforce_trajectory(self.trajectory,self.manifest,c))
        c=cp(self.config);c['configuration_status']='TEMPLATE'
        self.reject(lambda:enforce_trajectory(self.trajectory,self.manifest,c))
        self.reject(lambda:enforce_trajectory(self.trajectory,self.manifest))

    def test_scientific_defaults_fail_closed_before_metrics(self):
        with patch('mrab_r1.evaluator.evaluate_trajectory') as metric:
            self.reject(lambda:evaluate_dataset([self.trajectory]))
            self.reject(lambda:evaluate_dataset([self.trajectory],mode='SCIENTIFIC',master_seed='arbitrary'))
            metric.assert_not_called()

    def test_arbitrary_seed_only_labeled_arithmetic_fixture(self):
        result=evaluate_dataset([],master_seed='arbitrary',draws=2,mode=TEST_VECTOR)
        self.assertEqual(result['result_kind'],TEST_VECTOR);self.assertEqual(result['empirical_entitlements'],[])
        self.reject(lambda:evaluate_dataset([],master_seed='arbitrary',frozen_config=self.config))

    def test_call_usage_latency_output_and_seed_capture_binding(self):
        events=read_events(self.path);first=next(i for i,e in enumerate(events) if e['kind']=='EPISODE_BEGIN');last=next(i for i,e in enumerate(events) if e['kind']=='EPISODE_RECORD')
        part=events[first:last+1];record=self.trajectory['episodes'][0]
        args=dict(architecture='B0',split=record['evaluator_private']['split'],block_id=self.plan['block_id'],item_index=0)
        verify_calls(part,record['calls'],self.config,**args)
        for field in ('latency_ms','input_tokens','output_tokens','output_sha256'):
            with self.subTest(mutation=field):
                calls=cp(record['calls']);calls[0][field]='a'*64 if field.endswith('sha256') else calls[0][field]+1
                self.reject(lambda:verify_calls(part,calls,self.config,**args))
        changed=cp(part);next(e for e in changed if e['kind']=='CALL_REQUEST')['payload']['call_config']['sampling_seed']+=1
        self.reject(lambda:verify_calls(changed,record['calls'],self.config,**args))
        changed=cp(part);next(e for e in changed if e['kind']=='CALL_RESPONSE')['payload']['raw_hex']='7b7d'
        self.reject(lambda:verify_calls(changed,record['calls'],self.config,**args))

    def test_resume_config_and_reference_identity(self):
        for mutation in ('config_sha256','reference_cells_sha256','calibration_artifact_sha256'):
            with self.subTest(mutation=mutation):
                rows=[dict(kind=e['kind'],payload=cp(e['payload'])) for e in read_events(self.path)]
                rows[0]['payload'][mutation]='c'*64
                path=self.root/(mutation+'.jsonl');chain(path,rows)
                self.reject(lambda:TrajectoryRunner(self.config,self.manifest,self.plan['trajectory_id'],FakeProvider([]),path,reference_cells(self.config,self.plan)))

    def test_prelock_all_settings_immutable_except_materialization(self):
        pre=cp(self.config);pre.update(configuration_status='TEMPLATE',selected_difficulty_tuples=[])
        lock=pre_calibration_lock(pre,self.content)
        self.assertTrue(verify_calibration_lock(lock,self.config,final=True))
        for field in ('master_seed','timeouts','model_configuration','generator_options'):
            with self.subTest(mutation=field):
                modified=cp(self.config)
                if field=='master_seed':modified[field]='different'
                elif field=='timeouts':modified[field]['tool_seconds']+=1
                elif field=='model_configuration':modified[field]['temperature']=.5
                else:modified[field]['symbolic_lengths']=[8]
                self.reject(lambda:verify_calibration_lock(lock,modified,final=True))

    def test_real_search_constructor_needs_lock_not_selected_tuples(self):
        pre=cp(self.config);pre.update(configuration_status='TEMPLATE',selected_difficulty_tuples=[])
        lock=pre_calibration_lock(pre,self.content)
        provider=Mock(kind='UNCONFIGURED_TEST_ADAPTER',identity_sha256=pre['runtime_identity']['provider_adapter']['sha256'])
        tokenizer=Mock(identity_sha256=pre['runtime_identity']['tokenizer']['sha256'])
        engine=CalibrationEngine(pre,provider,lambda *_:None,tokenizer,True,self.content,pre_lock=lock)
        self.assertEqual(engine.config['selected_difficulty_tuples'],[]);provider.invoke.assert_not_called()

    def test_real_runner_rejects_external_cells_and_missing_artifact(self):
        provider=Mock(kind='UNCONFIGURED_TEST_ADAPTER',identity_sha256=self.config['runtime_identity']['provider_adapter']['sha256'])
        tokenizer=Mock(identity_sha256=self.config['runtime_identity']['tokenizer']['sha256'])
        with tempfile.TemporaryDirectory() as td:
            for cells in (reference_cells(self.config,self.plan),None):
                with self.subTest(external_cells=cells is not None),self.assertRaises(Failure) as caught:
                    TrajectoryRunner(self.config,self.manifest,self.plan['trajectory_id'],provider,Path(td)/'forbidden.jsonl',cells,
                        tokenizer=tokenizer,enable_real_provider=True,content=self.content)
                self.assertIn(caught.exception.code,{'EXTERNAL_REAL_REFERENCE_CELLS_FORBIDDEN','SEALED_CALIBRATION_ARTIFACT_REQUIRED'})
            provider.invoke.assert_not_called();self.assertFalse((Path(td)/'forbidden.jsonl').exists())

    def test_failed_confirm_terminal_no_search_retry(self):
        pre=cp(self.config);pre.update(configuration_status='TEMPLATE',selected_difficulty_tuples=[])
        count={'search':0,'confirm':0}
        def measured(engine,items,arch,phase,block):
            if phase=='SEARCH':
                count['search']+=1
                return dict(n=40,successes=36 if int(block.split(':')[1])%2==0 else 25)
            count['confirm']+=1;return dict(n=200,successes=0)
        with tempfile.TemporaryDirectory() as td,EventStore(Path(td)/'events.jsonl') as store:
            with patch('mrab_r1.calibration.calibration_items',return_value=[]),patch.object(CalibrationEngine,'measure_cell',measured):
                with self.assertRaises(Failure) as caught:search_and_confirm(pre,lambda _:FakeProvider([]),store,offline_fixture=True,content=self.content)
                self.assertEqual(caught.exception.kind,'CALIBRATION_NOT_FEASIBLE')
                self.assertEqual(count,dict(search=20,confirm=20))
                self.assertEqual(store.events[-1]['kind'],'CALIBRATION_TERMINAL_FAILURE')
                failed=next(e['payload'] for e in store.events if e['kind']=='CALIBRATION_ARTIFACT_SEAL')
                self.assertEqual(failed['payload']['gate_status'],'CALIBRATION_NOT_FEASIBLE')
                self.assertEqual(len(failed['payload']['confirmation_cells']),20)
                with self.assertRaises(Failure):search_and_confirm(pre,lambda _:FakeProvider([]),store,offline_fixture=True,content=self.content)
                self.assertEqual(count,dict(search=20,confirm=20))

    def test_cli_requires_scientific_inputs(self):
        path=self.root/'input.json';path.write_text('[]',encoding='utf8')
        run=subprocess.run([sys.executable,'-B','-m','mrab_r1','evaluate',str(path)],capture_output=True,text=True)
        self.assertEqual(run.returncode,2);self.assertEqual(json.loads(run.stdout)['type'],'INFRA_FAILURE')

    def test_offline_cli_and_replay_pass_actual_frozen_config(self):
        from mrab_r1.__main__ import main
        from mrab_r1.replay import replay_trajectory
        # Isolate orchestration from episode arithmetic (covered by original runner
        # tests). The invariant function still runs against the actual full config.
        with patch('mrab_r1.__main__.read',side_effect=lambda p: {'config':self.config,'manifest':self.manifest,'cells':self.trajectory['calibration_cells'],'script':[]}[p]), \
             patch('mrab_r1.runner.TrajectoryRunner') as runner,patch('mrab_r1.__main__.output') as output, \
             patch.object(sys,'argv',['mrab_r1','run-trajectory','config','manifest','--trajectory-id',self.plan['trajectory_id'],'--reference-cells','cells','--events','unused','--offline-script','script']):
            runner.return_value.run.return_value=cp(self.trajectory);runner.return_value.store.events=[]
            self.assertEqual(main(),0)
            self.assertEqual(output.call_args.args[0]['invariants']['status'],'PASS')
        with tempfile.TemporaryDirectory() as td,patch('mrab_r1.replay.TrajectoryRunner') as runner:
            runner.return_value.run.return_value=cp(self.trajectory)
            result=replay_trajectory(self.config,self.manifest,self.plan['trajectory_id'],[],Path(td)/'new.jsonl',self.trajectory['calibration_cells'])
            self.assertEqual(result['invariants']['status'],'PASS');self.assertEqual(result['result_kind'],TEST_VECTOR)

    def test_batch_jcs_matches_single_number_and_unicode_vectors(self):
        values=[{'number':1e-7,'other':1e20,'text':'Матрёшка'},[None,True,False,0,-0.0],{'\U0001f600':1,'\ue000':2},{}]
        self.assertEqual(canonical_many(values),[canonical(v) for v in values])


class SealedIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.config,cls.content,cls.tuples,cls.artifact,cls.cal_path=calibration_fixture(cls.root)
        cls.manifest=build_manifest(cls.config,cls.tuples,content=cls.content)
        cls.plan=next(t for t in cls.manifest['payload']['trajectories'] if t['architecture']=='B3' and t['condition']=='C1')
        cls.path=cls.root/'run.jsonl'
        cls.trajectory=TrajectoryRunner(cls.config,cls.manifest,cls.plan['trajectory_id'],FakeProvider(scripts(cls.manifest,cls.plan,'VERIFY')),cls.path,
            calibration_artifact=cls.artifact,calibration_events=cls.cal_path).run(2)
        cls.artifact_evidence=dict(result_kind=TEST_VECTOR,config_sha256=semantic_sha(cls.config),calibration_artifact_sha256=cls.artifact['sha256'],
            calibration_event_log_sha256=raw_sha(cls.cal_path.read_bytes()),confirmation_cells=20,confirmation_measurements=4000,search_measurements=800,
            construction='SYNTHETIC_CAPTURE_RECORDS_NO_PROVIDER_INVOCATIONS',real_provider_calls=0)
        cls.kw=dict(planned_manifest=cls.manifest,frozen_config=cls.config,event_logs={cls.plan['trajectory_id']:cls.path},calibration_artifact=cls.artifact,calibration_events=cls.cal_path,mode=TEST_VECTOR)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def reject(self,call):
        with self.assertRaises(Failure) as caught:call()
        self.assertEqual(caught.exception.kind,'INFRA_FAILURE');return caught.exception.code

    def test_full_sealed_fixture_bundle_round_trip(self):
        report=verify_artifact(self.artifact,self.config,self.cal_path,scientific=False)
        self.assertEqual(report['status'],'PASS')
        bundle=collect_run_bundle([self.trajectory],self.kw['event_logs'],self.manifest,self.config,self.artifact,self.cal_path,scientific=False)
        from mrab_r1.seed import Stream
        with patch('mrab_r1.evaluator.Stream',wraps=Stream) as streams:
            result=evaluate_dataset(bundle,tool_durations=bundle['payload']['tool_durations'],**self.kw)
            self.assertTrue(streams.called)
            self.assertTrue(all(c.args[0]==self.config['master_seed'] and c.args[3]=='BOOTSTRAP' for c in streams.call_args_list))
        self.assertEqual(result['validated_bundle_sha256'],bundle['sha256'])
        self.assertEqual(result['bootstrap_provenance']['master_seed'],self.config['master_seed'])
        self.assertEqual(result['bootstrap_provenance']['domain'],'BOOTSTRAP')
        self.assertEqual(result['result_kind'],TEST_VECTOR)
        self.assertEqual(len(self.artifact['payload']['confirmation_cells']),20)
        expected_latency=sum(c['latency_ms'] for e in self.trajectory['episodes'] for c in e['calls'])+sum(bundle['payload']['tool_durations'][self.plan['trajectory_id']].values())
        self.assertEqual(result['trajectory_reports'][0]['resources']['LATENCY_MS']['value'],expected_latency)

    def test_calibration_success_and_dataset_mutations(self):
        for field,value in [('successes',181),('dataset_hash','a'*64),('n',199),('architecture','B1')]:
            with self.subTest(mutation=field):
                a=cp(self.artifact);a['payload']['confirmation_cells'][0][field]=value;a['sha256']=semantic_sha(a['payload'])
                self.reject(lambda:verify_artifact(a,self.config,self.cal_path,scientific=False))

    def test_reference_cells_uniqueness_scope_modes_and_tuple(self):
        for field,value in [('band','MID'),('tuple_sha256','b'*64),('scope',{})]:
            with self.subTest(mutation=field):
                a=cp(self.artifact);a['payload']['confirmation_cells'][0][field]=value;a['sha256']=semantic_sha(a['payload'])
                with self.assertRaises(Failure):materialize_reference_cells(a,self.config,self.plan)
        cells=materialize_reference_cells(self.artifact,self.config,self.plan)
        self.assertEqual(cells,self.trajectory['calibration_cells'])
        for field,value in [('successes',181),('dataset_hash','b'*64)]:
            t=cp(self.trajectory);t['calibration_cells'][0][field]=value
            self.reject(lambda:evaluate_dataset([t],**self.kw))

    def test_no_metrics_after_invariant_failure(self):
        t=cp(self.trajectory);t['block_id']='changed'
        with patch('mrab_r1.evaluator.evaluate_trajectory') as metric:
            self.reject(lambda:evaluate_dataset([t],**self.kw));metric.assert_not_called()

    def test_loose_usage_resource_sidecar_and_arbitrary_seed(self):
        for field in ('latency_ms','input_tokens','output_tokens'):
            with self.subTest(mutation=field):
                t=cp(self.trajectory);t['episodes'][0]['calls'][0][field]+=99
                self.reject(lambda:evaluate_dataset([t],**self.kw))
        self.assertEqual(self.reject(lambda:evaluate_dataset([self.trajectory],tool_durations={},**self.kw)),'UNBOUND_RESOURCE_SIDECAR')
        self.assertEqual(self.reject(lambda:evaluate_dataset([self.trajectory],master_seed='override',**self.kw)),'ARBITRARY_SCIENTIFIC_BOOTSTRAP_SEED_FORBIDDEN')

    def test_scripted_artifact_cannot_be_scientific(self):
        kwargs=dict(self.kw,mode='SCIENTIFIC')
        self.reject(lambda:evaluate_dataset([self.trajectory],**kwargs))

    def test_event_chain_tamper_is_not_a_metric(self):
        data=self.path.read_bytes();path=self.root/'tampered.jsonl'
        rows=data.splitlines();row=json.loads(rows[0]);row['payload']['config_sha256']='d'*64
        rows[0]=json.dumps(row).encode();path.write_bytes(b'\n'.join(rows)+b'\n')
        kwargs=dict(self.kw,event_logs={self.plan['trajectory_id']:path})
        self.reject(lambda:evaluate_dataset([self.trajectory],**kwargs))


if __name__=='__main__':unittest.main()
