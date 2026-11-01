"""The auditable Python -> Lean serialization boundary.

Builds the exact JSON documents the Lean checker reads:

* capability and requirement quantities are converted EXACTLY to SI rationals
  with dimensions (cryolean.units);
* cooling-power capabilities get a companion ``<key>.temperature`` capability
  carrying the documented temperature (same evidence), so coupled models can
  check that the cooling power used applies at the operating temperature;
* coupled-model templates (data/physics/coupled_models.json) are expanded per
  configuration.  A model that is not 'validated', or whose slot cannot be
  resolved, is emitted as an explicitly UNSUPPORTED or UNKNOWN check — never
  dropped, never a pass;
* material references in parameters ("material:<id>@<mK>") are resolved from
  the materials table with their evidence ids.

Nothing in this module decides a verdict.
"""
from __future__ import annotations

import copy
import hashlib
import json
from fractions import Fraction

from . import units
from .catalog import Catalog

# A dimension mismatch that Lean always reports as `unsupported` (used for models that are not validated).
UNSUPPORTED_LHS = {"op": "lit", "q": {"num": 1, "den": 1, "dim": {"K": 1}}}
UNSUPPORTED_RHS = {"op": "lit", "q": {"num": 1, "den": 1, "dim": {"m": 1}}}


class SerializationError(ValueError):
    pass


def _strict_int(x, what):
    if isinstance(x, bool) or not isinstance(x, int):
        raise SerializationError(f"{what} must be an integer, got {x!r}")
    return x


def quantity(q: dict) -> dict:
    """{"value": int|str, "unit": sym} (catalog/user form) -> Lean quantity.
    Internal exact form {"num", "den", "dim"} (only produced by CryoLean itself) is accepted with strict integers."""
    if not isinstance(q, dict):
        raise SerializationError(f"quantity must be an object, got {q!r}")
    if "num" in q or "den" in q:
        if "value" in q or "unit" in q:
            raise SerializationError("a quantity must be either {value, unit} or {num, den, dim}, not both")
        num, den = _strict_int(q.get("num"), "num"), _strict_int(q.get("den"), "den")
        if den <= 0:
            raise SerializationError("den must be positive")
        d = q.get("dim", {})
        if not isinstance(d, dict) or any(k not in units.DIM_KEYS or not isinstance(v, int) or isinstance(v, bool) for k, v in d.items()):
            raise SerializationError(f"invalid dim {d!r}")
        return {"num": num, "den": den, "dim": d}
    return units.lean_quantity(q["value"], q["unit"])


def cap_value(v: dict) -> dict:
    k = v.get("kind")
    if k == "range":
        return {"kind": "range", "lo": quantity(v["lo"]), "hi": quantity(v["hi"])}
    if k in ("max", "min"):
        return {"kind": k, "q": quantity(v["q"])}
    if k == "flag":
        return {"kind": "flag", "b": bool(v["b"])}
    if k == "count":
        return {"kind": "count", "n": int(v["n"])}
    if k == "enum":
        return {"kind": "enum", "s": str(v["s"])}
    if k == "set":
        return {"kind": "set", "xs": [str(x) for x in v["xs"]]}
    if k == "unknown":
        return {"kind": "unknown"}
    raise SerializationError(f"unknown capability value kind {k!r}")


def constraint(c: dict) -> dict:
    k = c.get("kind")
    if k in ("point_within", "at_least", "at_most"):
        return {"kind": k, "q": quantity(c["q"])}
    if k == "range_within":
        return {"kind": k, "lo": quantity(c["lo"]), "hi": quantity(c["hi"])}
    if k in ("present", "absent"):
        return {"kind": k}
    if k == "flag_is":
        return {"kind": k, "b": bool(c["b"])}
    if k in ("count_at_least", "count_equals"):
        return {"kind": k, "n": int(c["n"])}
    if k == "enum_in":
        return {"kind": k, "allowed": [str(x) for x in c["allowed"]]}
    if k == "set_contains":
        return {"kind": k, "needed": [str(x) for x in c["needed"]]}
    raise SerializationError(f"unknown constraint kind {k!r}")


