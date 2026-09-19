"""G01: immutable domain separation and unbiased uint32 draws."""
import hashlib
import struct
from . import PROTOCOL_REVISION
from .canonical import integer_dsl_bytes
from .errors import Failure

SPLITS = {"CALIBRATION_SEARCH", "CALIBRATION_CONFIRM", "MAIN", "TRANSFER"}
STREAMS = {"TASK", "TASK_ID", "FAMILY_ORDER", "SURFACE", "PROFILE", "MODEL", "BOOTSTRAP"}


class Stream:
    def __init__(self, master_seed, split, block_id, stream, item_index=0,
                 generation_attempt=0, architecture=None, phase=None):
        if split not in SPLITS or stream not in STREAMS:
            raise Failure("CONFIGURATION_FAILURE", "INVALID_SEED_DOMAIN")
        if any(type(n) is not int or n < 0 for n in (item_index, generation_attempt)):
            raise Failure("CONFIGURATION_FAILURE", "INVALID_SEED_INDEX")
        if stream != "MODEL" and (architecture is not None or phase is not None):
            raise Failure("CONFIGURATION_FAILURE", "MODEL_DOMAIN_ONLY")
        if stream == "MODEL" and (architecture not in {"B0", "B1", "B2", "B3", "B4"} or phase not in {"PREP", "ACTION", "REPAIR"}):
            raise Failure("CONFIGURATION_FAILURE", "INVALID_MODEL_DOMAIN")
        self.base = ["MRAB-R1", PROTOCOL_REVISION, master_seed, split, block_id,
                     stream, item_index, generation_attempt, 0, architecture, phase]
        try:
            integer_dsl_bytes(self.base)
        except (ValueError, UnicodeError):
            raise Failure("CONFIGURATION_FAILURE", "NON_ASCII_SEED") from None
        self.counter, self.words = 0, []

    def digest(self, counter=0):
        value = self.base[:]
        value[8] = counter
        return hashlib.sha256(integer_dsl_bytes(value)).digest()

    def randint(self, a, b):
        m = b - a + 1
        if not 1 <= m <= 2**32:
            raise Failure("CONFIGURATION_FAILURE", "INVALID_RANDOM_RANGE")
        limit = (2**32 // m) * m
        while True:
            if not self.words:
                self.words = list(struct.unpack(">8I", self.digest(self.counter)))
                self.counter += 1
            x = self.words.pop(0)
            if x < limit:
                return a + x % m

    def shuffle(self, values):
        values = list(values)
        for i in range(len(values) - 1, 0, -1):
            j = self.randint(0, i)
            values[i], values[j] = values[j], values[i]
        return values

    def weighted(self, weights):
        if not weights or any(type(v) is not int or v <= 0 for v in weights.values()):
            raise Failure("CONFIGURATION_FAILURE", "INVALID_WEIGHTS")
        draw = self.randint(1, sum(weights.values()))
        for key in sorted(weights):
            draw -= weights[key]
            if draw <= 0:
                return key
