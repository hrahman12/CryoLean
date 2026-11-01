#!/usr/bin/env python
"""Import the verified 20-industry expansion (research/v4/result.json, workflow cryolean-industry-expansion) into data/.

    python scripts/import_research_v4.py [--dry-run]

Rules (each record was re-fetched by an independent verifier agent):
* vocabulary: new keys from the vocabulary designer are added; existing keys are never changed.
* experiments: a profile is imported only if every MANDATORY requirement was accepted (a verifier fixed_value replaces
  the constraint); rejected optional requirements are dropped. Profiles a verifier flagged as duplicates are skipped,
  and so are ids already in data/experiments.
* machines: an accepted capability keeps its value (or the verifier's fixed_value); a rejected one is written as
  UNKNOWN with evidence_status unknown, so it can only produce NEED_MORE_INFORMATION, never a pass or a fail. The same
  equipment researched for several industries is merged (first verified configuration wins).
* every requirement and capability gets an evidence record with the verbatim quote, URL, location and the verifier note.
Files: data/experiments/v4_<id>.json, data/cryostats/v4_<equipment>.json, data/evidence/v4_<industry>.json."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ACCESSED = "2026-11-01"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    res = json.loads((ROOT / "research/v4/result.json").read_text(encoding="utf-8"))
    vocab_path = DATA / "capability_vocabulary.json"
    vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
    added_keys = []
    for k in res["vocab"]["new_keys"]:
        if k["key"] not in vocab["keys"]:
            vocab["keys"][k["key"]] = {"shape": k["shape"], "unit": k.get("unit") or "", "better": k.get("better", "none"),
                                       "description": k["description"], "status": "established",
                                       "proposed_by": "research/v4/vocabulary.json"}
            added_keys.append(k["key"])

    existing_exp = {json.loads(p.read_text(encoding="utf-8"))["id"] for p in (DATA / "experiments").glob("*.json")}
    existing_cfg, existing_eq = set(), set()
    for p in (DATA / "cryostats").glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        existing_eq.add(d["id"])
        existing_cfg |= {c["id"] for c in d["configurations"]}

    stats = Counter()
    exp_out, eq_out, ev_out = {}, {}, {}
    plain_seen = set()
    for block in res["results"]:
        ind = block["industry"]
        evs = ev_out.setdefault(ind, [])
        vexp = {v["ref"]: v for v in (block["vexp"] or {}).get("results", [])}
        dup_ids = {d.split()[0] for d in (block["vexp"] or {}).get("duplicates", [])}
        for e in (block["exp"] or {}).get("experiments", []):
            if e["id"] in existing_exp or e["id"] in exp_out or e["id"] in dup_ids:
                stats["experiments skipped (duplicate)"] += 1
                continue
            reqs, ok = [], True
            for i, r in enumerate(e["requirements"]):
                v = vexp.get(f"{e['id']}#{i}")
                if not v or not v["accept"]:
                    if v and v.get("fixed_value") and v["fixed_value"].get("kind"):
                        r = {**r, "constraint": v["fixed_value"]}
                    elif r["mandatory"]:
                        ok = False
                        break
                    else:
                        stats["optional requirements dropped"] += 1
                        continue
                elif v.get("fixed_value") and v["fixed_value"].get("kind"):
                    r = {**r, "constraint": v["fixed_value"]}
                evid = f"v4e_{e['id']}_{i}"
                evs.append({"id": evid, "claim": r["rationale"], "value_as_printed": json.dumps(r["constraint"]),
                            "quote": r["quote"], "source_url": r["source_url"], "document_title": r["document_title"],
                            "location": r["location"], "evidence_status": r.get("evidence_status") or "experimental_observation",
                            "accessed": r.get("accessed") or ACCESSED, "applies_to": e["id"],
                            "verification": {"by": "independent verifier agent (research/v4)", "accepted": True,
                                             "note": (v or {}).get("note", "")}})
                req = {"constraint": r["constraint"], "mandatory": bool(r["mandatory"]), "applicable": True,
                       "origin": r.get("evidence_status") or "experimental_observation", "rationale": r["rationale"],
                       "evidence_ids": [evid], "conditions": []}
                if len(r["keys"]) == 1:
                    req["key"] = r["keys"][0]
                else:
                    req["keys"] = r["keys"]
                reqs.append(req)
            if not ok or not reqs:
                stats["experiments skipped (a mandatory requirement was not verified)"] += 1
                continue
            plain = e["plain_name"].strip()
            if plain.lower() in plain_seen:
                stats["experiments skipped (plain name repeats)"] += 1
                continue
            plain_seen.add(plain.lower())
            exp_out[e["id"]] = {
                "id": e["id"], "name": e["name"], "plain_name": plain, "industry": ind, "description": e["description"],
                "keywords": [plain, ind], "sources": [{"citation": s["citation"], "url": s["url"], "accessed": ACCESSED} for s in e["sources"]],
                "reported_conditions": [], "reported_equipment": e.get("reported_equipment", []), "requirements": reqs,
                "params": [], "coupled": [], "missing_information": [], "confirmed": True,
                "confirmation_note": "Requirements taken from the cited procedure and independently re-verified against the source "
                                     "(research/v4, 2026-11-01). Users must confirm them for their own run; edits require confirmation again.",
                "source": "research/v4"}
            stats["experiments imported"] += 1

        veq = {v["ref"]: v for v in (block["veq"] or {}).get("results", [])}
        for eq in (block["eq"] or {}).get("equipment", []):
            eid = slug(eq["id"])
            if eid in existing_eq:
                stats["equipment skipped (already in catalog)"] += 1
                continue
            rec = eq_out.setdefault(eid, {"id": eid, "manufacturer": eq["manufacturer"], "model": eq["model"], "family": eq["family"],
                                          "description": eq["description"], "documents": [], "configurations": [], "unknowns": [],
                                          "modeling_notes": "Imported from research/v4 (20-industry expansion); every value re-verified by an independent agent.",
                                          "industries": []})
            if ind not in rec["industries"]:
                rec["industries"].append(ind)
            for d in eq["documents"]:
                if d["url"] not in {x["url"] for x in rec["documents"]}:
                    rec["documents"].append({"id": f"doc_{eid}_{len(rec['documents'])}", "url": d["url"], "title": d["title"], "accessed": ACCESSED})
            have = {c["id"] for c in rec["configurations"]}
            for cfg in eq["configurations"]:
                cid = slug(cfg["id"])
                if cid in have or cid in existing_cfg:
                    stats["configurations skipped (duplicate)"] += 1
                    continue
                caps = []
                for c in cfg["capabilities"]:
                    v = veq.get(f"{cfg['id']}#{c['key']}")
                    value = (v.get("fixed_value") if v and v.get("fixed_value") and v["fixed_value"].get("kind") else c["value"])
                    evid = f"v4c_{cid}_{c['key']}"
                    accepted = bool(v and v["accept"]) or bool(v and v.get("fixed_value") and v["fixed_value"].get("kind"))
                    absence = c["install"] in ("not_available", "optional_not_installed")   # documented absence/option: value not needed
                    if accepted and c["evidence_status"] != "unknown" and (value.get("kind") != "unknown" or absence):
                        caps.append({"key": c["key"], "value": value, "install": c["install"], "evidence_status": c["evidence_status"],
                                     "evidence_ids": [evid]})
                        stats["capabilities verified"] += 1
                        evs.append({"id": evid, "claim": c["claim"], "value_as_printed": c["value_as_printed"], "quote": c["quote"],
                                    "source_url": c["source_url"], "document_title": c["document_title"], "location": c["location"],
                                    "evidence_status": c["evidence_status"], "accessed": ACCESSED, "applies_to": cid,
                                    "verification": {"by": "independent verifier agent (research/v4)", "accepted": True, "note": v.get("note", "")}})
                    else:
                        caps.append({"key": c["key"], "value": {"kind": "unknown"}, "install": "unknown", "evidence_status": "unknown", "evidence_ids": []})
                        rec["unknowns"].append({"configuration_id": cid, "key": c["key"],
                                                "why": (v or {}).get("note") or "not verified"})
                        stats["capabilities left UNKNOWN (not verified)"] += 1
                seen, uniq = set(), []
                for c in caps:
                    if c["key"] not in seen:
                        seen.add(c["key"]); uniq.append(c)
                rec["configurations"].append({"id": cid, "name": cfg["name"], "configuration_basis": cfg["configuration_basis"], "capabilities": uniq})
                have.add(cid)
                stats["configurations imported"] += 1

    print(dict(stats))
    print("new vocabulary keys:", len(added_keys))
    if a.dry_run:
        return
    vocab_path.write_text(json.dumps(vocab, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for eid, e in exp_out.items():
        (DATA / "experiments" / f"v4_{eid}.json").write_text(json.dumps(e, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for eid, eq in eq_out.items():
        if eq["configurations"]:
            (DATA / "cryostats" / f"v4_{eid}.json").write_text(json.dumps(eq, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for ind, evs in ev_out.items():
        if evs:
            (DATA / "evidence" / f"v4_{ind}.json").write_text(json.dumps(evs, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("written:", len(exp_out), "experiments,", sum(1 for e in eq_out.values() if e["configurations"]), "equipment files")


if __name__ == "__main__":
    main()
