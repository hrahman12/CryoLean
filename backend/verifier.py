"""Verification: hand the exact documents to Lean, enrich the result with evidence.

The verdict and every per-requirement outcome come from Lean.  This module only
adds the user-facing headline, the evidence records behind each check, and a
binding token so stale results can be detected.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Callable

from .catalog import Catalog
from . import lean_runner

HEADLINES = {
    "ACCEPT": "Requirements met",
    "REJECT": "Doesn't meet requirements",
    "NEED_MORE_INFORMATION": "Need more information",
}
USER_SENTENCES = {
    "ACCEPT": "This machine meets the requirements for your experiment.",
    "REJECT": "This machine cannot meet at least one requirement of your experiment.",
    "NEED_MORE_INFORMATION": "We need more information before this setup can be verified.",
}


def result_token(catalog_version: str, lean_input_doc: dict) -> str:
    h = hashlib.sha256()
    h.update(catalog_version.encode())
    h.update(json.dumps(lean_input_doc, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return h.hexdigest()[:32]


def _first_failure_sentence(lean: dict) -> str | None:
    for c in lean.get("checks", []):
        if c.get("mandatory") and c.get("outcome") == "fail":
            return c.get("explanation")
    return None


def _first_open_sentence(lean: dict) -> str | None:
    for c in lean.get("checks", []):
        if c.get("mandatory") and c.get("outcome") in ("unknown", "unsupported"):
            return c.get("explanation")
    return None


def verify(catalog: Catalog, experiment_doc: dict, configuration_doc: dict,
           run: Callable[[dict, dict], dict] = lean_runner.run_check,
           extra: dict | None = None) -> dict:
    """Run Lean on exactly `configuration_doc` × `experiment_doc` and build the API result."""
    lean = run(configuration_doc, experiment_doc)
    verdict = lean["verdict"]
    checks = []
    for c in lean.get("checks", []):
        cap = c.get("capability")
        checks.append({
            "key": c["key"],
            "mandatory": c["mandatory"],
            "outcome": c["outcome"],
            "constraint": c["constraint"],
            "capability": cap,
            "explanation": c["explanation"],
            "requirement_origin": c.get("requirement_origin"),
            "requirement_rationale": c.get("requirement_rationale"),
            "requirement_evidence": catalog.evidence_for(c.get("requirement_evidence_ids", [])),
            "capability_evidence": catalog.evidence_for(cap.get("evidence_ids", [])) if cap else [],
            "vocabulary": catalog.vocabulary_key(c["key"]),
        })
    missing = [c["key"] for c in checks if c["mandatory"] and c["outcome"] in ("unknown", "unsupported")]
    failed = [c["key"] for c in checks if c["mandatory"] and c["outcome"] == "fail"]
    if verdict == "REJECT":
        sentence = _first_failure_sentence(lean) or USER_SENTENCES[verdict]
        next_step = "Choose another configuration or cryostat, or ask for alternatives."
    elif verdict == "NEED_MORE_INFORMATION":
        sentence = _first_open_sentence(lean) or lean.get("summary") or USER_SENTENCES[verdict]
        if not experiment_doc.get("confirmed"):
            sentence = "Please review and confirm the experiment requirements before checking."
            next_step = "Confirm the requirements, then check again."
        elif not any(r.get("mandatory") for r in experiment_doc.get("requirements", [])):
            next_step = "Add at least one mandatory requirement to the experiment."
        else:
            next_step = "Supply the missing value (or a sourced specification) and check again."
    else:
        sentence = USER_SENTENCES[verdict]
        next_step = "View the checks or save the result."
    input_doc = lean.pop("_input_document")
    return {
        "verdict": verdict,
        "headline": HEADLINES[verdict],
        "user_message": sentence,
        "next_step": next_step,
        "summary": lean.get("summary"),
        "verified_by_lean": True,
        "checker": lean.get("checker"),
        "lean_version": lean.get("lean_version"),
        "lean_input_hash": lean.get("input_hash"),
        "configuration_id": lean["configuration_id"],
        "equipment_id": lean["equipment_id"],
        "experiment_id": lean["experiment_id"],
        "experiment_name": lean.get("experiment_name"),
        "industry": lean.get("industry"),
        "mandatory_requirements": lean.get("mandatory_requirements"),
        "missing_information": missing,
        "failed_requirements": failed,
        "checks": checks,
        "catalog_version": catalog.version,
        "result_token": result_token(catalog.version, input_doc),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "lean_input": input_doc,
        **(extra or {}),
    }


def verify_ids(catalog: Catalog, experiment_id: str, configuration_id: str, confirmed: bool | None = None,
               run: Callable[[dict, dict], dict] = lean_runner.run_check) -> dict:
    ex = catalog.lean_experiment(catalog.get_experiment(experiment_id))
    if confirmed is not None:
        ex["confirmed"] = bool(confirmed)
    cfg = catalog.lean_configuration(catalog.get_configuration(configuration_id))
    return verify(catalog, ex, cfg, run=run)
