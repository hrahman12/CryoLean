"""Experiment x configuration verdicts at catalog scale.

Every pair is decided by the Lean checker (`check-batch`). `build` spreads the work over worker processes, each with
its own catalog and its own Lean subprocesses, and only compact outcomes travel back and are stored (table `grid`), so
the frontend can show counts per industry, per experiment and per machine without re-running Lean."""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import json
import os
from collections import Counter
from typing import Callable

from . import db, lean_runner, modifications, serialize
from .catalog import Catalog

CHUNK = 800
SCHEMA = """
CREATE TABLE IF NOT EXISTS grid (experiment_id TEXT NOT NULL, configuration_id TEXT NOT NULL, verdict TEXT NOT NULL,
  failing TEXT NOT NULL, missing TEXT NOT NULL, passes INTEGER NOT NULL, PRIMARY KEY (experiment_id, configuration_id));
CREATE INDEX IF NOT EXISTS grid_by_configuration ON grid (configuration_id, verdict);
CREATE TABLE IF NOT EXISTS grid_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def workers() -> int:
    return max(1, min(24, (os.cpu_count() or 4) - 2))


def check_parallel(pairs: list[tuple[dict, dict]], n_workers: int | None = None) -> list[dict]:
    """lean_runner.check_batch over chunks on threads (one Lean process each); results in input order."""
    chunks = [pairs[i:i + CHUNK] for i in range(0, len(pairs), CHUNK)]
    if len(chunks) <= 1:
        return lean_runner.check_batch(pairs) if pairs else []
    with cf.ThreadPoolExecutor(max_workers=n_workers or workers()) as pool:
        parts = list(pool.map(lean_runner.check_batch, chunks))
    return [r for part in parts for r in part]


def outcome(r: dict) -> dict:
    """Compact form of one Lean result: the mandatory applicable checks that failed or could not be decided."""
    failing, missing, passes = [], [], 0
    for c in r.get("checks", []):
        if not c.get("mandatory") or not c.get("applicable"):
            continue
        label = " | ".join(c["keys"])
        if c["outcome"] == "fail":
            failing.append(label)
        elif c["outcome"] == "unknown":
            missing.append(label)
        else:
            passes += 1
    for c in r.get("coupled_checks", []):
        if c.get("mandatory") and c.get("applicable") and c["outcome"] in ("fail", "unknown"):
            (failing if c["outcome"] == "fail" else missing).append("model:" + c.get("model", c.get("id", "?")))
    return {"verdict": r["verdict"], "failing": failing, "missing": missing, "passes": passes}


def configuration_documents(catalog: Catalog, ids: list[str] | None = None) -> dict[str, tuple[dict, dict]]:
    """{configuration_id: (configuration with registered modifications applied, its Lean document)}."""
    out = {}
    for cid in ids or sorted(catalog.configurations):
        cfg = catalog.get_configuration(cid)
        cfg_mod = modifications.apply(catalog, cfg, modifications.for_configuration(catalog, cid))
        out[cid] = (cfg_mod, serialize.configuration_doc(catalog, cfg_mod))
    return out


def experiment_pairs(catalog: Catalog, experiment: dict, cfgs: dict[str, tuple[dict, dict]]) -> list[tuple[dict, dict]]:
    return [(cfg_doc, serialize.experiment_doc(catalog, experiment, cfg_mod)[0]) for cfg_mod, cfg_doc in cfgs.values()]


# ---------------------------------------------------------------------------- worker processes
_W: dict = {}


def _init(db_path: str):
    _W.update(catalog=Catalog(db_path), cfgs={}, exps={})


def _task(eid: str, cids: list[str]) -> list[dict]:
    cat = _W["catalog"]
    missing = [c for c in cids if c not in _W["cfgs"]]
    _W["cfgs"].update(configuration_documents(cat, missing) if missing else {})
    if eid not in _W["exps"]:
        _W["exps"] = {eid: serialize.working_experiment(cat, eid, None, None, True)}
    pairs = experiment_pairs(cat, _W["exps"][eid], {c: _W["cfgs"][c] for c in cids})
    return [outcome(r) for r in lean_runner.check_batch(pairs)]


def build(catalog: Catalog, experiment_ids: list[str] | None = None, n_workers: int | None = None,
          progress: Callable[[str], None] | None = None) -> dict:
    """Decide every experiment x configuration pair with Lean and store the outcomes in the catalog database."""
    cids = sorted(catalog.configurations)
    exps = experiment_ids or sorted(catalog.experiments)
    con = catalog.connect()
    con.executescript(SCHEMA)
    with con:
        if experiment_ids is None:
            con.execute("DELETE FROM grid")
        else:
            con.executemany("DELETE FROM grid WHERE experiment_id = ?", [(e,) for e in exps])
    size = max(50, min(CHUNK, -(-len(cids) // (n_workers or workers()))))
    chunks = [cids[i:i + size] for i in range(0, len(cids), size)]
    tasks = [(eid, k) for eid in exps for k in range(len(chunks))]
    total, rows, done = Counter(), [], 0
    with cf.ProcessPoolExecutor(max_workers=n_workers or workers(), initializer=_init,
                                initargs=(str(catalog.db_path),)) as pool:
        # every (experiment, chunk) task is queued at once so all workers stay busy; map keeps task order
        for (eid, k), outs in zip(tasks, pool.map(_task, [t[0] for t in tasks], [chunks[t[1]] for t in tasks])):
            for cid, o in zip(chunks[k], outs):
                total[o["verdict"]] += 1
                rows.append((eid, cid, o["verdict"], db.dumps(o["failing"]), db.dumps(o["missing"]), o["passes"]))
            if k == len(chunks) - 1:
                with con:
                    con.executemany("INSERT OR REPLACE INTO grid VALUES (?,?,?,?,?,?)", rows)
                done += 1
                if progress:
                    progress(f"{done}/{len(exps)} {eid}: {dict(Counter(r[2] for r in rows))}")
                rows = []
    meta = {"built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "experiments": len(exps),
            "configurations": len(cids), "pairs": sum(total.values()), "counts": dict(total),
            "lean_source_hash": lean_runner.source_hash()}
    with con:
        con.executemany("INSERT OR REPLACE INTO grid_meta VALUES (?,?)", [(k, db.dumps(v)) for k, v in meta.items()])
    con.close()
    return meta


# ---------------------------------------------------------------------------- reading the stored grid
def summary(catalog: Catalog, industry: str | None = None) -> dict:
    """Verdict counts overall, per industry and per experiment from the stored grid."""
    con = catalog.connect()
    con.executescript(SCHEMA)
    meta = {k: json.loads(v) for k, v in con.execute("SELECT key, value FROM grid_meta")}
    rows = con.execute("SELECT experiment_id, verdict, COUNT(*) FROM grid GROUP BY experiment_id, verdict").fetchall()
    con.close()
    per_exp: dict[str, Counter] = {}
    for eid, v, n in rows:
        per_exp.setdefault(eid, Counter())[v] += n
    per_ind: dict[str, Counter] = {}
    experiments = []
    for eid, c in sorted(per_exp.items()):
        e = catalog.experiments.get(eid)
        if not e:
            continue
        ind = e.get("industry") or "unassigned"
        if industry and ind != industry:
            continue
        per_ind.setdefault(ind, Counter()).update(c)
        experiments.append({"experiment_id": eid, "name": e.get("plain_name") or e.get("name"), "industry": ind,
                            **_counts(c)})
    overall = sum(per_ind.values(), Counter())
    return {"built_at": meta.get("built_at"), "lean_source_hash": meta.get("lean_source_hash"),
            "configurations": meta.get("configurations"), "overall": _counts(overall),
            "industries": {k: _counts(v) for k, v in sorted(per_ind.items())}, "experiments": experiments}


def matches(catalog: Catalog, experiment_id: str, verdict: str | None = None, offset: int = 0, limit: int = 100) -> dict:
    """Stored outcomes of one experiment against every configuration (paged), green first."""
    con = catalog.connect()
    con.executescript(SCHEMA)
    q = "SELECT configuration_id, verdict, failing, missing, passes FROM grid WHERE experiment_id = ?"
    args: list = [experiment_id]
    if verdict:
        q += " AND verdict = ?"
        args.append(verdict)
    order = {"REQUIREMENTS_MET": 0, "NEED_MORE_INFORMATION": 1, "DOES_NOT_MEET_REQUIREMENTS": 2}
    rows = sorted(con.execute(q, args).fetchall(), key=lambda r: (order.get(r[1], 3), -r[4], r[0]))
    con.close()
    out = []
    for cid, v, failing, missing, passes in rows[offset:offset + limit]:
        c = catalog.configurations.get(cid, {})
        out.append({"configuration_id": cid, "equipment_id": c.get("equipment_id"), "manufacturer": c.get("manufacturer"),
                    "model": c.get("model"), "name": c.get("name"), "verdict": v, "failing": json.loads(failing),
                    "missing": json.loads(missing), "documented_passes": passes})
    return {"experiment_id": experiment_id, "total": len(rows), "offset": offset, "results": out}


def _counts(c: Counter) -> dict:
    n = sum(c.values())
    return {"pairs": n, "met": c["REQUIREMENTS_MET"], "not_met": c["DOES_NOT_MEET_REQUIREMENTS"],
            "need_info": c["NEED_MORE_INFORMATION"]}
