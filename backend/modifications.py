"""Known modifications and user-entered instrument values.

A user can describe *their* instrument where it differs from the catalog
configuration:

* ``documented: true``  – a modification or measured value the user vouches for
  (e.g. "our transport puck accepts samples up to 5 x 5 mm").  The capability is
  replaced with ``evidence_status: user_entered`` — Lean may use it, and every
  result shows that the evidence is user-entered.
* ``documented: false`` – an undocumented modification that affects a
  capability (e.g. "the magnet was re-wound by a third party").  The capability
  becomes UNKNOWN (value unknown, install unknown) so Lean can only answer
  NEED_MORE_INFORMATION for any requirement on it.

The modified document gets a new id ``<configuration_id>~mod:<hash>`` so a
verdict for a modified instrument can never be mistaken for one about the
catalog configuration (the Lean result echoes the id it checked).
"""
from __future__ import annotations

import copy
import hashlib
import json

from .catalog import Catalog
from .validation import Report, validate_cap_value

VALID_INSTALL = {"installed", "optional_not_installed", "unknown"}


class ModificationError(ValueError):
    pass


def apply_overrides(catalog: Catalog, cfg_doc: dict, overrides: list[dict]) -> dict:
    if not overrides:
        return cfg_doc
    doc = copy.deepcopy(cfg_doc)
    caps = {c["key"]: c for c in doc["capabilities"]}
    applied = []
    for i, o in enumerate(overrides):
        key = o.get("key")
        if not key:
            raise ModificationError(f"override {i}: missing key")
        vk = catalog.vocabulary_key(key)
        if vk is None:
            raise ModificationError(f"override {i}: key '{key}' is not in the vocabulary; propose it first")
        documented = bool(o.get("documented", False))
        if documented:
            value = o.get("value")
            if value is None:
                raise ModificationError(f"override {i}: a documented override needs a value")
            rep = Report()
            validate_cap_value(value, f"override[{i}].value", rep, vk.get("shape"), vk.get("unit") or None)
            if not rep.ok:
                raise ModificationError("; ".join(str(e) for e in rep.errors))
            install = o.get("install", "installed")
            if install not in VALID_INSTALL:
                raise ModificationError(f"override {i}: install must be one of {sorted(VALID_INSTALL)}")
            new = {"key": key, "value": value, "install": install, "evidence_status": "user_entered",
                   "evidence_ids": [f"user_override:{key}"]}
        else:
            new = {"key": key, "value": {"kind": "unknown"}, "install": "unknown", "evidence_status": "unknown",
                   "evidence_ids": [f"undocumented_modification:{key}"]}
        caps[key] = new
        applied.append({"key": key, "documented": documented, "note": o.get("note", "")})
    doc["capabilities"] = list(caps.values())
    digest = hashlib.sha256(json.dumps(applied + [c for c in doc["capabilities"] if c["key"] in {a["key"] for a in applied}],
                                       sort_keys=True).encode()).hexdigest()[:8]
    doc["id"] = f"{cfg_doc['id']}~mod:{digest}"
    doc["name"] = f"{cfg_doc.get('name', cfg_doc['id'])} (with user-described modifications)"
    return doc


def describe_overrides(overrides: list[dict]) -> list[dict]:
    out = []
    for o in overrides or []:
        out.append({"key": o.get("key"), "documented": bool(o.get("documented", False)), "note": o.get("note", ""),
                    "effect": ("user-entered value used by the checker" if o.get("documented")
                               else "capability treated as UNKNOWN (undocumented modification)")})
    return out
