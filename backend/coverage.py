"""Research coverage registry, computed from the data — never hand-maintained."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .catalog import Catalog
from .validation import validate_catalog


def build_coverage(catalog: Catalog) -> dict:
    rep = validate_catalog(catalog)
    error_paths = {i.path.split(":")[0] for i in rep.errors}

    industries = []
    for ind in sorted(catalog.industries.values(), key=lambda x: x["id"]):
        industries.append({"id": ind["id"], "name": ind.get("name"), "status": ind.get("status"),
                           "source": ind.get("source"), "experiment_ids": ind.get("experiment_ids", [])})
    researched = [i for i in industries if i["experiment_ids"]]

    verified_profiles, unverified_profiles = [], []
    for ex in catalog.experiments.values():
        ok = ex.get("confirmed") and ex["_file"] not in error_paths and any(r.get("mandatory") for r in ex.get("requirements", []))
        (verified_profiles if ok else unverified_profiles).append({"id": ex["id"], "industry": ex.get("industry"),
                                                                 "mandatory_requirements": sum(1 for r in ex.get("requirements", []) if r.get("mandatory")),
                                                                 "missing_information": ex.get("missing_information", [])})

    families = []
    unknown_caps = []
    estimate_caps = []
    for eq in catalog.equipment.values():
        cfg_ids = [c["id"] for c in eq.get("configurations", [])]
        families.append({"equipment_id": eq["id"], "manufacturer": eq.get("manufacturer"), "model": eq.get("model"),
                         "configurations": cfg_ids, "documents": len(eq.get("documents", [])),
                         "validation_ok": eq["_file"] not in error_paths})
        for cfg in eq.get("configurations", []):
            for cap in cfg.get("capabilities", []):
                if cap.get("value", {}).get("kind") == "unknown" or cap.get("install") == "unknown":
                    unknown_caps.append({"configuration_id": cfg["id"], "key": cap["key"], "note": "UNKNOWN in documentation"})
                elif cap.get("evidence_status") == "inferred_estimate":
                    estimate_caps.append({"configuration_id": cfg["id"], "key": cap["key"], "note": "inferred estimate; cannot support ACCEPT"})

    ev_status = Counter(r.get("evidence_status") for r in catalog.evidence.values())
    ev_sources = Counter((r.get("source_url") or "").split("/")[2] if "//" in (r.get("source_url") or "") else "?" for r in catalog.evidence.values())

    # requirement keys that no equipment documents at all, or that are outside the vocabulary
    cap_keys = {cap["key"] for eq in catalog.equipment.values() for cfg in eq.get("configurations", []) for cap in cfg.get("capabilities", [])}
    req_keys = Counter(r["key"] for ex in catalog.experiments.values() for r in ex.get("requirements", []))
    unsupported = []
    for key, n in sorted(req_keys.items()):
        if catalog.vocabulary_key(key) is None:
            unsupported.append({"key": key, "used_by_requirements": n, "reason": "not in vocabulary (Lean: unknown/unsupported, never pass)"})
        elif key not in cap_keys:
            unsupported.append({"key": key, "used_by_requirements": n, "reason": "no registered equipment documents this capability"})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog_version": catalog.version,
        "disclaimer": ("Coverage reflects only what has been researched and validated in this repository. "
                       "A universal architecture does not mean every experiment or industry has been researched."),
        "industries": {"known": len(industries), "researched": len(researched),
                       "researched_ids": [i["id"] for i in researched], "entries": industries},
        "experiment_profiles": {"verified": verified_profiles, "unverified": unverified_profiles},
        "equipment_families": families,
        "manufacturer_evidence": {"records": len(catalog.evidence), "by_status": dict(ev_status), "by_host": dict(ev_sources)},
        "missing_scientific_data": {"unknown_capabilities": unknown_caps, "inferred_estimates": estimate_caps,
                                    "experiment_missing_information": [{"experiment_id": e["id"], "missing": e.get("missing_information", [])}
                                                                       for e in catalog.experiments.values() if e.get("missing_information")]},
        "unsupported_requirement_types": unsupported,
        "vocabulary": {"established_keys": len(catalog.vocabulary["keys"]), "proposed_keys": [p["key"] for p in catalog.vocabulary_proposals]},
        "validation": {"errors": len(rep.errors), "warnings": len(rep.warnings)},
    }
