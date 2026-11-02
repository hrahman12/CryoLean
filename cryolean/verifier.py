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

from . import outcome, lean_runner, modifications, serialize, smt, units
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
    result["outcome_card"] = outcome.card(verdict, experiment, cfg_doc, exp_doc, result["failed_requirements"], result["missing_information"])
    result["verdict_card"] = verdict_card(verdict, msg, lean, result["failed_requirements"], result["missing_information"])
    result["suggestions"] = (suggest(catalog, experiment, cfg_doc, exp_doc, lean, max_alternatives, configuration_id,
                                     extra_modifications) if suggestions else None)
    return result


# The theorems that justify each verdict (names exactly as in lean/CryoLean/*.lean).
CARD_THEOREMS = {
    "REQUIREMENTS_MET": ["verdict_accept_iff", "verdict_accept_sound", "accept_no_unknown", "accept_all_coupled",
                         "pass_dims_all_match", "run_binds_inputs"],
    "DOES_NOT_MEET_REQUIREMENTS": ["verdict_reject_sound", "fail_implies_reject", "fail_needs_trusted",
                                   "violation_prevents_accept", "run_binds_inputs"],
    "NEED_MORE_INFORMATION": ["accept_no_unknown", "missing_capability_unknown", "untrusted_never_passes",
                              "untrusted_never_fails", "verdict_reject_complete", "run_binds_inputs"],
}


def verdict_card(verdict: str, reason: str, lean: dict, failed: list, missing: list) -> dict:
    """The card the UI shows: verdict, reason, theorem names, their axioms, and the source hash.
    'Z3 output is a hint, never a verdict' -- the card only ever reports the Lean result."""
    audit = lean_runner.axiom_audit()
    names = CARD_THEOREMS[verdict]
    axioms = {n: audit.get("theorems", {}).get(n) for n in names}
    return {
        "verdict": verdict,
        "reason": reason,
        "failed": failed,
        "missing": missing,
        "decided_by": "Lean 4 checker (CryoLean.verdict, compiled)",
        "theorems": names,
        "axioms": axioms,
        "axioms_standard_only": bool(audit.get("all_standard")) and all(a is not None for a in axioms.values()),
        "axiom_audit": audit.get("status"),
        "source_hash": _cached_source_hash(),
        "lean_input_hash": lean.get("input_hash"),
        "lean_version": lean.get("lean_version"),
        "z3_role": "Z3 output is a hint, never a verdict",
    }


def config_path(*parts):
    from . import config
    return config.ROOT.joinpath(*parts)


_SRC_CACHE: dict = {}


def _cached_source_hash() -> str:
    from . import config
    files = sorted((config.LEAN_DIR / "CryoLean").glob("*.lean")) + [config.LEAN_DIR / "Main.lean"]
    b = lean_runner.lean_binary()
    key = tuple((str(f), f.stat().st_mtime_ns) for f in files + ([b] if b else []))
    if key not in _SRC_CACHE:
        _SRC_CACHE.clear()
        _SRC_CACHE[key] = lean_runner.source_hash()
    return _SRC_CACHE[key]


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
# The gate: a fix is shown to the user ONLY if the Lean checker returned REQUIREMENTS_MET on the exact documents
# that "Apply fix" will rebuild (same catalog path: working experiment -> build_documents -> Lean). Candidates that
# return DOES_NOT_MEET_REQUIREMENTS, NEED_MORE_INFORMATION or error are discarded and only counted.
NUDGES = (Fraction(0), Fraction(1, 1000), Fraction(1, 100), Fraction(5, 100), Fraction(10, 100))


def _lean_evidence(lr: dict) -> dict:
    return {"verdict": lr["verdict"], "lean_input_hash": lr.get("input_hash"), "lean_version": lr.get("lean_version"),
            "checker": lr.get("checker"), "summary": lr.get("summary"),
            "theorems": CARD_THEOREMS["REQUIREMENTS_MET"] if lr["verdict"] == "REQUIREMENTS_MET" else []}


