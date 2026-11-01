"""Equipment modifications that affect compatibility.

Three statuses, never confused:
* ``installed_documented`` – a modification that IS fitted and is documented by
  the user (e.g. "larger sample holder, 5 x 5 mm"); its values enter the check
  as ``user_entered`` evidence.
* ``proposed`` – a possible upgrade that is NOT installed; it never changes a
  check of the real configuration (it can be evaluated as a separate
  hypothetical configuration, clearly labelled).
* ``undocumented`` – something was changed but its effect is not documented; the
  affected capability becomes UNKNOWN, so any requirement on it is
  NEED_MORE_INFORMATION.

The modified document gets a new configuration id ``<id>~mod:<hash>`` so a
verdict for a modified instrument can never be mistaken for one about the
catalog configuration.
"""
from __future__ import annotations

import copy
import hashlib
import json
import uuid

from . import db
from .catalog import Catalog
from .validation import Report, validate_cap_value

STATUSES = ("installed_documented", "proposed", "undocumented")


class ModificationError(ValueError):
    pass


def validate_modification(catalog: Catalog, mod: dict) -> None:
    if mod.get("status") not in STATUSES:
        raise ModificationError(f"status must be one of {STATUSES}")
    for i, ch in enumerate(mod.get("changes", [])):
        key = ch.get("key")
        vk = catalog.vocabulary_key(key or "")
        if vk is None:
            raise ModificationError(f"change {i}: key {key!r} is not in the vocabulary")
        if mod["status"] != "undocumented":
            if "value" not in ch:
                raise ModificationError(f"change {i}: a documented or proposed modification needs a value")
            rep = Report()
            validate_cap_value(ch["value"], f"change[{i}]", rep, vk["shape"], vk.get("unit") or None)
            if not rep.ok:
                raise ModificationError("; ".join(str(e) for e in rep.errors))


def apply(catalog: Catalog, cfg: dict, mods: list[dict], include_proposed: bool = False) -> dict:
    """Return a configuration dict (catalog form) with modifications applied."""
    active = [m for m in mods if m["status"] != "proposed" or include_proposed]
    if not active:
        return cfg
    out = copy.deepcopy(cfg)
    caps = {c["key"]: c for c in out["capabilities"]}
    for m in active:
        validate_modification(catalog, m)
        for ch in m.get("changes", []):
            key = ch["key"]
            if m["status"] == "undocumented":
                caps[key] = {"key": key, "value": {"kind": "unknown"}, "install": "unknown", "evidence_status": "unknown",
                             "evidence_ids": [f"undocumented_modification:{key}"]}
            else:
                caps[key] = {"key": key, "value": ch["value"], "install": ch.get("install", "installed"),
                             "evidence_status": "user_entered", "evidence_ids": [f"user_override:{key}"]}
    out["capabilities"] = list(caps.values())
    digest = hashlib.sha256(json.dumps([{k: m.get(k) for k in ("status", "changes")} for m in active], sort_keys=True).encode()).hexdigest()[:8]
    out["id"] = f"{cfg['id']}~mod:{digest}"
    out["name"] = f"{cfg.get('name', cfg['id'])} (with {'proposed' if include_proposed else 'documented'} modifications)"
    out["modifications_applied"] = [{"id": m.get("id"), "status": m["status"], "description": m.get("description", "")} for m in active]
    out["hypothetical"] = any(m["status"] == "proposed" for m in active)
    return out


def register(catalog: Catalog, configuration_id: str, status: str, changes: list[dict], description: str = "") -> dict:
    catalog.get_configuration(configuration_id)
    mod = {"status": status, "changes": changes, "description": description}
    validate_modification(catalog, mod)
    mid = "mod_" + uuid.uuid4().hex[:10]
    con = catalog.connect()
    with con:
        con.execute("INSERT INTO modifications VALUES (?,?,?,?,?)", (mid, configuration_id, status, db.now(), db.dumps(mod)))
    con.close()
    catalog.reload()
    return catalog.modifications[mid]


def for_configuration(catalog: Catalog, configuration_id: str) -> list[dict]:
    return [m for m in catalog.modifications.values() if m["configuration_id"] == configuration_id]
