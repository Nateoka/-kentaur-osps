"""One shared, evaluator-blind B2/B3 admissibility committer."""
from copy import deepcopy as cp
from .canonical import canonical
from .errors import Failure
from .schemas import Schemas

SCOPE_FIELDS = ("scope_id", "task_family", "difficulty_scope", "context_condition",
                "tool_condition", "capability_configuration_ref", "execution_modes")
SETS = ("difficulty_scope", "context_condition", "execution_modes")
IDENTITIES = tuple(k for k in SCOPE_FIELDS if k not in SETS)


def scope_of(claim):
    return {k: cp(claim[k]) for k in SCOPE_FIELDS}


def subset(a, b):
    return all(a[k] == b[k] for k in IDENTITIES) and all(set(a[k]) <= set(b[k]) for k in SETS)


def same_scope(a, b):
    return subset(a, b) and subset(b, a)


def applies(scope, feedback):
    return (all(scope[k] == feedback[k] for k in IDENTITIES)
        and feedback["difficulty_scope"] in scope["difficulty_scope"]
        and feedback["context_condition"] in scope["context_condition"]
        and feedback["execution_mode"] in scope["execution_modes"])


def informative(feedback):
    return (feedback.get("outcome") in {"CORRECT", "INCORRECT"}
        and feedback.get("chosen_action") in {"SOLO", "VERIFY"}
        and type(feedback.get("solo_correct")) is bool
        and feedback.get("prep_skip_reason") not in {"PROTOCOL_FAILURE", "INFRA_FAILURE", "EXPLICIT_NONEXECUTION"})


