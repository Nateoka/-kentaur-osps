"""Verify sealed archive/sidecars then run ONLY read-only verifier in new process.

Never regenerates checked artifacts, never runs models or production runtime.
"""
import argparse,hashlib,json,zipfile,subprocess,sys
from pathlib import Path
def sha(b):return hashlib.sha256(b).hexdigest()
def main(a):
    archive=a.archive.resolve();manifest_path=a.manifest.resolve();checksum=a.checksum.resolve()
    dest=a.extract_to.resolve();output=a.output.resolve();final=a.final_report.resolve()
    if any(p.exists() for p in [dest,output,final]):raise FileExistsError('Fresh extraction/output/final report required; no overwrite')
    if dest==output or dest in output.parents or output in dest.parents or dest in final.parents:raise ValueError('Separate extraction and verification outputs required')
    raw=archive.read_bytes();before=sha(raw);manifest=json.loads(manifest_path.read_bytes())
    checksum_words=checksum.read_text(encoding='ascii').strip().split(maxsplit=1)
    assert checksum_words==[before,archive.name], 'External SHA256 mismatch'
    assert manifest['archive_sha256']==before and manifest['bytes']==len(raw)
    expected={r['path']:r for r in manifest['files']};assert len(expected)==len(manifest['files'])
    dest.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(expected)
        for name in z.namelist():
            prefix,rel=name.split('/',1);assert prefix=='mrab_r1_engineering_design_0.2.1'
            target=(dest/rel).resolve()
            if dest not in target.parents:raise ValueError('Unsafe archive member')
            content=z.read(name);assert sha(content)==expected[name]['sha256'] and len(content)==expected[name]['bytes']
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(content)
    command=[sys.executable,'-B','-X','utf8',str(dest/'design_tools/verify_design.py'),'--package',str(dest),'--output',str(output)]
    if a.dependencies:command+=['--dependencies',str(a.dependencies.resolve())]
    run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8')
    print(run.stdout);print(run.stderr)
    report=json.loads((output/'MRAB_R1_ENGINEERING_DESIGN_CHECK_0.2.1.json').read_bytes())
    report['artifact']='MRAB_R1_FINAL_VERIFICATION_0.2.1'
    report['release_integrity']=dict(archive=archive.name,sha256_before=before,sha256_after=sha(archive.read_bytes()),
        external_sha256_matches=True,external_manifest_matches=True,all_member_hashes_match=True,crc='PASS',fresh_extraction=True,fresh_process_exit=run.returncode,members=len(expected))
    assert report['release_integrity']['sha256_after']==before
    assert report['verification_stage']=='SEALED_FRESH_EXTRACTION'
    groups={'redundancy_goldens':'E07:RED21-','probe_goldens':'PROBE21:','prep_paths':'PREP21:','b4_policy_checks':'B4-21:','closure_checks':'CLOSURE21:'}
    report['feature_results']={name:dict(pass_count=sum(c['status']=='PASS' for c in report['checks'] if c['id'].startswith(prefix)),
        fail_count=sum(c['status']=='FAIL' for c in report['checks'] if c['id'].startswith(prefix)),checks=[c for c in report['checks'] if c['id'].startswith(prefix)]) for name,prefix in groups.items()}
    report['count_definition']='executed_pass/failed are read-only design checks; release_integrity is separate archive envelope validation, not an invented additional PASS count.'
    final.parent.mkdir(parents=True,exist_ok=True)
    with final.open('xb') as f:f.write((json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    print(json.dumps(dict(final_report=final.name,readiness=report['readiness'],executed_pass=report['executed_pass'],executed_fail=report['executed_fail'],model_calls=report['model_calls'],archive_sha256=before)))
    return run.returncode
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['archive','manifest','checksum','extract-to','output','final-report']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--dependencies',type=Path);sys.exit(main(p.parse_args()))
