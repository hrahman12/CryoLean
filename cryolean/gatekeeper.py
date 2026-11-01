"""Gatekeeper: admits proposed Lean code (from an LLM, from Lanyon's exported proofs, from a person)
into the rule Registry only if it is checked.

A candidate passes only if ALL hold:
1. no escape hatches in the source: sorry, admit, native_decide/bv_decide, `axiom`, `opaque`, unsafe,
   implemented_by, extern, debug.skipKernelTC, #exit, maxHeartbeats 0 (disabled style linters are recorded as warnings);
2. it compiles with `lake env lean` against the CryoLean project (CryoLean importable);
3. `#print axioms` of every theorem it declares is a subset of {propext, Classical.choice, Quot.sound};
4. (when the for-all-dev/forensics checkout is present) its static smells are recorded with the entry.

Admitted rules go to the `rule_registry` table with the source SHA-256, theorem names and axioms.
Nothing in the Registry changes how a verdict is computed: the Lean checker is fixed; admitted rules are
additional proven facts (e.g. a Lanyon scheme property) that evidence records may cite.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from pathlib import Path

from . import config, db, lean_runner
from .catalog import Catalog

STANDARD = {"propext", "Classical.choice", "Quot.sound"}
ESCAPE_HATCHES = [
    (r"\bsorry\b", "sorry"), (r"\badmit\b", "admit"), (r"\bnative_decide\b", "native_decide"),
    (r"\bbv_decide\b", "bv_decide"), (r"^\s*(private\s+|noncomputable\s+)*axiom\b", "axiom declaration"),
    (r"^\s*opaque\b", "opaque"), (r"\bunsafe\b", "unsafe"), (r"implemented_by", "implemented_by"),
    (r"@\[\s*extern", "extern"), (r"debug\.skipKernelTC", "debug.skipKernelTC"), (r"^\s*#exit\b", "#exit"),
    (r"maxHeartbeats\s+0\b", "unbounded heartbeats"),
]
# Recorded with the entry but not blocking: they do not change what the kernel accepts.
WARNINGS = [(r"set_option\s+linter\.[\w.]+\s+false", "style linter disabled")]

SCHEMA = """
CREATE TABLE IF NOT EXISTS rule_registry (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE, proposer TEXT NOT NULL,
    admitted_at TEXT NOT NULL, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS gatekeeper_log (
    id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, admitted INTEGER NOT NULL, created_at TEXT NOT NULL, doc TEXT NOT NULL);
"""


def _strip_comments(src: str) -> str:
    src = re.sub(r"/-.*?-/", " ", src, flags=re.S)
    return "\n".join(line.split("--")[0] for line in src.splitlines())


def _theorem_names(src: str) -> list[str]:
    """Fully qualified names of the declared theorems/lemmas, following nested `namespace ... end` blocks."""
    stack, names = [], []
    for line in _strip_comments(src).splitlines():
        m = re.match(r"^\s*namespace\s+([\w.]+)", line)
        if m:
            stack.append(m.group(1))
            continue
        m = re.match(r"^\s*end\s+([\w.]+)\s*$", line)
        if m and stack and stack[-1] == m.group(1):
            stack.pop()
            continue
        m = re.match(r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+)?(?:theorem|lemma)\s+([\w.']+)", line)
        if m:
            names.append(".".join(stack + [m.group(1)]))
    return names


def check(source: str) -> dict:
    """Run the gate on a Lean source text. Returns a report; `admissible` is True only if every check passes."""
    report = {"sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(), "escape_hatches": [], "compiled": False,
              "compile_output": "", "theorems": {}, "nonstandard": {}, "admissible": False}
    code = _strip_comments(source)
    for pat, name in ESCAPE_HATCHES:
        if re.search(pat, code, flags=re.M):
            report["escape_hatches"].append(name)
    report["warnings"] = [name for pat, name in WARNINGS if re.search(pat, code, flags=re.M)]
    names = _theorem_names(source)
    report["declared_theorems"] = names
    uses_mathlib = bool(re.search(r"^\s*import\s+Mathlib", code, flags=re.M))
    workspace = config.LEAN_DIR
    if uses_mathlib:
        mw = os.environ.get("CRYOLEAN_MATHLIB_PROJECT") or str(config.ROOT / ".tools" / "mathlib-gate")
        if not mw or not (Path(mw) / "lakefile.toml").exists() and not (Path(mw) / "lakefile.lean").exists():
            report["reason"] = ("imports Mathlib; set CRYOLEAN_MATHLIB_PROJECT to a Lake project that depends on Mathlib "
                                "(same toolchain, `lake exe cache get` done) so the Gatekeeper can compile it")
            report["workspace"] = None
            report["forensics"] = _forensics_note()
            return report
        workspace = Path(mw)
    report["workspace"] = str(workspace)
    if not names:
        report["reason"] = "no theorem declared"
        return report
    with tempfile.TemporaryDirectory(prefix="cryolean_gate_") as d:
        f = Path(d) / "Candidate.lean"
        f.write_text(source + "\n\n" + "\n".join(f"#print axioms {n}" for n in names) + "\n", encoding="utf-8")
        rc, out, err = lean_runner.run_lean_file(f, cwd=workspace)
    report["compile_output"] = (out + err)[-20000:]
    report["compiled"] = rc == 0 and not re.search(r"\berror\b", out)
    for line in out.splitlines():
        m = re.match(r"'([^']+)' (depends on axioms: \[(.*)\]|does not depend on any axioms)", line.strip())
        if m:
            ax = [a.strip() for a in (m.group(3) or "").split(",") if a.strip()]
            report["theorems"][m.group(1)] = ax
            extra = sorted(set(ax) - STANDARD)
            if extra:
                report["nonstandard"][m.group(1)] = extra
    missing = [n for n in names if not any(k == n or k.endswith("." + n) for k in report["theorems"])]
    report["admissible"] = (report["compiled"] and not report["escape_hatches"] and not report["nonstandard"]
                            and not missing)
    if not report["admissible"]:
        reasons = []
        if report["escape_hatches"]:
            reasons.append("escape hatches: " + ", ".join(report["escape_hatches"]))
        if not report["compiled"]:
            errs = [re.sub(r"^.*Candidate\.lean:", "line ", l.strip()) for l in report["compile_output"].splitlines() if "error" in l]
            report["compile_errors"] = len(errs)
            reasons.append(f"does not compile ({len(errs)} Lean error(s); first: " + " | ".join(errs[:3]) + ")")
        if report["nonstandard"]:
            reasons.append("non-standard axioms: " + json.dumps(report["nonstandard"]))
        if missing and report["compiled"]:
            reasons.append("axioms not printed for: " + ", ".join(missing))
        report["reason"] = "; ".join(reasons)
    report["forensics"] = _forensics_note()
    return report


def _forensics_note() -> dict:
    fx = config.ROOT / ".tools" / "forensics"
    return {"available": fx.exists(), "path": str(fx) if fx.exists() else None,
            "note": "Run scripts/run_forensics.py for the full for-all-dev/forensics static report and judge indicators."}


def submit(catalog: Catalog, name: str, source: str, proposer: str) -> dict:
    """Gate a proposal and, if it passes, admit it to the Registry. Returns {admitted, report, entry}."""
    rep = check(source)
    con = catalog.connect()
    con.executescript(SCHEMA)
    with con:
        con.execute("INSERT INTO gatekeeper_log VALUES (?,?,?,?,?)",
                    ("gk_" + uuid.uuid4().hex[:10], rep["sha256"], int(rep["admissible"]), db.now(),
                     db.dumps({"name": name, "proposer": proposer, "report": rep})))
        entry = None
        if rep["admissible"]:
            existing = con.execute("SELECT doc FROM rule_registry WHERE sha256 = ?", (rep["sha256"],)).fetchone()
            if existing:
                entry = json.loads(existing["doc"])
            else:
                entry = {"id": "rule_" + uuid.uuid4().hex[:10], "name": name, "sha256": rep["sha256"], "proposer": proposer,
                         "admitted_at": db.now(), "theorems": rep["theorems"], "source": source}
                con.execute("INSERT INTO rule_registry VALUES (?,?,?,?,?,?)",
                            (entry["id"], name, rep["sha256"], proposer, entry["admitted_at"], db.dumps(entry)))
    con.close()
    return {"admitted": rep["admissible"], "report": rep, "entry": entry}


def registry(catalog: Catalog) -> list[dict]:
    con = catalog.connect()
    con.executescript(SCHEMA)
    try:
        return [json.loads(r["doc"]) for r in con.execute("SELECT doc FROM rule_registry ORDER BY admitted_at")]
    finally:
        con.close()


def admitted(catalog: Catalog, sha256: str) -> bool:
    con = catalog.connect()
    con.executescript(SCHEMA)
    try:
        return con.execute("SELECT 1 FROM rule_registry WHERE sha256 = ?", (sha256,)).fetchone() is not None
    finally:
        con.close()
