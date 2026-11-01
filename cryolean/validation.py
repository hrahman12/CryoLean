"""Source-data validation: structure and provenance of the catalog (never changes a value).

This is the gate for research candidates and the check run by
``scripts/validate_sources.py``.  It is separate from, and weaker than, the Lean
proofs: it checks that data is well formed and traceable, not that it is true.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import units

EVIDENCE_STATUSES = {"manufacturer_specification", "experimental_observation", "reference_data", "textbook_model",
                     "user_entered", "inferred_estimate", "unknown"}
LEAN_STATUSES = {"manufacturer_specification", "experimental_observation", "reference_data", "user_entered",
                 "inferred_estimate", "unknown"}
INSTALL = {"installed", "optional_not_installed", "unknown"}
VALUE_KINDS = {"range", "max", "min", "flag", "count", "enum", "set", "unknown"}
CONSTRAINT_KINDS = {"point_within", "range_within", "at_least", "at_most", "present", "absent", "flag_is",
                    "count_at_least", "count_equals", "enum_in", "set_contains"}
SHAPE_TO_CONSTRAINTS = {
    "range": {"point_within", "range_within", "at_least", "at_most"},
    "max": {"at_least"}, "min": {"at_most"},
    "flag": {"present", "absent", "flag_is"},
    "count": {"count_at_least", "count_equals"},
    "enum": {"enum_in"}, "set": {"set_contains"},
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


@dataclass
class Issue:
    level: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.path}: {self.message}"


@dataclass
class Report:
    issues: list = field(default_factory=list)

    def error(self, path, msg):
        self.issues.append(Issue("error", path, msg))

    def warn(self, path, msg):
        self.issues.append(Issue("warning", path, msg))

    @property
    def errors(self):
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self):
        return [i for i in self.issues if i.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {"ok": self.ok, "errors": [str(i) for i in self.errors], "warnings": [str(i) for i in self.warnings]}


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate_quantity(q, path, rep, unit=None):
    if not isinstance(q, dict):
        rep.error(path, "quantity must be {value, unit}")
        return
    if not (_int(q.get("value")) or (isinstance(q.get("value"), str) and q["value"].strip())):
        rep.error(path, f"quantity value must be an integer or an exact decimal string, got {q.get('value')!r}")
    sym = q.get("unit")
    if sym not in units.UNITS:
        rep.error(path, f"unit {sym!r} is not registered in cryolean/units.py")
        return
    try:
        units.to_si(q["value"], sym)
    except Exception as e:  # noqa: BLE001
        rep.error(path, f"value not convertible exactly: {e}")
    if unit and unit in units.UNITS and units.UNITS[sym].dim != units.UNITS[unit].dim:
        rep.error(path, f"unit {sym!r} has a different dimension from the vocabulary unit {unit!r} (Lean would report unsupported)")


def validate_cap_value(v, path, rep, shape, unit):
    if not isinstance(v, dict) or v.get("kind") not in VALUE_KINDS:
        rep.error(path, f"value.kind must be one of {sorted(VALUE_KINDS)}")
        return
    k = v["kind"]
    if k == "unknown":
        return
    if shape and k != shape:
        rep.error(path, f"value kind {k!r} does not match the vocabulary shape {shape!r}")
    if k == "range":
        validate_quantity(v.get("lo"), path + ".lo", rep, unit)
        validate_quantity(v.get("hi"), path + ".hi", rep, unit)
        try:
            if units.to_si(v["lo"]["value"], v["lo"]["unit"]) > units.to_si(v["hi"]["value"], v["hi"]["unit"]):
                rep.error(path, "range lo > hi")
        except Exception:  # noqa: BLE001
            pass
    elif k in ("max", "min"):
        validate_quantity(v.get("q"), path + ".q", rep, unit)
    elif k == "flag" and not isinstance(v.get("b"), bool):
        rep.error(path, "flag needs boolean b")
    elif k == "count" and not (_int(v.get("n")) and v["n"] >= 0):
        rep.error(path, "count needs non-negative integer n")
    elif k == "enum" and not isinstance(v.get("s"), str):
        rep.error(path, "enum needs string s")
    elif k == "set" and not (isinstance(v.get("xs"), list) and all(isinstance(x, str) for x in v["xs"])):
        rep.error(path, "set needs a list of strings xs")


def validate_constraint(c, path, rep, shape, unit):
    if not isinstance(c, dict) or c.get("kind") not in CONSTRAINT_KINDS:
        rep.error(path, f"constraint.kind must be one of {sorted(CONSTRAINT_KINDS)}")
        return
    k = c["kind"]
    if shape and k not in SHAPE_TO_CONSTRAINTS.get(shape, set()):
        rep.error(path, f"constraint {k!r} cannot be checked against a {shape!r} capability (Lean would report unsupported)")
    if k in ("point_within", "at_least", "at_most"):
        validate_quantity(c.get("q"), path + ".q", rep, unit)
    elif k == "range_within":
        validate_quantity(c.get("lo"), path + ".lo", rep, unit)
        validate_quantity(c.get("hi"), path + ".hi", rep, unit)
        try:
            if units.to_si(c["lo"]["value"], c["lo"]["unit"]) > units.to_si(c["hi"]["value"], c["hi"]["unit"]):
                rep.error(path, "range_within lo > hi")
        except Exception:  # noqa: BLE001
            pass
    elif k in ("enum_in", "set_contains") and not (c.get("allowed") or c.get("needed")):
        rep.error(path, f"{k} needs a non-empty list")
    elif k in ("count_at_least", "count_equals") and not _int(c.get("n")):
        rep.error(path, "needs integer n")


def validate_evidence_record(rec, path, rep):
    st = rec.get("evidence_status")
    for k in ("id", "source_url", "document_title", "evidence_status", "accessed"):
        if not rec.get(k):
            rep.error(path, f"missing required field {k!r}")
    if st not in EVIDENCE_STATUSES:
        rep.error(path, f"evidence_status {st!r} not in {sorted(EVIDENCE_STATUSES)}")
    if not rec.get("claim") and st != "unknown":
        rep.error(path, "missing claim")
    url = rec.get("source_url") or ""
    if url and not url.startswith(("http://", "https://")):
        rep.error(path, f"source_url must be http(s): {url}")
    if rec.get("accessed") and not DATE_RE.match(str(rec["accessed"])):
        rep.error(path, "accessed must be YYYY-MM-DD")
    if st in ("manufacturer_specification", "experimental_observation", "reference_data", "textbook_model") and not rec.get("quote"):
        rep.error(path, "a sourced record must carry a verbatim quote")
    if rec.get("doi") and not DOI_RE.match(str(rec["doi"])):
        rep.error(path, f"malformed DOI {rec['doi']!r}")
    if st == "unknown" and rec.get("normalized") not in (None, {}):
        rep.error(path, "an UNKNOWN record must not carry a normalized value")


def _key_info(catalog, key):
    v = catalog.vocabulary.get(key)
    if v is None and key.endswith(".temperature") and key[: -len(".temperature")] in catalog.vocabulary:
        return "max", "mK", True
    return (v["shape"], v.get("unit") or None, True) if v else (None, None, False)


def validate_configuration(catalog, cfg, path, rep):
    seen = set()
    for i, cap in enumerate(cfg.get("capabilities", [])):
        key = cap.get("key")
        p = f"{path}.capabilities[{i}]({key})"
        if key in seen:
            rep.error(p, "duplicate capability key (Lean uses the first match)")
        seen.add(key)
        shape, unit, known = _key_info(catalog, key or "")
        if not known:
            rep.error(p, f"key {key!r} is not in the vocabulary")
        if cap.get("install") not in INSTALL:
            rep.error(p, f"install must be one of {sorted(INSTALL)}")
        st = cap.get("evidence_status")
        if st not in LEAN_STATUSES:
            rep.error(p, f"capability evidence_status must be one of {sorted(LEAN_STATUSES)}")
        validate_cap_value(cap.get("value"), p + ".value", rep, shape, unit)
        kind = (cap.get("value") or {}).get("kind")
        if kind == "unknown" and st != "unknown":
            rep.error(p, "an UNKNOWN value must carry evidence_status 'unknown'")
        if kind != "unknown" and st == "unknown":
            rep.error(p, "a concrete value must not carry evidence_status 'unknown'")
        ids = cap.get("evidence_ids", [])
        if st in ("manufacturer_specification", "experimental_observation", "reference_data") and not ids:
            rep.error(p, "sourced capability has no evidence_ids")
        for eid in ids:
            if eid not in catalog.evidence and not str(eid).startswith(("user_override:", "undocumented_modification:")):
                rep.error(p, f"evidence id {eid!r} not found")


def validate_experiment(catalog, ex, path, rep):
    for k in ("id", "name", "industry", "requirements", "confirmed"):
        if k not in ex:
            rep.error(path, f"missing {k!r}")
    if not ex.get("sources"):
        rep.error(path, "experiment profile has no sources")
    for i, s in enumerate(ex.get("sources", [])):
        if not (s.get("doi") or s.get("url")):
            rep.error(f"{path}.sources[{i}]", "source needs a DOI or URL")
        if s.get("doi") and not DOI_RE.match(str(s["doi"])):
            rep.error(f"{path}.sources[{i}]", f"malformed DOI {s['doi']!r}")
    mandatory = 0
    names = [p.get("name") for p in ex.get("params", [])]
    for dup in sorted({n for n in names if names.count(n) > 1}):
        rep.error(path, f"duplicate parameter {dup!r} (Lean refuses documents with duplicate parameters)")
    for i, r in enumerate(ex.get("requirements", [])):
        keys = r.get("keys") or ([r["key"]] if r.get("key") else [])
        p = f"{path}.requirements[{i}]({'|'.join(keys)})"
        if not keys:
            rep.error(p, "requirement needs key or keys")
        for key in keys:
            shape, unit, known = _key_info(catalog, key)
            if not known:
                rep.error(p, f"key {key!r} is not in the vocabulary (Lean would report unknown, never pass)")
            else:
                validate_constraint(r.get("constraint"), p + ".constraint", rep, shape, unit)
        if not isinstance(r.get("mandatory"), bool):
            rep.error(p, "mandatory must be boolean")
        elif r["mandatory"] and r.get("applicable", True):
            mandatory += 1
        if r.get("origin") not in LEAN_STATUSES:
            rep.error(p, f"origin must be one of {sorted(LEAN_STATUSES)}")
        if r.get("origin") in ("experimental_observation", "manufacturer_specification", "reference_data") and not r.get("evidence_ids"):
            rep.error(p, "sourced requirement has no evidence_ids")
        if r.get("origin") == "inferred_estimate" and r.get("mandatory"):
            rep.warn(p, "mandatory requirement rests on an inferred estimate; a reviewer/user must confirm it")
        for c in r.get("conditions", []):
            if c.get("kind") not in ("cap_flag", "param_at_most", "param_at_least"):
                rep.error(p, f"unknown condition kind {c.get('kind')!r}")
            elif c["kind"] != "cap_flag":
                validate_quantity(c.get("q"), p + ".condition.q", rep)
        for eid in r.get("evidence_ids", []):
            if eid not in catalog.evidence:
                rep.error(p, f"evidence id {eid!r} not found")
    for i, prm in enumerate(ex.get("params", [])):
        p = f"{path}.params[{i}]({prm.get('name')})"
        v = prm.get("value")
        if v is not None and not (isinstance(v, str) and v.startswith("material:")):
            validate_quantity(v, p, rep)
        if prm.get("origin") not in LEAN_STATUSES:
            rep.error(p, f"origin must be one of {sorted(LEAN_STATUSES)}")
        if prm.get("origin") == "experimental_observation" and v is not None and not prm.get("evidence_ids"):
            rep.error(p, "sourced parameter has no evidence_ids")
        for eid in prm.get("evidence_ids", []):
            if eid not in catalog.evidence and not str(eid).startswith("user_param:"):
                rep.error(p, f"evidence id {eid!r} not found")
    for i, c in enumerate(ex.get("coupled", [])):
        p = f"{path}.coupled[{i}]({c.get('model')})"
        m = catalog.coupled_models.get(c.get("model"))
        if m is None:
            rep.error(p, "unknown coupled model")
        elif m.get("status") != "validated":
            (rep.error if c.get("mandatory", True) else rep.warn)(p, f"model status {m.get('status')!r}: it is reported as UNSUPPORTED")
        else:
            if c.get("mandatory", True):
                mandatory += 1
            names = {prm["name"] for prm in ex.get("params", [])}
            for needed in (m.get("parameters") or {}):
                if needed not in names:
                    rep.warn(p, f"parameter {needed!r} is not declared; the check stays NEED_MORE_INFORMATION until supplied")
    if mandatory == 0:
        rep.warn(path, "no mandatory requirements: Lean will always answer NEED_MORE_INFORMATION")


def validate_catalog(catalog) -> Report:
    rep = Report()
    for eid, rec in catalog.evidence.items():
        validate_evidence_record(rec, f"evidence:{eid}", rep)
    for eq in catalog.equipment.values():
        if not eq.get("configurations"):
            rep.error(f"equipment:{eq['id']}", "equipment has no configurations")
        for k in ("manufacturer", "model"):
            if not eq.get(k):
                rep.error(f"equipment:{eq['id']}", f"missing {k!r}")
        for cfg in eq.get("configurations", []):
            validate_configuration(catalog, cfg, f"configuration:{cfg['id']}", rep)
    for ex in catalog.experiments.values():
        validate_experiment(catalog, ex, f"experiment:{ex['id']}", rep)
    for m in catalog.coupled_models.values():
        for eid in m.get("justification_evidence_ids", []):
            if eid not in catalog.evidence:
                rep.error(f"model:{m['id']}", f"justification evidence {eid!r} not found")
    return rep
