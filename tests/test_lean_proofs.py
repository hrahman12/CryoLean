"""Genuine Lean proof compilation and audit."""
import re
import subprocess
from pathlib import Path

import pytest

from backend import lean_runner

LEAN = Path(__file__).resolve().parents[1] / "lean"

REQUIRED_THEOREMS = [
    "verdict_accept_sound", "verdict_accept_complete", "verdict_accept_iff", "verdict_reject_sound",
    "accept_no_unknown", "fail_implies_reject", "missing_capability_unknown", "not_installed_never_passes",
    "unknown_install_never_passes", "estimate_never_passes", "no_provenance_never_passes",
    "unknown_value_never_passes", "pass_implies_units_match", "unconfirmed_not_accept", "empty_not_accept",
    "satisfies_violates_exclusive", "run_binds_inputs", "verdict_industry_irrelevant", "checks_cover_requirements",
]


@pytest.mark.slow
def test_lake_build_compiles_all_proofs():
    """`lake build` re-checks every proof (no-op if up to date, still exits non-zero on any error)."""
    p = subprocess.run(["lake", "build"], cwd=LEAN, capture_output=True, text=True, timeout=1200)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    assert "error" not in p.stdout.lower().replace("errors", "")


def test_no_sorry_admit_or_custom_axioms():
    for f in (LEAN / "CryoLean").glob("*.lean"):
        text = f.read_text(encoding="utf-8")
        code = re.sub(r"/-.*?-/", "", text, flags=re.S)           # strip block comments / docstrings
        code = "\n".join(l.split("--")[0] for l in code.splitlines())
        assert not re.search(r"\bsorry\b", code), f"sorry in {f.name}"
        assert not re.search(r"\badmit\b", code), f"admit in {f.name}"
        assert not re.search(r"^\s*axiom\b", code, flags=re.M), f"custom axiom in {f.name}"
        assert "native_decide" not in code, f"native_decide in {f.name}"


def test_required_theorems_present():
    names = {t["name"] for t in lean_runner.proof_inventory()["theorems"]}
    missing = [t for t in REQUIRED_THEOREMS if t not in names]
    assert not missing, missing


@pytest.mark.slow
def test_axiom_audit_has_no_sorryAx():
    p = subprocess.run(["lake", "env", "lean", "Audit.lean"], cwd=LEAN, capture_output=True, text=True, timeout=600)
    assert p.returncode == 0, p.stderr
    lines = [l for l in p.stdout.splitlines() if "depends on axioms" in l or "does not depend" in l]
    assert len(lines) == len(REQUIRED_THEOREMS), p.stdout
    for l in lines:
        assert "sorryAx" not in l, l
        axioms = re.findall(r"\[(.*)\]", l)
        if axioms:
            assert set(a.strip() for a in axioms[0].split(",")) <= {"propext", "Classical.choice", "Quot.sound"}, l


def test_binary_selftest(lean_available):
    ok, out = lean_runner.selftest()
    assert ok, out
