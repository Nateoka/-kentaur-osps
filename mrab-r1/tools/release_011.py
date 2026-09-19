"""Hermetic 0.1.1 release and external fresh-extraction attestation. No network."""
import argparse,ast,hashlib,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];PARENT=ROOT.parent
sys.path.insert(0,str(ROOT))
from mrab_r1.canonical import raw_sha,loads
from mrab_r1.verification import verify_design

NAME='MRAB_R1_Runtime_0.1.1'
BASELINE_SHA='8646dec2a5353d94036d32880862adf47de27d3959a623d45efdce400e9b1199'


def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')


def baseline(report):
    archive=PARENT/'MRAB_R1_Runtime_0.1.zip'
    assert raw_sha(archive.read_bytes())==BASELINE_SHA
    with zipfile.ZipFile(archive) as source:
        old=loads(source.read('mrab_r1_runtime/MRAB_R1_RUNTIME_VERIFICATION_0.1.json'))
        tests=[n for n in source.namelist() if n.startswith('mrab_r1_runtime/tests/') and n.endswith('.py')]
        for name in tests:assert source.read(name)==(ROOT/Path(name).relative_to('mrab_r1_runtime')).read_bytes(),name
        protected=('classifier.py','b4.py','controller.py','profiles.py','seed.py','tasks.py','state.py','prompts.py')
        for name in protected:assert source.read('mrab_r1_runtime/mrab_r1/'+name)==(ROOT/'mrab_r1'/name).read_bytes(),name
        old_ast=ast.parse(source.read('mrab_r1_runtime/mrab_r1/evaluator.py'))
        new_ast=ast.parse((ROOT/'mrab_r1/evaluator.py').read_bytes())
        def body(tree,name):return ast.dump(ast.Module(body=next(n.body for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),type_ignores=[]),include_attributes=False)
        metric_functions=('evaluate_trajectory','opportunity','resource_totals','reference_distance_verdict','bootstrap_pairs')
        for name in metric_functions:assert body(old_ast,name)==body(new_ast,name),name
        assert body(old_ast,'evaluate_dataset')==body(new_ast,'_evaluate_dataset_unchecked')
    ids={r['test_id'] for r in old['executed'] if not r.get('subtest') and r['status']=='PASS'}
    current={r['test_id'] for r in report['executed'] if not r.get('subtest') and r['status']=='PASS'}
    assert len(ids)==109 and ids<=current
    return dict(archive_sha256=BASELINE_SHA,test_files_byte_identical=True,original_test_methods=109,original_pass=109,added_pass=len(current-ids),
        protected_runtime_files_byte_identical=list(protected),scientific_metric_bodies_ast_identical=[*metric_functions,'evaluate_dataset_arithmetic_body'])


def sanitize(value):
    """Public attestation never carries local absolute installation/user paths."""
    if isinstance(value,dict):return {k:sanitize(v) for k,v in value.items()}
    if isinstance(value,list):return [sanitize(v) for v in value]
    if isinstance(value,str):
        value=value.replace(str(PARENT),'<workspace>').replace(str(PARENT).replace('\\','/'),'<workspace>')
    return value


