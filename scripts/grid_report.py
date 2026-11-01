#!/usr/bin/env python
"""Run every experiment x configuration pair through the Lean checker and report the verdict split,
the yellow (NEED_MORE_INFORMATION) causes and per-configuration completeness.

    python scripts/grid_report.py [--db PATH] [--json OUT]

Set CRYOLEAN_LEAN_BIN to use a different checker binary."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryolean import completeness, db, lean_runner, serialize, verifier  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--rebuild", action="store_true", help="rebuild the database from data/ first")
    ap.add_argument("--json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.rebuild:
        db.build_database(db_path=Path(a.db) if a.db else None)
    cat = Catalog(a.db)
    exps, cfgs = sorted(cat.experiments), sorted(cat.configurations)
    pairs, meta = [], []
    for eid in exps:
        ex = serialize.working_experiment(cat, eid, None, None, True)
        for cid in cfgs:
            cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
            pairs.append((cd, ed))
            meta.append((eid, cid))
    res = lean_runner.check_batch(pairs)
    counts = Counter(r["verdict"] for r in res)
    causes, keys = Counter(), Counter()
    rows = []
    for (eid, cid), (cd, ed), r in zip(meta, pairs, res):
        g = completeness.classify(cd, ed, r)
        rows.append({"experiment": eid, "configuration": cid, "verdict": r["verdict"], "config_gaps": g["configuration"],
                     "experiment_gaps": g["experiment"]})
        if r["verdict"] == "NEED_MORE_INFORMATION":
            causes["cryostat data missing" if g["configuration"] else "experiment value missing"] += 1
            for k in g["configuration"] + g["experiment"]:
                keys[k.split(" (")[0]] += 1
    n = len(res)
    print(f"{n} pairs: MET {counts['REQUIREMENTS_MET']} ({counts['REQUIREMENTS_MET'] / n:.0%}) | "
          f"NOT MET {counts['DOES_NOT_MEET_REQUIREMENTS']} ({counts['DOES_NOT_MEET_REQUIREMENTS'] / n:.0%}) | "
          f"NEED INFO {counts['NEED_MORE_INFORMATION']} ({counts['NEED_MORE_INFORMATION'] / n:.0%})")
    print("yellow causes:", dict(causes))
    print("top missing:", keys.most_common(15))
    per_exp = {}
    for r in rows:
        per_exp.setdefault(r["experiment"], Counter())[r["verdict"]] += 1
    for e, c in per_exp.items():
        print(f"  {e:46} MET {c['REQUIREMENTS_MET']:2}  NOT {c['DOES_NOT_MEET_REQUIREMENTS']:2}  INFO {c['NEED_MORE_INFORMATION']:2}")
    if a.json:
        Path(a.json).write_text(json.dumps({"counts": counts, "rows": rows}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
