"""Explicit configuration identity; placeholders never become runnable defaults."""
from copy import deepcopy
from .canonical import loads, raw_sha, semantic_sha
from .errors import Failure
from .schemas import Schemas, DESIGN
from . import PROTOCOL_REVISION


def template():
    return loads((DESIGN/"r1_config.default.json").read_bytes())


def _validate(config, content=None, *, pre_calibration=False):
    config = deepcopy(config)
    schemas = Schemas()
    schemas.validate(config, schemas.ref("config"), "CONFIGURATION_FAILURE")
    if config["configuration_status"] != ("TEMPLATE" if pre_calibration else "FROZEN"):
        raise Failure("CONFIGURATION_FAILURE", "TEMPLATE_NOT_RUNNABLE")
    if config["protocol_revision"] != PROTOCOL_REVISION:
        raise Failure("CONFIGURATION_FAILURE", "PROTOCOL_REVISION_MISMATCH")
    def walk(value, path="", hashed=False):
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, path+"/"+key, hashed or "sha256" in key or key.endswith("_hash"))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, path+"/"+str(i), hashed)
        elif isinstance(value, str):
            if any(x in value.upper() for x in ("CONFIGURE", "PLACEHOLDER", "AUTHOR_DECISION_REQUIRED")):
                raise Failure("CONFIGURATION_FAILURE", "UNRESOLVED_SETTING", path)
            if hashed and (len(value) != 64 or any(c not in "0123456789abcdef" for c in value) or value == "0"*64 or content is not None and (value not in content or raw_sha(content[value]) != value)):
                raise Failure("CONFIGURATION_FAILURE", "UNRESOLVED_CONTENT_HASH", path)
    walk(config)
    expected = {(f,b) for f in ("SYMBOLIC_PIPELINE","RULE_GRID") for b in ("HIGH","MID")}
    if pre_calibration and config["selected_difficulty_tuples"]:
        raise Failure("CONFIGURATION_FAILURE", "SEARCH_REQUIRES_UNSELECTED_TUPLES")
    if not pre_calibration and ({(x["family"],x["band"]) for x in config["selected_difficulty_tuples"]} != expected or len(config["selected_difficulty_tuples"]) != 4):
        raise Failure("CONFIGURATION_FAILURE", "FOUR_SELECTED_TUPLES_REQUIRED")
    if not pre_calibration and len({x["scope_id"] for x in config["selected_difficulty_tuples"]}) != 4:
        raise Failure("CONFIGURATION_FAILURE", "SELECTED_SCOPE_NOT_UNIQUE")
    if config["compute_settings"]["usage_accounting"] == "UNKNOWN":
        raise Failure("CONFIGURATION_FAILURE", "ACCOUNTING_NOT_CONFIGURED")
    if set(config["architectures"]) != {"B0","B1","B2","B3","B4"} or set(config["profile_conditions"]) != {"C0","C1","C2","C3"}:
        raise Failure("CONFIGURATION_FAILURE", "RESERVED_ARCHITECTURE_OR_CONDITION")
    fixed = template()
    for key in ("policy", "budgets", "analysis_windows", "evaluator", "evaluation_policy", "structural_relations", "b4_policy_version", "history_window", "design_decisions", "calibration_bands", "calibration_plan", "profile_stimulus", "ordering_policy", "transfer_scope"):
        if config[key] != fixed[key]:
            raise Failure("CONFIGURATION_FAILURE", "FROZEN_PROTOCOL_SETTING_CHANGED", "/"+key)
    expected_modes = {"B0":["NO_PREP_INTERFACE"], "B1":["PREP_EXECUTED"], "B2":["PREP_EXECUTED"], "B3":["PREP_EXECUTED","PREP_SKIPPED"], "B4":["NO_PREP_INTERFACE"]}
    for architecture,modes in expected_modes.items():
        if config["capability_configurations"][architecture]["execution_modes"] != modes or config["capability_configurations"][architecture]["prep_policy"] != fixed["capability_configurations"][architecture]["prep_policy"]:
            raise Failure("CONFIGURATION_FAILURE", "CAPABILITY_PREP_POLICY_CHANGED")
    from .identity import verify_frozen_implementation
    verify_frozen_implementation(config)
    return dict(config=config, config_sha256=semantic_sha(config))


def freeze(config, content):
    """Creation gate: every referenced digest must resolve to actual CAS bytes."""
    if not isinstance(content,dict):
        raise Failure("CONFIGURATION_FAILURE","CONTENT_ADDRESSED_BYTES_REQUIRED")
    return _validate(config, content)


def validate_frozen(config):
    """Consumption gate: schema, fixed semantics and loaded runtime/prompt identity.

    External adapter/tokenizer and tuple bytes were bound by freeze; run/calibration
    seals bind this exact config. This is not a replacement for the creation gate.
    """
    return _validate(config)


def pre_calibration_lock(config, content):
    _validate(config, content, pre_calibration=True)
    payload=deepcopy(config)
    return dict(payload=payload,sha256=semantic_sha(payload))


def verify_calibration_lock(lock, config, *, final=False):
    if semantic_sha(lock["payload"]) != lock["sha256"]:
        raise Failure("INFRA_FAILURE", "CALIBRATION_LOCK_HASH_MISMATCH")
    _validate(lock["payload"], pre_calibration=True)
    projected=deepcopy(config)
    if final:
        validate_frozen(config)
        projected["configuration_status"]="TEMPLATE"
        projected["selected_difficulty_tuples"]=[]
    if projected != lock["payload"]:
        raise Failure("INFRA_FAILURE", "PRE_CALIBRATION_SETTINGS_DRIFT")
    return True


class OfflineTokenizer:
    """Deterministic test tokenizer. Never a claim about a real model tokenizer."""
    identity = "BYTE_QUARTER_TEST_TOKENIZER_0.1"
    def count(self, data):
        return (len(data)+3)//4
