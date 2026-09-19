"""P01-P07 exact fenced templates + explicit public-only assembly."""
from copy import deepcopy as cp
import re
from .canonical import canonical, raw_sha
from .errors import Failure
from .schemas import DESIGN, Schemas

COMMIT_RULES = """Use only existing claims and known past episode references. At most one proposal per episode. ACTIVE, REVISED, NARROWED and UNKNOWN may pass through QUESTIONED to ACTIVE, REVISED, NARROWED or UNKNOWN atomically. UNKNOWN has no interval; QUESTIONED restores the last numeric estimate as disputed. REVISED keeps scope; NARROWED takes a strict nonempty subset. ACTIVE restoration requires an addressed known historical version or the last numeric estimate. Configuration and slot identity cannot change. Numerical/scope changes need local independent SOLO or pre-tool VERIFY evidence. A QUESTIONED estimate may cite other standard local feedback. The committer tests admissibility, not the truth of an estimate."""
PROBE_RULES = """Only SOLO_CURRENT, VERIFY_CURRENT or VERIFY_NEXT_MATCHED are available probes. NEXT_MATCHED needs the latest known informative observation with the same public operational key; no extra task is created. Stop reflection does not cancel ACTION or the pending probe. Explicit cancellation precedes replacement. Expiry is after declared episode plus four. Returned observations may restart preparation. Distinct predictions or loci do not establish causal discrimination."""


class Prompts:
    def __init__(self):
        doc = (DESIGN/"MRAB_R1_PROMPT_CONTRACTS_0.2.1.md").read_text(encoding="utf-8")
        fences = re.findall(r"```text\n(.*?)\n```", doc, re.S)
        if len(fences) != 8:
            raise Failure("CONFIGURATION_FAILURE", "PROMPT_TEMPLATE_COUNT_MISMATCH")
        self.system, self.action, self.b1, self.b2, self.b3, self.b4, self.calibration, self.repair = fences
        self.supplement = doc.split("Публичное уточнение к shared instruction:\n",1)[1].strip()
        self.schemas = Schemas()

    def schema_ref(self, phase, architecture):
        return self.schemas.ref("config", "action_record") if phase == "ACTION" else self.schemas.ref("reflexive_record", architecture.lower())

    def request(self, phase, architecture, state, prep_record=None, receipt=None, fixed_action=None, calibration=False):
        if architecture not in {"B0","B1","B2","B3","B4"} or phase not in {"PREP","ACTION"}:
            raise Failure("CONFIGURATION_FAILURE", "UNKNOWN_INVOCATION_INTERFACE")
        if phase == "PREP" and architecture not in {"B1","B2","B3"}:
            raise Failure("PROTOCOL_FAILURE", "PREP_FORBIDDEN")
        state = self.schemas.validate(state, self.schemas.ref("trajectory","agent_state"), "LEAKAGE_FAILURE")
        if receipt is not None and set(receipt) != {"validation_status","rejection_codes","effective_episode"}:
            raise Failure("LEAKAGE_FAILURE", "INVALID_COMMIT_RECEIPT")
        instruction = self.action if phase == "ACTION" else {"B1":self.b1,"B2":self.b2,"B3":self.b3}[architecture]
        if phase == "PREP" and architecture in {"B2","B3"}:
            instruction += "\n"+COMMIT_RULES
        if phase == "PREP" and architecture == "B3":
            instruction += "\n"+PROBE_RULES
        if architecture == "B4":
            if fixed_action not in {"SOLO","VERIFY"}:
                raise Failure("CONFIGURATION_FAILURE", "B4_MODEL_ACTION_NOT_REQUIRED")
            instruction += "\n"+self.b4.replace("{fixed_action}",fixed_action)
        if calibration:
            instruction += "\n"+self.calibration
        result = dict(system=self.system+"\n"+self.supplement, instruction=instruction,
            output_schema=self.schemas.public_bundle(self.schema_ref(phase,architecture)),
            agent_state=state, prep_record=cp(prep_record), commit_receipt=cp(receipt))
        return canonical(result)

    def repair_request(self, invalid_output, errors, ref):
        if any(set(e) != {"code","pointer"} for e in errors):
            raise Failure("LEAKAGE_FAILURE", "UNSAFE_REPAIR_ERRORS")
        return canonical(dict(system=self.repair, invalid_output=invalid_output,
            validation_errors=cp(errors), output_schema=self.schemas.public_bundle(ref)))