def _param_unit(experiment: dict, name: str, dim: dict) -> str:
    """The unit the experiment already uses for this parameter (so the applied value is in the user's own unit)."""
    for prm in experiment.get("params", []):
        if prm["name"] == name and isinstance(prm.get("value"), dict) and prm["value"].get("unit"):
            return prm["value"]["unit"]
    for sym, u in units.UNITS.items():
        if u.scale == 1 and u.dim_dict() == dim:
            return sym
    return "count"


def _candidate_values(best: Fraction, direction: str, is_int: bool):
    """Z3's optimum first, then the same value pushed further into the feasible side (still the user's own parameter;
    no requirement or specification is changed). Lean decides each one."""
    seen = []
    for n in NUDGES:
        v = best * (1 - n) if direction == "decrease" else best * (1 + n)
        if is_int:
            v = Fraction(int(v // 1)) if direction == "decrease" else Fraction(-int((-v) // 1))
        if v not in seen and (direction != "decrease" or v >= 0):
            seen.append(v)
    return seen


def _lean_on_applied(catalog: Catalog, experiment: dict, configuration_id: str, extra_modifications, param_values: dict | None):
    """Rebuild exactly what check_compatibility will build after Apply fix, and ask Lean."""
    from .edits import apply_parameter_values
    ex2 = copy.deepcopy(experiment)
    if param_values:
        apply_parameter_values(catalog, ex2, param_values)
    cd, ed, _, _ = build_documents(catalog, ex2, configuration_id, extra_modifications)
    return lean_runner.check(cd, ed)


def suggest(catalog: Catalog, experiment: dict, cfg_doc: dict, exp_doc: dict, lean: dict, max_alternatives: int = 5,
            configuration_id: str | None = None, extra_modifications=None) -> dict:
    configuration_id = configuration_id or cfg_doc["id"].split("~")[0]
    out = {"engine": "z3", "gate": "lean_verified_only",
           "note": ("Lanyon (when enabled) and Z3 propose candidates; every candidate is checked by the Lean checker on the exact configuration Apply "
                    "will use. Only REQUIREMENTS_MET candidates are listed; all others are discarded.")}
    out["conflicts"] = smt.all_conflicts(cfg_doc, exp_doc)
    out["requirements_self_consistent"] = smt.requirements_self_consistent(exp_doc)
    discarded = {"DOES_NOT_MEET_REQUIREMENTS": 0, "NEED_MORE_INFORMATION": 0, "error": 0, "needs_uninstalled_options": 0}
    fixes: list[dict] = []

    def ask(param_values, cid=configuration_id, mods=extra_modifications):
        try:
            lr = _lean_on_applied(catalog, experiment, cid, mods, param_values)
        except (lean_runner.LeanUnavailable, lean_runner.LeanDecodeError, Exception) as e:   # noqa: BLE001 - any failure = not verified
            discarded["error"] += 1
            out.setdefault("lean_errors", []).append(str(e)[:300])
            return None
        if lr["verdict"] != "REQUIREMENTS_MET":
            discarded[lr["verdict"]] += 1
            return None
        return lr

    # 1. parameter changes for failing coupled relations: Z3 proposes, Lean decides each candidate value
    failing = [c["id"] for c in lean["coupled_checks"] if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"]
    adjustable = {}
    for c in exp_doc.get("coupled", []):
        adjustable.update(catalog.coupled_models.get(c["model"], {}).get("parameters", {}) or {})
    # 1a. Lanyon (AI proposer) first, when enabled: each candidate is Lean-checked exactly like Z3's
    out["proposers"] = {"z3": {"enabled": True}}
    from . import lanyon
    lan = lanyon.proposer_enabled()
    out["proposers"]["lanyon"] = {"enabled": lan["enabled"], "reason": lan["reason"]}
    if failing and lan["enabled"]:
        failing_checks = [c for c in lean["coupled_checks"] if c["id"] in failing]
        try:
            lp = lanyon.propose_repairs(catalog, exp_doc, cfg_doc, failing_checks, adjustable)
            out["proposers"]["lanyon"].update({k: lp[k] for k in ("session_id", "certified", "evidence_status", "why_not_certified")},
                                              candidates=len(lp["candidates"]))
            for c in lp["candidates"]:
                pv = {c["parameter"]: {"value": c["value"], "unit": c["unit"]}}
                lr = ask(pv)
                if lr:
                    cur = next((prm.get("value") for prm in experiment.get("params", []) if prm["name"] == c["parameter"]), None)
                    fixes.append({"kind": "parameter_change", "proposed_by": "lanyon", "lanyon_session": lp["session_id"],
                                  "lanyon_certified": lp["certified"], "configuration_id": configuration_id, "parameters": pv,
                                  "changes": [{"parameter": c["parameter"],
                                               "from": units.display_catalog(cur["value"], cur["unit"]) if isinstance(cur, dict) else str(cur),
                                               "to": units.display_catalog(c["value"], c["unit"]), "value": c["value"], "unit": c["unit"]}],
                                  "parameter": c["parameter"], "status": "found", "lean_verdict": lr["verdict"], "verified": True,
                                  "lean": _lean_evidence(lr)})
        except Exception as e:   # noqa: BLE001 - Lanyon failing never blocks Z3 or Lean
            out["proposers"]["lanyon"]["error"] = str(e)[:300]
    proposals = smt.suggest_parameters(cfg_doc, exp_doc, failing, adjustable) if failing else []
    found = [p for p in proposals if p.get("status") == "found"]
    passed_single = []
    for p in found:
        q = p["suggested_quantity"]
        best = Fraction(int(q["num"]), int(q["den"]))
        u = _param_unit(experiment, p["parameter"], q.get("dim", {}))
        is_int = bool((adjustable.get(p["parameter"]) or {}).get("integer"))
        for si in _candidate_values(best, p.get("direction") or "decrease", is_int):
            val = si / units.unit(u).scale
            pv = {p["parameter"]: {"value": str(val.numerator) if val.denominator == 1 else f"{val.numerator}/{val.denominator}", "unit": u}}
            lr = ask(pv)
            if lr:
                fx = {"kind": "parameter_change", "proposed_by": "z3", "configuration_id": configuration_id, "parameters": pv,
                      "changes": [{"parameter": p["parameter"], "from": p["current"],
                                   "to": units.display(si, units.dims_of({"dim": q.get("dim", {})})),
                                   "value": pv[p["parameter"]]["value"], "unit": u,
                                   "z3_optimum": p["suggested"], "nudged_from_z3": si != best}],
                      "lean": _lean_evidence(lr),
                      # flat fields kept for existing callers
                      "parameter": p["parameter"], "coupled_id": p["coupled_id"], "status": "found", "current": p["current"],
                      "suggested": units.display(si, units.dims_of({"dim": q.get("dim", {})})),
                      "suggested_exact": str(si), "lean_verdict": lr["verdict"], "verified": True}
                fixes.append(fx)
                passed_single.append(p["parameter"])
                break
    # 1b. still nothing? Lean-check Z3's proposals applied together (each relation repaired at once)
    if found and not passed_single and len(found) > 1:
        pv, chg = {}, []
        for p in found:
            q = p["suggested_quantity"]
            si = Fraction(int(q["num"]), int(q["den"]))
            u = _param_unit(experiment, p["parameter"], q.get("dim", {}))
            val = si / units.unit(u).scale
            pv[p["parameter"]] = {"value": f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator), "unit": u}
            chg.append({"parameter": p["parameter"], "from": p["current"], "to": p["suggested"], "value": pv[p["parameter"]]["value"], "unit": u})
        lr = ask(pv)
        if lr:
            fixes.append({"kind": "parameter_change", "proposed_by": "z3", "configuration_id": configuration_id, "parameters": pv, "changes": chg,
                          "status": "found", "lean_verdict": lr["verdict"], "verified": True, "lean": _lean_evidence(lr)})
    out["z3_parameter_proposals"] = len(found)

    # 2. requirement relaxations are NEVER offered as fixes (that would change the scientific requirement).
    out["requirement_relaxations"] = []

    # 3. alternative configurations, ranked by Z3, decided by Lean on the exact catalog configuration
    if lean["verdict"] != "REQUIREMENTS_MET":
        pairs = []
        for cid in catalog.configurations:
            if cid == configuration_id:
                continue
            cd, ed, _, _ = build_documents(catalog, experiment, cid)
            pairs.append((cd, ed))
        models = {cid: f"{cfg.get('manufacturer', '')} {cfg.get('model', '')} {cfg.get('name', '')}" for cid, cfg in catalog.configurations.items()}
        ranked = [r for r in smt.rank_alternatives(pairs, reported_equipment=experiment.get("reported_equipment", []), models=models)
                  if r["evaluation"]["status"] != "conflict"
                  and (r["evaluation"]["status"] != "pending_information" or r["evaluation"]["documented_passes"] > 0)]
        n_alt = 0
        for r in ranked:
            if n_alt >= max_alternatives:
                break
            ev = r["evaluation"]
            if ev["added_options"]:
                discarded["needs_uninstalled_options"] += 1     # would need hardware the catalog does not list as installed
                continue
            cid = r["configuration_document"]["id"].split("~")[0].split("+")[0]
            lr = ask(None, cid, None)
            if lr:
                cfg = catalog.configurations.get(cid, {})
                fixes.append({"kind": "alternative_configuration", "proposed_by": "z3", "configuration_id": cid, "parameters": {},
                              "name": r["configuration_document"]["name"], "manufacturer": cfg.get("manufacturer"),
                              "model": cfg.get("model"), "equipment_id": ev["equipment_id"],
                              "min_relative_margin": ev["min_relative_margin"], "named_in_sources": ev["named_in_sources"],
                              "z3_status": ev["status"], "added_options": [], "hypothetical": False,
                              "lean_verdict": lr["verdict"], "verified": True, "lean": _lean_evidence(lr)})
                n_alt += 1
    for i, f in enumerate(fixes):
        f["fix_id"] = f"fix_{i + 1}"
    out["verified_fixes"] = fixes
    out["discarded"] = discarded
    out["status"] = "verified_solutions_found" if fixes else "no_verified_solution_found"
    out["message"] = (f"{len(fixes)} Lean-verified fix(es)." if fixes else "No verified solution found")
    # legacy keys, now restricted to verified entries only
    out["parameter_changes"] = [f for f in fixes if f["kind"] == "parameter_change"]
    out["alternatives"] = [f for f in fixes if f["kind"] == "alternative_configuration"]
    return out


def apply_fix(catalog: Catalog, experiment: dict, fix: dict, extra_modifications=None) -> dict:
    """Apply the exact verified configuration and run Lean again. The fix's parameters are already merged into
    `experiment` by the caller (working_experiment), so this is a plain check of that exact configuration."""
    res = check(catalog, experiment, fix["configuration_id"], extra_modifications, suggestions=False)
    expected = (fix.get("lean") or {}).get("lean_input_hash")
    got = res["verification"]["concrete_evaluation"]["lean_input_hash"]
    res["apply_fix"] = {"fix_id": fix.get("fix_id"), "verdict": res["verdict"], "expected_lean_input_hash": expected,
                        "lean_input_hash": got, "same_configuration": expected == got,
                        "confirmed": res["verdict"] == "REQUIREMENTS_MET" and expected == got}
    return res


def verify_candidates(catalog: Catalog, experiment: dict, candidate_docs: list[dict]) -> list[dict]:
    """Lean `check-candidates` (theorem candidates_accept_sound) for externally proposed configurations."""
    if not candidate_docs:
        return []
    exp_doc, _ = serialize.experiment_doc(catalog, experiment, catalog.get_configuration(candidate_docs[0]["id"].split("+")[0].split("~")[0]))
    return lean_runner.check_candidates(exp_doc, candidate_docs)
