#!/usr/bin/env python
"""Run `lake env lean Audit.lean` and cache the axioms of every audited theorem in lean/audit-axioms.json,
together with the source hash, so every verdict card can cite theorem names + axioms + source hash.
Fails (exit 1) if any theorem depends on sorryAx or a non-standard axiom."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryolean import lean_runner  # noqa: E402

STANDARD = {"propext", "Classical.choice", "Quot.sound"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = subprocess.run(["lake", "env", "lean", "Audit.lean"], cwd=ROOT / "lean", capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print(p.stdout, p.stderr)
        return 1
    theorems, bad = {}, []
    for line in p.stdout.splitlines():
        m = re.match(r"'CryoLean\.([^']+)' (depends on axioms: \[(.*)\]|does not depend on any axioms)", line.strip())
        if not m:
            continue
        axioms = [a.strip() for a in (m.group(3) or "").split(",") if a.strip()]
        theorems[m.group(1)] = axioms
        if not set(axioms) <= STANDARD:
            bad.append((m.group(1), axioms))
    out = {"source_hash": lean_runner.source_hash(), "standard_axioms": sorted(STANDARD), "theorems": theorems,
           "all_standard": not bad, "count": len(theorems)}
    lean_runner.AUDIT_FILE.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"audited {len(theorems)} theorems; all standard axioms: {not bad}; wrote {lean_runner.AUDIT_FILE}")
    for name, ax in bad:
        print("NON-STANDARD:", name, ax)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
