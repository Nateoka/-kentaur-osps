"""Recover exact unchanged wheels from the local pip cache, without networking."""
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def normalized(name):return re.sub(r"[-_.]+","-",name).lower()


def collect(cache):
    requested={}
    for line in (ROOT/"requirements.lock").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name,version=line.split()[0].split("==");requested[normalized(name)]=version
    found={};destination=ROOT/"wheelhouse";destination.mkdir(exist_ok=True)
    for candidate in Path(cache).rglob("*.body"):
        with candidate.open("rb") as stream:
            if stream.read(4)!=b"PK\x03\x04":continue
        try:
            with zipfile.ZipFile(candidate) as archive:
                metadata_names=[n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
                if len(metadata_names)!=1:continue
                folder=metadata_names[0].rsplit("/",1)[0]
                metadata=BytesParser().parsebytes(archive.read(metadata_names[0]));name=normalized(metadata["Name"]);version=metadata["Version"]
                if requested.get(name)!=version:continue
                wheel=BytesParser().parsebytes(archive.read(folder+"/WHEEL"));tags=wheel.get_all("Tag",[])
                compatible=next((tag for tag in tags if tag in {"py3-none-any","py2.py3-none-any","cp312-cp312-win_amd64"}),None)
                if compatible is None:continue
                filename=name.replace("-","_")+"-"+version+"-"+compatible+".whl"
                raw=candidate.read_bytes();digest=hashlib.sha256(raw).hexdigest();target=destination/filename
                if target.exists() and target.read_bytes()!=raw:raise RuntimeError("Conflicting cached wheel")
                if not target.exists():shutil.copyfile(candidate,target)
                found[name]=dict(version=version,file=filename,sha256=digest,tag=compatible,bytes=len(raw))
        except zipfile.BadZipFile:continue
    missing=set(requested)-set(found)
    if missing:raise RuntimeError("Missing cached wheels: "+", ".join(sorted(missing)))
    (ROOT/"requirements.offline.lock").write_text("# Generated from exact cached wheel bytes; Python 3.12 Windows x64.\n"+"".join(f"{name}=={r['version']} --hash=sha256:{r['sha256']}\n" for name,r in sorted(found.items())),encoding="utf-8")
    (destination/"WHEEL_MANIFEST.json").write_text(json.dumps(found,indent=2)+"\n",encoding="utf-8")
    return dict(status="PASS",wheels=len(found),network_calls=0,bytes=sum(r["bytes"] for r in found.values()))


if __name__=="__main__":print(json.dumps(collect(sys.argv[1])))
