"""Public errors never include private input values or solver answers."""
FAILURE_TYPES = frozenset({"CONFIGURATION_FAILURE", "GENERATION_FAILURE",
    "INFRA_FAILURE", "PROTOCOL_FAILURE", "CALIBRATION_NOT_FEASIBLE",
    "AMBIGUOUS_TASK", "UNSAT_TASK", "LEAKAGE_FAILURE", "LIFECYCLE_VIOLATION",
    "DESIGN_CONTRACT_CONFLICT"})


class Failure(Exception):
    def __init__(self, kind, code, pointer=""):
        if kind not in FAILURE_TYPES:
            raise ValueError("Unknown failure taxonomy")
        self.kind, self.code, self.pointer = kind, code, pointer
        super().__init__(f"{kind}:{code}:{pointer}")

    def as_dict(self):
        return dict(type=self.kind, code=self.code, pointer=self.pointer)
