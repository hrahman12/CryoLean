#!/usr/bin/env python
"""Export the 20 industries x 3 experiments x 3 configurations (from research/expansion/*_manifest.json) with the
Lean checker's verdict for every pairing to site/data.json, the data file of the static CryoLean site.

    python scripts/export_site_data.py [--db PATH]"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryolean import db, grid, lean_runner, serialize  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

MANIFESTS = ["a_manifest.json", "b_manifest.json", "c_manifest.json"]
NAMES = {"scientific_research": "Scientific research", "healthcare_and_medicine": "Healthcare and medicine",
         "biology_and_biotechnology": "Biology and biotechnology", "chemistry_and_pharmaceuticals": "Chemistry and pharmaceuticals",
         "materials_and_nanotechnology": "Materials and nanotechnology", "quantum_computing_and_sensing": "Quantum computing and sensing",
         "physics_and_particle_accelerators": "Physics and particle accelerators", "aerospace_and_space_exploration": "Aerospace and space exploration",
         "astronomy_and_astrophysics": "Astronomy and astrophysics", "semiconductors_and_electronics": "Semiconductors and electronics",
         "photonics_and_telecommunications": "Photonics and telecommunications", "energy_and_hydrogen": "Energy and hydrogen",
         "nuclear_engineering_and_fusion": "Nuclear engineering and fusion", "manufacturing_and_industrial_processing": "Manufacturing and industrial processing",
         "automotive_and_transportation": "Automotive and transportation", "food_and_agriculture": "Food and agriculture",
         "environmental_science": "Environmental science", "geology_and_oceanography": "Geology and oceanography",
         "metrology_and_calibration": "Metrology and calibration", "defense_and_security": "Defense and security"}


def group(keys: list[str]) -> str:
    """The three questions on the page: cold enough, does the sample fit, right equipment."""
    k = keys[0]
    if k.startswith(("temperature.", "cooling_power", "probe.temperature", "condenser.temperature", "trap.")):
        return "cold"
    if k.startswith(("sample.", "carrier.", "milling.jar", "optical.clear_aperture", "chamber.")):
        return "fit"
    return "equipment"


def _has_grid(cat) -> bool:
    con = cat.connect()
    try:
        return con.execute("SELECT COUNT(*) FROM grid").fetchone()[0] > 0
    except Exception:
        return False
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--keep-grid", action="store_true", help="use the database as built (with its stored grid) instead of rebuilding")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    dbp = Path(a.db) if a.db else None
    ap_grid = a.keep_grid
    if not ap_grid:
        db.build_database(db_path=dbp)
    cat = Catalog(dbp)
    industries, scenes = [], {}
    for f in MANIFESTS:
        m = json.loads((ROOT / "research/expansion" / f).read_text(encoding="utf-8"))
        scenes.update(m.get("experiment_scenes", {}))
    # featured set: 3 experiments x 3 machines per industry, no machine used twice (scripts/select note in the file)
    sel = json.loads((ROOT / "research/v4/site_selection.json").read_text(encoding="utf-8"))
    industries = [{"id": k, "experiment_ids": v["experiment_ids"], "configuration_ids": v["configuration_ids"]} for k, v in sel.items()]
    order = list(NAMES)
    industries.sort(key=lambda i: order.index(i["id"]))
    cfg_ids = sorted({c for i in industries for c in i["configuration_ids"]})
    missing = [c for c in cfg_ids if c not in cat.configurations] + \
              [e for i in industries for e in i["experiment_ids"] if e not in cat.experiments]
    if missing:
        sys.exit(f"ids in the manifests but not in the catalog: {missing}")
    cfgs = grid.configuration_documents(cat, cfg_ids)
    pairs, meta = [], []
    for ind in industries:
        for eid in ind["experiment_ids"]:
            ex = serialize.working_experiment(cat, eid, None, None, True)
            for cid in ind["configuration_ids"]:
                cm, cd = cfgs[cid]
                pairs.append((cd, serialize.experiment_doc(cat, ex, cm)[0]))
                meta.append((ind["id"], eid, cid))
    results = grid.check_parallel(pairs)
    verdicts, counts = {}, Counter()
    for (iid, eid, cid), r in zip(meta, results):
        counts[r["verdict"]] += 1
        checks = []
        for c in r["checks"]:
            if not c.get("applicable"):
                continue
            avail = next((pk["available_display"] for pk in c["per_key"] if pk["outcome"] == "pass"),
                         c["per_key"][0]["available_display"] if c["per_key"] else "not documented")
            checks.append({"group": group(c["keys"]), "keys": c["keys"], "outcome": c["outcome"], "mandatory": c["mandatory"],
                           "required": c["required_display"], "available": avail, "explanation": c["explanation"]})
        for c in r.get("coupled_checks", []):
            if c.get("applicable"):
                checks.append({"group": "equipment", "keys": [c.get("model", "")], "outcome": c["outcome"],
                               "mandatory": c["mandatory"], "required": c.get("name", ""), "available": "",
                               "explanation": c["explanation"]})
        verdicts[f"{eid}|{cid}"] = {"verdict": r["verdict"], "summary": r["summary"], "checks": checks}

    def exp_view(eid):
        e = cat.experiments[eid]
        return {"id": eid, "name": e.get("name"), "plain_name": e.get("plain_name") or e.get("name"),
                "description": e.get("description", ""), "sample": (scenes.get(eid) or {}).get("sample_shape"),
                "steps": (scenes.get(eid) or {}).get("steps", []),
                "sources": [{"citation": s.get("citation"), "url": s.get("url") or (f"https://doi.org/{s['doi']}" if s.get("doi") else None)}
                            for s in e.get("sources", [])][:3]}

    def cfg_view(cid):
        c, eq = cat.configurations[cid], cat.equipment[cat.configurations[cid]["equipment_id"]]
        return {"id": cid, "name": c.get("name"), "manufacturer": eq.get("manufacturer"), "model": eq.get("model"),
                "family": eq.get("family"), "description": eq.get("description", ""),
                "documents": [{"title": d.get("title"), "url": d.get("url")} for d in eq.get("documents", [])][:3]}

    out = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "lean_source_hash": lean_runner.source_hash(), "lean_version": lean_runner.version(),
           "counts": dict(counts), "pairings": len(results),
           "industries": [{"id": i["id"], "name": NAMES[i["id"]], "experiments": [exp_view(e) for e in i["experiment_ids"]],
                           "configurations": [cfg_view(c) for c in i["configuration_ids"]]} for i in industries],
           "verdicts": verdicts,
           "catalog": {"experiments": len(cat.experiments), "configurations": len(cat.configurations),
                       **({k: v for k, v in grid.summary(cat)["overall"].items()} if _has_grid(cat) else {})}}
    (ROOT / "site").mkdir(exist_ok=True)
    (ROOT / "site/data.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(len(industries), "industries,", sum(len(i["experiment_ids"]) for i in industries), "experiments,",
          len(cfg_ids), "configurations,", len(results), "pairings:", dict(counts))
    per = Counter()
    for (iid, _, _), r in zip(meta, results):
        per[(iid, r["verdict"][:4])] += 1
    for i in industries:
        print(f"  {i['id']:42} MET {per[(i['id'], 'REQU')]}  NOT {per[(i['id'], 'DOES')]}  INFO {per[(i['id'], 'NEED')]}")


if __name__ == "__main__":
    main()
