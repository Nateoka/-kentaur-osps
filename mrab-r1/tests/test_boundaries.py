from copy import deepcopy as cp
import subprocess
import unittest
from unittest.mock import patch
from mrab_r1.schemas import Schemas,BASE
from mrab_r1.prompts import Prompts
from mrab_r1.errors import Failure
from mrab_r1.tool_dispatch import execute_sealed_tool
from mrab_r1.generator_options import resolve_options
from mrab_r1.config import template
from tools.check_request_capacity import witness


class BoundaryTests(unittest.TestCase):
    def test_private_schema_error_receipt_history_probe_canaries(self):
        prompts=Prompts();state=witness()["state"]
        baseline=prompts.request("ACTION","B0",state)
        schema=prompts.schemas.docs[prompts.schemas.ref("config")]
        schema["$defs"]["profile_condition"]["enum"]=["CANARY_HIDDEN_SCHEMA"]
        self.assertEqual(prompts.request("ACTION","B0",state),baseline)
        for field in ("hidden_id","private_label","hidden_history","private_probe"):
            changed=cp(state);changed[field]="CANARY_HIDDEN_VALUE"
            with self.assertRaises(Failure) as caught:prompts.request("ACTION","B0",changed)
            self.assertNotIn("CANARY_HIDDEN_VALUE",str(caught.exception.as_dict()))
        receipt=dict(validation_status="REJECTED",rejection_codes=[],effective_episode=32,private_receipt="CANARY_HIDDEN")
        with self.assertRaises(Failure):prompts.request("ACTION","B0",state,receipt=receipt)
        with self.assertRaises(Failure):prompts.repair_request("{}",[dict(code="SCHEMA_TYPE",pointer="",hidden_error="CANARY_HIDDEN")],prompts.schema_ref("ACTION","B0"))
        self.assertEqual(prompts.repair_request("{}",[dict(code="SCHEMA_TYPE",pointer="")],prompts.schema_ref("ACTION","B0")),prompts.repair_request("{}",[dict(code="SCHEMA_TYPE",pointer="")],prompts.schema_ref("ACTION","B0")))

    def test_enforced_tool_timeout_typed_and_no_retry(self):
        spec=dict(family="SYMBOLIC_PIPELINE",initial=[1,2],operations=[dict(op="ADD",index=0,value=1)])
        with patch("mrab_r1.tool_dispatch.subprocess.run",side_effect=subprocess.TimeoutExpired("tool",30)) as invoke:
            with self.assertRaises(Failure) as caught:execute_sealed_tool(spec,30)
            self.assertEqual(caught.exception.code,"TOOL_DEADLINE_EXCEEDED")
            self.assertEqual(invoke.call_count,1)

    def test_frozen_generator_weights_not_ignored(self):
        config=template();config["generator_options"]["operation_weights"]["ADD"]=7
        resolved=resolve_options(config,"SYMBOLIC_PIPELINE",dict(n=3,length=8))
        self.assertEqual(resolved["weights"]["ADD"],7)
        with self.assertRaises(Failure):resolve_options(config,"SYMBOLIC_PIPELINE",dict(n=3,length=8,weights={"ADD":1}))


if __name__=="__main__":unittest.main()
