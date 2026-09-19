"""Mechanical changed-file inventory against immutable parent0.2."""
import argparse,zipfile,json,hashlib
from pathlib import Path
NAME='CHANGED_FILES_0.2_TO_0.2.1.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def main(root):
    root=root.resolve()
    parent=root/'references/MRAB_R1_Engineering_Design_Package_0.2.zip'
    with zipfile.ZipFile(parent) as z:old={n.split('/',1)[1]:z.read(n) for n in z.namelist()}
    actual={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and p.name not in {NAME,'CONTENT_MANIFEST.json'} and '__pycache__' not in p.parts}
    entries=[];used=set();unchanged=[]
    for name,raw in sorted(actual.items()):
        prior=name if name in old else name.replace('_0.2.1.','_0.2.')
        if prior not in old:prior=None
        if prior:used.add(prior)
        if prior==name and old[prior]==raw:unchanged.append(name);continue
        entries.append(dict(path=name,previous_path=prior,change='ADDED' if prior is None else 'RENAMED_AND_MODIFIED' if prior!=name and old[prior]!=raw else 'RENAMED' if prior!=name else 'MODIFIED',
            old_sha256=sha(old[prior]) if prior else None,new_sha256=sha(raw)))
    used.add('CONTENT_MANIFEST.json')
    entries.extend([dict(path=NAME,previous_path=None,change='ADDED',old_sha256=None,new_sha256=None,hash_resolution='External release manifest; avoid self-hash'),
        dict(path='CONTENT_MANIFEST.json',previous_path='CONTENT_MANIFEST.json',change='REGENERATED_RELEASE_METADATA',old_sha256=sha(old['CONTENT_MANIFEST.json']),new_sha256=None,hash_resolution='Generated after inventory; external release manifest')])
    for name in sorted(set(old)-used):entries.append(dict(path=None,previous_path=name,change='REMOVED_FROM_ACTIVE_RELEASE',old_sha256=sha(old[name]),new_sha256=None,
        preserved_in='references/MRAB_R1_Engineering_Design_Package_0.2.zip'))
    out=dict(artifact='MRAB_R1_CHANGED_FILES_0.2_TO_0.2.1',parent_zip_sha256=sha(parent.read_bytes()),entries=entries,unchanged_files=unchanged,
        release_sidecars=['MRAB_R1_Engineering_Design_Package_0.2.1.zip','MRAB_R1_Engineering_Design_Package_0.2.1.manifest.json','MRAB_R1_Engineering_Design_Package_0.2.1.zip.sha256','MRAB_R1_FINAL_VERIFICATION_0.2.1.json'])
    (root/NAME).write_bytes((json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(changed_entries=len(entries),unchanged_files=len(unchanged))))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);main(p.parse_args().package)