def condition(c: dict) -> dict:
    k = c.get("kind")
    if k == "cap_flag":
        return {"kind": k, "key": c["key"], "b": bool(c["b"])}
    if k in ("param_at_most", "param_at_least"):
        return {"kind": k, "name": c["name"], "q": quantity(c["q"])}
    raise SerializationError(f"unknown condition kind {k!r}")


# ---------------------------------------------------------------------------- configuration
def configuration_doc(catalog: Catalog, cfg: dict) -> dict:
    caps = []
    for c in cfg.get("capabilities", []):
        caps.append({"key": c["key"], "value": cap_value(c["value"]), "install": c["install"],
                     "evidence_status": c["evidence_status"], "evidence_ids": list(c.get("evidence_ids", []))})
        voc = catalog.vocabulary.get(c["key"], {})
        at = voc.get("at_temperature")
        if at:
            caps.append({"key": c["key"] + ".temperature",
                         "value": {"kind": "max", "q": units.lean_quantity(at["value"], at["unit"])} if c["value"].get("kind") != "unknown" else {"kind": "unknown"},
                         "install": c["install"], "evidence_status": c["evidence_status"],
                         "evidence_ids": list(c.get("evidence_ids", []))})
    return {"id": cfg["id"], "equipment_id": cfg["equipment_id"], "name": cfg.get("name", cfg["id"]), "capabilities": caps}


# ---------------------------------------------------------------------------- parameters
def _material(catalog: Catalog, ref: str):
    """'material:<id>@<mK>' -> (contraction quantity | None, evidence ids, temperature in mK). The temperature is mandatory."""
    mid, sep, at = ref[len("material:"):].partition("@")
    if not sep or not at.endswith("mK") or not at[:-2].isdigit():
        raise SerializationError(f"material reference {ref!r} must name its temperature, e.g. 'material:{mid}@4000mK'")
    mat = catalog.materials.get(mid)
    if mat is None:
        raise SerializationError(f"unknown material '{mid}'")
    want = int(at[:-2])
    for val in mat["values"]:
        if val["to_temperature"]["value"] == want and val["to_temperature"]["unit"] == "mK":
            return units.lean_quantity(val["contraction"], "1"), list(val["evidence_ids"]), want
    return None, [], want                    # no tabulated value at that temperature -> missing (UNKNOWN)


def _param_value(catalog: Catalog, p: dict):
    """Returns (lean quantity | None, evidence ids, origin)."""
    v = p.get("value")
    if v is None:
        return None, list(p.get("evidence_ids", [])), p.get("origin", "user_entered")
    if isinstance(v, str) and v.startswith("material:"):
        q, ids, _ = _material(catalog, v)
        return q, ids, "reference_data"
    if isinstance(v, dict):
        return quantity(v), list(p.get("evidence_ids", [])), p.get("origin", "user_entered")
    raise SerializationError(f"parameter {p.get('name')!r} has an unsupported value {v!r}")


def params_doc(catalog: Catalog, params: list[dict]) -> list[dict]:
    out = []
    temps = set()
    for p in params:
        q, _, origin = _param_value(catalog, p)
        if isinstance(p.get("value"), str) and p["value"].startswith("material:"):
            temps.add(_material(catalog, p["value"])[2])
        out.append({"name": p["name"], "value": q, "origin": origin})
    if temps:
        # the temperature of the contraction data actually used is DERIVED, never taken from the user
        out = [x for x in out if x["name"] != "contraction_data_temperature"]
        out.append({"name": "contraction_data_temperature",
                    "value": units.lean_quantity(temps.pop(), "mK") if len(temps) == 1 else None,
                    "origin": "reference_data"})
    return out


