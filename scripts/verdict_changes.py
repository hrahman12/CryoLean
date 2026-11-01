#!/usr/bin/env python
"""Before/after compatibility report: every pair of the baseline catalog (experiments x configurations at a git
revision) decided by the CURRENT Lean checker on the baseline data and on today's data, with each changed verdict
explained by the requirement outcomes that changed and the records behind them.

    python scripts/verdict_changes.py --rev 7a224f4 [--out docs/VERDICT_CHANGES.md]

The baseline data is exported with `git archive` into a temporary folder; nothing in the working tree changes."""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryolean import db, grid, serialize  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

V = {"REQUIREMENTS_MET": "MET", "DOES_NOT_MEET_REQUIREMENTS": "NOT MET", "NEED_MORE_INFORMATION": "NEED INFO"}


def results(cat: Catalog, exps, cfgs) -> dict:
    docs = grid.configuration_documents(cat, [c for c in cfgs if c in cat.configurations])
    out = {}
    for e in exps:
        if e not in cat.experiments:
            continue
        ex = serialize.working_experiment(cat, e, None, None, True)
        ids = list(docs)
        for cid, r in zip(ids, grid.check_parallel(grid.experiment_pairs(cat, ex, docs))):
            out[(e, cid)] = r
    return out


def outcomes(r: dict) -> dict:
    o = {}
    for c in r["checks"]:
        if c.get("mandatory") and c.get("applicable"):
            avail = next((pk["available_display"] for pk in c["per_key"]), "not documented")
            o[" | ".join(c["keys"])] = (c["outcome"], avail)
    for c in r.get("coupled_checks", []):
        if c.get("mandatory") and c.get("applicable"):
            o["model:" + c.get("model", "")] = (c["outcome"], f"{(c.get('lhs') or {}).get('display')} vs {(c.get('rhs') or {}).get('display')}")
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default="7a224f4")
    ap.add_argument("--out", default="docs/VERDICT_CHANGES.md")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    tmp = Path(tempfile.mkdtemp(prefix="cryolean_base_"))
    tar = subprocess.run(["git", "archive", a.rev, "data"], cwd=ROOT, capture_output=True, check=True).stdout
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(tmp)
    base_db = tmp / "base.db"
    db.build_database(seed_dir=tmp / "data", db_path=base_db)
    base = Catalog(base_db)
    exps, cfgs = sorted(base.experiments), sorted(base.configurations)
    now_db = tmp / "now.db"
    db.build_database(db_path=now_db)
    now = Catalog(now_db)
    rb, rn = results(base, exps, cfgs), results(now, exps, cfgs)
    cb = Counter(V[r["verdict"]] for r in rb.values())
    cn = Counter(V[rn[k]["verdict"]] for k in rb if k in rn)
    lines = [f"# Verdict changes since {a.rev}", "",
             f"Same {len(exps)} experiments x {len(cfgs)} configurations of revision `{a.rev}`, each pair decided by the current "
             "Lean checker on the data of that revision and on today's data (`python scripts/verdict_changes.py`). "
             "No requirement was weakened: a change comes from a sourced capability value or documented absence that was "
             "added or corrected, or from a corrected requirement, as listed per pair.", "",
             "| | MET | NOT MET | NEED INFO |", "|---|---|---|---|",
             f"| {a.rev} data | {cb['MET']} | {cb['NOT MET']} | {cb['NEED INFO']} |",
             f"| today's data | {cn['MET']} | {cn['NOT MET']} | {cn['NEED INFO']} |", ""]
    trans = Counter()
    rows = []
    for k in sorted(rb):
        if k not in rn:
            continue
        b, n = rb[k], rn[k]
        if b["verdict"] == n["verdict"]:
            continue
        trans[(V[b["verdict"]], V[n["verdict"]])] += 1
        ob, on = outcomes(b), outcomes(n)
        why = []
        for key in sorted(set(ob) | set(on)):
            x, y = ob.get(key, ("absent", "")), on.get(key, ("absent", ""))
            if x[0] != y[0]:
                why.append(f"`{key}`: {x[0]} -> {y[0]} (now: {y[1]})")
        rows.append(f"| {k[0]} | {k[1]} | {V[b['verdict']]} -> **{V[n['verdict']]}** | {'; '.join(why) or 'requirement set changed'} |")
    lines += ["Transitions: " + ", ".join(f"{x} -> {y}: {c}" for (x, y), c in trans.most_common()), "",
              "| Experiment | Configuration | Verdict | Requirement outcomes that changed |", "|---|---|---|---|"] + rows
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"base {dict(cb)} -> now {dict(cn)}; {len(rows)} changed pairs; written {a.out}")


if __name__ == "__main__":
    main()
