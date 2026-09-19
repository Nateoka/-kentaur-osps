from copy import deepcopy as cp
import unittest
from mrab_r1.config import template,freeze
from mrab_r1.canonical import canonical,raw_sha,loads
from mrab_r1.identity import component_content
from mrab_r1.errors import Failure
from mrab_r1.provider import ProviderResponse


def frozen_fixture():
    """Explicit offline configuration test, not selection of a real provider/model."""
    config=template();config["configuration_status"]="FROZEN";content={}
    components,prompts=component_content()
    def register(raw):
        digest=raw_sha(raw);content[digest]=raw;return digest
    for name,raw in components.items():config["runtime_identity"][name]=dict(identity="test:"+name,sha256=register(raw))
    for name in ("provider_adapter","tokenizer"):
        config["runtime_identity"][name]=dict(identity="test:"+name,sha256=register(("OFFLINE_ONLY_"+name).encode()))
    model=config["model_configuration"];model.update(model_id="OFFLINE_FIXTURE_NOT_A_MODEL",model_revision="TEST_V1")
    for name,value in prompts.items():model[name]={a:register(raw) for a,raw in value.items()} if isinstance(value,dict) else register(value)
    config["compute_settings"].update(reasoning_mode="OFFLINE_FIXTURE",usage_accounting="OUTPUT_INCLUDES_REASONING")
    for family in ("SYMBOLIC_PIPELINE","RULE_GRID"):
        for i,band in enumerate(("HIGH","MID")):
            difficulty=dict(n=3,length=8+4*i) if family=="SYMBOLIC_PIPELINE" else dict(n=3,k=1+i)
            digest=register(canonical(difficulty))
            config["selected_difficulty_tuples"].append(dict(family=family,band=band,scope_id="scope:"+digest[:12],tuple_sha256=digest))
    return config,content


class FreezeTests(unittest.TestCase):
    def test_frozen_actual_content_binding(self):
        config,content=frozen_fixture()
        self.assertEqual(freeze(config,content)["config"],config)
        modified=cp(config);raw=b"unrelated parser";modified["runtime_identity"]["parser"]["sha256"]=raw_sha(raw);content[raw_sha(raw)]=raw
        with self.assertRaises(Failure) as caught:freeze(modified,content)
        self.assertEqual(caught.exception.code,"LOADED_RUNTIME_IDENTITY_MISMATCH")

    def test_F18_reserved_and_protocol_tuning_rejected(self):
        config,content=frozen_fixture()
        for name,value in [("architectures",["B0","B1","B2","B3","B4","B5"]),("profile_conditions",["C0","C1","C2","C3","C4"])]:
            modified=cp(config);modified[name]=value
            with self.assertRaises(Failure):freeze(modified,content)
        config["policy"]["solo_threshold"]=.7
        with self.assertRaises(Failure):freeze(config,content)

    def test_unrepresentable_float_and_bad_observed_usage_rejected(self):
        with self.assertRaises(Failure):loads('{"x":1e-9999}')
        self.assertEqual(loads('{"x":-0.0}')["x"],0)
        with self.assertRaises(Failure):ProviderResponse(b"{}","x","0","1",input_tokens=-1)


if __name__=="__main__":unittest.main()
