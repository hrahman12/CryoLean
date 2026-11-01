"""Research coverage registry — computed from the data, never hand-maintained or rounded up."""
from __future__ import annotations

from collections import Counter

from . import db
from .catalog import Catalog
from .validation import validate_catalog


def property_status(catalog: Catalog) -> list[dict]:
    """Status of each of the 40 physical properties from what the data actually supports."""
    documented = {cap["key"] for cfg in catalog.configurations.values() for cap in cfg["capabilities"]
                  if cap["value"].get("kind") != "unknown"}
    required = {k for ex in catalog.experiments.values() for r in ex.get("requirements", []) for k in (r.get("keys") or [r.get("key")])}
    out = []
    for p in catalog.properties.values():
        keys = [k for k in p.get("keys", []) if k in catalog.vocabulary]
        models = [catalog.coupled_models.get(m) for m in p.get("models", [])]
        validated = [m["id"] for m in models if m and m.get("status") == "validated"]
        unvalidated = [m["id"] for m in models if m and m.get("status") != "validated"]
        with_data = sorted(k for k in keys if k in documented)
        if (with_data or validated) and (with_data or any(_model_has_data(catalog, m) for m in validated)):
            status = "implemented_with_data"
        elif keys or validated:
            status = "representable_no_data"
        elif unvalidated:
            status = "model_not_validated"
        else:
            status = "representable_only"
        out.append({"id": p["id"], "category": p["category"], "name": p["name"], "status": status,
                    "keys": keys, "keys_with_documented_values": with_data, "used_by_experiments": sorted(k for k in keys if k in required),
                    "validated_models": validated, "unvalidated_models": unvalidated, "note": p.get("note", "")})
    return out


def _model_has_data(catalog: Catalog, model_id: str) -> bool:
    return any(c.get("model") == model_id for ex in catalog.experiments.values() for c in ex.get("coupled", []))


def build(catalog: Catalog) -> dict:
    rep = validate_catalog(catalog)
    bad = {i.path.split(".")[0] for i in rep.errors}
    industries = sorted(catalog.industries.values(), key=lambda i: i["id"])
    researched = [i["id"] for i in industries if i["experiment_ids"]]
    validated, unvalidated = [], []
    for ex in catalog.experiments.values():
        ok = ex.get("confirmed") and f"experiment:{ex['id']}" not in bad
        (validated if ok else unvalidated).append({"id": ex["id"], "industry": ex.get("industry"),
                                                   "missing_information": ex.get("missing_information", []),
                                                   "review": ex.get("review")})
    unknown_caps = [{"configuration_id": cfg["id"], "key": c["key"]} for cfg in catalog.configurations.values()
                    for c in cfg["capabilities"] if c["value"].get("kind") == "unknown" or c["install"] == "unknown"]
    estimates = [{"configuration_id": cfg["id"], "key": c["key"]} for cfg in catalog.configurations.values()
                 for c in cfg["capabilities"] if c["evidence_status"] == "inferred_estimate"]
    cap_keys = {c["key"] for cfg in catalog.configurations.values() for c in cfg["capabilities"]}
    unsupported = []
    for ex in catalog.experiments.values():
        for r in ex.get("requirements", []):
            for k in (r.get("keys") or [r.get("key")]):
                if k not in catalog.vocabulary:
                    unsupported.append({"experiment_id": ex["id"], "key": k, "reason": "not in vocabulary"})
                elif k not in cap_keys:
                    unsupported.append({"experiment_id": ex["id"], "key": k, "reason": "no registered equipment documents it"})
        for c in ex.get("coupled", []):
            m = catalog.coupled_models.get(c["model"])
            if not m or m.get("status") != "validated":
                unsupported.append({"experiment_id": ex["id"], "model": c["model"], "reason": f"model status {(m or {}).get('status', 'unknown')}"})
    props = property_status(catalog)
    con = catalog.connect()
    try:
        n_candidates = con.execute("SELECT COUNT(*) FROM candidates WHERE review_status != 'promoted'").fetchone()[0]
        n_requests = con.execute("SELECT COUNT(*) FROM research_requests").fetchone()[0]
    finally:
        con.close()
    return {
        "generated_at": db.now(), "catalog_version": catalog.version,
        "disclaimer": ("Coverage reflects only what has been researched and validated here. The architecture accepts any "
                       "industry, but that does not mean every experiment or industry has been researched or verified."),
        "industries": {"registered_or_known": len(industries), "researched": len(researched), "researched_ids": researched,
                       "entries": [{k: i.get(k) for k in ("id", "name", "status", "source", "experiment_ids")} for i in industries]},
        "experiment_profiles": {"available": len(catalog.experiments), "validated": validated, "not_validated": unvalidated},
        "equipment_families": [{"equipment_id": e["id"], "manufacturer": e.get("manufacturer"), "model": e.get("model"),
                                "family": e.get("family"), "configurations": [c["id"] for c in e.get("configurations", [])]}
                               for e in catalog.equipment.values()],
        "manufacturer_evidence": {"records": len(catalog.evidence),
                                  "by_status": dict(Counter(r.get("evidence_status") for r in catalog.evidence.values()))},
        "physical_properties": {"total": len(props), "by_status": dict(Counter(p["status"] for p in props)), "properties": props},
        "coupled_constraints": {"models": [{"id": m["id"], "name": m["name"], "status": m["status"], "coupling": m.get("coupling")}
                                           for m in catalog.coupled_models.values()]},
        "missing_scientific_data": {"unknown_capabilities": unknown_caps, "inferred_estimates": estimates,
                                    "experiment_missing_information": [{"experiment_id": e["id"], "missing": e.get("missing_information", [])}
                                                                       for e in catalog.experiments.values() if e.get("missing_information")]},
        "unsupported_physical_requirements": unsupported,
        "research_pipeline": {"open_candidates": n_candidates, "requests": n_requests},
        "source_validation": {"errors": len(rep.errors), "warnings": len(rep.warnings)},
    }