# ---------------------------------------------------------------------------- coupled models
def _expr(template: dict, slots: dict[str, str]) -> dict:
    op = template["op"]
    if op == "lit":
        if "q" in template:
            return {"op": "lit", "q": template["q"]}
        return {"op": "lit", "q": units.lean_quantity(template["value"], template["unit"])}
    if op == "cap":
        key = template["key"]
        if key.startswith("$"):
            base, _, suffix = key[1:].partition(".")
            key = slots.get(base, f"__unresolved_slot__{base}") + (("." + suffix) if suffix else "")
        return {"op": "cap", "key": key, "sel": template["sel"]}
    if op == "param":
        return {"op": "param", "name": template["name"]}
    if op in ("add", "sub", "mul"):
        return {"op": op, "a": _expr(template["a"], slots), "b": _expr(template["b"], slots)}
    if op == "neg":
        return {"op": "neg", "a": _expr(template["a"], slots)}
    raise SerializationError(f"unknown expression op {op!r}")


def _params_in(x) -> list[dict]:
    out = []
    if isinstance(x, dict):
        if x.get("op") == "param":
            out.append(x)
        for v in x.values():
            out += _params_in(v)
    elif isinstance(x, list):
        for v in x:
            out += _params_in(v)
    return out


def resolve_slots(catalog: Catalog, model: dict, cfg: dict, params: list[dict]) -> tuple[dict[str, str], list[str]]:
    """Resolve '$slot' capability keys for one configuration. Returns (slots, notes)."""
    slots, notes = {}, []
    for name, spec in (model.get("slots") or {}).items():
        pattern = spec["pattern"]
        if pattern == "cooling_power.at_*":
            top = next((p for p in params if p["name"] == "operating_temperature"), None)
            t_op = units.to_si(top["value"]["value"], top["value"]["unit"]) if top and isinstance(top.get("value"), dict) else None
            best = None
            for c in cfg.get("capabilities", []):
                voc = catalog.vocabulary.get(c["key"], {})
                at = voc.get("at_temperature")
                if (not c["key"].startswith("cooling_power.at_") or not at or c["value"].get("kind") == "unknown"
                        or c.get("install") != "installed"):
                    continue
                t_doc = units.to_si(at["value"], at["unit"])
                if t_op is not None and t_doc <= t_op and (best is None or t_doc > best[0]):
                    best = (t_doc, c["key"])
            if best:
                slots[name] = best[1]
                notes.append(f"{name}: using {best[1]} (highest documented temperature not above the operating temperature)")
            else:
                notes.append(f"{name}: no documented cooling power at or below the operating temperature -> missing")
        else:
            notes.append(f"{name}: unsupported slot pattern {pattern}")
    return slots, notes


