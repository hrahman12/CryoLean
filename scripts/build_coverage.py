#!/usr/bin/env python
"""Regenerate data/coverage.json (research coverage registry) from the catalog."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.catalog import Catalog  # noqa: E402
from backend.coverage import build_coverage  # noqa: E402


def main() -> int:
    cat = Catalog()
    cov = build_coverage(cat)
    out = cat.data_dir / "coverage.json"
    out.write_text(json.dumps(cov, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"industries known {cov['industries']['known']}, researched {cov['industries']['researched']}; "
          f"verified profiles {len(cov['experiment_profiles']['verified'])}; equipment families {len(cov['equipment_families'])}; "
          f"evidence records {cov['manufacturer_evidence']['records']}; unknown capabilities {len(cov['missing_scientific_data']['unknown_capabilities'])}; "
          f"unsupported requirement types {len(cov['unsupported_requirement_types'])}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
