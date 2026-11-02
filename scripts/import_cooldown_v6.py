#!/usr/bin/env python
"""Import verified cooldown_time.max values from the run-time research batch.

    python scripts/import_cooldown_v6.py RESULT_JSON

A value is imported only if the independent verifier accepted (or fixed) it AND its quote occurs word for word in the
local snapshot of the cited source AND the printed number occurs in the quote. Writes data/evidence/v6_cooldown.json and
updates the configuration's cooldown_time.max (never overwriting an already trusted value)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from v5_common import CACHE, number_in, quote_in  # noqa: E402

TRUSTED = {"manufacturer_specification", "experimental_observation", "reference_data"}


def _snapshot_title(sid):
    """The cited page's own <title> (or PDF title) from the snapshot metadata."""
    m = CACHE / f"{sid}.json"
    return json.loads(m.read_text(encoding="utf-8")).get("title") or None if m.exists() else None


def main(path):
    sys.stdout.reconfigure(encoding="utf-8")
    groups = json.loads(Path(path).read_text(encoding="utf-8"))["result"]["groups"]
    accepted, rejected = {}, []
    for g in groups:
        checks = {c["id"]: c for c in g["checks"]}
        for it in g["items"]:
            if it["status"] != "found":
                continue
            c = checks.get(it["id"])
            if not c or c["verdict"] == "reject":
                rejected.append((it["id"], "verifier: " + (c["reason"][:120] if c else "not checked")))
                continue
            value, unit, quote = it["value"], it["unit"], it["quote"]
            if c["verdict"] == "fix":
                value, unit, quote = c.get("fixed_value") or value, c.get("fixed_unit") or unit, c.get("fixed_quote") or quote
            snap = CACHE / f"{it.get('snapshot_id', '')}.txt"
            if not snap.exists():
                rejected.append((it["id"], "no local snapshot"))
                continue
            if not quote_in(snap.read_text(encoding="utf-8"), quote):
                rejected.append((it["id"], "quote not verbatim in snapshot"))
                continue
            if not number_in(quote, value):
                rejected.append((it["id"], f"value {value} not printed in quote"))
                continue
            if unit not in ("s", "min", "h", "d") or it.get("evidence_status") not in TRUSTED:
                rejected.append((it["id"], f"unit {unit} / status {it.get('evidence_status')}"))
                continue
            accepted[it["id"]] = {**it, "value": value, "unit": unit, "quote": quote}
    evidence, updated = [], []
    for f in sorted((ROOT / "data" / "cryostats").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for cfg in d["configurations"]:
            it = accepted.get(cfg["id"])
            if not it:
                continue
            ev_id = f"ev_v6_cool_{len(evidence) + 1:03d}"
            evidence.append({"id": ev_id, "claim": f"cooldown time of {cfg['id']}", "value_as_printed": it.get("value_as_printed"),
                             "normalized": f"{it['value']} {it['unit']}", "source_url": it.get("source_url"),
                             "document_title": it.get("document_title") or _snapshot_title(it.get("snapshot_id")), "location": it.get("location"), "quote": it["quote"],
                             "doi": it.get("doi"), "applies_to": cfg["id"], "evidence_status": it["evidence_status"],
                             "accessed": "2026-11-01", "snapshot_id": it.get("snapshot_id"),
                             "verification": "independent agent verifier + verbatim quote check against local snapshot",
                             "note": it.get("note")})
            cap = {"key": "cooldown_time.max", "value": {"kind": "min", "q": {"value": it["value"], "unit": it["unit"]}},
                   "install": "installed", "evidence_status": it["evidence_status"], "evidence_ids": [ev_id]}
            old = next((c for c in cfg["capabilities"] if c["key"] == "cooldown_time.max"), None)
            if old and old.get("evidence_status") in TRUSTED and old["value"].get("kind") != "unknown":
                evidence.pop()
                continue
            if old:
                cfg["capabilities"][cfg["capabilities"].index(old)] = cap
            else:
                cfg["capabilities"].append(cap)
            changed = True
            updated.append(cfg["id"])
        if changed:
            f.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "data" / "evidence" / "v6_cooldown.json").write_text(json.dumps(evidence, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"imported {len(updated)} cooldown times; rejected {len(rejected)}")
    for r in rejected:
        print("  rejected", *r)


if __name__ == "__main__":
    main(sys.argv[1])