def coupled_docs(catalog: Catalog, experiment: dict, cfg: dict) -> tuple[list[dict], list[dict]]:
    """Expand the experiment's coupled entries for this configuration. Returns (lean docs, explanations)."""
    docs, info = [], []
    for i, entry in enumerate(experiment.get("coupled", [])):
        model = catalog.coupled_models.get(entry["model"])
        mandatory = bool(entry.get("mandatory", True))
        applicable = bool(entry.get("applicable", True))
        base = {"mandatory": mandatory, "applicable": applicable,
                "conditions": [condition(c) for c in entry.get("conditions", [])],
                "origin": entry.get("origin", "experimental_observation"),
                "rationale": entry.get("rationale", "")}
        if model is None or model.get("status") != "validated" or not model.get("relations"):
            reason = "unknown model" if model is None else f"model status '{model.get('status')}'"
            docs.append({**base, "id": f"{entry['model']}#{i}", "name": (model or {}).get("name", entry["model"]),
                         "model": entry["model"], "lhs": UNSUPPORTED_LHS, "rhs": UNSUPPORTED_RHS, "validity": [],
                         "evidence_ids": [], "rationale": f"{base['rationale']} [{reason}: not evaluated -> UNSUPPORTED]".strip()})
            info.append({"model": entry["model"], "status": (model or {}).get("status", "unknown_model"), "slots": {}, "notes": [reason]})
            continue
        slots, notes = resolve_slots(catalog, model, cfg, experiment.get("params", []))
        # physical parameters are non-negative unless the model marks them "signed": enforced by Lean as validity bounds
        nonneg = []
        for pname, meta in sorted((model.get("parameters") or {}).items()):
            if meta.get("signed"):
                continue
            sym = meta.get("unit_dim", "1")
            zero = {"num": 0, "den": 1, "dim": units.unit(sym).dim_dict()} if sym in units.UNITS else None
            if zero is not None:
                nonneg.append({"a": {"op": "lit", "q": zero}, "b": {"op": "param", "name": pname}})
        for j, rel in enumerate(model["relations"]):
            used = {x["name"] for x in _params_in(rel) + [p for v in model.get("validity", []) for p in _params_in(v)]}
            docs.append({**base, "id": f"{model['id']}#{i}.{j}", "name": model["name"] + (f" (relation {j + 1})" if len(model["relations"]) > 1 else ""),
                         "model": model["id"], "lhs": _expr(rel["lhs"], slots), "rhs": _expr(rel["rhs"], slots),
                         "validity": [{"a": _expr(v["a"], slots), "b": _expr(v["b"], slots)} for v in model.get("validity", [])]
                                     + [v for v in nonneg if v["b"]["name"] in used],
                         "evidence_ids": list(model.get("justification_evidence_ids", []))})
        info.append({"model": model["id"], "status": model["status"], "equation": model.get("equation"),
                     "assumptions": model.get("assumptions", []), "valid_range": model.get("valid_range"),
                     "slots": slots, "notes": notes})
    return docs, info


# ---------------------------------------------------------------------------- experiment
def requirement_doc(r: dict) -> dict:
    keys = r.get("keys") or [r["key"]]
    return {"keys": list(keys), "constraint": constraint(r["constraint"]), "mandatory": bool(r["mandatory"]),
            "applicable": bool(r.get("applicable", True)), "conditions": [condition(c) for c in r.get("conditions", [])],
            "origin": r["origin"], "rationale": r.get("rationale", ""), "evidence_ids": list(r.get("evidence_ids", []))}


def experiment_doc(catalog: Catalog, experiment: dict, cfg: dict) -> tuple[dict, list[dict]]:
    coupled, info = coupled_docs(catalog, experiment, cfg)
    doc = {"id": experiment["id"], "name": experiment.get("name", experiment["id"]),
           "industry": experiment.get("industry", "unspecified"),
           "params": params_doc(catalog, experiment.get("params", [])),
           "requirements": [requirement_doc(r) for r in experiment.get("requirements", [])],
           "coupled": coupled, "confirmed": bool(experiment.get("confirmed", False))}
    return doc, info


def fingerprint(*docs: dict) -> str:
    h = hashlib.sha256()
    for d in docs:
        h.update(json.dumps(d, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return h.hexdigest()


def working_experiment(catalog: Catalog, experiment_id: str, parameters: dict | None = None,
                       requirement_edits: list[dict] | None = None, confirmed: bool | None = None) -> dict:
    """Copy of a prepared profile with the user's parameters and edits applied (rules in edits.py)."""
    from .edits import apply_parameter_values, apply_requirement_edits
    ex = copy.deepcopy(catalog.get_experiment(experiment_id))
    if parameters:
        apply_parameter_values(catalog, ex, parameters)
    if requirement_edits:
        apply_requirement_edits(ex, requirement_edits, catalog)
    # strict: only an explicit boolean True confirms; the stored profile flag is never inherited
    ex["confirmed"] = confirmed is True
    return ex


def display_lean_quantity(q: dict) -> str:
    return units.display(Fraction(int(q["num"]), int(q["den"])), units.dims_of(q))
