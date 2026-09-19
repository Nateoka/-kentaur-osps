"""Executed test evidence, separate from release-completeness entitlement."""
import io
import os
import sys
from copy import deepcopy
from pathlib import Path
import socket
import time
import unittest
from unittest.mock import patch
import zipfile
from . import READINESS,DESIGN_SHA256,RUNTIME_VERSION,PROTOCOL_REVISION
from .canonical import raw_sha
from .schemas import DESIGN
from .errors import Failure


def verify_design(archive):
    archive=Path(archive)
    if raw_sha(archive.read_bytes())!=DESIGN_SHA256:raise Failure("CONFIGURATION_FAILURE","DESIGN_ZIP_HASH_MISMATCH")
    checked=[]
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            if entry.is_dir():continue
            name=Path(entry.filename)
            relative=Path(*name.parts[1:]) if name.parts[0]==DESIGN.name else name
            target=DESIGN/relative
            if not target.is_file() or target.read_bytes()!=source.read(entry):raise Failure("INFRA_FAILURE","IMMUTABLE_DESIGN_FILE_MISMATCH")
            checked.append(relative.as_posix())
    actual={p.relative_to(DESIGN).as_posix() for p in DESIGN.rglob("*") if p.is_file()}
    if actual!=set(checked):raise Failure("INFRA_FAILURE","IMMUTABLE_DESIGN_FILE_SET_MISMATCH")
    return dict(status="PASS",design_sha256=DESIGN_SHA256,files=len(checked),source_unchanged=True,
        runtime_corrections=["R1-E07-HARM-01","R1-STORAGE-REQUEST-01"])


class EvidenceResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.executed=[];self.started={}
    def startTest(self,test):
        self.started[test.id()]=time.perf_counter()
        if os.environ.get("MRAB_TEST_PROGRESS")=="1":print("[runtime test] "+test.id(),file=sys.stderr,flush=True)
        super().startTest(test)
    def note(self,test,status):
        row=dict(test_id=test.id(),status=status,seconds=round(time.perf_counter()-self.started.get(test.id(),time.perf_counter()),6))
        if hasattr(test,"artifact_evidence"):row["artifact_evidence"]=deepcopy(test.artifact_evidence)
        self.executed.append(row)
    def addSuccess(self,test):self.note(test,"PASS");super().addSuccess(test)
    def addError(self,test,err):self.note(test,"ERROR");super().addError(test,err)
    def addFailure(self,test,err):self.note(test,"FAIL");super().addFailure(test,err)
    def addSkip(self,test,reason):self.note(test,"SKIP");super().addSkip(test,reason)
    def addSubTest(self,test,subtest,err):
        self.executed.append(dict(test_id=subtest.id(),status="PASS" if err is None else "FAIL",subtest=True))
        super().addSubTest(test,subtest,err)


def verify_runtime(manifest_plans=False):
    root=Path(__file__).resolve().parents[1]
    output=io.StringIO();network_attempts=[]
    def deny(*args,**kwargs):
        network_attempts.append("BLOCKED")
        raise Failure("INFRA_FAILURE","NETWORK_FORBIDDEN_IN_VERIFICATION")
    suite=unittest.defaultTestLoader.discover(str(root/"tests"),top_level_dir=str(root))
    with patch.object(socket.socket,"connect",deny),patch.object(socket,"create_connection",deny):
        result=unittest.TextTestRunner(stream=output,verbosity=2,resultclass=EvidenceResult).run(suite)
        plans=[]
        if manifest_plans:
            from .config import template
            from .manifest import build_manifest,verify_manifest,FAMILIES
            config=template();tuples={(f,b):dict(n=3,length=8) if f==FAMILIES[0] else dict(n=4,k=2) for f in FAMILIES for b in ("HIGH","MID")}
            for run in ("SMOKE","PILOT"):
                manifest=build_manifest(config,tuples,planned_run=run,offline_fixture=True)
                plans.append(dict(planned_run=run,**verify_manifest(manifest,config)))
    report=dict(status="PASS" if result.wasSuccessful() and not network_attempts else "FAIL",readiness=READINESS,
        runtime_version=RUNTIME_VERSION,protocol_revision=PROTOCOL_REVISION,tests_run=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),executed=result.executed,
        output=output.getvalue(),plans=plans,real_model_calls=0,real_calibration_calls=0,real_smoke_calls=0,real_pilot_calls=0,
        verification_network_attempts=len(network_attempts),verification_network_calls_completed=0,
        development_external_documentation_lookups=0,
        note="Test PASS is not a release verdict; invariant/fixture coverage and fresh archive verification are separate gates.")
    from .coverage import coverage_report
    report["coverage"]=coverage_report(report)
    if report["coverage"]["status"]!="PASS":report["status"]="FAIL"
    return report
