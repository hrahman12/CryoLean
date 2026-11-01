#!/usr/bin/env python
"""Regenerate data/coverage.json (research coverage registry) from the catalog database."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryolean import db  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402
from cryolean.coverage import build  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    db.ensure_database()
    cov = build(Catalog())
    out = ROOT / "data" / "coverage.json"
    out.write_text(json.dumps(cov, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    p = cov["physical_properties"]["by_status"]
    print(f"industries {cov['industries']['registered_or_known']} (researched {cov['industries']['researched']}); "
          f"profiles {cov['experiment_profiles']['available']}; equipment families {len(cov['equipment_families'])}; "
          f"evidence {cov['manufacturer_evidence']['records']}; properties {p}; "
          f"unknown capabilities {len(cov['missing_scientific_data']['unknown_capabilities'])}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
