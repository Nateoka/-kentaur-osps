"""B3 explicit stop/probe controller; no evaluator thresholds or causal judge."""
from copy import deepcopy as cp
from .b4 import KEY_FIELDS
from .errors import Failure
from .profiles import informative

ABNORMAL = {"PROTOCOL_FAILURE", "INFRA_FAILURE", "EXPLICIT_NONEXECUTION"}


def prep_path(architecture, mode, prep_calls, skip_reason=None, controller_authorized=False):
    abnormal = skip_reason in ABNORMAL
    if architecture in {"B0", "B4"}:
        valid = mode == "NO_PREP_INTERFACE" and prep_calls == 0 and skip_reason is None
    elif architecture in {"B1", "B2", "B3"}:
        valid = (mode == "PREP_EXECUTED" and prep_calls == 1 and skip_reason is None) or (mode == "PREP_SKIPPED" and prep_calls == 0 and (abnormal or architecture == "B3" and controller_authorized and skip_reason == "B3_STOP_CONTROLLER"))
    else:
        valid = False
    return dict(valid=valid, normal=valid and not abnormal, itt_included=valid,
        operational_evidence_eligible=valid and not abnormal,
        architecture_saving_eligible=valid and not abnormal,
        abnormal_reason=skip_reason if abnormal else None)