class ProfileStore:
    def __init__(self, profile, event_sink=None):
        self.schemas = Schemas()
        if profile is not None:
            self.schemas.validate(profile, self.schemas.ref("self_profile"), "CONFIGURATION_FAILURE")
            if len({x["claim_id"] for x in profile["claims"]}) != 2:
                raise Failure("LIFECYCLE_VIOLATION", "DUPLICATE_CLAIM_ID")
        self.initial = cp(profile)
        self.current = cp(profile)
        self.attempts, self.submitted_episodes = [], set()
        self.sink = event_sink

    def snapshots(self, claim_id):
        if self.initial is None:
            return []
        snapshots = [cp(c) for c in self.initial["claims"] if c["claim_id"] == claim_id]
        for event in self.attempts:
            if event["validation_status"] == "COMMITTED" and event["proposal"]["claim_id"] == claim_id:
                snapshots += cp(event["stage_snapshots"])
        return snapshots

    def anchors(self):
        if self.current is None:
            return []
        anchors = []
        for claim in self.current["claims"]:
            history = self.snapshots(claim["claim_id"])
            numeric = next((c for c in reversed(history) if c["estimated_success_interval"] is not None), None)
            parent = next((c for c in reversed(history) if subset(claim, c) and not same_scope(claim, c)), None)
            for reason, snapshot in (("LAST_NUMERIC", numeric), ("SCOPE_PARENT", parent)):
                if snapshot:
                    anchors.append(dict(reason=reason, claim_id=claim["claim_id"], version=snapshot["version"], claim=cp(snapshot)))
        if len(anchors) > 8:
            raise Failure("CONFIGURATION_FAILURE", "ANCHOR_OVERFLOW")
        return anchors

    def commit(self, proposal, actor, episode, public_evidence, sequence):
        self.schemas.validate(proposal, self.schemas.ref("self_profile", "proposal"))
        if episode in self.submitted_episodes:
            raise Failure("LIFECYCLE_VIOLATION", "ONE_PROPOSAL_PER_EPISODE")
        if self.current is None:
            raise Failure("LIFECYCLE_VIOLATION", "NO_PROFILE_UPDATE_AUTHORITY")
        self.submitted_episodes.add(episode)
        claim = next((c for c in self.current["claims"] if c["claim_id"] == proposal["claim_id"]), None)
        errors = set()
        if actor not in {"B2", "B3"}:
            errors.add("UNAUTHORIZED_ACTOR")
        if claim is None:
            errors.add("UNKNOWN_CLAIM")
        if claim and proposal["expected_version"] != claim["version"]:
            errors.add("STALE_VERSION")
        known = {f["episode_id"]: f for f in public_evidence}
        if any(r not in known or known[r]["episode_index"] >= episode for r in proposal["evidence_refs"]):
            errors.add("FUTURE_EVIDENCE")
        local, path, numeric = [], [], None
        if claim:
            scope, interval, status = proposal["new_scope"], proposal["new_interval"], proposal["new_status"]
            history = self.snapshots(claim["claim_id"])
            numeric = next((x for x in reversed(history) if x["estimated_success_interval"] is not None), None)
            visible_versions = {a["version"] for a in self.anchors() if a["claim_id"] == claim["claim_id"]} | {claim["version"]}
            for e in self.attempts[-10:]:
                for c in [e["before_claim"], e["after_claim"], *e["stage_snapshots"]]:
                    if c and c["claim_id"] == claim["claim_id"]:
                        visible_versions.add(c["version"])
            restored = next((x for x in history if x["version"] == proposal["restore_version"] and x["version"] in visible_versions), None)
            if proposal["restore_version"] is not None and (restored is None or status != "ACTIVE"):
                errors.add("LIFECYCLE_VIOLATION")
            rollback = restored is not None and status == "ACTIVE" and same_scope(scope, restored)
            if not subset(scope, claim) and not rollback:
                errors.add("SCOPE_VIOLATION")
            if scope["scope_id"] != claim["scope_id"]:
                errors.add("SCOPE_VIOLATION")
            if (status == "UNKNOWN") != (interval is None) or (interval is not None and not 0 <= interval["lower"] <= interval["upper"] <= 1):
                errors.add("INVALID_INTERVAL")
            local = [known[r] for r in proposal["evidence_refs"] if r in known and known[r]["episode_index"] < episode and applies(scope, known[r])]
            # QUESTIONED retains a prior estimate; it is not a new solo estimate.
            numerical = (status != "QUESTIONED" and interval != claim["estimated_success_interval"]) or not same_scope(scope, claim)
            if not local or numerical and not any(informative(f) for f in local):
                errors.add("NO_LOCAL_EVIDENCE")
            if status == claim["status"] == "QUESTIONED":
                errors.add("LIFECYCLE_VIOLATION")
            if claim["status"] == "UNKNOWN" and numeric is None:
                errors.add("LIFECYCLE_VIOLATION")
            if status == "QUESTIONED" and (numeric is None or interval != numeric["estimated_success_interval"] or not same_scope(scope, claim)):
                errors.add("LIFECYCLE_VIOLATION")
            if status == "ACTIVE":
                expected = restored or numeric
                if expected is None or interval != expected["estimated_success_interval"] or (not rollback and not same_scope(scope, claim)):
                    errors.add("LIFECYCLE_VIOLATION")
            if status == "REVISED" and not same_scope(scope, claim):
                errors.add("SCOPE_VIOLATION")
            if status == "NARROWED" and (not subset(scope, claim) or same_scope(scope, claim)):
                errors.add("SCOPE_VIOLATION")
            if status == "UNKNOWN" and not same_scope(scope, claim):
                errors.add("SCOPE_VIOLATION")
            path = [claim["status"]] + ([] if claim["status"] == "QUESTIONED" else ["QUESTIONED"]) + ([] if status == "QUESTIONED" else [status])
        event = dict(proposal=cp(proposal), validation_status="REJECTED" if errors else "COMMITTED",
            rejection_codes=sorted(errors), transition_path=[] if errors else path,
            before_claim=cp(claim), after_claim=None, effective_episode=episode, sequence=sequence,
            profile_version_before=self.current["version"], profile_version_after=self.current["version"], stage_snapshots=[])
        updated = cp(self.current)
        if not errors:
            current = cp(claim)
            for status in path[1:]:
                current.update(status=status, version=current["version"]+1, last_updated_episode=episode,
                    evidence_label="OBSERVED_OUTCOMES", evidence_n=len({f["episode_id"] for f in local if informative(f)}))
                if status == "QUESTIONED" and current["estimated_success_interval"] is None:
                    current["estimated_success_interval"] = cp(numeric["estimated_success_interval"])
                if status == proposal["new_status"]:
                    current.update(cp(proposal["new_scope"]))
                    current["estimated_success_interval"] = cp(proposal["new_interval"])
                event["stage_snapshots"].append(cp(current))
            event["after_claim"] = cp(current)
            event["profile_version_after"] += 1
            updated["version"] += 1
            updated["claims"] = [current if c["claim_id"] == current["claim_id"] else c for c in updated["claims"]]
        self.schemas.validate(event, self.schemas.ref("self_profile", "update_event"))
        if self.sink:
            self.sink("PROFILE_ATTEMPT", event)  # Durable before exposing mutation.
        self.current = updated
        self.attempts.append(cp(event))
        return cp(event)