def release(report_path):
    report=loads(Path(report_path).read_bytes())
    assert report['status']=='PASS' and report['coverage']['status']=='PASS'
    prior=baseline(report)
    design=PARENT/'MRAB_R1_Engineering_Design_Package_0.2.1.zip';design_check=verify_design(design)
    archive=PARENT/(NAME+'.zip')
    if archive.exists():raise RuntimeError('Refusing to overwrite a release archive')
    regressions=[r for r in report['executed'] if r['test_id'].startswith('tests.test_hardening.')]
    regression=dict(status='PASS',kind='DESIGN_TEST_VECTOR_NOT_MODEL_RESULT',baseline=prior,executed=regressions,
        synthetic_confirmation_cells=20,synthetic_measurements=4000,provider_calls_for_synthetic_calibration=0,
        real_model_calls=0,real_search_calls=0,real_confirm_calls=0,real_smoke_calls=0,real_pilot_calls=0)
    dump(ROOT/'MRAB_R1_RUNTIME_REGRESSION_EVIDENCE_0.1.1.json',regression)
    source_report=dict(report,baseline=prior,immutable_design=design_check,readiness='PENDING_FRESH_EXTRACTION',source_release_status='TESTED_CANDIDATE_NOT_EXTERNAL_ATTESTATION')
    dump(ROOT/'MRAB_R1_RUNTIME_VERIFICATION_0.1.1.json',sanitize(source_report))
    files={p.relative_to(ROOT).as_posix():p.read_bytes() for p in ROOT.rglob('*') if p.is_file()
        and '__pycache__' not in p.parts and p.suffix!='.pyc' and not p.name.endswith('.writer.lock')
        and p!=ROOT/'CONTENT_MANIFEST.json'
        and p.name not in {'package_snapshot.py','verify_working_snapshot.py','release_runtime.py'}}
    files['design_package/'+design.name]=design.read_bytes()
    content=dict(artifact=NAME,entries=[dict(path=n,bytes=len(b),sha256=raw_sha(b)) for n,b in sorted(files.items())])
    files['CONTENT_MANIFEST.json']=(json.dumps(content,ensure_ascii=False,indent=2)+'\n').encode()
    (ROOT/'CONTENT_MANIFEST.json').write_bytes(files['CONTENT_MANIFEST.json'])
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo('mrab_r1_runtime/'+name,date_time=(2026,9,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,data)
    digest=raw_sha(archive.read_bytes())
    sidecar=dict(archive=archive.name,sha256=digest,bytes=archive.stat().st_size,content=content,
        internal_manifest_sha256=raw_sha(files['CONTENT_MANIFEST.json']),archive_entry_count=len(files))
    dump(PARENT/(NAME+'.manifest.json'),sidecar)
    (PARENT/(NAME+'.zip.sha256')).write_text(digest+'  '+archive.name+'\n',encoding='ascii')
    print(json.dumps(dict(stage='FRESH_EXTRACTION',sha256=digest,entries=len(files))),flush=True)
    fresh=Path(tempfile.mkdtemp(prefix='q-',dir=PARENT))
    with zipfile.ZipFile(archive) as z:z.extractall(fresh)
    extracted=fresh/'mrab_r1_runtime'
    def check_bytes():
        actual={p.relative_to(extracted).as_posix() for p in extracted.rglob('*') if p.is_file()}
        assert actual==set(files)
        for n,b in files.items():assert (extracted/n).read_bytes()==b,n
    check_bytes()
    environment=fresh/'env';subprocess.run([sys.executable,'-m','venv',str(environment)],check=True)
    python=environment/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    env=dict(os.environ);env.pop('PYTHONPATH',None);env['PIP_NO_INDEX']='1';env['PYTHONDONTWRITEBYTECODE']='1'
    subprocess.run([str(python),'-m','pip','install','--no-index','--find-links',str(extracted/'wheelhouse'),'--require-hashes','-r',str(extracted/'requirements.offline.lock')],env=env,capture_output=True,check=True)
    verify=subprocess.run([str(python),'-B','-m','mrab_r1','verify-design-contract','--zip',str(extracted/'design_package'/design.name)],cwd=extracted,env=env,capture_output=True,check=True)
    assert json.loads(verify.stdout)['files']==65
    independent=fresh/'FRESH_RUNTIME_VERIFICATION.json'
    subprocess.run([str(python),'-B','-X','utf8','-m','mrab_r1','--output',str(independent),'verify-runtime'],cwd=extracted,env=env,check=True)
    checked=loads(independent.read_bytes());assert checked['status']=='PASS'
    assert baseline(checked)==prior
    source_artifacts={r['artifact_evidence']['calibration_artifact_sha256'] for r in report['executed'] if 'artifact_evidence' in r}
    fresh_artifacts={r['artifact_evidence']['calibration_artifact_sha256'] for r in checked['executed'] if 'artifact_evidence' in r}
    assert len(source_artifacts)==1 and source_artifacts==fresh_artifacts
    check_bytes()
    verify=subprocess.run([str(python),'-B','-m','mrab_r1','verify-design-contract','--zip',str(extracted/'design_package'/design.name)],cwd=extracted,env=env,capture_output=True,check=True)
    assert json.loads(verify.stdout)['files']==65
    final=sanitize(dict(checked,baseline=prior,immutable_design=design_check,archive_sha256=digest,archive_bytes=archive.stat().st_size,
        readiness='TECHNICAL_RUNTIME_READY_FOR_PROVIDER_CONFIGURATION',source_release_status='FRESH_EXTRACT_VERIFIED',
        fresh_extraction=dict(status='PASS',evidence_directory=fresh.name,report='FRESH_RUNTIME_VERIFICATION.json',entries=len(files),offline_install='PASS',payload_unchanged=True,tests_run=checked['tests_run']),
        scientific_result='NOT_RUN_NOT_ESTABLISHED',synthetic_capture_artifact_reproducibility='EXACT_HASH_MATCH_SOURCE_AND_FRESH',real_search_calls=0,real_confirm_calls=0,real_smoke_runs=0,real_pilot_runs=0,
        audit_scope='ISOLATED_FRESH_EXTRACTION_OFFLINE_TEST_AND_MUTATION_AUDIT_NOT_EXTERNAL_HUMAN_REVIEW'))
    text=json.dumps(final,ensure_ascii=False)
    assert 'C:\\Users\\' not in text and 'C:/Users/' not in text and 'P`etr' not in text
    dump(PARENT/'MRAB_R1_RUNTIME_VERIFICATION_0.1.1.json',final)
    regression['executed']=[r for r in checked['executed'] if r['test_id'].startswith('tests.test_hardening.')]
    regression.update(archive_sha256=digest,evidence_origin='FRESH_EXTRACTION')
    dump(PARENT/'MRAB_R1_RUNTIME_REGRESSION_EVIDENCE_0.1.1.json',regression)
    for name in ('MRAB_R1_RUNTIME_IMPLEMENTATION_DECISIONS_0.1.1.md','MRAB_R1_RUNTIME_CHANGELOG_0.1.1.md','MRAB_R1_RUNTIME_BOUNDARY_AUDIT_0.1.1.md'):
        target=PARENT/name
        if target.exists():raise RuntimeError('Sidecar already exists: '+name)
        target.write_bytes((ROOT/name).read_bytes())
    print(json.dumps(dict(status=final['readiness'],sha256=digest,tests=checked['tests_run'],baseline=prior)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('report');release(parser.parse_args().report)