class Controller:
    def __init__(self, next_sequence, event_sink=None):
        self.next_sequence, self.sink = next_sequence, event_sink
        self.states, self.signatures = {}, {}
        self.pending, self.pending_key = None, None
        self.probe_events, self.latch_events = [], []

    def _state(self, scope):
        return self.states.setdefault(scope, dict(scope_id=scope, latched=False,
            since_episode=0, new_observations=0, pending_probe=None))

    def _latch(self, scope, latched, reason, episode):
        state = self._state(scope)
        state.update(latched=latched, since_episode=episode, new_observations=0)
        event = dict(scope_id=scope, sequence=self.next_sequence(), latched=latched, reason=reason)
        self.latch_events.append(event)
        if self.sink:
            self.sink("LATCH", event)

    def _probe(self, kind, resolution, reason, executed=False):
        event = cp(self.pending)
        event.update(event_kind=kind, resolution=resolution, reason=reason,
                     executed=executed, sequence=self.next_sequence())
        self.probe_events.append(event)
        if self.sink:
            self.sink("PROBE", event)
        return event

    def _clear(self):
        if self.pending:
            self._state(self.pending["scope_id"])["pending_probe"] = None
        self.pending, self.pending_key = None, None

    def begin(self, episode, key, tool_available=True):
        self.probe_events, self.latch_events = [], []
        if self.pending and self.pending["expires_episode"] is not None and episode > self.pending["expires_episode"]:
            scope = self.pending["scope_id"]
            self._probe("EXPIRED", "EXPIRED", "EXPIRY_AFTER_DECLARED_PLUS_FOUR")
            self._clear()
            self._latch(scope, False, "PROBE_EXPIRED", episode)
        scope = key["scope_id"]
        signature = (key["difficulty_scope"], key["context_condition"], key["tool_condition"], key["capability_configuration_ref"], tool_available)
        old = self.signatures.get(scope)
        if old is None:
            self._latch(scope, False, "NEW_SCOPE", episode)
        elif old != signature:
            reason = "TOOL_AVAILABILITY_CHANGED" if old[-1] != tool_available else "CONTEXT_CHANGED"
            self._latch(scope, False, reason, episode)
        self.signatures[scope] = signature
        return not self._state(scope)["latched"]

    def accept_prep(self, record, episode, key, evidence, defer_stop=False):
        scope = key["scope_id"]
        if record["cancel_pending_probe"] and self.pending:
            previous = self.pending["scope_id"]
            self._probe("CANCELLED", "CANCELLED", "EXPLICIT_CANCEL")
            self._clear()
            self._latch(previous, False, "PROBE_CANCELLED", episode)
        if record["probe_needed"]:
            kind = record["probe_type"]
            reference, target_key = None, cp(key)
            if kind == "VERIFY_NEXT_MATCHED":
                # Future normal mode is determined by this declared stop flag.
                target_key["execution_mode"] = "PREP_SKIPPED" if record["stop_reflection"] else "PREP_EXECUTED"
                target_key["history_class"] = "NONEMPTY"
                matches = [f for f in evidence if f["episode_index"] < episode and informative(f)
                    and all(f[k] == target_key[k] for k in KEY_FIELDS)]
                if not matches:
                    raise Failure("PROTOCOL_FAILURE", "NO_PAST_EXACT_MATCH_FOR_PROBE")
                reference = max(matches, key=lambda f: f["episode_index"])["episode_id"]
            if self.pending:
                old_scope = self.pending["scope_id"]
                self._probe("CANCELLED", "CANCELLED", "REPLACED_BY_NEW_DECLARATION")
                self._clear()
                self._latch(old_scope, False, "PROBE_CANCELLED", episode)
            sequence = self.next_sequence()
            self.pending = dict(probe_type=kind, predictions=cp(record["probe_predictions"]),
                reference_episode=reference, scope_id=scope, declared_episode=episode,
                expires_episode=episode+4 if kind == "VERIFY_NEXT_MATCHED" else None,
                executed=False, resolution="PENDING", probe_id=f"probe:{episode}:{sequence}",
                event_kind="DECLARED", sequence=sequence, reason="BOUNDED_EVIDENCE_PROBE")
            self.pending_key = target_key
            self._state(scope)["pending_probe"] = cp(self.pending)
            self.probe_events.append(cp(self.pending))
            if self.sink:
                self.sink("PROBE", self.pending)
        if record["stop_reflection"] and not defer_stop:
            self._latch(scope, True, "STOP_DECLARED", episode)

    def apply_stop(self, record, episode, key):
        if record["stop_reflection"]:
            self._latch(key["scope_id"], True, "STOP_DECLARED", episode)

    def action(self, episode, key, action):
        if not self.pending:
            return False
        kind = self.pending["probe_type"]
        scheduled = episode > self.pending["declared_episode"] if kind == "VERIFY_NEXT_MATCHED" else episode == self.pending["declared_episode"]
        expected_action = "SOLO" if kind == "SOLO_CURRENT" else "VERIFY"
        matches = scheduled and all(key[k] == self.pending_key[k] for k in KEY_FIELDS)
        executed = matches and action == expected_action
        if executed:
            event = self._probe("ACTION", "PENDING", "MATCHING_SCHEDULED_ACTION", True)
            self._state(self.pending["scope_id"])["pending_probe"] = cp(event)
        return executed

    def feedback(self, episode, key, feedback, claim, probe_executed=False, last_numeric=None):
        scope = key["scope_id"]
        state = self._state(scope)
        if self.pending and probe_executed and informative(feedback):
            owner = self.pending["scope_id"]
            self._probe("FEEDBACK", "EVIDENCE_RETURNED", "OBSERVED_NOT_CAUSALLY_IDENTIFIED", True)
            self._clear()
            self._latch(owner, False, "PROBE_RETURNED", episode)
        if self.pending and self.pending["probe_type"] != "VERIFY_NEXT_MATCHED" and self.pending["declared_episode"] == episode:
            owner = self.pending["scope_id"]
            self._probe("CANCELLED", "CANCELLED", "ACTION_NOT_EXECUTED_OR_NO_USABLE_RESPONSE")
            self._clear()
            self._latch(owner, False, "PROBE_CANCELLED", episode)
        if state["latched"] and informative(feedback):
            state["new_observations"] += 1
            interval = None if claim is None else claim["estimated_success_interval"]
            if interval is None and last_numeric is not None:
                interval = last_numeric["estimated_success_interval"]
            mid = None if interval is None else (interval["lower"]+interval["upper"])/2
            surprise = mid is not None and ((mid <= .4 and feedback["solo_correct"]) or (mid >= .8 and not feedback["solo_correct"]))
            unknown = claim is None or claim["status"] in {"UNKNOWN", "QUESTIONED"}
            if surprise:
                self._latch(scope, False, "SURPRISE", episode)
            elif unknown and state["new_observations"] >= 2:
                self._latch(scope, False, "NEW_EVIDENCE", episode)

    def finish(self):
        if self.pending:
            self._probe("END_PENDING", "PENDING", "NO_ADDITIONAL_EPISODE")
            return "END_PENDING"
        return "END_NO_PENDING"

    def public_state(self):
        return [cp(self.states[k]) for k in sorted(self.states)]
