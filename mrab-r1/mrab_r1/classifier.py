"""E07 runtime classifier, including author-approved R1-E07-HARM-01.

The immutable design checker is provenance, not an executable oracle. This
module evaluates independently available findings before conditional gates.
"""
import math

POLICY = dict(eq=.05, accuracy=.02, c1=.05, resource=.20, min_pairs=6,
              min_reach=.50, reach_gap=.25, gain=.05)


def classify_summary(summary):
    p = POLICY
    findings, reasons, by = [], [], {}
    def valid(ci):
        return isinstance(ci, list) and len(ci) == 2 and all(type(x) in (float, int) and math.isfinite(x) for x in ci) and ci[0] <= ci[1]
    def equivalent(ci, margin):
        return valid(ci) and -margin <= ci[0] and ci[1] <= margin
    def worse(ci, margin):
        return valid(ci) and ci[0] > margin
    def better(ci, margin=0):
        return valid(ci) and ci[1] < -margin
    def add(comparator, kind, conditions, reason):
        findings.append(dict(comparator=comparator, kind=kind, conditions=conditions, reason=reason))
    guard = summary.get("c1", {})
    scopes = ["target_accuracy_loss", "control_accuracy_loss"]
    resources = guard.get("resource_ratios", {})
    resource_known = bool(resources) and all(valid(x) for x in resources.values())
    c1_harm = any(worse(guard.get(scope), p["c1"]) for scope in scopes)
    c1_safe = (all(valid(guard.get(scope)) and guard[scope][1] <= p["c1"] for scope in scopes)
        and ((resource_known and all(x[1] <= p["resource"] for x in resources.values())) or all(better(guard.get(scope), p["c1"]) for scope in scopes)))
    if c1_harm:
        add("B0/B2:C1", "HARM", ["C1"], "Known C1 accuracy loss")
    if not c1_safe and not c1_harm:
        reasons.append("C1:GUARD_UNRESOLVED")
    for comparator in ("B1", "B2", "B4"):
        data = summary.get("comparators", {}).get(comparator)
        if not data:
            reasons.append(comparator+":MISSING_COMPARATOR")
            continue
        costs = data.get("resource_ratios", {})
        usage = data.get("usage_known") is True and bool(costs) and all(valid(v) for v in costs.values())
        normal = data.get("normal_execution_comparison", True)
        comparable = usage and normal and all(equivalent(v, .2) for v in costs.values())
        costly = usage and normal and any(worse(v, .2) for v in costs.values()) and not any(better(v, .2) for v in costs.values())
        cheap = usage and normal and any(better(v, .2) for v in costs.values()) and not any(worse(v, .2) for v in costs.values())
        benefits, harms, equivalences = [], [], []
        eligible = True
        for condition in ("C2", "C3"):
            row = data.get(condition, {})
            accuracy, completion = row.get("accuracy_loss"), row.get("completion_loss")
            fixed, primary = row.get("fixed_ci"), row.get("primary_ci")
            enough = row.get("n_pairs", 0) >= 6
            missing = not all(valid(x) for x in (accuracy, completion, fixed, primary))
            reach = row.get("reach")
            reached = isinstance(reach, list) and len(reach) == 2 and all(type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1 for x in reach) and min(reach) >= .5 and abs(reach[0]-reach[1]) <= .25
            # R1-E07-HARM-01: no early continue can remove known independent harm.
            if enough and (worse(accuracy, .02) or worse(fixed, .05)):
                harms.append(condition)
            if not enough:
                reasons.append(f"{comparator}:{condition}:LOW_PAIRED_N")
            if missing:
                reasons.append(f"{comparator}:{condition}:MISSING_CI")
            if not reached:
                reasons.append(f"{comparator}:{condition}:LOW_OR_DIFFERENTIAL_REACH")
            if not enough or missing or not reached:
                eligible = False
                continue
            if better(primary) and better(fixed) and type(row.get("point")) in (int, float) and row["point"] <= -.05 and accuracy[1] <= .02 and completion[1] <= .05:
                benefits.append(condition)
            equivalences.append(equivalent(primary, .05) and equivalent(fixed, .05) and equivalent(accuracy, .02) and equivalent(completion, .05))
        eq = eligible and len(equivalences) == 2 and all(equivalences)
        by[comparator] = dict(benefit=benefits, harm=harms, equivalent=eq,
            comparable=comparable, more_costly=costly, eligible=eligible, usage_known=usage)
        if harms:
            add(comparator, "HARM", harms, "Independent adverse endpoint; uncertainty does not erase finding")
        if benefits:
            add(comparator, "BENEFIT", benefits, "Conditional and fixed benefit with guards")
        if eq and comparator in ("B2", "B4"):
            add(comparator, "REDUNDANT", ["C2", "C3"], "EQUIVALENT and predeclared structural relation")
            add(comparator, "REDUNDANT_BY_STRUCTURE", ["C2", "C3"], "Predeclared B3 structural complexity, not computed score")
            if costly:
                add(comparator, "REDUNDANT_BY_COST", ["C2", "C3"], "Materially higher observed cost")
        if cheap and data.get("resource_advantage_eligible", True):
            add(comparator, "RESOURCE_ADVANTAGE_B3", [], "Observed resource advantage independent of redundancy")
        if comparator == "B1" and comparable and (eq or harms):
            add(comparator, "NO_STRUCTURAL_ADVANTAGE", [], "Extra compute is sufficient at comparable resources")
        if not usage:
            reasons.append(comparator+":UNKNOWN_USAGE")
        if not normal:
            reasons.append(comparator+":RESOURCE_COMPARISON_NONEXECUTION")
    kinds = {x["kind"] for x in findings}
    if "HARM" in kinds and "BENEFIT" in kinds:
        outcome = "MIXED_TRADEOFF"
    elif "HARM" in kinds:
        outcome = "COUNTERPRODUCTIVE"
    elif "REDUNDANT" in kinds:
        outcome = "REDUNDANT"
    elif "NO_STRUCTURAL_ADVANTAGE" in kinds:
        outcome = "NO_STRUCTURAL_ADVANTAGE"
    elif c1_safe and all(k in by and by[k]["eligible"] and by[k]["usage_known"] for k in ("B1", "B2", "B4")) and len(by["B2"]["benefit"]) == 2 and by["B1"]["benefit"] and by["B4"]["benefit"] and by["B1"]["comparable"]:
        outcome = "PROMISING"
    else:
        outcome = None
    if outcome is None and not reasons:
        reasons.append("CI_OR_GUARD_UNRESOLVED")
    return dict(decision_status="CLASSIFIABLE" if outcome else "INSUFFICIENT_EVIDENCE",
        outcome_class=outcome, comparator_findings=findings, uncertainty_reasons=sorted(set(reasons)),
        unit="TRAJECTORY", author_corrections=["R1-E07-HARM-01"])
