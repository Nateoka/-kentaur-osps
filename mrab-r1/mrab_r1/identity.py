"""Bind frozen hashes to the implementation actually loaded, not arbitrary blobs."""
import os
from pathlib import Path
import shutil
from .canonical import canonical,raw_sha
from .errors import Failure
from .prompts import Prompts,COMMIT_RULES,PROBE_RULES
from .schemas import Schemas,DESIGN
from . import RUNTIME_VERSION


def component_content():
    root=Path(__file__).resolve().parent;prompts=Prompts();registry=Schemas()
    node=os.environ.get("MRAB_JCS_NODE") or shutil.which("node")
    if not node:raise Failure("CONFIGURATION_FAILURE","ECMASCRIPT_CANONICALIZER_UNAVAILABLE")
    files={p.name:raw_sha(p.read_bytes()) for p in root.glob("*.py")}
    files["jcs.cjs"]=raw_sha((root/"jcs.cjs").read_bytes())
    def bundle(kind,extra=None):return canonical(dict(kind=kind,version=RUNTIME_VERSION,files=files,extra=extra))
    content=dict(canonicalizer=bundle("JCS",dict(ecmascript_binary_sha256=raw_sha(Path(node).read_bytes()))),
        parser=bundle("STRICT_JSON_AND_STRUCTURAL_REPAIR"),symbolic_tool=bundle("F1_EXACT_TOOL"),grid_tool=bundle("F2_EXACT_TOOL"),
        output_schema_bundle=canonical(dict(source=registry.source_docs,effective=registry.docs,patches=registry.applied_patches)),
        prompt_bundle=bundle("P01_P07",dict(contract=raw_sha((DESIGN/"MRAB_R1_PROMPT_CONTRACTS_0.2.1.md").read_bytes()))))
    architectures=dict(B0=prompts.action,B1=prompts.b1,B2=prompts.b2+"\n"+COMMIT_RULES,
        B3=prompts.b3+"\n"+COMMIT_RULES+"\n"+PROBE_RULES,B4=prompts.b4)
    prompt_bytes=dict(system_prompt_sha256=(prompts.system+"\n"+prompts.supplement).encode("utf-8"),action_prompt_sha256=prompts.action.encode("utf-8"),
        architecture_prompt_sha256={a:s.encode("utf-8") for a,s in architectures.items()})
    return content,prompt_bytes


def verify_frozen_implementation(config,provider=None,tokenizer=None):
    components,prompts=component_content()
    for name,raw in components.items():
        if config["runtime_identity"][name]["sha256"]!=raw_sha(raw):
            raise Failure("CONFIGURATION_FAILURE","LOADED_RUNTIME_IDENTITY_MISMATCH","/runtime_identity/"+name)
    for name,value in prompts.items():
        expected={a:raw_sha(raw) for a,raw in value.items()} if isinstance(value,dict) else raw_sha(value)
        if config["model_configuration"][name]!=expected:raise Failure("CONFIGURATION_FAILURE","LOADED_PROMPT_HASH_MISMATCH","/model_configuration/"+name)
    for name,implementation in (("provider_adapter",provider),("tokenizer",tokenizer)):
        if implementation is not None and getattr(implementation,"identity_sha256",None)!=config["runtime_identity"][name]["sha256"]:
            raise Failure("CONFIGURATION_FAILURE","EXTERNAL_COMPONENT_IDENTITY_MISMATCH","/runtime_identity/"+name)
    return dict(status="PASS",components=list(components))
