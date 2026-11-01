#!/usr/bin/env python
"""Decide every experiment x configuration pair with the Lean checker and store the outcomes (table grid).

    python scripts/build_grid.py [--db PATH] [--rebuild] [--workers N]

Set CRYOLEAN_LEAN_BIN to use a different checker binary."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryolean import db, grid  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--rebuild", action="store_true", help="rebuild the database from data/ first")
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.rebuild:
        db.build_database(db_path=Path(a.db) if a.db else None)
    cat = Catalog(a.db)
    print(len(cat.experiments), "experiments x", len(cat.configurations), "configurations", flush=True)
    t = time.time()
    m = grid.build(cat, n_workers=a.workers)
    s = grid.summary(cat)
    print(f"{m['pairs']} pairs in {time.time() - t:.0f} s: {s['overall']}")
    for ind, c in s["industries"].items():
        print(f"  {ind:42} met {c['met']:5}  not {c['not_met']:6}  info {c['need_info']:5}")


if __name__ == "__main__":
    main()
