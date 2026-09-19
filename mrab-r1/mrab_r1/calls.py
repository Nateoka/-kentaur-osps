"""One primary call per phase and one structural repair per episode."""
from copy import deepcopy as cp
import json
import re
from .canonical import canonical, loads, raw_sha
from .errors import Failure
from .seed import Stream

RESOURCE_FIELDS = ("input_tokens","output_tokens","reasoning_tokens","cached_tokens","latency_ms","monetary_cost")


def preserve_semantics(raw, repaired):
    """Conservative repair guard. No semantic answer/decision can be invented.

    Extract already present JSON values for every repaired operational field.
    This is comparison only, never an alternative successful parser path.
    """
    if not isinstance(repaired, dict):
        return False
    try:
        original = loads(raw)
    except Failure:
        original = None
    if isinstance(original, dict):
        candidates = [original] + [x for x in original.values() if isinstance(x,dict)]
        return any(all(k == "record_kind" and k not in obj or k in obj and obj[k] == v for k,v in repaired.items()) for obj in candidates)
    decoder = json.JSONDecoder()
    for key,value in repaired.items():
        if key == "record_kind":
            continue  # Schema constant supplies no new operational information.
        matches = list(re.finditer('"'+re.escape(key)+'"\\s*:\\s*',raw))
        found = []
        for match in matches:
            try:
                parsed,end = decoder.raw_decode(raw[match.end():])
                found.append(parsed)
            except ValueError:
                pass
        if len(found) != 1 or found[0] != value:
            return False
    return True


