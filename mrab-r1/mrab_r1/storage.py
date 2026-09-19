"""Single-writer append-only hash chain; rejects truncated or mutated history.

Internal events, not a replacement for normative episode/trajectory records.
Exclusive writer lease is explicit; a stale lease is never silently removed.
"""
import os
from pathlib import Path
from .canonical import canonical, canonical_many, loads, raw_sha
from .errors import Failure


def read_events(path):
    path = Path(path)
    if not path.exists():
        return []
    data = path.read_bytes()
    return decode_events(data)


def decode_events(data):
    """Validate one immutable byte snapshot (also avoids file re-read races)."""
    if data and not data.endswith(b"\n"):
        raise Failure("INFRA_FAILURE", "INCOMPLETE_EVENT_TAIL")
    previous, events = "0"*64, [loads(raw) for raw in data.splitlines()]
    unsigned=[]
    for event in events:
        if set(event) != {"sequence", "previous_sha256", "kind", "payload", "sha256"}:
            raise Failure("INFRA_FAILURE", "INVALID_EVENT_ENVELOPE")
        unsigned.append({k:v for k,v in event.items() if k!="sha256"})
    encoded=[]
    for start in range(0,len(unsigned),128):encoded.extend(canonical_many(unsigned[start:start+128]))
    for i,(event,raw) in enumerate(zip(events,encoded),1):
        checksum=event["sha256"]
        if event["sequence"] != i or event["previous_sha256"] != previous or raw_sha(raw) != checksum:
            raise Failure("INFRA_FAILURE", "EVENT_CHAIN_MISMATCH")
        previous = checksum
    return events


class EventStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lease = self.path.with_suffix(self.path.suffix + ".writer.lock")
        try:
            self.lock_fd = os.open(self.lease, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise Failure("INFRA_FAILURE", "WRITER_LEASE_EXISTS") from None
        try:
            self.events = read_events(self.path)
            self.fd = os.open(self.path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
        except BaseException:
            os.close(self.lock_fd)
            self.lease.unlink()
            raise

    def append(self, kind, payload):
        event = dict(sequence=len(self.events)+1,
            previous_sha256=self.events[-1]["sha256"] if self.events else "0"*64,
            kind=kind, payload=loads(canonical(payload)))
        event["sha256"] = raw_sha(canonical(event))
        encoded = canonical(event) + b"\n"
        written = 0
        while written < len(encoded):
            n = os.write(self.fd, encoded[written:])
            if n <= 0:
                raise Failure("INFRA_FAILURE", "EVENT_WRITE_FAILED")
            written += n
        os.fsync(self.fd)
        self.events.append(event)
        return loads(canonical(event))

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            os.close(self.lock_fd)
            self.fd = None
            self.lease.unlink()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
