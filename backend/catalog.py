"""Trusted catalog loader.

Everything the checker reasons about is data under ``data/``:

* ``capability_vocabulary.json`` – extensible key/unit vocabulary
* ``cryostats/*.json``            – equipment with one or more *exact* configurations
* ``experiments/*.json``          – research-grounded experiment profiles
* ``evidence/*.json``             – provenance fragments (compiled into ``evidence.json``)
* ``industries.json``             – curated industries; ``registry/industries.json`` – registered at runtime

Industries are opaque labels here and in Lean; nothing branches on them.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config

STANDARD_INDUSTRIES = [
    ("scientific_research", "Scientific research"),
    ("healthcare_and_medicine", "Healthcare and medicine"),
    ("biology_and_biotechnology", "Biology and biotechnology"),
    ("chemistry_and_pharmaceuticals", "Chemistry and pharmaceuticals"),
    ("materials_and_nanotechnology", "Materials and nanotechnology"),
    ("quantum_computing_and_sensing", "Quantum computing and sensing"),
    ("physics_and_particle_accelerators", "Physics and particle accelerators"),
    ("aerospace_and_space_exploration", "Aerospace and space exploration"),
    ("astronomy_and_astrophysics", "Astronomy and astrophysics"),
    ("semiconductors_and_electronics", "Semiconductors and electronics"),
    ("photonics_and_telecommunications", "Photonics and telecommunications"),
    ("energy_and_hydrogen", "Energy and hydrogen"),
    ("nuclear_engineering_and_fusion", "Nuclear engineering and fusion"),
    ("manufacturing_and_industrial_processing", "Manufacturing and industrial processing"),
    ("automotive_and_transportation", "Automotive and transportation"),
    ("food_and_agriculture", "Food and agriculture"),
    ("environmental_science", "Environmental science"),
    ("geology_and_oceanography", "Geology and oceanography"),
    ("metrology_and_calibration", "Metrology and calibration"),
    ("defense_and_security", "Defense and security"),
]


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def slugify(name: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


class CatalogError(Exception):
    pass


class Catalog:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir or config.DATA_DIR)
        self.reload()

    # ------------------------------------------------------------------ loading
    def reload(self) -> None:
        d = self.data_dir
        self.vocabulary: dict = _read_json(d / "capability_vocabulary.json")
        reg_vocab = d / "registry" / "vocabulary_proposals.json"
        self.vocabulary_proposals: list[dict] = _read_json(reg_vocab) if reg_vocab.exists() else []
        # per-file proposals: a profile may document a fact under a key the vocabulary lacks yet
        for sub in ("cryostats", "experiments"):
            for p in sorted((d / sub).glob("*.json")):
                for prop in _read_json(p).get("proposed_vocabulary", []) or []:
                    if "key" in prop and not any(x["key"] == prop["key"] for x in self.vocabulary_proposals):
                        self.vocabulary_proposals.append({**prop, "status": "proposed", "proposed_in": p.name})

        self.equipment: dict[str, dict] = {}
        self.configurations: dict[str, dict] = {}
        for p in sorted((d / "cryostats").glob("*.json")):
            eq = _read_json(p)
            eq["_file"] = p.name
            if eq["id"] in self.equipment:
                raise CatalogError(f"duplicate equipment id {eq['id']} in {p}")
            self.equipment[eq["id"]] = eq
            for cfg in eq.get("configurations", []):
                if cfg["id"] in self.configurations:
                    raise CatalogError(f"duplicate configuration id {cfg['id']} in {p}")
                c = dict(cfg)
                c["equipment_id"] = eq["id"]
                c["manufacturer"] = eq.get("manufacturer")
                c["model"] = eq.get("model")
                self.configurations[cfg["id"]] = c

        self.experiments: dict[str, dict] = {}
        for p in sorted((d / "experiments").glob("*.json")):
            ex = _read_json(p)
            ex["_file"] = p.name
            if ex["id"] in self.experiments:
                raise CatalogError(f"duplicate experiment id {ex['id']} in {p}")
            self.experiments[ex["id"]] = ex

        self.evidence: dict[str, dict] = {}
        ev_dir = d / "evidence"
        if ev_dir.exists():
            for p in sorted(ev_dir.glob("*.json")):
                for rec in _read_json(p):
                    rec["_file"] = f"evidence/{p.name}"
                    self.evidence.setdefault(rec["id"], rec)
        compiled = d / "evidence.json"
        if compiled.exists():
            for rec in _read_json(compiled):
                self.evidence.setdefault(rec["id"], rec)

        self.industries: dict[str, dict] = {}
        for iid, name in STANDARD_INDUSTRIES:
            self.industries[iid] = {"id": iid, "name": name, "status": "known", "experiment_ids": [], "source": "standard_list"}
        cur = d / "industries.json"
        if cur.exists():
            for ind in _read_json(cur):
                self.industries[ind["id"]] = {**self.industries.get(ind["id"], {}), **ind, "source": "curated"}
        reg = d / "registry" / "industries.json"
        if reg.exists():
            for ind in _read_json(reg):
                self.industries[ind["id"]] = {**self.industries.get(ind["id"], {}), **ind, "source": "registered"}
        # attach experiments to industries (an experiment may name an industry not yet listed → auto-register as known)
        for ex in self.experiments.values():
            iid = ex.get("industry", "unspecified")
            ind = self.industries.setdefault(iid, {"id": iid, "name": iid.replace("_", " ").capitalize(), "status": "known", "experiment_ids": [], "source": "from_experiment"})
            ind.setdefault("experiment_ids", [])
            if ex["id"] not in ind["experiment_ids"]:
                ind["experiment_ids"].append(ex["id"])
        for ind in self.industries.values():
            ind.setdefault("experiment_ids", [])
            ind["status"] = "researched" if ind["experiment_ids"] else ind.get("status", "known")

        self.version = self._compute_version()
        self.loaded_at = datetime.now(timezone.utc).isoformat()

    def _compute_version(self) -> str:
        h = hashlib.sha256()
        for p in sorted(self.data_dir.rglob("*.json")):
            if "candidates" in p.parts or "research_requests" in p.parts or p.name == "coverage.json":
                continue
            h.update(p.relative_to(self.data_dir).as_posix().encode())
            h.update(p.read_bytes())
        return h.hexdigest()[:16]

    # ------------------------------------------------------------------ accessors
    def get_experiment(self, exp_id: str) -> dict:
        try:
            return self.experiments[exp_id]
        except KeyError:
            raise CatalogError(f"unknown experiment '{exp_id}'")

    def get_configuration(self, cfg_id: str) -> dict:
        try:
            return self.configurations[cfg_id]
        except KeyError:
            raise CatalogError(f"unknown configuration '{cfg_id}'")

    def get_equipment(self, eq_id: str) -> dict:
        try:
            return self.equipment[eq_id]
        except KeyError:
            raise CatalogError(f"unknown equipment '{eq_id}'")

    def evidence_for(self, ids: Iterable[str]) -> list[dict]:
        out = []
        for i in ids or []:
            rec = self.evidence.get(i)
            out.append({k: v for k, v in rec.items() if not k.startswith("_")} if rec else {"id": i, "missing": True})
        return out

    # ------------------------------------------------------------------ Lean documents
    @staticmethod
    def lean_configuration(cfg: dict) -> dict:
        """The exact document handed to Lean. Only the fields the checker understands."""
        return {
            "id": cfg["id"],
            "equipment_id": cfg["equipment_id"],
            "name": cfg.get("name", cfg["id"]),
            "capabilities": [
                {
                    "key": c["key"],
                    "value": c["value"],
                    "install": c["install"],
                    "evidence_status": c["evidence_status"],
                    "evidence_ids": list(c.get("evidence_ids", [])),
                }
                for c in cfg.get("capabilities", [])
            ],
        }

    @staticmethod
    def lean_experiment(ex: dict) -> dict:
        return {
            "id": ex["id"],
            "name": ex.get("name", ex["id"]),
            "industry": ex.get("industry", "unspecified"),
            "requirements": [
                {
                    "key": r["key"],
                    "constraint": r["constraint"],
                    "mandatory": bool(r["mandatory"]),
                    "origin": r["origin"],
                    "rationale": r.get("rationale", ""),
                    "evidence_ids": list(r.get("evidence_ids", [])),
                }
                for r in ex.get("requirements", [])
            ],
            "confirmed": bool(ex.get("confirmed", False)),
        }

    # ------------------------------------------------------------------ public summaries
    def public_experiment(self, ex: dict) -> dict:
        return {k: v for k, v in ex.items() if not k.startswith("_")}

    def public_configuration(self, cfg: dict) -> dict:
        return {k: v for k, v in cfg.items() if not k.startswith("_")}

    def public_equipment(self, eq: dict) -> dict:
        return {k: v for k, v in eq.items() if not k.startswith("_")}

    # ------------------------------------------------------------------ dynamic registration
    def register_industry(self, name: str, description: str = "", industry_id: str | None = None) -> dict:
        iid = industry_id or slugify(name)
        reg_path = self.data_dir / "registry" / "industries.json"
        existing = _read_json(reg_path) if reg_path.exists() else []
        if iid in self.industries and self.industries[iid].get("source") != "standard_list":
            return self.industries[iid]
        rec = {
            "id": iid,
            "name": name,
            "description": description,
            "status": "registered",
            "experiment_ids": [],
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        existing = [e for e in existing if e["id"] != iid] + [rec]
        _write_json(reg_path, existing)
        self.reload()
        return self.industries[iid]

    def propose_vocabulary_key(self, key: str, shape: str, unit: str, description: str) -> dict:
        if shape not in ("range", "max", "min", "flag", "count"):
            raise CatalogError("shape must be range|max|min|flag|count")
        if shape not in ("flag",) and unit not in self.vocabulary["units"]:
            raise CatalogError(f"unit '{unit}' is not a registered canonical unit; register the unit first")
        if key in self.vocabulary["keys"]:
            return {"key": key, **self.vocabulary["keys"][key]}
        reg_path = self.data_dir / "registry" / "vocabulary_proposals.json"
        existing = _read_json(reg_path) if reg_path.exists() else []
        rec = {"key": key, "shape": shape, "unit": unit, "description": description, "status": "proposed",
               "proposed_at": datetime.now(timezone.utc).isoformat()}
        existing = [e for e in existing if e["key"] != key] + [rec]
        _write_json(reg_path, existing)
        self.reload()
        return rec

    def vocabulary_key(self, key: str) -> dict | None:
        if key in self.vocabulary["keys"]:
            return {"key": key, **self.vocabulary["keys"][key]}
        for p in self.vocabulary_proposals:
            if p["key"] == key:
                return p
        return None


def deep_copy(obj: Any) -> Any:
    return copy.deepcopy(obj)
