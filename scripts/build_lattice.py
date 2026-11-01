#!/usr/bin/env python
"""Lean outcome lattice for the site's live step 3 (site/lattice.json).

For each featured experiment (research/v4/site_selection.json) and EVERY catalog configuration:
* the Lean result of the prepared experiment (per-requirement and coupled outcomes, verdict);
* for each editable requirement (one numeric constraint, no conditions): the configuration's documented limits for the
  requirement's keys split the number line into intervals; Lean decides the requirement at every limit and at one point
  inside every open interval. A single-key comparison cannot change between two consecutive limits, so the outcome of
  any value the user types is the Lean outcome of its interval. range_within requirements are decided per end as the
  degenerate range [v, v]; the page combines the two ends (an interval capability contains [lo, hi] iff it contains
  lo and hi).

    python scripts/build_lattice.py [--db PATH] [--workers N]"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryolean import grid, lean_runner, serialize  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

CODE = {"pass": "p", "fail": "f", "unknown": "u"}
EDITABLE = ("at_least", "at_most", "point_within", "range_within")
_W: dict = {}


def frac(q: dict) -> Fraction:
    return Fraction(int(q["num"]), int(q["den"]))


def q_of(x: Fraction, dim: dict) -> dict:
    return {"num": x.numerator, "den": x.denominator, "dim": dim}


def editable(r: dict) -> bool:
    return r["constraint"]["kind"] in EDITABLE and not r.get("conditions")


def limits(cfg_doc: dict, keys: list[str]) -> list[Fraction]:
    out = set()
    for c in cfg_doc["capabilities"]:
        if c["key"] in keys:
            v = c["value"]
            if v["kind"] == "range":
                out |= {frac(v["lo"]), frac(v["hi"])}
            elif v["kind"] in ("max", "min"):
                out.add(frac(v["q"]))
    return sorted(out)


def points(bs: list[Fraction], fallback: Fraction) -> list[Fraction]:
    """One point below all limits, every limit, every midpoint, one point above (2n + 1 points)."""
    if not bs:
        return [fallback]
    lo = bs[0] / 2 if bs[0] > 0 else bs[0] - 1
    hi = bs[-1] * 2 if bs[-1] > 0 else bs[-1] + 1
    pts = [lo]
    for i, b in enumerate(bs):
        pts.append(b)
        pts.append((b + bs[i + 1]) / 2 if i + 1 < len(bs) else hi)
    return pts


def _init(db_path: str):
    _W.update(cat=Catalog(db_path), cfgs={}, exps={})


def _task(eid: str, cids: list[str]) -> dict:
    cat = _W["cat"]
    missing = [c for c in cids if c not in _W["cfgs"]]
    if missing:
        _W["cfgs"].update(grid.configuration_documents(cat, missing))
    if eid not in _W["exps"]:
        _W["exps"] = {eid: serialize.working_experiment(cat, eid, None, None, True)}
    ex = _W["exps"][eid]
    pairs, slots = [], []
    for cid in cids:
        cm, cd = _W["cfgs"][cid]
        ed = serialize.experiment_doc(cat, ex, cm)[0]
        pairs.append((cd, ed)); slots.append((cid, "base", None, None))
        for i, r in enumerate(ed["requirements"]):
            if not editable(r):
                continue
            c = r["constraint"]
            dim = (c.get("q") or c.get("lo"))["dim"]
            src = frac(c["q"]) if "q" in c else frac(c["lo"])
            bs = limits(cd, r["keys"])
            for p in points(bs, src):
                v = json.loads(json.dumps(ed))
                v["requirements"][i]["constraint"] = ({"kind": "range_within", "lo": q_of(p, dim), "hi": q_of(p, dim)}
                                                      if c["kind"] == "range_within" else {"kind": c["kind"], "q": q_of(p, dim)})
                pairs.append((cd, v)); slots.append((cid, i, bs, p))
    res = lean_runner.check_batch(pairs)
    out = {}
    for (cid, i, bs, p), r in zip(slots, res):
        o = out.setdefault(cid, {"edits": {}})
        if i == "base":
            o["verdict"] = r["verdict"][0]   # R(equirements met) / D(oes not meet) / N(eed more information)
            o["checks"] = "".join(CODE[c["outcome"]] for c in r["checks"])
            o["coupled"] = "".join(CODE[c["outcome"]] for c in r.get("coupled_checks", []) if c.get("mandatory") and c.get("applicable"))
        else:
            e = o["edits"].setdefault(str(i), {"limits": [float(b) for b in bs], "outcomes": ""})
            e["outcomes"] += CODE[r["checks"][i]["outcome"]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    cat = Catalog(a.db)
    sel = json.loads((ROOT / "research/v4/site_selection.json").read_text(encoding="utf-8"))
    exps = [e for s in sel.values() for e in s["experiment_ids"]]
    cids = sorted(cat.configurations)
    chunks = [cids[i:i + 40] for i in range(0, len(cids), 40)]
    tasks = [(e, k) for e in exps for k in range(len(chunks))]
    t = time.time()
    lattice = {e: {} for e in exps}
    with cf.ProcessPoolExecutor(max_workers=a.workers or grid.workers(), initializer=_init, initargs=(str(cat.db_path),)) as pool:
        for (e, k), part in zip(tasks, pool.map(_task, [x[0] for x in tasks], [chunks[x[1]] for x in tasks])):
            lattice[e].update(part)
    reqs = {}
    for e in exps:
        ex = serialize.working_experiment(cat, e, None, None, True)
        cm, _ = grid.configuration_documents(cat, [cids[0]])[cids[0]]
        ed = serialize.experiment_doc(cat, ex, cm)[0]
        rows = []
        for i, (r, d) in enumerate(zip(ex["requirements"], ed["requirements"])):
            c = d["constraint"]
            vocab = cat.vocabulary.get(r.get("key") or (r.get("keys") or [""])[0], {})
            rows.append({"index": i, "keys": d["keys"], "kind": c["kind"], "mandatory": d["mandatory"], "editable": editable(d),
                         "unit": (r["constraint"].get("q") or r["constraint"].get("lo") or {}).get("unit"),
                         "value": r["constraint"].get("q", {}).get("value") if "q" in r["constraint"] else None,
                         "lo": r["constraint"].get("lo", {}).get("value"), "hi": r["constraint"].get("hi", {}).get("value"),
                         "si": float(frac(c["q"])) if "q" in c else None,
                         "si_lo": float(frac(c["lo"])) if "lo" in c else None, "si_hi": float(frac(c["hi"])) if "hi" in c else None,
                         "rationale": r.get("rationale", ""), "description": vocab.get("description", "")})
        reqs[e] = rows
    # Lean's rule for unconfirmed requirements, checked once on a real pair
    ex = serialize.working_experiment(cat, exps[0], None, None, False)
    cm, cd = grid.configuration_documents(cat, [cids[0]])[cids[0]]
    unconfirmed = lean_runner.check_batch([(cd, serialize.experiment_doc(cat, ex, cm)[0])])[0]["verdict"]
    names = {c: {"m": cat.configurations[c].get("manufacturer"), "n": cat.configurations[c].get("name"),
                 "e": cat.configurations[c].get("equipment_id")} for c in cids}
    n = sum(len(o["checks"]) + sum(len(x["outcomes"]) for x in o["edits"].values()) for e in lattice.values() for o in e.values())
    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "lean_source_hash": lean_runner.source_hash(),
           "unconfirmed_verdict": unconfirmed, "configurations": names, "requirements": reqs, "lattice": lattice,
           "lean_outcomes": n}
    (ROOT / "site/lattice.json").write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{len(exps)} experiments x {len(cids)} configurations; {n} Lean outcomes in {time.time() - t:.0f} s; "
          f"unconfirmed -> {unconfirmed}")


if __name__ == "__main__":
    main()
