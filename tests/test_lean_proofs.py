"""Genuine Lean compilation, proof audit and runtime self-test."""
import re
import subprocess
from pathlib import Path

import pytest

from cryolean import lean_runner

LEAN = Path(__file__).resolve().parents[1] / "lean"
REQUIRED = [
    "verdict_accept_sound", "accept_all_coupled", "verdict_accept_complete", "verdict_accept_iff", "verdict_reject_sound",
    "verdict_reject_complete", "accept_no_unknown", "missing_capability_unknown", "unknown_value_never_passes",
    "estimate_never_passes", "no_provenance_never_passes", "cap_not_usable_missing", "fail_implies_reject",
    "violation_prevents_accept", "verdict_ignores_optional", "verdict_ignores_nonapplicable", "condition_false_not_applicable",
    "not_installed_never_passes", "unknown_install_never_passes", "run_binds_inputs", "verdict_deterministic",
    "run_reports_everything", "candidates_accept_sound", "candidates_verdicts_are_lean", "verdict_industry_irrelevant",
    "verdict_name_irrelevant", "pass_implies_dims_match", "coupled_pass_dims_match", "Q.le_scale_left", "Q.le_scale_right",
    "evalExpr_sound", "evalExpr_complete", "satisfies_spec_exclusive",
    # forensics fix: rejections rest on trusted evidence; dimensions for every constraint shape
    "fail_needs_trusted", "untrusted_never_passes", "untrusted_never_fails", "pass_dims_all_match",
    # campaign scheduling
    "validSchedule_sound", "validSchedule_complete", "validSchedule_bounds", "validSchedule_disjoint",
    "validSchedule_only_accepted", "validSchedule_rejects_unaccepted", "resolve_ids",
]


@pytest.mark.slow
def test_lake_build_compiles_every_proof():
    p = subprocess.run(["lake", "build"], cwd=LEAN, capture_output=True, text=True, timeout=1800)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]


def test_no_sorry_admit_axiom_or_native_decide():
    inv = lean_runner.theorem_inventory()
    assert inv["unproved_or_unsafe_markers"] == []


def test_required_theorems_present():
    names = {t["name"] for t in lean_runner.theorem_inventory()["theorems"]}
    short = {n.split(".")[-1] for n in names} | names
    missing = [t for t in REQUIRED if t not in short and t.split(".")[-1] not in short]
    assert not missing, missing


@pytest.mark.slow
def test_axiom_audit_standard_axioms_only():
    p = subprocess.run(["lake", "env", "lean", "Audit.lean"], cwd=LEAN, capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stderr
    lines = [l for l in p.stdout.splitlines() if "axioms" in l]
    assert len(lines) == len(REQUIRED), p.stdout
    for l in lines:
        assert "sorryAx" not in l
        found = re.findall(r"\[(.*)\]", l)
        if found:
            assert {a.strip() for a in found[0].split(",")} <= {"propext", "Classical.choice", "Quot.sound"}, l


def test_runtime_binary_selftest(lean_available):
    ok, out = lean_runner.selftest()
    assert ok, out


def test_audit_cache_matches_sources():
    """lean/audit-axioms.json must be regenerated (scripts/audit_axioms.py) whenever the trusted sources change."""
    audit = lean_runner.axiom_audit()
    assert audit["status"] == "current", "run: python scripts/audit_axioms.py"
    assert audit["all_standard"] and set(audit["theorems"]) >= {t for t in REQUIRED}
