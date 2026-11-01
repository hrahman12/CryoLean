"""Verification orchestration: Lean verdict first, then Z3 suggestions, each re-checked by Lean.

    working experiment + configuration
          │  serialize (exact SI rationals, coupled models expanded)
          ▼
    Lean checker  ──►  verdict (REQUIREMENTS_MET | DOES_NOT_MEET_REQUIREMENTS | NEED_MORE_INFORMATION)
          │
          ▼
    Z3:  why it fails (unsat cores) · alternative configurations · parameter changes
          │
          ▼
    Lean re-checks every suggested configuration / parameter set  ──►  only Lean passes are "verified"
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from fractions import Fraction

from . import lean_runner, modifications, serialize, smt, units
from .catalog import Catalog
from .validation import Report, validate_configuration, validate_experiment

HEADLINES = {"REQUIREMENTS_MET": "Requirements met",
             "DOES_NOT_MEET_REQUIREMENTS": "Doesn't meet requirements",
             "NEED_MORE_INFORMATION": "Need more information"}
GENERIC_THEOREMS = ["verdict_accept_sound", "verdict_accept_iff", "accept_no_unknown", "fail_implies_reject",
                    "violation_prevents_accept", "verdict_ignores_optional", "verdict_ignores_nonapplicable",
                    "not_installed_never_passes", "run_binds_inputs", "candidates_accept_sound",
                    "candidates_verdicts_are_lean", "verdict_industry_irrelevant", "coupled_pass_dims_match"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_documents(catalog: Catalog, experiment: dict, configuration_id: str, extra_modifications: list[dict] | None = None,
                    include_proposed: bool = False) -> tuple[dict, dict, list, dict]:
    cfg = catalog.get_configuration(configuration_id)
    mods = modifications.for_configuration(catalog, configuration_id) + list(extra_modifications or [])
    cfg_mod = modifications.apply(catalog, cfg, mods, include_proposed=include_proposed)
    cfg_doc = serialize.configuration_doc(catalog, cfg_mod)
    exp_doc, coupled_info = serialize.experiment_doc(catalog, experiment, cfg_mod)
    return cfg_doc, exp_doc, coupled_info, cfg_mod


def _source_validation(catalog: Catalog, experiment: dict, cfg: dict) -> dict:
    rep = Report()
    validate_experiment(catalog, experiment, f"experiment:{experiment['id']}", rep)
    validate_configuration(catalog, cfg, f"configuration:{cfg['id']}", rep)
    return rep.as_dict()


def _check_view(catalog: Catalog, c: dict) -> dict:
    """Frontend view of one Lean requirement check, with evidence attached."""
    keys = c["keys"]
    first = next((pk for pk in c["per_key"] if pk["outcome"] == "pass"), c["per_key"][0] if c["per_key"] else None)
    cap = first["capability"] if first else None
    return {
        "kind": "requirement", "keys": keys, "mandatory": c["mandatory"], "applicable": c["applicable"],
        "outcome": c["outcome"], "required": c["required_display"],
        "available": first["available_display"] if first else "not documented",
        "constraint": c["constraint"], "conditions": c["conditions"], "explanation": c["explanation"],
        "property": None, "per_key": c["per_key"],
        "requirement_origin": c["requirement_origin"], "requirement_rationale": c["requirement_rationale"],
        "requirement_evidence": catalog.evidence_for(c["requirement_evidence_ids"]),
        "capability_evidence": catalog.evidence_for(cap["evidence_ids"]) if cap else [],
    }


def _coupled_view(catalog: Catalog, c: dict, info_by_model: dict) -> dict:
    info = info_by_model.get(c["model"], {})
    return {"kind": "coupled", "id": c["id"], "name": c["name"], "model": c["model"], "mandatory": c["mandatory"],
            "applicable": c["applicable"], "outcome": c["outcome"], "lhs": c["lhs"], "rhs": c["rhs"],
            "validity": c["validity"], "explanation": c["explanation"], "equation": info.get("equation"),
            "assumptions": info.get("assumptions", []), "valid_range": info.get("valid_range"),
            "slot_resolution": info.get("slots", {}), "notes": info.get("notes", []), "rationale": c["rationale"],
            "evidence": catalog.evidence_for(c["evidence_ids"])}


def _property_index(catalog: Catalog) -> dict:
    idx = {}
    for p in catalog.properties.values():
        for k in p.get("keys", []):
            idx.setdefault(k, p["id"])
        for m in p.get("models", []):
            idx.setdefault("model:" + m, p["id"])
    return idx


def _user_message(verdict: str, checks: list, coupled: list, confirmed: bool) -> tuple[str, str]:
    mand_fail = [c for c in checks + coupled if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"]
    mand_open = [c for c in checks + coupled if c["mandatory"] and c["applicable"] and c["outcome"] in ("unknown", "unsupported")]
    if verdict == "REQUIREMENTS_MET":
        return "This machine meets the requirements for your experiment.", "View the checks or save the result."
    if verdict == "DOES_NOT_MEET_REQUIREMENTS":
        return mand_fail[0]["explanation"] if mand_fail else "A documented limitation conflicts with a requirement.", \
            "See why it fails and the suggested alternatives below."
    if not confirmed:
        return "Please review and confirm the experiment requirements before checking.", "Confirm the requirements, then check again."
    if mand_open:
        return mand_open[0]["explanation"], "Supply the missing value (or a sourced specification) and check again."
    return "This experiment has no applicable mandatory requirements yet.", "Add or confirm requirements."


def check(catalog: Catalog, experiment: dict, configuration_id: str, extra_modifications: list[dict] | None = None,
          suggestions: bool = True, max_alternatives: int = 5) -> dict:
    """Full check of one configuration: Lean verdict, then Z3 suggestions (each re-checked by Lean)."""
    cfg_doc, exp_doc, coupled_info, cfg_mod = build_documents(catalog, experiment, configuration_id, extra_modifications)
    lean = lean_runner.check(cfg_doc, exp_doc)
    info_by_model = {i["model"]: i for i in coupled_info}
    pidx = _property_index(catalog)
    checks = [_check_view(catalog, c) for c in lean["checks"]]
    for c in checks:
        c["property"] = next((pidx[k] for k in c["keys"] if k in pidx), None)
    coupled = [_coupled_view(catalog, c, info_by_model) for c in lean["coupled_checks"]]
    for c in coupled:
        c["property"] = pidx.get("model:" + c["model"])
    verdict = lean["verdict"]
    msg, nxt = _user_message(verdict, checks, coupled, exp_doc["confirmed"])
    fp = serialize.fingerprint({"catalog_version": catalog.version}, cfg_doc, exp_doc)
    result = {
        "verdict": verdict,
        "headline": HEADLINES[verdict],
        "user_message": msg,
        "next_step": nxt,
        "summary": lean["summary"],
        "equipment": {"id": cfg_mod["equipment_id"], "manufacturer": cfg_mod.get("manufacturer"), "model": cfg_mod.get("model"),
                      "configuration_id": cfg_doc["id"], "configuration_name": cfg_doc["name"],
                      "catalog_configuration_id": configuration_id,
                      "modifications_applied": cfg_mod.get("modifications_applied", [])},
        "experiment": {"id": experiment["id"], "name": experiment.get("name"), "plain_name": experiment.get("plain_name"),
                       "industry": experiment.get("industry"), "confirmed": exp_doc["confirmed"],
                       "parameters": [{"name": p["name"], "value": p.get("value"), "origin": p.get("origin"),
                                       "display": units.display_catalog(p["value"]["value"], p["value"]["unit"]) if isinstance(p.get("value"), dict) else p.get("value")}
                                      for p in experiment.get("params", [])]},
        "checks": checks,
        "coupled_checks": coupled,
        "missing_information": [("/".join(c["keys"]) if c["kind"] == "requirement" else c["name"])
                                for c in checks + coupled if c["mandatory"] and c["applicable"] and c["outcome"] in ("unknown", "unsupported")],
        "failed_requirements": [("/".join(c["keys"]) if c["kind"] == "requirement" else c["name"])
                                for c in checks + coupled if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"],
        "verification": {
            "generic_theorems": {"status": "kernel-checked when the Lean project is built (`lake build`, `lean/Audit.lean`)",
                                 "key_theorems": GENERIC_THEOREMS},
            "concrete_evaluation": {"engine": lean["checker"], "lean_version": lean["lean_version"],
                                    "verified_by_lean": True, "lean_input_hash": lean["input_hash"], "verdict": verdict},
            "source_data_validation": _source_validation(catalog, experiment, cfg_mod),
            "physical_model_assumptions": [{"model": i["model"], "status": i["status"], "equation": i.get("equation"),
                                            "assumptions": i.get("assumptions", []), "valid_range": i.get("valid_range")}
                                           for i in coupled_info],
        },
        "references": _references(catalog, experiment, checks, coupled),
        "fingerprint": fp,
        "catalog_version": catalog.version,
        "checked_at": _now(),
        "lean_input": {"configuration": cfg_doc, "experiment": exp_doc},
    }
    result["suggestions"] = suggest(catalog, experiment, cfg_doc, exp_doc, lean, max_alternatives) if suggestions else None
    return result


def _references(catalog: Catalog, experiment: dict, checks: list, coupled: list) -> list[dict]:
    seen, out = set(), []
    for s in experiment.get("sources", []):
        key = s.get("doi") or s.get("url")
        if key and key not in seen:
            seen.add(key)
            out.append({"type": "experiment_source", **{k: s.get(k) for k in ("citation", "doi", "url", "accessed")}})
    for c in checks + coupled:
        for e in c.get("capability_evidence", []) + c.get("requirement_evidence", []) + c.get("evidence", []):
            key = e.get("source_url")
            if key and key not in seen and not e.get("missing"):
                seen.add(key)
                out.append({"type": e.get("evidence_status"), "document_title": e.get("document_title"),
                            "url": key, "doi": e.get("doi"), "accessed": e.get("accessed")})
    return out


# ---------------------------------------------------------------------------- Z3 suggestions (after Lean)
def suggest(catalog: Catalog, experiment: dict, cfg_doc: dict, exp_doc: dict, lean: dict, max_alternatives: int = 5) -> dict:
    out = {"engine": "z3", "note": ("Suggestions come from the Z3 solver. A suggestion is marked verified only if the Lean "
                                    "checker accepted the exact suggested configuration and parameters.")}
    # 1. why it fails / what blocks it
    out["conflicts"] = smt.all_conflicts(cfg_doc, exp_doc)
    out["requirements_self_consistent"] = smt.requirements_self_consistent(exp_doc)

    # 2. parameter changes for failing coupled relations, re-checked by Lean
    failing = [c["id"] for c in lean["coupled_checks"] if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"]
    adjustable = {}
    for c in exp_doc.get("coupled", []):
        model = catalog.coupled_models.get(c["model"], {})
        adjustable.update(model.get("parameters", {}) or {})
    params = smt.suggest_parameters(cfg_doc, exp_doc, failing, adjustable) if failing else []
    for p in params:
        if p.get("status") != "found":
            continue
        exp2 = copy.deepcopy(exp_doc)
        for prm in exp2["params"]:
            if prm["name"] == p["parameter"]:
                prm["value"] = p["suggested_quantity"]
                prm["origin"] = "user_entered"
        try:
            r = lean_runner.check(cfg_doc, exp2)
            p["lean_verdict"] = r["verdict"]
            p["verified"] = r["verdict"] == "REQUIREMENTS_MET"
            p["coupled_after"] = next((c["explanation"] for c in r["coupled_checks"] if c["id"] == p["coupled_id"]), None)
        except lean_runner.LeanUnavailable as e:
            p["lean_verdict"] = None
            p["verified"] = False
            p["lean_error"] = str(e)
    out["parameter_changes"] = params

    # 3. requirement relaxations (only offered, never applied): the documented limit for each failing requirement
    relax = []
    for c in lean["checks"]:
        if c["mandatory"] and c["applicable"] and c["outcome"] == "fail":
            for pk in c["per_key"]:
                cap = pk["capability"]
                if cap and cap["install"] == "installed" and cap["value"]["kind"] in ("max", "min", "range"):
                    relax.append({"keys": c["keys"], "your_requirement": c["required_display"],
                                  "documented_limit": pk["available_display"],
                                  "note": "Only if your experiment can tolerate it: changing a requirement is your decision and resets confirmation."})
    out["requirement_relaxations"] = relax

    # 4. alternative configurations across all equipment, ranked by Z3, each re-checked by Lean
    if lean["verdict"] != "REQUIREMENTS_MET":
        pairs = []
        for cid in catalog.configurations:
            if cid == cfg_doc["id"].split("~")[0]:
                continue
            # same documents a direct check would use: registered modifications applied
            cd, ed, _, _ = build_documents(catalog, experiment, cid)
            ed["confirmed"] = exp_doc["confirmed"]
            pairs.append((cd, ed))
        models = {cid: f"{cfg.get('manufacturer', '')} {cfg.get('model', '')} {cfg.get('name', '')}" for cid, cfg in catalog.configurations.items()}
        ranked = [r for r in smt.rank_alternatives(pairs, reported_equipment=experiment.get("reported_equipment", []), models=models)
                  if r["evaluation"]["status"] != "conflict"
                  and (r["evaluation"]["status"] != "pending_information" or r["evaluation"]["documented_passes"] > 0)][:max_alternatives]
        alts = []
        try:
            # one Lean call per distinct experiment document (slots may differ per configuration)
            for r in ranked:
                lr = lean_runner.check(r["configuration_document"], r["experiment_document"])
                ev = r["evaluation"]
                alts.append({"configuration_id": r["configuration_document"]["id"], "equipment_id": ev["equipment_id"],
                             "name": r["configuration_document"]["name"],
                             "z3_status": ev["status"], "added_options": ev["added_options"],
                             "z3_unknown_items": ev["unknown_items"], "min_relative_margin": ev["min_relative_margin"],
                             "named_in_sources": ev["named_in_sources"], "documented_passes": ev["documented_passes"],
                             "hypothetical": bool(ev["added_options"]), "lean_verdict": lr["verdict"],
                             "verified": lr["verdict"] == "REQUIREMENTS_MET", "lean_summary": lr["summary"]})
        except lean_runner.LeanUnavailable as e:
            out["alternatives_error"] = str(e)
        out["alternatives"] = alts
        out["ranking_criteria"] = ["Z3 status tier: satisfiable < needs documented options < pending information",
                                   "fewest added optional accessories", "equipment model named in the experiment's sources",
                                   "fewest unknown items", "most mandatory items documented as passing",
                                   "largest smallest relative margin over numeric requirements"]
    else:
        out["alternatives"] = []
    return out


def verify_candidates(catalog: Catalog, experiment: dict, candidate_docs: list[dict]) -> list[dict]:
    """Lean `check-candidates` (theorem candidates_accept_sound) for externally proposed configurations."""
    if not candidate_docs:
        return []
    exp_doc, _ = serialize.experiment_doc(catalog, experiment, catalog.get_configuration(candidate_docs[0]["id"].split("+")[0].split("~")[0]))
    return lean_runner.check_candidates(exp_doc, candidate_docs)