class EpisodeCalls:
    def __init__(self, provider, prompts, config, tokenizer, architecture, episode_id, next_sequence, sink, seed_context=None):
        self.provider, self.prompts, self.config, self.tokenizer = provider,prompts,config,tokenizer
        self.architecture,self.episode_id,self.seq,self.sink=architecture,episode_id,next_sequence,sink
        self.calls, self.primary, self.repaired = [], set(), False
        self.seed_context = seed_context or dict(split="MAIN",block_id=episode_id,item_index=0)

    def _invoke(self, request, phase, repair_of=None):
        budgets=self.config["budgets"]
        if self.tokenizer.count(request)>budgets["max_input_tokens"]:
            raise Failure("CONFIGURATION_FAILURE","CALL_INPUT_OVERFLOW")
        cap=budgets["repair_output_tokens"] if phase=="REPAIR" else budgets["prep_output_tokens"] if phase=="PREP" else budgets["action_output_tokens"]
        call_config=dict(phase=phase,repair_of=repair_of,max_output_tokens=cap,
            timeout_seconds=self.config["timeouts"]["model_call_seconds"],
            temperature=self.config["model_configuration"]["temperature"], top_p=self.config["model_configuration"]["top_p"])
        seed=Stream(self.config["master_seed"],stream="MODEL",architecture=self.architecture,phase=phase,**self.seed_context)
        call_config.update(sampling_seed=seed.randint(0,2**32-1),seed_digest=seed.digest().hex())
        sequence=self.seq(); call_id=f"{self.episode_id}:call:{sequence}"
        self.sink("CALL_REQUEST",dict(call_id=call_id,request_hex=request.hex(),request_sha256=raw_sha(request),call_config=call_config))
        try:
            response=self.provider.invoke(request,call_config)
        except Exception as error:
            # Do not leak provider exception strings, keys or request contents.
            self.sink("CALL_NOT_ACCEPTED",dict(call_id=call_id,error_class=type(error).__name__))
            if isinstance(error,Failure):raise
            raise Failure("INFRA_FAILURE","PROVIDER_ADAPTER_EXCEPTION") from None
        raw=response.raw_bytes
        self.sink("CALL_RESPONSE",dict(call_id=call_id,raw_hex=None if raw is None else raw.hex(),
            provider_request_id=response.provider_request_id,started_at=response.started_at,ended_at=response.ended_at,
            status=response.status,error_classification=response.error_classification,observed_model_revision=response.observed_model_revision,
            resource_observations={k:getattr(response,k) for k in RESOURCE_FIELDS if k!="monetary_cost"}))
        if self.provider.kind not in {"FAKE","REPLAY"} and response.observed_model_revision!=self.config["model_configuration"]["model_revision"]:
            raise Failure("INFRA_FAILURE","MODEL_REVISION_NOT_CONFIRMED")
        try:
            visible=None if raw is None else raw.decode("utf-8","strict")
        except UnicodeError:
            visible=None
        oversized=visible is not None and len(visible)>20000
        row=dict(call_id=call_id,phase=phase,repair_of=repair_of,input_sha256=raw_sha(request),
            output_sha256=None if raw is None else raw_sha(raw),visible_output=None if oversized else visible,
            model_revision=self.config["model_configuration"]["model_revision"],sequence=sequence,request_bytes=request.decode(),
            response_status={"OK":"RETURNED","TIMEOUT":"TIMEOUT","CANCELLED":"CANCELLED","TRANSPORT_FAILURE":"TRANSPORT_FAILURE"}.get(response.status,"TRANSPORT_FAILURE"),
            output_includes_reasoning={"OUTPUT_INCLUDES_REASONING":True,"OUTPUT_EXCLUDES_REASONING":False}.get(self.config["compute_settings"]["usage_accounting"]))
        for key in RESOURCE_FIELDS:
            row[key]=None if key=="monetary_cost" else getattr(response,key)
        row["usage_availability"]={k:"UNAVAILABLE" if row[k] is None else "OBSERVED" for k in RESOURCE_FIELDS}
        row["usage_reason"]={k:"PROVIDER_UNAVAILABLE_OR_PRICE_UNCONFIGURED" if row[k] is None else "" for k in RESOURCE_FIELDS}
        self.prompts.schemas.validate(row,self.prompts.schemas.ref("episode_record","call_usage"),"INFRA_FAILURE")
        self.calls.append(row);self.sink("CALL_USAGE",row)
        if response.error_classification=="INFRA_FAILURE" or response.status=="TRANSPORT_FAILURE":
            raise Failure("INFRA_FAILURE","PROVIDER_TRANSPORT_FAILURE")
        if raw is None or visible is None or oversized or response.status!="OK":
            raise Failure("PROTOCOL_FAILURE","MODEL_RESPONSE_UNAVAILABLE_OR_INVALID_ENCODING")
        if response.output_tokens is not None and response.output_tokens>cap:
            raise Failure("PROTOCOL_FAILURE","OUTPUT_TOKEN_CAP_EXCEEDED")
        return visible

    def structured(self, request, phase, fixed_action=None):
        if phase in self.primary:
            raise Failure("PROTOCOL_FAILURE","DUPLICATE_PRIMARY_PHASE")
        self.primary.add(phase)
        ref=self.prompts.schema_ref(phase,self.architecture)
        raw=self._invoke(request,phase)
        def check(text):
            try:
                value=loads(text)
            except Failure:
                return None,[dict(code="INVALID_JSON",pointer="")]
            errors=self.prompts.schemas.errors(value,ref)
            if not errors and phase=="ACTION" and fixed_action is not None and value["action"]!=fixed_action:
                errors=[dict(code="FIXED_ACTION_MISMATCH",pointer="/action")]
            if not errors and phase=="PREP" and self.architecture=="B3" and value["proposal"] is not None:
                prop=value["proposal"]
                if value["profile_update_status"]!=prop["new_status"] or value["proposed_new_interval"]!=prop["new_interval"] or value["proposed_new_scope"]!=prop["new_scope"] or value["relevant_self_claim"]!=prop["claim_id"]:
                    errors=[dict(code="PROPOSAL_MIRROR_MISMATCH",pointer="/proposal")]
            return value,errors
        value,errors=check(raw)
        if not errors:
            return value
        self.sink("OUTPUT_VALIDATION_ERRORS",dict(phase=phase,errors=errors))
        if self.repaired:
            raise Failure("PROTOCOL_FAILURE","SECOND_INVALID_OUTPUT")
        self.repaired=True
        repaired=self._invoke(self.prompts.repair_request(raw,errors,ref),"REPAIR",phase)
        value,errors=check(repaired)
        if errors or not preserve_semantics(raw,value):
            raise Failure("PROTOCOL_FAILURE","REPAIR_INVALID_OR_SEMANTIC_CHANGE")
        return value
