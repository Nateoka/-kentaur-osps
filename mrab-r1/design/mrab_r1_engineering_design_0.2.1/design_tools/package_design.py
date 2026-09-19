"""Seal an existing design package, no test regeneration or model execution."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def digest(data):return hashlib.sha256(data).hexdigest()
def data(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
def main(root,archive):
    root=root.resolve();archive=archive.resolve()
    if root==archive or root in archive.parents:raise ValueError('Archive must be outside package')
    manifest=archive.with_suffix('.manifest.json');checksum=Path(str(archive)+'.sha256')
    if any(p.exists() for p in [archive,manifest,checksum,root/'CONTENT_MANIFEST.json']):raise FileExistsError('Refuse to overwrite a sealed release')
    report=json.loads((root/'MRAB_R1_ENGINEERING_DESIGN_CHECK_0.2.1.json').read_bytes())
    if report['executed_fail']:raise ValueError('Technical failures forbid sealing')
    # Verify all hashes from pre-seal checks before adding report/capture envelope.
    for name,h in report['input_hashes'].items():
        if digest((root/name).read_bytes())!=h:raise ValueError('Changed after pre-seal verification: '+name)
    entries=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        if '__pycache__' in p.parts:raise ValueError('Unexpected bytecode in release')
        raw=p.read_bytes();entries.append(dict(path=p.relative_to(root).as_posix(),bytes=len(raw),sha256=digest(raw)))
    content=dict(artifact='MRAB_R1_CONTENT_MANIFEST_0.2.1',package_version='0.2.1',protocol_revision='R1_0.1_DESIGN_PATCH_0.2.1',
        readiness=report['readiness'],files=entries,excludes=['CONTENT_MANIFEST.json (self-reference)'],canonical_sources_modified=False,model_calls=0)
    (root/'CONTENT_MANIFEST.json').write_bytes(data(content))
    prefix=root.name+'/'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file():
                info=zipfile.ZipInfo(prefix+p.relative_to(root).as_posix(),date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16
                z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise ValueError('Archive CRC failure')
        files=[dict(path=i.filename,bytes=i.file_size,sha256=digest(z.read(i))) for i in z.infolist()]
    h=digest(archive.read_bytes())
    manifest.write_bytes(data(dict(artifact='MRAB_R1_RELEASE_MANIFEST_0.2.1',archive=archive.name,archive_sha256=h,bytes=archive.stat().st_size,
        readiness=report['readiness'],files=files,preseal_pass=report['executed_pass'],preseal_fail=report['executed_fail'],
        final_verification='Run read-only verifier from fresh extraction; report is outside ZIP to avoid self-hash cycle.',benchmark_runs=0)))
    checksum.write_bytes((h+'  '+archive.name+'\n').encode('ascii'))
    print(json.dumps(dict(archive=archive.name,sha256=h,files=len(files),bytes=archive.stat().st_size,readiness=report['readiness'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);a=p.parse_args();main(a.package,a.archive)
