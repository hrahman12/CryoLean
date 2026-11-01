"""SQLite evidence and catalog database.

The JSON seed files under ``data/`` are the reviewable, version-controlled source.
``build_database`` compiles them into ``data/cryolean.db`` (created automatically
on first use).  Everything at runtime reads the database; runtime registrations
(industries, experiments, equipment, modifications, research requests and
untrusted research candidates) are written to it.  Candidates live in their own
table and never reach the trusted tables without ``promote_candidate`` and a
reviewer name.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS industries (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, source TEXT NOT NULL,
    registered_at TEXT, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS equipment (
    id TEXT PRIMARY KEY, manufacturer TEXT, model TEXT, family TEXT, trust TEXT NOT NULL,
    source TEXT, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS configurations (
    id TEXT PRIMARY KEY, equipment_id TEXT NOT NULL REFERENCES equipment(id), name TEXT, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS capabilities (
    configuration_id TEXT NOT NULL REFERENCES configurations(id), key TEXT NOT NULL,
    value TEXT NOT NULL, install TEXT NOT NULL, evidence_status TEXT NOT NULL, evidence_ids TEXT NOT NULL,
    PRIMARY KEY (configuration_id, key));
CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY, industry TEXT NOT NULL, name TEXT, plain_name TEXT, trust TEXT NOT NULL,
    source TEXT, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY, evidence_status TEXT NOT NULL, source_url TEXT, document_title TEXT,
    location TEXT, quote TEXT, doi TEXT, accessed TEXT, source TEXT, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS vocabulary (key TEXT PRIMARY KEY, shape TEXT NOT NULL, unit TEXT, status TEXT NOT NULL, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS units_registered (symbol TEXT PRIMARY KEY, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY, category TEXT NOT NULL, name TEXT NOT NULL, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS coupled_models (id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS materials (id TEXT PRIMARY KEY, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS modifications (
    id TEXT PRIMARY KEY, configuration_id TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS research_requests (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, review_status TEXT NOT NULL, submitted_by TEXT,
    submitted_at TEXT NOT NULL, request_id TEXT, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS results (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, created_at TEXT NOT NULL, doc TEXT NOT NULL);
"""

TRUSTED_TABLES = ("industries", "equipment", "configurations", "capabilities", "experiments", "evidence",
                  "vocabulary", "properties", "coupled_models", "materials", "modifications")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    p = Path(path or config.db_path())
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


