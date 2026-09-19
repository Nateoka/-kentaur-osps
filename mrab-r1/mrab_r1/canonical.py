"""Strict JSON + RFC 8785 through ECMAScript's native number serialization.

No Python float rounding rule. The explicit Node runtime is a recorded auxiliary
dependency, not a model tool. Executable path is trusted harness configuration.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from .errors import Failure


def raw_sha(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Failure("PROTOCOL_FAILURE", "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _check(value):
    if type(value) is int and abs(value) > 9007199254740991:
        raise Failure("PROTOCOL_FAILURE", "UNSUPPORTED_INTEGER_REPRESENTATION")
    if type(value) is float and not math.isfinite(value):
        raise Failure("PROTOCOL_FAILURE", "NONFINITE_NUMBER")
    if isinstance(value, str):
        try:
            value.encode("utf-8", "strict")
        except UnicodeError:
            raise Failure("PROTOCOL_FAILURE", "INVALID_UNICODE") from None
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise Failure("PROTOCOL_FAILURE", "NONSTRING_KEY")
            _check(key)
            _check(item)
    elif isinstance(value, list):
        for item in value:
            _check(item)
    elif value is not None and type(value) not in (bool, int, float):
        raise Failure("PROTOCOL_FAILURE", "UNSUPPORTED_JSON_TYPE")


def loads(data):
    def bad_constant(_):
        raise Failure("PROTOCOL_FAILURE", "NONFINITE_NUMBER")
    def parse_float(text):
        value=float(text)
        mantissa=text.lower().split("e")[0]
        if value==0 and any(c in "123456789" for c in mantissa):
            raise Failure("PROTOCOL_FAILURE","UNREPRESENTABLE_FLOAT_UNDERFLOW")
        if not math.isfinite(value):raise Failure("PROTOCOL_FAILURE","NONFINITE_NUMBER")
        return value
    try:
        text = data.decode("utf-8", "strict") if isinstance(data, bytes) else data
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=bad_constant,parse_float=parse_float)
        _check(value)
        return value
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise Failure("PROTOCOL_FAILURE", "INVALID_JSON") from None


def canonical(value):
    _check(value)
    executable = os.environ.get("MRAB_JCS_NODE") or shutil.which("node")
    if not executable:
        raise Failure("CONFIGURATION_FAILURE", "ECMASCRIPT_CANONICALIZER_UNAVAILABLE")
    data = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
    try:
        process = subprocess.run([executable, str(Path(__file__).with_name("jcs.cjs"))],
            input=data, capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise Failure("CONFIGURATION_FAILURE", "CANONICALIZER_EXECUTION_FAILED") from None
    if process.returncode:
        raise Failure("PROTOCOL_FAILURE", "CANONICALIZATION_FAILED")
    return process.stdout


def semantic_sha(value):
    return raw_sha(canonical(value))


def canonical_many(values):
    """Same JCS serializer, amortized subprocess cost for verified event chains."""
    if not values:return []
    _check(values)
    executable=os.environ.get("MRAB_JCS_NODE") or shutil.which("node")
    if not executable:raise Failure("CONFIGURATION_FAILURE","ECMASCRIPT_CANONICALIZER_UNAVAILABLE")
    data=json.dumps(values,ensure_ascii=False,allow_nan=False,separators=(",",":")).encode()
    try:
        process=subprocess.run([executable,str(Path(__file__).with_name("jcs.cjs")),"--batch"],input=data,capture_output=True,timeout=60)
    except (OSError,subprocess.TimeoutExpired):
        raise Failure("CONFIGURATION_FAILURE","CANONICALIZER_EXECUTION_FAILED") from None
    if process.returncode:raise Failure("PROTOCOL_FAILURE","CANONICALIZATION_FAILED")
    rows=process.stdout.splitlines()
    if len(rows)!=len(values):raise Failure("INFRA_FAILURE","JCS_BATCH_CARDINALITY")
    return rows


def integer_dsl_bytes(value):
    """G01/G07 ASCII/integer certificate, NOT general profile canonicalization."""
    def visit(x):
        if type(x) is float:
            raise Failure("CONFIGURATION_FAILURE", "FLOAT_IN_INTEGER_CERTIFICATE")
        if isinstance(x, dict):
            for k, v in x.items():
                k.encode("ascii")
                visit(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                visit(v)
        elif isinstance(x, str):
            x.encode("ascii")
    visit(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
