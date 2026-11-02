"""Export read-only preview data through the real bridge, without verdicts/status.

Run from the repository root: python scripts/export_frontend_catalog.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cryolean.bridge import CryoLeanAPI


def export():
    api = CryoLeanAPI()

    def read(envelope):
        if envelope.get("ok") is not True:
            raise RuntimeError(envelope.get("error"))
        return envelope["data"]

    industries = read(api.list_industries())["industries"]
    experiments = read(api.list_experiments())["experiments"]
    equipment = read(api.list_equipment())["equipment"]
    profiles = {e["id"]: read(api.get_experiment_requirements(e["id"])) for e in experiments}
    details = {}
    for item in equipment:
        doc = read(api.get_equipment_details(item["id"]))
        for configuration in doc["configurations"]:
            details[configuration["id"]] = configuration
    seed_files = sorted((ROOT / "data").rglob("*.json"))
    seed_hash = hashlib.sha256(b"".join(p.read_bytes() for p in seed_files)).hexdigest()
    output = ROOT / "frontend/src/data/catalog.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "provenance": {"source": "CryoLeanAPI read-only catalog export", "seed_sha256": seed_hash,
                       "note": "Preview data only. Contains no compatibility outcomes or checker status."},
        "industries": industries, "experiments": experiments, "equipment": equipment,
        "profiles": profiles, "configurations": details,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Exported {len(experiments)} profiles and {len(details)} configurations to {output}")


if __name__ == "__main__":
    export()