def _read(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_database(seed_dir: Path | str | None = None, db_path: Path | str | None = None) -> Path:
    """(Re)build the trusted tables from the JSON seeds. Runtime tables (requests, candidates,
    results) and runtime registrations are preserved."""
    seed = Path(seed_dir or config.SEED_DIR)
    dbp = Path(db_path or config.db_path())
    dbp.parent.mkdir(parents=True, exist_ok=True)
    con = connect(dbp)
    with con:
        # keep runtime registrations (source = 'registered'), rebuild curated rows
        for t in ("capabilities", "configurations"):
            con.execute(f"DELETE FROM {t} WHERE configuration_id IN (SELECT c.id FROM configurations c JOIN equipment e ON c.equipment_id = e.id WHERE e.source = 'seed')" if t == "capabilities"
                        else f"DELETE FROM {t} WHERE equipment_id IN (SELECT id FROM equipment WHERE source = 'seed')")
        for t in ("equipment", "experiments", "evidence", "industries"):
            con.execute(f"DELETE FROM {t} WHERE source = 'seed'")
        for t in ("vocabulary", "units_registered", "properties", "coupled_models", "materials"):
            con.execute(f"DELETE FROM {t}")

        vocab = _read(seed / "capability_vocabulary.json")
        for key, k in vocab["keys"].items():
            con.execute("INSERT OR REPLACE INTO vocabulary VALUES (?,?,?,?,?)",
                        (key, k["shape"], k.get("unit") or "", k.get("status", "established"), dumps({"key": key, **k})))
        for sym, u in vocab.get("units", {}).items():
            con.execute("INSERT OR REPLACE INTO units_registered VALUES (?,?)", (sym, dumps({"symbol": sym, **u})))

        for p in sorted((seed / "evidence").glob("*.json")):
            for rec in _read(p):
                con.execute("INSERT OR REPLACE INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (rec["id"], rec.get("evidence_status", "unknown"), rec.get("source_url"), rec.get("document_title"),
                             rec.get("location"), rec.get("quote"), rec.get("doi"), rec.get("accessed"), "seed",
                             dumps({**rec, "_fragment": p.name})))

        for p in sorted((seed / "cryostats").glob("*.json")):
            eq = _read(p)
            insert_equipment(con, eq, source="seed", trust="trusted", source_file=p.name)

        for p in sorted((seed / "experiments").glob("*.json")):
            ex = _read(p)
            con.execute("INSERT OR REPLACE INTO experiments VALUES (?,?,?,?,?,?,?)",
                        (ex["id"], ex.get("industry", "unspecified"), ex.get("name"), ex.get("plain_name"), "trusted", "seed",
                         dumps({**ex, "_file": p.name})))

        ind_path = seed / "industries.json"
        if ind_path.exists():
            for ind in _read(ind_path):
                con.execute("INSERT OR REPLACE INTO industries VALUES (?,?,?,?,?,?)",
                            (ind["id"], ind["name"], ind.get("description", ""), "seed", None, dumps(ind)))

        phys = seed / "physics"
        if (phys / "properties.json").exists():
            for prop in _read(phys / "properties.json")["properties"]:
                con.execute("INSERT INTO properties VALUES (?,?,?,?)", (prop["id"], prop["category"], prop["name"], dumps(prop)))
        if (phys / "coupled_models.json").exists():
            for m in _read(phys / "coupled_models.json")["models"]:
                con.execute("INSERT INTO coupled_models VALUES (?,?,?,?)", (m["id"], m["name"], m["status"], dumps(m)))
        if (phys / "materials.json").exists():
            for m in _read(phys / "materials.json")["materials"]:
                con.execute("INSERT INTO materials VALUES (?,?)", (m["id"], dumps(m)))

        con.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (now(),))
        con.execute("INSERT OR REPLACE INTO meta VALUES ('seed_dir', ?)", (str(seed),))
    con.close()
    return dbp


def insert_equipment(con: sqlite3.Connection, eq: dict, source: str, trust: str, source_file: str = "", replace: bool = True) -> None:
    verb = "INSERT OR REPLACE" if replace else "INSERT"
    con.execute(f"{verb} INTO equipment VALUES (?,?,?,?,?,?,?)",
                (eq["id"], eq.get("manufacturer"), eq.get("model"), eq.get("family"), trust, source,
                 dumps({**{k: v for k, v in eq.items() if k != "configurations"}, "_file": source_file})))
    for cfg in eq.get("configurations", []):
        con.execute(f"{verb} INTO configurations VALUES (?,?,?,?)",
                    (cfg["id"], eq["id"], cfg.get("name"), dumps({k: v for k, v in cfg.items() if k != "capabilities"})))
        con.execute("DELETE FROM capabilities WHERE configuration_id = ?", (cfg["id"],))
        for cap in cfg.get("capabilities", []):
            con.execute(f"{verb} INTO capabilities VALUES (?,?,?,?,?,?)",
                        (cfg["id"], cap["key"], dumps(cap["value"]), cap["install"], cap["evidence_status"],
                         dumps(cap.get("evidence_ids", []))))


def ensure_database() -> Path:
    p = config.db_path()
    if not p.exists():
        build_database()
    return p


def content_hash(con: sqlite3.Connection) -> str:
    """Deterministic hash of every trusted table (the catalog version)."""
    h = hashlib.sha256()
    for t in TRUSTED_TABLES + ("units_registered",):
        rows = con.execute(f"SELECT * FROM {t}").fetchall()
        for r in sorted(tuple(r) for r in rows):
            h.update(dumps(list(r)).encode("utf-8"))
    return h.hexdigest()[:16]


def rows(con: sqlite3.Connection, sql: str, args: Iterable = ()) -> list[sqlite3.Row]:
    return con.execute(sql, tuple(args)).fetchall()
