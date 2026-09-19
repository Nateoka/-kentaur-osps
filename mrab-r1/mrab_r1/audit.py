"""Immutable checker provenance, with separately authorized runtime correction."""
from copy import deepcopy
import importlib.util
import json
from .canonical import loads, raw_sha
from .schemas import DESIGN


def design_checker():
    path = DESIGN / "design_tools" / "contract_checks.py"
    spec = importlib.util.spec_from_file_location("mrab_frozen_design_checker", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def e07_conflict():
    goldens = loads((DESIGN / "design_checks" / "goldens.json").read_bytes())
    # Keep every comparator/condition present: this is not a malformed or
    # incomplete summary. Derive new authored input, never overwrite a golden.
    source = next(case for case in goldens["summary_cases"] if case["id"] == "WIDE-CI")
    summary = deepcopy(source["input"])
    row = summary["comparators"]["B2"]["C3"]
    row.update(n_pairs=8, primary_ci=None, point=None, reach=[0, 0],
               accuracy_loss=[.10, .15], fixed_ci=[.10, .15], completion_loss=[0, .01])
    result = design_checker().classify_summary(summary)
    has_harm = any(f["kind"] == "HARM" and f["comparator"] == "B2" for f in result["comparator_findings"])
    return dict(issue_id="E07-MISSING-PRIMARY-HIDES-FIXED-HARM", kind="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT",
        source_golden="WIDE-CI (copied, not modified)", input=summary,
        existing_checker_result=result,
        textual_contract_requirement=dict(comparator="B2", kind="HARM", condition="C3",
            basis="E07: accuracy_loss.lower > .02 or fixed.lower > .05; known independent findings retained despite missing CI"),
        reproduced=not has_harm,
        expected_requirement_is_new_authorized_golden=False,
        runtime_resolution="R1-E07-HARM-01 — AUTHOR_APPROVED_RUNTIME_CORRECTION",
        status="RESOLVED_SOURCE_CHECKER_DEFECT" if not has_harm else "NOT_REPRODUCED")


def verify_immutable_against(parent_root):
    from pathlib import Path
    parent = Path(parent_root)
    mismatches = []
    files = [p for p in DESIGN.rglob("*") if p.is_file()]
    for p in files:
        relative = p.relative_to(DESIGN)
        origin = parent / relative
        if not origin.is_file() or raw_sha(origin.read_bytes()) != raw_sha(p.read_bytes()):
            mismatches.append(relative.as_posix())
    return dict(files_checked=len(files), mismatches=mismatches)
