"""Rules for user edits of a prepared experiment profile.

* A requirement's `mandatory` flag cannot be changed and a mandatory requirement
  cannot be removed (the AI or the UI can never weaken a profile this way).
* Editing a value marks the requirement `user_entered`, clears its evidence ids
  and resets confirmation; Lean never accepts an unconfirmed profile.
* Parameters may be set by the user; a supplied value becomes `user_entered`.
"""
from __future__ import annotations

from . import units


class EditError(ValueError):
    pass


def _req_id(r: dict) -> str:
    return "|".join(r.get("keys") or [r["key"]])


def _user_quantity(q, where: str) -> None:
    """User input must be exactly {value, unit}: no internal num/den/dim, no floats."""
    if not isinstance(q, dict) or set(q) != {"value", "unit"}:
        raise EditError(f"{where} must be exactly {{value, unit}}, got {q!r}")
    units.to_si(q["value"], q["unit"])


def _check_constraint(catalog, key: str, c) -> None:
    if not isinstance(c, dict):
        raise EditError("constraint must be an object")
    for side in ("q", "lo", "hi"):
        if side in c:
            _user_quantity(c[side], f"constraint.{side}")
    if catalog is not None:
        from .validation import Report, validate_constraint
        voc = catalog.vocabulary.get(key)
        if voc is None:
            raise EditError(f"key {key!r} is not in the vocabulary (propose it first)")
        rep = Report()
        validate_constraint(c, f"edit({key})", rep, voc["shape"], voc.get("unit") or None)
        if not rep.ok:
            raise EditError("; ".join(str(i) for i in rep.errors))


def apply_requirement_edits(ex: dict, edits: list[dict], catalog=None) -> None:
    reqs = ex["requirements"]
    for e in edits:
        key = e.get("key")
        if not key:
            raise EditError("an edit needs a key")
        existing = next((r for r in reqs if _req_id(r) == key or r.get("key") == key), None)
        if e.get("remove"):
            if existing is None:
                raise EditError(f"no requirement '{key}' to remove")
            if existing["mandatory"]:
                raise EditError(f"'{key}' is a mandatory requirement of the prepared experiment and cannot be removed")
            reqs.remove(existing)
            continue
        if "mandatory" in e and e["mandatory"] is not None and existing is not None and bool(e["mandatory"]) != bool(existing["mandatory"]):
            raise EditError("the mandatory flag of a prepared requirement cannot be changed")
        if e.get("constraint") is not None:
            _check_constraint(catalog, key, e["constraint"])
        if existing is None:
            if "constraint" not in e:
                raise EditError(f"new requirement '{key}' needs a constraint")
            reqs.append({"key": key, "constraint": e["constraint"], "mandatory": bool(e.get("mandatory", True)),
                         "origin": "user_entered", "rationale": e.get("rationale") or "Entered by the user.", "evidence_ids": []})
        elif "constraint" in e and e["constraint"] is not None:
            existing["constraint"] = e["constraint"]
            existing["origin"] = "user_entered"
            existing["rationale"] = e.get("rationale") or f"Edited by the user (was: {existing.get('rationale', '')})"
            existing["evidence_ids"] = []
    ex["confirmed"] = False


def apply_parameter_values(catalog, ex: dict, parameters: dict) -> None:
    """parameters: {name: {"value": "...", "unit": "..."} | "material:<id>@<mK>" | null}."""
    by_name = {p["name"]: p for p in ex.setdefault("params", [])}
    for name, v in parameters.items():
        if v is not None and not (isinstance(v, str) and v.startswith("material:")):
            _user_quantity(v, f"parameter '{name}'")
        if name == "contraction_data_temperature":
            raise EditError("contraction_data_temperature is derived from the material data and cannot be set")
        p = by_name.get(name)
        if p is None:
            p = {"name": name}
            ex["params"].append(p)
            by_name[name] = p
        p["value"] = v
        p["origin"] = "user_entered" if not (isinstance(v, str) and v.startswith("material:")) else "reference_data"
        p["evidence_ids"] = [f"user_param:{name}"] if p["origin"] == "user_entered" else []
