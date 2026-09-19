"""Strong tracker policy 0.2; integer Beta prior and exact key partitioning."""
from fractions import Fraction
from math import comb
from .errors import Failure

KEY_FIELDS = ("task_family", "difficulty_scope", "context_condition", "tool_condition",
              "capability_configuration_ref", "execution_mode", "history_class")


def beta_sf(x, a, b):
    if type(a) is not int or type(b) is not int or min(a, b) < 1:
        raise Failure("CONFIGURATION_FAILURE", "INTEGER_BETA_REQUIRED")
    x = Fraction(str(x))
    if not 0 <= x <= 1:
        raise Failure("CONFIGURATION_FAILURE", "INVALID_BETA_POINT")
    n = a+b-1
    return sum(Fraction(comb(n, j))*x**j*(1-x)**(n-j) for j in range(a))


def choose_action(successes, failures, opportunity, tool_available=True):
    if any(type(v) is not int or v < 0 for v in (successes, failures)) or type(opportunity) is not int or opportunity < 1:
        raise Failure("CONFIGURATION_FAILURE", "INVALID_TRACKER_COUNTS")
    mean = Fraction(1+successes, 2+successes+failures)
    if not tool_available:
        return "SOLO" if mean >= Fraction(4, 5) else "ABSTAIN"
    if mean >= Fraction(4, 5):
        return "SOLO"
    mass = beta_sf("0.8", 1+successes, 1+failures)
    if successes+failures < 4 or Fraction(1, 10) <= mass <= Fraction(9, 10) or opportunity % 3 == 0:
        return "VERIFY"
    return "DELEGATE"


class Tracker:
    def __init__(self):
        self.cells = {}
        self.seen = set()

    def opportunity(self, public_key, tool_available=True):
        key = tuple(public_key[k] for k in KEY_FIELDS)
        cell = self.cells.setdefault(key, dict(successes=0, failures=0, opportunity=0))
        cell["opportunity"] += 1
        return choose_action(**cell, tool_available=tool_available)

    def observe(self, public_key, latent_fingerprint, action, solo_correct,
                seal_precedes_tool=False, protocol_status="OK"):
        if protocol_status != "OK" or action not in {"SOLO", "VERIFY"} or type(solo_correct) is not bool:
            return False
        if action == "VERIFY" and not seal_precedes_tool:
            return False
        if latent_fingerprint in self.seen:
            return False
        key = tuple(public_key[k] for k in KEY_FIELDS)
        cell = self.cells.setdefault(key, dict(successes=0, failures=0, opportunity=0))
        cell["successes" if solo_correct else "failures"] += 1
        self.seen.add(latent_fingerprint)
        return True
