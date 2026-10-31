"""Structural and provenance validation of catalog data.

Used by ``scripts/validate_sources.py`` (CI gate) and by the research pipeline
(candidate intake).  Validation never changes a value; it only reports.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

EVIDENCE_STATUSES = {"manufacturer_specification", "experimental_observation", "user_entered", "inferred_estimate", "unknown"}
INSTALL_STATUSES = {"installed", "optional_not_installed", "unknown"}
VALUE_KINDS = {"range", "max", "min", "flag", "count", "unknown"}
CONSTRAINT_KINDS = {"point_within", "range_within", "at_least", "at_most", "present", "count_at_least"}
SHAPE_TO_CONSTRAINTS = {
    "range": {"point_within", "range_within", "at_least", "at_most"},
    "max": {"at_least"},
    "min": {"at_most"},
    "flag": {"present"},
    "count": {"count_at_least"},
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


@dataclass
class Issue:
    level: str  # "error" | "warning"
    path: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.path}: {self.message}"


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def error(self, path: str, msg: str) -> None:
        self.issues.append(Issue("error", path, msg))

    def warn(self, path: str, msg: str) -> None:
        self.issues.append(Issue("warning", path, msg))

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate_quantity(q: Any, path: str, rep: Report, unit: str | None = None) -> None:
    if not isinstance(q, dict):
        rep.error(path, "quantity must be an object {value, unit}")
        return
    if not _is_int(q.get("value")):
        rep.error(path, f"quantity value must be an integer in canonical units, got {q.get('value')!r}")
    if not isinstance(q.get("unit"), str) or not q["unit"]:
        rep.error(path, "quantity unit must be a non-empty string")
    elif unit is not None and q["unit"] != unit:
        rep.error(path, f"unit '{q['unit']}' does not match the vocabulary canonical unit '{unit}' (Lean would report unsupported)")


def _validate_normalized(norm, path: str, rep: Report, units: dict) -> None:
    """`normalized` is a quantity {value, unit}, a range {lo, hi} (optionally kind:"range"), or a dict of
    named integer fields sharing a `unit`. Integers only; units should be canonical (warning otherwise, since
    evidence records may document facts under proposed vocabulary keys that Lean never sees)."""
    if not isinstance(norm, dict):
        rep.error(path, f"normalized must be an object; got {norm!r}")
        return
    def check_unit(u):
        if not isinstance(u, str) or not u:
            rep.error(path, "normalized unit must be a non-empty string")
        elif u not in units:
            rep.warn(path, f"normalized unit '{u}' is not a canonical unit (fine for evidence, but Lean cannot compare it)")
    if "lo" in norm and "hi" in norm:
        for side in ("lo", "hi"):
            q = norm[side]
            if not isinstance(q, dict) or not _is_int(q.get("value")):
                rep.error(path, f"normalized.{side} must be {{value:int, unit}}")
            else:
                check_unit(q.get("unit"))
        return
    if "unit" in norm:
        check_unit(norm["unit"])
        for k, v in norm.items():
            if k in ("unit", "kind"):
                continue
            if not _is_int(v):
                rep.error(path, f"normalized.{k} must be an integer; got {v!r}")
        if not any(_is_int(v) for k, v in norm.items() if k not in ("unit", "kind")):
            rep.error(path, "normalized has a unit but no integer value")
        return
    rep.error(path, f"normalized must be {{value,unit}}, {{lo,hi}} or named integer fields with a unit; got {norm!r}")


def validate_evidence_record(rec: dict, path: str, rep: Report, units: dict) -> None:
    for k in ("id", "claim", "source_url", "document_title", "evidence_status", "accessed"):
        if not rec.get(k) and not (k == "claim" and rec.get("evidence_status") == "unknown"):
            rep.error(path, f"missing required field '{k}'")
    st = rec.get("evidence_status")
    if st not in EVIDENCE_STATUSES:
        rep.error(path, f"evidence_status '{st}' not in {sorted(EVIDENCE_STATUSES)}")
    url = rec.get("source_url", "")
    if url and not (url.startswith("http://") or url.startswith("https://")):
        rep.error(path, f"source_url must be http(s): {url}")
    if rec.get("accessed") and not DATE_RE.match(str(rec["accessed"])):
        rep.error(path, "accessed must be YYYY-MM-DD")
    if st in ("manufacturer_specification", "experimental_observation"):
        if not rec.get("quote"):
            rep.error(path, "a specification/observation record must carry a verbatim quote")
        if not rec.get("location"):
            rep.warn(path, "no page/section/table location recorded")
    if rec.get("doi") and not DOI_RE.match(str(rec["doi"])):
        rep.error(path, f"malformed DOI {rec['doi']!r}")
    norm = rec.get("normalized")
    if norm is not None:
        _validate_normalized(norm, path, rep, units)
        if not rec.get("value_as_printed"):
            rep.warn(path, "normalized value without value_as_printed")
    if st == "unknown" and norm is not None:
        rep.error(path, "an UNKNOWN record must not carry a normalized value")


def validate_cap_value(v: Any, path: str, rep: Report, shape: str | None, unit: str | None) -> None:
    if not isinstance(v, dict) or v.get("kind") not in VALUE_KINDS:
        rep.error(path, f"value.kind must be one of {sorted(VALUE_KINDS)}")
        return
    kind = v["kind"]
    if kind == "unknown":
        return
    if shape and kind != shape:
        rep.error(path, f"value kind '{kind}' does not match vocabulary shape '{shape}' for this key")
    if kind == "range":
        validate_quantity(v.get("lo"), path + ".lo", rep, unit)
        validate_quantity(v.get("hi"), path + ".hi", rep, unit)
        if isinstance(v.get("lo"), dict) and isinstance(v.get("hi"), dict) and _is_int(v["lo"].get("value")) and _is_int(v["hi"].get("value")):
            if v["lo"]["value"] > v["hi"]["value"]:
                rep.error(path, "range lo > hi")
    elif kind in ("max", "min"):
        validate_quantity(v.get("q"), path + ".q", rep, unit)
    elif kind == "flag":
        if not isinstance(v.get("b"), bool):
            rep.error(path, "flag value must have boolean b")
    elif kind == "count":
        if not _is_int(v.get("n")) or v["n"] < 0:
            rep.error(path, "count value must have non-negative integer n")


def validate_constraint(c: Any, path: str, rep: Report, shape: str | None, unit: str | None) -> None:
    if not isinstance(c, dict) or c.get("kind") not in CONSTRAINT_KINDS:
        rep.error(path, f"constraint.kind must be one of {sorted(CONSTRAINT_KINDS)}")
        return
    kind = c["kind"]
    if shape and kind not in SHAPE_TO_CONSTRAINTS.get(shape, set()):
        rep.error(path, f"constraint '{kind}' cannot be checked against a '{shape}' capability (Lean would report unsupported)")
    if kind in ("point_within", "at_least", "at_most"):
        validate_quantity(c.get("q"), path + ".q", rep, unit)
    elif kind == "range_within":
        validate_quantity(c.get("lo"), path + ".lo", rep, unit)
        validate_quantity(c.get("hi"), path + ".hi", rep, unit)
    elif kind == "count_at_least":
        if not _is_int(c.get("n")):
            rep.error(path, "count_at_least needs integer n")


def _key_info(key: str, vocab: dict, proposals: list[dict]) -> tuple[str | None, str | None, bool]:
    if key in vocab["keys"]:
        k = vocab["keys"][key]
        return k["shape"], (k["unit"] or None), True
    for p in proposals:
        if p["key"] == key:
            return p["shape"], (p.get("unit") or None), True
    return None, None, False


def validate_configuration(cfg: dict, path: str, rep: Report, vocab: dict, evidence: dict, proposals: list[dict] | None = None) -> None:
    proposals = proposals or []
    for k in ("id", "name", "capabilities"):
        if k not in cfg:
            rep.error(path, f"missing '{k}'")
    seen = set()
    for i, cap in enumerate(cfg.get("capabilities", [])):
        p = f"{path}.capabilities[{i}]({cap.get('key')})"
        key = cap.get("key")
        if not key:
            rep.error(p, "missing key")
            continue
        if key in seen:
            rep.error(p, "duplicate capability key in one configuration (Lean uses the first match)")
        seen.add(key)
        shape, unit, known = _key_info(key, vocab, proposals)
        if not known:
            rep.error(p, f"key '{key}' is not in the vocabulary or proposals")
        if cap.get("install") not in INSTALL_STATUSES:
            rep.error(p, f"install must be one of {sorted(INSTALL_STATUSES)}")
        st = cap.get("evidence_status")
        if st not in EVIDENCE_STATUSES:
            rep.error(p, f"evidence_status must be one of {sorted(EVIDENCE_STATUSES)}")
        validate_cap_value(cap.get("value"), p + ".value", rep, shape, unit)
        kind = (cap.get("value") or {}).get("kind")
        if kind == "unknown" and st not in ("unknown",):
            rep.error(p, "an unknown value must carry evidence_status 'unknown'")
        if kind != "unknown" and st == "unknown":
            rep.error(p, "a concrete value must not carry evidence_status 'unknown' (give it a sourced record or mark the value unknown)")
        ids = cap.get("evidence_ids", [])
        if st in ("manufacturer_specification", "experimental_observation") and not ids:
            rep.error(p, "sourced capability has no evidence_ids")
        for eid in ids:
            if eid not in evidence:
                rep.error(p, f"evidence id '{eid}' not found")
            else:
                rec = evidence[eid]
                if st in ("manufacturer_specification", "experimental_observation") and rec.get("evidence_status") not in (st,):
                    rep.warn(p, f"capability evidence_status '{st}' differs from record '{eid}' status '{rec.get('evidence_status')}'")
                norm = rec.get("normalized")
                if norm and "value" in norm and kind in ("max", "min") and isinstance(cap["value"].get("q"), dict):
                    q = cap["value"]["q"]
                    if norm.get("unit") == q.get("unit") and norm.get("value") != q.get("value") and len(ids) == 1:
                        rep.warn(p, f"capability value {q} differs from the single cited record's normalized {norm}")


def validate_experiment(ex: dict, path: str, rep: Report, vocab: dict, evidence: dict, proposals: list[dict] | None = None) -> None:
    proposals = proposals or []
    for k in ("id", "name", "industry", "requirements", "confirmed"):
        if k not in ex:
            rep.error(path, f"missing '{k}'")
    if not ex.get("sources"):
        rep.error(path, "experiment profile has no sources")
    for i, s in enumerate(ex.get("sources", [])):
        if not (s.get("doi") or s.get("url")):
            rep.error(f"{path}.sources[{i}]", "source needs a DOI or URL")
        if s.get("doi") and not DOI_RE.match(str(s["doi"])):
            rep.error(f"{path}.sources[{i}]", f"malformed DOI {s['doi']!r}")
    mandatory = 0
    for i, r in enumerate(ex.get("requirements", [])):
        p = f"{path}.requirements[{i}]({r.get('key')})"
        key = r.get("key")
        shape, unit, known = _key_info(key or "", vocab, proposals)
        if not known:
            rep.error(p, f"requirement key '{key}' is not in the vocabulary or proposals (Lean would report unknown/unsupported, never pass)")
        if not isinstance(r.get("mandatory"), bool):
            rep.error(p, "mandatory must be boolean")
        elif r["mandatory"]:
            mandatory += 1
        if r.get("origin") not in EVIDENCE_STATUSES:
            rep.error(p, f"origin must be one of {sorted(EVIDENCE_STATUSES)}")
        validate_constraint(r.get("constraint"), p + ".constraint", rep, shape, unit)
        if r.get("origin") in ("experimental_observation", "manufacturer_specification") and not r.get("evidence_ids"):
            rep.error(p, "sourced requirement has no evidence_ids")
        if r.get("origin") == "user_entered" and not r.get("rationale"):
            rep.warn(p, "user-entered requirement without rationale")
        if r.get("origin") == "inferred_estimate" and r.get("mandatory"):
            rep.warn(p, "mandatory requirement rests on an inferred estimate; a reviewer/user must confirm it before the profile is relied on")
        for eid in r.get("evidence_ids", []):
            if eid not in evidence:
                rep.error(p, f"evidence id '{eid}' not found")
    if mandatory == 0:
        rep.warn(path, "no mandatory requirements: Lean will always answer NEED_MORE_INFORMATION")


def validate_catalog(catalog) -> Report:
    rep = Report()
    units = catalog.vocabulary["units"]
    for eid, rec in catalog.evidence.items():
        validate_evidence_record(rec, f"{rec.get('_file', 'evidence')}:{eid}", rep, units)
    for eq in catalog.equipment.values():
        for k in ("id", "manufacturer", "model", "configurations"):
            if k not in eq:
                rep.error(eq["_file"], f"missing '{k}'")
        if not eq.get("configurations"):
            rep.error(eq["_file"], "equipment has no configurations")
        for cfg in eq.get("configurations", []):
            validate_configuration(cfg, f"{eq['_file']}:{cfg.get('id')}", rep, catalog.vocabulary, catalog.evidence, catalog.vocabulary_proposals)
    for ex in catalog.experiments.values():
        validate_experiment(ex, ex["_file"], rep, catalog.vocabulary, catalog.evidence, catalog.vocabulary_proposals)
    return rep
