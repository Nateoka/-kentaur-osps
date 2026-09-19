"""Offline request-byte contract. No real provider adapters are registered."""
from dataclasses import asdict, dataclass
from copy import deepcopy
import math
from pathlib import Path
from typing import Protocol,runtime_checkable
from .canonical import raw_sha
from .errors import Failure


@runtime_checkable
class ProviderAdapter(Protocol):
    """Trusted harness extension, never supplied by a model response.

    Real adapters enforce the call_config deadline and preserve acceptance,
    raw response, observed revision and usage. They never add retries or history.
    identity_sha256 binds their registered implementation bytes for real runs.
    """
    kind: str
    identity_sha256: str
    def invoke(self,request_bytes: bytes,call_config: dict) -> "ProviderResponse": ...


@dataclass(frozen=True)
class ProviderResponse:
    raw_bytes: bytes | None
    provider_request_id: str
    started_at: str
    ended_at: str
    status: str = "OK"
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    reasoning_tokens: int | None = None
    latency_ms: float | None = None
    error_classification: str | None = None
    observed_model_revision: str | None = None

    def __post_init__(self):
        if self.raw_bytes is not None and type(self.raw_bytes) is not bytes:
            raise Failure("INFRA_FAILURE","INVALID_PROVIDER_RAW_BYTES")
        if self.status not in {"OK","TIMEOUT","CANCELLED","TRANSPORT_FAILURE"}:
            raise Failure("INFRA_FAILURE","INVALID_PROVIDER_STATUS")
        for name in ("input_tokens","output_tokens","cached_tokens","reasoning_tokens"):
            value=getattr(self,name)
            if value is not None and (type(value) is not int or value<0):raise Failure("INFRA_FAILURE","INVALID_PROVIDER_USAGE")
        if self.latency_ms is not None and (type(self.latency_ms) not in (int,float) or not math.isfinite(self.latency_ms) or self.latency_ms<0):
            raise Failure("INFRA_FAILURE","INVALID_PROVIDER_LATENCY")


class FakeProvider:
    kind = "FAKE"
    real_model_calls = 0
    network_calls = 0

    @property
    def identity_sha256(self):return raw_sha(Path(__file__).read_bytes())

    def __init__(self, scripted_responses):
        self.responses = tuple(deepcopy(scripted_responses))
        self.position = 0
        self.captures = []

    def invoke(self, request_bytes, call_config):
        if type(request_bytes) is not bytes:
            raise Failure("CONFIGURATION_FAILURE", "REQUEST_MUST_BE_BYTES")
        if self.position >= len(self.responses):
            raise Failure("INFRA_FAILURE", "FAKE_SCRIPT_EXHAUSTED")
        response = self.responses[self.position]
        self.position += 1
        self.captures.append(dict(request_hex=request_bytes.hex(),
            request_sha256=raw_sha(request_bytes), call_config=deepcopy(call_config),
            response={**asdict(response), "raw_bytes": None,
                "raw_hex": None if response.raw_bytes is None else response.raw_bytes.hex()},
            response_sha256=None if response.raw_bytes is None else raw_sha(response.raw_bytes)))
        return response


class ReplayProvider:
    kind = "REPLAY"
    real_model_calls = 0
    network_calls = 0

    @property
    def identity_sha256(self):return raw_sha(Path(__file__).read_bytes())

    def __init__(self, captures):
        self.captures = deepcopy(captures)
        self.position = 0

    def invoke(self, request_bytes, call_config):
        if self.position >= len(self.captures):
            raise Failure("INFRA_FAILURE", "REPLAY_EXHAUSTED")
        entry = self.captures[self.position]
        if raw_sha(request_bytes) != entry["request_sha256"] or request_bytes.hex() != entry["request_hex"] or call_config != entry["call_config"]:
            raise Failure("INFRA_FAILURE", "REPLAY_REQUEST_MISMATCH")
        response = deepcopy(entry["response"])
        raw_hex = response.pop("raw_hex")
        response["raw_bytes"] = None if raw_hex is None else bytes.fromhex(raw_hex)
        actual = None if response["raw_bytes"] is None else raw_sha(response["raw_bytes"])
        if actual != entry["response_sha256"]:
            raise Failure("INFRA_FAILURE", "REPLAY_RESPONSE_HASH_MISMATCH")
        self.position += 1
        return ProviderResponse(**response)

    def assert_consumed(self):
        if self.position != len(self.captures):
            raise Failure("INFRA_FAILURE", "REPLAY_UNCONSUMED_CALLS")
