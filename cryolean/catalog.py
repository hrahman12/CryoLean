"""Catalog: the trusted data, read from the SQLite database.

Industries, equipment, experiments, vocabulary, physical properties, coupled
models and materials are all rows; nothing here branches on an industry.
"""
from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path

from . import config, db
from .catalog_standard import STANDARD_INDUSTRIES


class CatalogError(LookupError):
    pass


def slugify(name: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


def _j(s: str):
    return json.loads(s)


class Catalog:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path or config.db_path())
        if not self.db_path.exists():
            db.build_database(db_path=self.db_path)
        self.reload()

    def connect(self) -> sqlite3.Connection:
        return db.connect(self.db_path)

    # ------------------------------------------------------------------ load
    def reload(self) -> None:
        con = self.connect()
        try:
            self.vocabulary = {r["key"]: _j(r["doc"]) for r in con.execute("SELECT * FROM vocabulary")}
            self.units_registered = {r["symbol"]: _j(r["doc"]) for r in con.execute("SELECT * FROM units_registered")}
            self.evidence = {r["id"]: _j(r["doc"]) for r in con.execute("SELECT * FROM evidence")}
            self.equipment = {}
            for r in con.execute("SELECT * FROM equipment"):
                eq = _j(r["doc"])
                eq.update({"id": r["id"], "trust": r["trust"], "source": r["source"], "configurations": []})
                self.equipment[r["id"]] = eq
            self.configurations = {}
            for r in con.execute("SELECT * FROM configurations"):
                cfg = _j(r["doc"])
                eq = self.equipment.get(r["equipment_id"], {})
                cfg.update({"id": r["id"], "equipment_id": r["equipment_id"], "manufacturer": eq.get("manufacturer"),
                            "model": eq.get("model"), "family": eq.get("family"), "capabilities": []})
                self.configurations[r["id"]] = cfg
            for r in con.execute("SELECT * FROM capabilities ORDER BY configuration_id, rowid"):
                cfg = self.configurations.get(r["configuration_id"])
                if cfg is not None:
                    cfg["capabilities"].append({"key": r["key"], "value": _j(r["value"]), "install": r["install"],
                                                "evidence_status": r["evidence_status"], "evidence_ids": _j(r["evidence_ids"])})
            for cfg in self.configurations.values():
                self.equipment.setdefault(cfg["equipment_id"], {"id": cfg["equipment_id"], "configurations": []})
                self.equipment[cfg["equipment_id"]]["configurations"].append(cfg)
            self.experiments = {}
            for r in con.execute("SELECT * FROM experiments"):
                ex = _j(r["doc"])
                ex.update({"id": r["id"], "trust": r["trust"], "source": r["source"]})
                ex.setdefault("params", [])
                ex.setdefault("coupled", [])
                self.experiments[r["id"]] = ex
            self.properties = {r["id"]: _j(r["doc"]) for r in con.execute("SELECT * FROM properties ORDER BY id")}
            self.coupled_models = {r["id"]: _j(r["doc"]) for r in con.execute("SELECT * FROM coupled_models")}
            self.materials = {r["id"]: _j(r["doc"]) for r in con.execute("SELECT * FROM materials")}
            self.modifications = {r["id"]: {**_j(r["doc"]), "id": r["id"], "configuration_id": r["configuration_id"],
                                            "status": r["status"], "created_at": r["created_at"]}
                                  for r in con.execute("SELECT * FROM modifications")}
            self.industries = {}
            for iid, name in STANDARD_INDUSTRIES:
                self.industries[iid] = {"id": iid, "name": name, "description": "", "source": "standard_list"}
            for r in con.execute("SELECT * FROM industries"):
                self.industries[r["id"]] = {**self.industries.get(r["id"], {}), **_j(r["doc"]), "id": r["id"],
                                            "name": r["name"], "source": r["source"], "registered_at": r["registered_at"]}
            for ex in self.experiments.values():
                iid = ex.get("industry", "unspecified")
                if iid not in self.industries:
                    self.industries[iid] = {"id": iid, "name": iid.replace("_", " ").capitalize(), "description": "", "source": "from_experiment"}
            for ind in self.industries.values():
                ind["experiment_ids"] = sorted(set(ind.get("coverage_experiment_ids", [])) | {e for e, x in self.experiments.items() if x.get("industry") == ind["id"]})
                ind["status"] = "researched" if ind["experiment_ids"] else ("registered" if ind["source"] == "registered" else "known")
            for ex in self.experiments.values():
                ex["industries"] = sorted({ex.get("industry", "unspecified")} | {i["id"] for i in self.industries.values() if ex["id"] in i["experiment_ids"]})
            self.version = db.content_hash(con)
        finally:
            con.close()

    # ------------------------------------------------------------------ accessors
    def get_experiment(self, exp_id: str) -> dict:
        if exp_id not in self.experiments:
            raise CatalogError(f"unknown experiment '{exp_id}'")
        return self.experiments[exp_id]

    def get_configuration(self, cfg_id: str) -> dict:
        if cfg_id not in self.configurations:
            raise CatalogError(f"unknown configuration '{cfg_id}'")
        return self.configurations[cfg_id]

    def get_equipment(self, eq_id: str) -> dict:
        if eq_id not in self.equipment:
            raise CatalogError(f"unknown equipment '{eq_id}'")
        return self.equipment[eq_id]

    def vocabulary_key(self, key: str) -> dict | None:
        v = self.vocabulary.get(key)
        return {"key": key, **v} if v else None

    def evidence_for(self, ids) -> list[dict]:
        out = []
        for i in ids or []:
            rec = self.evidence.get(i)
            if rec:
                out.append({k: v for k, v in rec.items() if not k.startswith("_")})
            elif isinstance(i, str) and (i.startswith("user_override:") or i.startswith("undocumented_modification:") or i.startswith("user_param:")):
                out.append({"id": i, "evidence_status": "user_entered" if not i.startswith("undocumented") else "unknown",
                            "claim": "value supplied by the user for this check"})
            else:
                out.append({"id": i, "missing": True})
        return out

    def public(self, obj: dict) -> dict:
        return {k: v for k, v in copy.deepcopy(obj).items() if not k.startswith("_")}

    # ------------------------------------------------------------------ registration (runtime, trusted tables)
    def register_industry(self, name: str, description: str = "", industry_id: str | None = None) -> dict:
        iid = industry_id or slugify(name)
        if not iid:
            raise CatalogError("industry name is empty")
        con = self.connect()
        with con:
            con.execute("INSERT OR REPLACE INTO industries VALUES (?,?,?,?,?,?)",
                        (iid, name, description, "registered", db.now(), db.dumps({"id": iid, "name": name, "description": description})))
        con.close()
        self.reload()
        return self.industries[iid]
