"""Industry coverage and real Lean batch evaluation; labels never decide suitability."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from . import lean_runner, serialize, verifier
from .catalog import Catalog, CatalogError


def registry(catalog: Catalog) -> dict:
    from .visuals import _research
    selection = _research()[3]
    industries = []
    for industry in sorted(catalog.industries.values(), key=lambda i: i["id"]):
        featured = selection.get(industry["id"], {})
        experiment_ids = list(dict.fromkeys(industry.get("coverage_experiment_ids", featured.get("experiment_ids", industry.get("experiment_ids", [])))))
        configuration_ids = list(dict.fromkeys(industry.get("coverage_configuration_ids", featured.get("configuration_ids", []))))
        missing_experiments = [eid for eid in experiment_ids if eid not in catalog.experiments]
        missing_configurations = [cid for cid in configuration_ids if cid not in catalog.configurations]
        if missing_experiments or missing_configurations:
            raise CatalogError(f"invalid coverage registry for {industry['id']}: experiments {missing_experiments}, configurations {missing_configurations}")
        gaps = list(industry.get("coverage_shortfalls", []))
        if len(experiment_ids) < 3:
            gaps.append(f"Only {len(experiment_ids)} of 3 documented experiment profiles established.")
        if len(configuration_ids) < 3:
            gaps.append(f"Only {len(configuration_ids)} of 3 real relevant configurations established.")
        industries.append({"id": industry["id"], "name": industry["name"],
                           "experiment_ids": experiment_ids, "configuration_ids": configuration_ids,
                           "shortfalls": gaps, "pair_count": len(experiment_ids) * len(configuration_ids),
                           "target_met": len(experiment_ids) >= 3 and len(configuration_ids) >= 3})
    return {"target": {"industries": 20, "experiments_per_industry": 3, "configurations_per_industry": 3, "pairings": 180},
            "industries": industries, "catalog_version": catalog.version,
            "note": "Industry membership establishes relevance only. Each experiment/configuration pair needs a separate Lean evaluation."}


def evaluate(catalog: Catalog, industry_ids: list[str] | None = None, *, confirmed: bool = False) -> tuple[dict, list[dict]]:
    if confirmed is not True:
        raise ValueError("Explicitly confirm evaluation of the prepared source-backed profiles as written.")
    coverage = registry(catalog)
    if industry_ids is not None:
        unknown = set(industry_ids) - {i["id"] for i in coverage["industries"]}
        if unknown:
            raise CatalogError(f"unknown industries: {sorted(unknown)}")
        coverage["industries"] = [i for i in coverage["industries"] if i["id"] in industry_ids]
    documents, metadata = [], []
    for industry in coverage["industries"]:
        for experiment_id in industry["experiment_ids"]:
            experiment = serialize.working_experiment(catalog, experiment_id, None, None, True)
            for configuration_id in industry["configuration_ids"]:
                config_doc, experiment_doc, coupled_info, _ = verifier.build_documents(catalog, experiment, configuration_id)
                documents.append((config_doc, experiment_doc))
                metadata.append((industry["id"], experiment_id, configuration_id, coupled_info))
    results = lean_runner.check_batch(documents) if documents else []
    if len(results) != len(documents):
        raise lean_runner.LeanUnavailable("Lean batch result count does not match the requested coverage pairings.")
    rows, full_records = [], []
    source_hash = lean_runner.source_hash()
    audit = lean_runner.axiom_audit()
    for meta, pair, result in zip(metadata, documents, results):
        industry_id, experiment_id, configuration_id, coupled_info = meta
        if result.get("error"):
            raise lean_runner.LeanDecodeError(str(result["error"]))
        if result.get("verdict") not in lean_runner.VERDICTS:
            raise lean_runner.LeanUnavailable("The checker did not return a valid compatibility verdict.")
        if result.get("experiment_id") != experiment_id or result.get("configuration_id") != pair[0]["id"]:
            raise lean_runner.LeanUnavailable("Lean response identity does not match the coverage input.")
        checks = [verifier._check_view(catalog, c) for c in result["checks"]]
        coupled = [verifier._coupled_view(catalog, c, {i["model"]: i for i in coupled_info}) for c in result["coupled_checks"]]
        relevant = [c for c in checks + coupled if c["mandatory"] and c["applicable"]]
        row = {"industry_id": industry_id, "experiment_id": experiment_id, "configuration_id": configuration_id,
               "verdict": result["verdict"], "summary": result["summary"],
               "failed_requirements": [c.get("keys") or c.get("name") for c in relevant if c["outcome"] == "fail"],
               "missing_information": [c.get("keys") or c.get("name") for c in relevant if c["outcome"] in ("unknown", "unsupported")],
               "lean_input_hash": result["input_hash"],
               "input_sha256": serialize.fingerprint(pair[0], pair[1]),
               "verified_by_lean": True,
               "checks": [{k: c.get(k) for k in ("kind", "keys", "name", "outcome", "required", "available", "explanation")} for c in checks + coupled]}
        rows.append(row)
        full_records.append({"row": row, "lean_input": {"configuration": pair[0], "experiment": pair[1]},
                             "lean_result": result, "checks": checks, "coupled_checks": coupled})
    counts = dict(Counter(r["verdict"] for r in rows))
    coverage.update({"audit_kind": "recorded_real_lean_evaluation", "evaluated_at": datetime.now(timezone.utc).isoformat(),
                     "confirmed_scope": "Prepared profiles as authored; no user customizations; not a current user setup verdict.",
                     "engine": results[0].get("checker") if results else None,
                     "lean_version": results[0].get("lean_version") if results else None,
                     "lean_source_hash": source_hash, "axiom_audit": audit.get("status"),
                     "axioms_standard_only": audit.get("all_standard", False),
                     "rows": rows, "counts": counts, "evaluated_pairings": len(rows)})
    return coverage, full_records
