"""PASS-only repair proposals. Z3 proposes; the existing Lean pipeline decides.

Candidates retain the reviewed requirements verbatim. Only model-declared
adjustable parameters and existing, documented catalog configurations are
searched. A hypothetical installation is never an applicable repair.
"""
from __future__ import annotations

import copy
import itertools
import json
import uuid
from fractions import Fraction

from . import db, edits, lean_runner, serialize, smt, units, verifier
from .catalog import CatalogError

MET = "REQUIREMENTS_MET"


class RepairStale(ValueError):
    pass


def _record(api, result_id):
    api._details(result_id)  # catalog / exact input freshness check
    con = api._catalog.connect()
    try:
        row = con.execute("SELECT doc FROM results WHERE id=?", (result_id,)).fetchone()
        if not row:
            raise CatalogError("The original verification record is unavailable; check again.")
        return json.loads(row[0])
    finally:
        con.close()


def _save(api, result_id, record):
    con = api._catalog.connect()
    try:
        with con:
            con.execute("UPDATE results SET doc=? WHERE id=?", (db.dumps(record), result_id))
    finally:
        con.close()


def _parameter_proposals(api, original, cfg, exp, lean):
    failing = [c["id"] for c in lean.get("coupled_checks", [])
               if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"]
    adjustable = {}
    for c in exp.get("coupled", []):
        adjustable.update(api._catalog.coupled_models.get(c["model"], {}).get("parameters", {}) or {})
    proposed = smt.suggest_parameters(cfg, exp, failing, adjustable) if failing else []
    by_name = {p["name"]: p for p in original.get("params", [])}
    choices = {}
    for p in proposed:
        name = p["parameter"]
        param = by_name.get(name, {})
        q = param.get("value")
        if p.get("status") != "found" or not isinstance(q, dict) or set(q) != {"value", "unit"}:
            continue
        target = units.from_lean(p["suggested_quantity"])
        current = units.to_si(q["value"], q["unit"])
        direction = adjustable.get(name, {}).get("adjustable")
        if (direction == "decrease" and target >= current) or (direction == "increase" and target <= current):
            continue
        # Keep exact rationals, in the original parameter's unit; never use a rounded display string.
        value = str(target / units.unit(q["unit"]).scale)
        quantity = {"value": value, "unit": q["unit"]}
        choices.setdefault(name, {})[value] = quantity
    names = sorted(choices)
    # Bounded combinations allow independent coupled failures to be repaired together.
    # Unchanged options are included; requirements and fixed parameters never enter the search.
    for combination in itertools.islice(itertools.product(*[[None, *choices[n].values()] for n in names]), 256):
        changes = {n: q for n, q in zip(names, combination) if q is not None}
        if changes:
            candidate = copy.deepcopy(original)
            edits.apply_parameter_values(api._catalog, candidate, changes)
            candidate["confirmed"] = True
            yield candidate, changes


def suggest(api, result_id: str, max_results: int = 6):
    record = _record(api, result_id)
    original = record["result"]
    if not original["experiment"]["confirmed"]:
        raise ValueError("Review and confirm the requirements before searching for repairs.")
    source_hash = verifier._cached_source_hash()
    cached = record.get("verified_repairs")
    if cached and cached["source_hash"] == source_hash:
        return cached["public"]
    if original["verdict"] == MET:
        return {"result_id": result_id, "fixes": [], "status": "already_compatible",
                "message": "This setup already meets the confirmed requirements."}
    cat, ex = api._catalog, record["experiment"]
    cfg, exp = original["lean_input"]["configuration"], original["lean_input"]["experiment"]
    # The input was already checked; obtain detailed failures from the real checker, never from UI text.
    checked = lean_runner.check(cfg, exp)
    proposed = []
    for candidate, changes in _parameter_proposals(api, ex, cfg, exp, checked):
        cd, ed, _, _ = verifier.build_documents(cat, candidate, record["configuration_id"], record["extra_modifications"])
        proposed.append((record["configuration_id"], candidate, changes, cd, ed, record["extra_modifications"]))
    alternatives = []
    for cid in sorted(cat.configurations):
        if cid == record["configuration_id"]:
            continue
        cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
        alternatives.append((cd, ed))
    models = {cid: f"{c.get('manufacturer', '')} {c.get('model', '')} {c.get('name', '')}"
              for cid, c in cat.configurations.items()}
    ranked = smt.rank_alternatives(alternatives, allow_options=False,
                                   reported_equipment=ex.get("reported_equipment", []), models=models)
    by_document = {verifier.build_documents(cat, ex, cid)[0]["id"]: cid for cid in cat.configurations}
    for r in ranked:
        if r["evaluation"]["status"] == "conflict":
            continue
        cd, ed = r["configuration_document"], r["experiment_document"]
        proposed.append((by_document[cd["id"]], copy.deepcopy(ex), {}, cd, ed, []))
    # EVERY candidate that reaches the solution list must pass Lean, including all coupled checks.
    results = lean_runner.check_batch([(p[3], p[4]) for p in proposed]) if proposed else []
    if len(results) != len(proposed):
        raise lean_runner.LeanUnavailable("Incomplete repair evaluation; no solutions can be recommended.")
    public, private = [], {}
    rejected = {"DOES_NOT_MEET_REQUIREMENTS": 0, "NEED_MORE_INFORMATION": 0}
    for p, raw in zip(proposed, results):
        cid, candidate, changes, cd, ed, mods = p
        if raw.get("verdict") != MET:
            if raw.get("verdict") not in rejected:
                raise lean_runner.LeanUnavailable("Invalid repair verdict; no solutions can be recommended.")
            rejected[raw["verdict"]] += 1
            continue
        if len(public) >= max_results:
            continue
        result = verifier.check(cat, candidate, cid, mods, suggestions=False)
        if result["verdict"] != MET or result["lean_input"] != {"configuration": cd, "experiment": ed}:
            raise RepairStale("The repair changed during verification. Run the original check again.")
        if candidate["requirements"] != ex["requirements"]:
            raise ValueError("Repair search must preserve all scientific requirements.")
        repair_id = "fix_" + uuid.uuid4().hex
        params = {p["name"]: p["value"] for p in candidate.get("params", []) if p.get("value") is not None}
        before = {p["name"]: p.get("value") for p in ex.get("params", [])}
        fix = {"id": repair_id, "kind": "parameter_adjustment" if changes else "alternative_equipment",
               "title": ("Adjust " + ", ".join(changes)) if changes else "Switch to " + result["equipment"]["configuration_name"],
               "reason": original["user_message"], "configuration_id": cid,
               "configuration_name": result["equipment"]["configuration_name"], "parameters": params,
               "changes": [{"parameter": n, "before": before[n], "after": q} for n, q in changes.items()],
               "verified": True, "lean_verdict": MET, "hypothetical": False,
               "verified_at": result["checked_at"], "verification": result["verification"],
               "verdict_card": result["verdict_card"], "lean_input": result["lean_input"],
               "fingerprint": result["fingerprint"], "checks": result["checks"], "coupled_checks": result["coupled_checks"],
               "references": result["references"]}
        public.append(fix)
        private[repair_id] = {"experiment": candidate, "configuration_id": cid, "extra_modifications": mods, "fix": fix}
    response = {"result_id": result_id, "fixes": public,
                "status": "verified_solutions" if public else "no_verified_solution",
                "message": f"{len(public)} Lean-verified solution(s) found." if public else "No verified solution found",
                "evaluated_candidates": len(proposed), "discarded": rejected,
                "search_scope": "Existing documented configurations and model-declared adjustable parameters; unchanged requirements; no assumed installations."}
    record["verified_repairs"] = {"source_hash": source_hash, "public": response, "candidates": private}
    _save(api, result_id, record)
    return response


def apply(api, result_id: str, repair_id: str):
    record = _record(api, result_id)
    saved = record.get("verified_repairs", {})
    if saved.get("source_hash") != verifier._cached_source_hash():
        raise RepairStale("The checker changed since this repair was verified. Search again.")
    candidate = saved.get("candidates", {}).get(repair_id)
    if not candidate:
        raise CatalogError("No verified repair with this ID belongs to the original result.")
    fix = candidate["fix"]
    ex, cid, mods = candidate["experiment"], candidate["configuration_id"], candidate["extra_modifications"]
    cd, ed, _, _ = verifier.build_documents(api._catalog, ex, cid, mods)
    fp = serialize.fingerprint({"catalog_version": api._catalog.version}, cd, ed)
    if fp != fix["fingerprint"] or {"configuration": cd, "experiment": ed} != fix["lean_input"]:
        raise RepairStale("The exact verified inputs have changed. Search again before applying a fix.")
    result = verifier.check(api._catalog, ex, cid, mods, suggestions=False)
    # Deterministic recheck is authoritative. Never coerce a changed or unexpected outcome to PASS.
    if result["verdict"] != MET or result["verification"]["concrete_evaluation"]["lean_input_hash"] != fix["verification"]["concrete_evaluation"]["lean_input_hash"]:
        raise RepairStale("Lean did not reproduce the verified repair. No passing result was applied; run a fresh check.")
    result["repair_application"] = {"original_result_id": result_id, "repair_id": repair_id,
                                    "requirements_unchanged": True, "matched_verified_input": True,
                                    "changes": fix["changes"], "parameters": fix["parameters"],
                                    "original_configuration_id": record["configuration_id"]}
    api._store(result, ex, cid, mods)
    return result
