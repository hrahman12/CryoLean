#!/usr/bin/env python
"""CryoLean vs the regular way: one command, every number in bench/RESULTS.md comes from here.

    python bench/vs_regular.py            # ~2-4 minutes on a laptop; needs `lake build` in lean/ first

The regular way is implemented in bench/regular_way.py (R1 spec-sheet checklist, R2 careful spreadsheet, R3
physics-aware float script). CryoLean's verdicts come only from the compiled Lean checker.

The tests are built so the right answer does NOT come from CryoLean:

  T0  catalog head-to-head   every experiment x configuration pair; no ground truth, but by the Lean theorem
                             `sound_checker_le_cryolean` every YES/NO a method gives where CryoLean does not is a
                             YES/NO the evidence does not support.
  T1  hide one line          take a pair the manufacturer's own trusted spec rules out; hide that datasheet line.
                             Truth: still NO (the machine did not change). Who says YES?
  T2  borrowed number        same pairs; fill the blank with the value printed for a sibling configuration of the
                             same instrument (the classic "read the 14 T column" mistake). Truth: still NO.
  T3  physics sweep          50-qubit wiring layout scaled from 1 to 200 qubits on every catalog configuration.
                             Truth: Krinner et al.'s published heat-budget rule, recomputed here in exact fractions.
  T4  project history        pairs decided on the catalog of revision 7a224f4 (Oct 31) vs the documentation found
                             since. Truth: today's sourced records, same experiment requirements.
  T5  fault injection        2,750 synthetic configurations with known defects (paper/scripts/paper_eval.py E4).
"""
from __future__ import annotations

import copy
import io
import json
import math
import random
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bench"))

import regular_way as rw  # noqa: E402
from cryolean import db, grid, lean_runner, serialize, units  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

MET, NOT, NI = rw.MET, rw.NOT, rw.NI
METHODS = ["R1", "R2", "R3", "CryoLean"]
OUT = ROOT / "bench" / "results"
HISTORY_REV = "7a224f4"
# pairs whose full story is kept for the write-up (well-known setups from the CryoLean demos and catalog)
FEATURED = {
    "t1_hide_one_line": {("mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res"),
                         ("chem_low_temperature_raman", "anton_paar_ttk600_ln2_vacuum")},
    "t2_borrowed_number": {("sci_graphene_yig_quantum_hall", "qd_dynacool_9T_eto_res"),
                           ("sci_graphene_yig_quantum_hall", "oxford_teslatronpt_8T"),
                           ("metro_plts2000_he3_melting_curve", "bluefors_ld250_manual_v2"),
                           ("semi_sfq_adc_cryocooler_test", "bluefors_ld250_manual_v2")},
}


def save(name: str, obj) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def lean_compact(r: dict) -> dict:
    """What a Lean result says, per mandatory applicable line."""
    lines = {}
    for c in r.get("checks", []):
        if c.get("mandatory") and c.get("applicable"):
            cap = next((pk.get("capability") for pk in c.get("per_key", []) if pk.get("capability")), None) or {}
            avail = next((pk.get("available_display") for pk in c.get("per_key", [])), None)
            if cap.get("install") in ("optional_not_installed", "not_available"):
                avail = "documented as not fitted / not available on this configuration"
            lines[" | ".join(c["keys"])] = {"outcome": c["outcome"], "keys": c["keys"], "available": avail,
                                            "required": c.get("required_display"),
                                            "evidence": cap.get("evidence_status"), "install": cap.get("install")}
    coupled = {}
    for c in r.get("coupled_checks", []):
        if c.get("mandatory") and c.get("applicable"):
            coupled["model:" + c.get("model", "?")] = {"outcome": c["outcome"],
                                                        "lhs": (c.get("lhs") or {}).get("display"),
                                                        "rhs": (c.get("rhs") or {}).get("display")}
    return {"verdict": r["verdict"], "lines": lines, "coupled": coupled}


def verdicts_for(pairs: list[tuple[dict, dict]]) -> list[dict]:
    """All four methods on the same documents. CryoLean = the compiled Lean checker."""
    lean = grid.check_parallel(pairs) if pairs else []
    out = []
    for (cd, ed), r in zip(pairs, lean):
        v = rw.all_verdicts(cd, ed)
        v["CryoLean"] = r["verdict"]
        out.append({"v": v, "lean": lean_compact(r)})
    return out


def tally(rows: list[dict], truth: str | None = None) -> dict:
    """Per method: verdict counts, and against a known truth the wrong YES / wrong NO counts."""
    out = {}
    for m in METHODS:
        c = Counter(r["v"][m] for r in rows)
        d = {"YES": c[MET], "NO": c[NOT], "NEED_INFO": c[NI]}
        if truth == NOT:
            d["wrong_YES"] = c[MET]
        if truth == MET:
            d["wrong_NO"] = c[NOT]
        out[m] = d
    return out


# ============================================================================== T0 catalog head-to-head
def t0_catalog(cat: Catalog, cfgs: dict) -> tuple[dict, dict]:
    print("T0 catalog head-to-head ...", flush=True)
    t = time.perf_counter()
    rows, per_pair = [], {}
    for eid in sorted(cat.experiments):
        ex = serialize.working_experiment(cat, eid, None, None, True)
        ids = list(cfgs)
        pairs = [(cfgs[c][1], serialize.experiment_doc(cat, ex, cfgs[c][0])[0]) for c in ids]
        for cid, (cd, ed), res in zip(ids, pairs, verdicts_for(pairs)):
            res.update(e=eid, c=cid)
            rows.append(res)
            per_pair[(eid, cid)] = res
    dt = time.perf_counter() - t
    # agreement matrices vs CryoLean, and why each method says YES where CryoLean does not
    order = [MET, NI, NOT]
    conf = {m: [[sum(1 for r in rows if r["v"][m] == a and r["v"]["CryoLean"] == b) for b in order] for a in order]
            for m in METHODS[:-1]}
    extra_yes = {}
    for m in METHODS[:-1]:
        why = Counter()
        for r in rows:
            if r["v"][m] == MET and r["v"]["CryoLean"] != MET:
                why[cause_of_yes(r, m)] += 1
        extra_yes[m] = dict(why)
    extra_no = {m: sum(1 for r in rows if r["v"][m] == NOT and r["v"]["CryoLean"] != NOT) for m in METHODS[:-1]}
    no_examples = [{"experiment": r["e"], "configuration": r["c"], **{m: rw.SHORT[r["v"][m]] for m in METHODS},
                    "unknown_lines": [f"{lbl} (install {l.get('install')}, evidence {l.get('evidence')})"
                                      for lbl, l in r["lean"]["lines"].items() if l["outcome"] == "unknown"]}
                   for r in rows if r["v"]["R2"] == NOT and r["v"]["CryoLean"] != NOT]
    yes_examples = [{"experiment": r["e"], "configuration": r["c"], **{m: rw.SHORT[r["v"][m]] for m in METHODS},
                     "lines": {lbl: f"{l['outcome']} ({l.get('evidence')})" for lbl, l in r["lean"]["lines"].items()},
                     "coupled": r["lean"]["coupled"]}
                    for r in rows if r["v"]["R2"] == MET and r["v"]["CryoLean"] != MET]
    res = {"pairs": len(rows), "experiments": len(cat.experiments), "configurations": len(cfgs), "seconds": round(dt, 1),
           "counts": tally(rows), "matrix_order": ["YES", "NEED_INFO", "NO"],
           "matrix_rows_method_cols_cryolean": conf,
           "yes_without_support": {m: sum(v.values()) for m, v in extra_yes.items()},
           "yes_without_support_by_cause": extra_yes,
           "no_without_support": extra_no, "no_without_support_examples": no_examples,
           "careful_spreadsheet_yes_without_support_examples": yes_examples}
    save("t0_catalog", res)
    print(f"   {len(rows)} pairs in {dt:.0f}s; YES counts " + ", ".join(f"{m}={res['counts'][m]['YES']}" for m in METHODS))
    return res, per_pair


def cause_of_yes(r: dict, m: str) -> str:
    """Why method m says YES where CryoLean does not (read off CryoLean's own per-line outcomes)."""
    lean = r["lean"]
    if r["v"]["CryoLean"] == NOT:
        if any(c["outcome"] == "fail" for c in lean["coupled"].values()):
            return "coupled physics fails"
        return "a sourced line fails"
    if any(c["outcome"] in ("unknown", "unsupported") for c in lean["coupled"].values()) and m == "R3":
        return "physics computed from unsourced or out-of-range numbers"
    outs = [l["outcome"] for l in lean["lines"].values()]
    if m == "R1" and "unknown" in outs:
        return "datasheet silent on a required line"
    return "number without a trusted source decided a line"


# ============================================================================== T1 / T2 hide or borrow a line
def example(cat: Catalog, cfgs: dict, r: dict) -> dict:
    e, c = cat.experiments[r["e"]], cfgs[r["c"]][0]
    return {"experiment_id": r["e"], "experiment": e.get("plain_name") or e.get("name"),
            "industry": e.get("industry"), "configuration_id": r["c"], "configuration": c.get("name"),
            "hidden": r.get("hidden"), "why_no": r.get("why_no"), "borrowed_from": r.get("borrowed_from"),
            **{m: rw.SHORT[r["v"][m]] for m in METHODS}}


def failing_lines(res: dict) -> list[dict] | None:
    """Lines CryoLean rejects on (trusted evidence by theorem `fail_needs_trusted`); None if a coupled check fails."""
    if res["v"]["CryoLean"] != NOT or any(c["outcome"] == "fail" for c in res["lean"]["coupled"].values()):
        return None
    return [l for l in res["lean"]["lines"].values() if l["outcome"] == "fail"]


def without_keys(cfg_mod: dict, keys: set[str]) -> dict:
    c = copy.deepcopy(cfg_mod)
    c["capabilities"] = [x for x in c["capabilities"] if x["key"] not in keys]
    return c


def t1_t2_hide_and_borrow(cat: Catalog, cfgs: dict, per_pair: dict) -> tuple[dict, dict]:
    print("T1 hide one line / T2 borrowed number ...", flush=True)
    exps = {e: serialize.working_experiment(cat, e, None, None, True) for e in cat.experiments}
    siblings = defaultdict(list)
    for cid, (cm, _) in cfgs.items():
        siblings[cm.get("equipment_id")].append(cid)
    hide_pairs, hide_meta, hide_all_pairs, hide_all_meta, borrow_pairs, borrow_meta = [], [], [], [], [], []
    for (eid, cid), res in per_pair.items():
        fl = failing_lines(res)
        if not fl:
            continue
        cm = cfgs[cid][0]
        ex = exps[eid]
        keys = {k for l in fl for k in l["keys"]}
        h = without_keys(cm, keys)
        pair = (serialize.configuration_doc(cat, h), serialize.experiment_doc(cat, ex, h)[0])
        meta = {"e": eid, "c": cid, "hidden": sorted(keys),
                "why_no": [f"{' | '.join(l['keys'])}: {l['required']}; sheet: {l['available']}" for l in fl]}
        hide_all_pairs.append(pair)
        hide_all_meta.append(meta)
        if len(fl) == 1:
            hide_pairs.append(pair)
            hide_meta.append(meta)
        # T2: every failing line can be "filled" from a sibling configuration whose printed value passes it
        patch, ok = {}, True
        for l in fl:
            got = None
            for sid in siblings.get(cm.get("equipment_id"), []):
                if sid == cid:
                    continue
                sres = per_pair.get((eid, sid))
                sl = sres and sres["lean"]["lines"].get(" | ".join(l["keys"]))
                if sl and sl["outcome"] == "pass":
                    rec = next((x for x in cfgs[sid][0]["capabilities"] if x["key"] in l["keys"]
                                and x.get("install") == "installed"), None)
                    if rec:
                        got = (sid, rec)
                        break
            if not got:
                ok = False
                break
            patch[got[1]["key"]] = got
        if ok and patch:
            b = copy.deepcopy(cm)
            caps = [x for x in b["capabilities"] if x["key"] not in keys]
            for key, (sid, rec) in patch.items():
                caps.append({**copy.deepcopy(rec), "evidence_status": "inferred_estimate",
                             "evidence_ids": [], "note": f"value printed for sibling configuration {sid}"})
            b["capabilities"] = caps
            borrow_pairs.append((serialize.configuration_doc(cat, b), serialize.experiment_doc(cat, ex, b)[0]))
            borrow_meta.append({**meta, "borrowed_from": {k: s for k, (s, _) in patch.items()}})

    def run(pairs, meta, name, label):
        rows = verdicts_for(pairs)
        for r, m in zip(rows, meta):
            r.update(m)
        t = tally(rows, truth=NOT)
        named = sum(1 for r in rows if r["v"]["CryoLean"] == NI and any(
            l["outcome"] == "unknown" and set(l["keys"]) & set(r["hidden"]) for l in r["lean"]["lines"].values()))
        seen, examples = set(), []
        wrong_key = "R2" if name.startswith("t2") else "R1"
        for r in sorted(rows, key=lambda r: (r["e"], r["c"])):
            if r["v"][wrong_key] == MET and r["e"] not in seen:
                seen.add(r["e"])
                examples.append(example(cat, cfgs, r))
        by_ind = defaultdict(lambda: {"cases": 0, **{m: 0 for m in METHODS}})
        for r in rows:
            ind = cat.experiments[r["e"]].get("industry") or "unassigned"
            by_ind[ind]["cases"] += 1
            for m in METHODS:
                by_ind[ind][m] += r["v"][m] == MET
        cryo_yes = [r for r in rows if r["v"]["CryoLean"] == MET]
        out = {"label": label, "cases": len(rows), "truth": "NO (the configuration's own trusted spec rules it out)",
               "by_method": t, "cryolean_need_info_names_the_hidden_line": named,
               "cryolean_yes_cases": [(r["e"], r["c"]) for r in cryo_yes], "wrong_yes_by_industry": dict(by_ind),
               "examples": examples[:60],
               "featured": [example(cat, cfgs, r) for r in rows if (r["e"], r["c"]) in FEATURED.get(name, ())],
               "rows": [{"e": r["e"], "c": r["c"], "hidden": r["hidden"], "borrowed_from": r.get("borrowed_from"),
                         **{m: rw.SHORT[r["v"][m]] for m in METHODS}} for r in rows] if len(rows) < 5000 else []}
        save(name, out)
        print(f"   {name}: {len(rows)} cases; wrong YES " + ", ".join(f"{m}={t[m]['wrong_YES']}" for m in METHODS))
        return out

    t1 = run(hide_pairs, hide_meta, "t1_hide_one_line", "one failing line hidden (pairs with exactly one failing line)")
    t1all = run(hide_all_pairs, hide_all_meta, "t1_hide_all_failing_lines", "every failing line hidden")
    t2 = run(borrow_pairs, borrow_meta, "t2_borrowed_number",
             "failing line(s) filled with the value printed for a sibling configuration")
    return {"one": t1, "all": t1all}, t2


# ============================================================================== T3 physics sweep (qubit wiring)
WIRING = "quantum_mxc_wiring_heat_budget"


def layout(n: int) -> dict:
    """Krinner et al.'s 50-qubit layout scaled to n qubits: 1 drive + 1 flux per qubit, 8 readout-drive and 8
    output lines per 50 qubits, 124 RF lines at n = 50 (58 drive + 50 flux + 8 out + 8 more)."""
    ro = math.ceil(8 * n / 50)
    return {"n_drive_lines": n + ro, "n_flux_lines": n, "n_output_lines": ro, "coax": n + ro + n + ro + ro}


def truth_wiring(cm: dict, ex: dict, lay: dict, vocab: dict) -> tuple[str, Fraction | None, Fraction | None]:
    """Independent exact recomputation of the published rule (no Lean, no serializer):
    base T <= 20 mK, RF lines >= needed, 3 x (sum of per-line loads) <= cooling power at a documented T <= 20 mK."""
    trusted = {"manufacturer_specification", "experimental_observation", "reference_data", "user_entered",
               "certified_simulation"}
    caps = {}
    for c in cm["capabilities"]:
        caps.setdefault(c["key"], c)

    def si(v):
        q = units.lean_quantity(v["value"], v["unit"])
        return Fraction(int(q["num"]), int(q["den"]))

    p = {x["name"]: x for x in ex["params"]}
    t_op = si(p["operating_temperature"]["value"])
    ok_unknown = []
    # 1) base temperature (a documented minimum, or the bottom of a documented range)
    b = caps.get("temperature.base")
    r = caps.get("temperature.range")
    tb = None
    for c, side in ((b, "min"), (r, "range")):
        if c and c["install"] == "installed" and c["evidence_status"] in trusted and c["value"].get("kind") == side:
            tb = si(c["value"]["q"] if side == "min" else c["value"]["lo"])
            break
    if tb is None:
        ok_unknown.append("base")
    elif tb > t_op:
        return NOT, None, None
    # 2) RF lines
    co = caps.get("electrical.coax_lines")
    if co and co["install"] == "installed" and co["evidence_status"] in trusted and co["value"].get("kind") == "count":
        if co["value"]["n"] < lay["coax"]:
            return NOT, None, None
    else:
        ok_unknown.append("coax")
    # 3) heat budget at the highest documented cooling-power temperature not above t_op
    load = si(p["design_margin"]["value"]) * (
        lay["n_drive_lines"] * si(p["q_drive_line"]["value"])
        + lay["n_flux_lines"] * (si(p["q_flux_line"]["value"]) + si(p["p_flux_dc"]["value"]))
        + lay["n_output_lines"] * si(p["q_output_line"]["value"]))
    best = None
    for key, c in caps.items():
        at = (vocab.get(key) or {}).get("at_temperature")
        if not key.startswith("cooling_power.") or not at or c["install"] != "installed" \
                or c["evidence_status"] not in trusted or c["value"].get("kind") != "max":
            continue
        t_doc = si(at)
        if t_doc <= t_op and (best is None or t_doc > best[0]):
            best = (t_doc, si(c["value"]["q"]))
    if best is None:
        return (NI, load, None)
    if load > best[1]:
        return NOT, load, best[1]
    return (NI if ok_unknown else MET), load, best[1]


def t3_physics(cat: Catalog, cfgs: dict, n_max: int = 200) -> dict:
    print("T3 physics sweep (qubit wiring) ...", flush=True)
    base = serialize.working_experiment(cat, WIRING, None, None, True)
    vocab = cat.vocabulary
    pairs, meta = [], []
    for n in range(1, n_max + 1):
        lay = layout(n)
        ex = copy.deepcopy(base)
        for prm in ex["params"]:
            if prm["name"] in lay:
                prm["value"] = {"unit": "count", "value": lay[prm["name"]]}
        for req in ex["requirements"]:
            if req.get("key") == "electrical.coax_lines" or "electrical.coax_lines" in (req.get("keys") or []):
                req["constraint"]["n"] = lay["coax"]
        for cid, (cm, cd) in cfgs.items():
            truth, load, cool = truth_wiring(cm, ex, lay, vocab)
            pairs.append((cd, serialize.experiment_doc(cat, ex, cm)[0]))
            meta.append({"n": n, "c": cid, "truth": truth, "load_W": float(load) if load is not None else None,
                         "cool_W": float(cool) if cool is not None else None})
    rows = verdicts_for(pairs)
    for r, m in zip(rows, meta):
        r.update(m)
    by = {}
    for m in METHODS:
        wy = sum(1 for r in rows if r["truth"] == NOT and r["v"][m] == MET)
        wn = sum(1 for r in rows if r["truth"] == MET and r["v"][m] == NOT)
        agree = sum(1 for r in rows if r["truth"] == r["v"][m])
        by[m] = {"wrong_YES": wy, "wrong_NO": wn, "agree_with_rule": agree}
    # per refrigerator: largest n each method says YES to vs the largest n the published rule allows
    fridges = {}
    for cid in cfgs:
        rs = [r for r in rows if r["c"] == cid]
        if not any(r["v"][m] == MET for r in rs for m in METHODS) and not any(r["truth"] == MET for r in rs):
            continue
        f = {"name": cfgs[cid][0].get("name"), "rule_max_qubits": max((r["n"] for r in rs if r["truth"] == MET), default=0)}
        for m in METHODS:
            f[m + "_max_yes"] = max((r["n"] for r in rs if r["v"][m] == MET), default=0)
        f["curve"] = [{"n": r["n"], "load_W": r["load_W"], "cool_W": r["cool_W"], "truth": rw.SHORT[r["truth"]],
                       **{m: rw.SHORT[r["v"][m]] for m in METHODS}} for r in rs]
        fridges[cid] = f
    res = {"cases": len(rows), "qubits": [1, n_max], "configurations": len(cfgs),
           "truth": "Krinner et al. design rule (3x margin) recomputed in exact fractions from the catalog",
           "by_method": by, "fridges": fridges}
    save("t3_physics_sweep", res)
    print(f"   {len(rows)} cases; wrong YES " + ", ".join(f"{m}={by[m]['wrong_YES']}" for m in METHODS))
    return res


# ============================================================================== T4 project history
def t4_history(rev: str = HISTORY_REV) -> dict | None:
    print(f"T4 project history ({rev} -> today) ...", flush=True)
    try:
        tar = subprocess.run(["git", "archive", rev, "data"], cwd=ROOT, capture_output=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"   skipped: git history for {rev} not available ({e})")
        return None
    tmp = Path(tempfile.mkdtemp(prefix="cryolean_hist_"))
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(tmp, filter="data")
    db.build_database(seed_dir=tmp / "data", db_path=tmp / "base.db")
    db.build_database(db_path=tmp / "now.db")
    old, new = Catalog(tmp / "base.db"), Catalog(tmp / "now.db")
    cids = [c for c in sorted(old.configurations) if c in new.configurations]
    eids = [e for e in sorted(old.experiments) if e in new.experiments]
    od, nd = grid.configuration_documents(old, cids), grid.configuration_documents(new, cids)
    o_pairs, n_pairs, keys = [], [], []
    same_question = 0
    for e in eids:
        oe = serialize.working_experiment(old, e, None, None, True)
        ne = serialize.working_experiment(new, e, None, None, True)
        for c in cids:
            oed = serialize.experiment_doc(old, oe, od[c][0])[0]
            ned = serialize.experiment_doc(new, ne, nd[c][0])[0]
            if json.dumps(oed["requirements"], sort_keys=True) != json.dumps(ned["requirements"], sort_keys=True) or \
                    json.dumps(oed["coupled"], sort_keys=True) != json.dumps(ned["coupled"], sort_keys=True):
                continue                      # the question itself changed: not a test of documentation
            same_question += 1
            o_pairs.append((od[c][1], oed))
            n_pairs.append((nd[c][1], ned))
            keys.append((e, c))
    o_rows, n_rows = verdicts_for(o_pairs), verdicts_for(n_pairs)
    later_no = [(k, o) for k, o, n in zip(keys, o_rows, n_rows) if n["v"]["CryoLean"] == NOT]
    later_yes = [(k, o) for k, o, n in zip(keys, o_rows, n_rows) if n["v"]["CryoLean"] == MET]
    by = {}
    for m in METHODS:
        by[m] = {"said_YES_later_documented_NO": sum(1 for _, o in later_no if o["v"][m] == MET),
                 "said_NO_later_documented_YES": sum(1 for _, o in later_yes if o["v"][m] == NOT),
                 "old_counts": dict(Counter(rw.SHORT[o["v"][m]] for o in o_rows))}
    ex = [{"experiment": k[0], "configuration": k[1], **{m: rw.SHORT[o["v"][m]] for m in METHODS},
           "today": "NO",
           "why_today": [f"{lbl}: {l['required']}; sheet now: {l['available']}" for lbl, l in n["lean"]["lines"].items()
                         if l["outcome"] == "fail"] + [f"{lbl}: {c['lhs']} vs {c['rhs']}" for lbl, c in
                                                        n["lean"]["coupled"].items() if c["outcome"] == "fail"]}
          for k, o, n in zip(keys, o_rows, n_rows) if n["v"]["CryoLean"] == NOT and o["v"]["R1"] == MET][:40]
    res = {"revision": rev, "pairs_same_question": same_question, "later_documented_NO": len(later_no),
           "later_documented_YES": len(later_yes), "by_method": by, "examples": ex,
           "truth": "the verdict on today's sourced records for the same experiment requirements"}
    save("t4_history", res)
    print(f"   {same_question} pairs; later NO {len(later_no)}; said YES on old data: " +
          ", ".join(f"{m}={by[m]['said_YES_later_documented_NO']}" for m in METHODS))
    return res


# ============================================================================== T5 fault injection
def t5_faults(n_single=1800, n_multi=900, seed=7) -> dict:
    print("T5 fault injection ...", flush=True)
    sys.path.insert(0, str(ROOT / "paper" / "scripts"))
    Q = units.lean_quantity

    def good(k):
        return {"temperature.range": {"kind": "range", "lo": Q(1, "K"), "hi": Q(400, "K")},
                "magnetic_field.max": {"kind": "max", "q": Q(20, "T")}, "optical_access": {"kind": "flag", "b": True},
                "electrical.dc_lines": {"kind": "count", "n": 48}, "sample.width.max": {"kind": "max", "q": Q(50, "mm")}}[k]

    keys = ["temperature.range", "magnetic_field.max", "optical_access", "electrical.dc_lines", "sample.width.max"]
    reqs = [{"keys": ["temperature.range"], "constraint": {"kind": "point_within", "q": Q(4, "K")}},
            {"keys": ["magnetic_field.max"], "constraint": {"kind": "at_least", "q": Q(9, "T")}},
            {"keys": ["optical_access"], "constraint": {"kind": "present"}},
            {"keys": ["electrical.dc_lines"], "constraint": {"kind": "count_at_least", "n": 8}},
            {"keys": ["sample.width.max"], "constraint": {"kind": "at_least", "q": Q(3, "mm")}}]
    bad = {"temperature.range": {"kind": "range", "lo": Q(10, "K"), "hi": Q(400, "K")},
           "magnetic_field.max": {"kind": "max", "q": Q(5, "T")}, "optical_access": {"kind": "flag", "b": False},
           "electrical.dc_lines": {"kind": "count", "n": 4}, "sample.width.max": {"kind": "max", "q": Q(2, "mm")}}
    # truth by construction: below_limit / optional_trusted make the setup impossible; every other defect means the
    # sheet cannot certify the line (the right answer is NEED INFO, never YES)
    defects = ["unknown_value", "estimate", "no_provenance", "install_unknown", "optional_trusted",
               "optional_untrusted", "wrong_dimension", "missing", "below_limit"]
    impossible = {"below_limit", "optional_trusted"}

    def cap(k, d):
        c = {"key": k, "value": good(k), "install": "installed", "evidence_status": "manufacturer_specification",
             "evidence_ids": []}
        if d == "unknown_value":
            c.update(value={"kind": "unknown"}, evidence_status="unknown")
        elif d == "estimate":
            c["evidence_status"] = "inferred_estimate"
        elif d == "no_provenance":
            c["evidence_status"] = "unknown"
        elif d == "install_unknown":
            c["install"] = "unknown"
        elif d == "optional_trusted":
            c["install"] = "optional_not_installed"
        elif d == "optional_untrusted":
            c.update(install="optional_not_installed", evidence_status="inferred_estimate")
        elif d == "wrong_dimension":
            v = c["value"]
            if v["kind"] in ("flag", "count"):
                c["value"] = {"kind": "max", "q": Q(1, "K")}
            else:
                for side in ("q", "lo", "hi"):
                    if side in v:
                        v[side] = {**v[side], "dim": {"kg": 1, "A": 3}}
        elif d == "below_limit":
            c["value"] = bad[k]
        return c

    rng = random.Random(seed)
    pairs, meta = [], []
    for i in range(n_single + n_multi + 50):
        if i < n_single:
            d = {rng.choice(keys): rng.choice(defects)}
        elif i < n_single + n_multi:
            d = {k: rng.choice(defects) for k in rng.sample(keys, rng.randint(2, 4))}
        else:
            d = {}
        caps = [cap(k, d.get(k)) for k in keys if d.get(k) != "missing"]
        cfg = {"id": f"f{i}", "equipment_id": "synthetic", "name": "synthetic", "capabilities": caps}
        exp = {"id": "e", "name": "e", "industry": "any", "params": [], "coupled": [], "confirmed": True,
               "requirements": [{**r, "mandatory": True, "applicable": True, "conditions": [], "origin": "user_entered",
                                 "rationale": "", "evidence_ids": []} for r in reqs]}
        truth = MET if not d else (NOT if set(d.values()) & impossible else NI)
        pairs.append((cfg, exp))
        meta.append({"defects": d, "truth": truth})
    rows = verdicts_for(pairs)
    for r, m in zip(rows, meta):
        r.update(m)
    by = {}
    for m in METHODS:
        by[m] = {"impossible_cases_said_YES": sum(1 for r in rows if r["truth"] == NOT and r["v"][m] == MET),
                 "uncertifiable_cases_said_YES": sum(1 for r in rows if r["truth"] == NI and r["v"][m] == MET),
                 "clean_controls_said_YES": sum(1 for r in rows if r["truth"] == MET and r["v"][m] == MET),
                 "exact_agreement_with_truth": sum(1 for r in rows if r["v"][m] == r["truth"])}
    per_defect = defaultdict(lambda: {m: 0 for m in METHODS})
    for r in rows:
        if len(r["defects"]) == 1:
            dname = next(iter(r["defects"].values()))
            for m in METHODS:
                per_defect[dname][m] += r["v"][m] == MET
    res = {"cases": len(rows), "impossible": sum(1 for r in rows if r["truth"] == NOT),
           "uncertifiable": sum(1 for r in rows if r["truth"] == NI), "controls": sum(1 for r in rows if r["truth"] == MET),
           "by_method": by, "single_defect_said_YES": dict(per_defect)}
    save("t5_fault_injection", res)
    print(f"   {len(rows)} cases; impossible said YES " +
          ", ".join(f"{m}={by[m]['impossible_cases_said_YES']}" for m in METHODS))
    return res


# ============================================================================== main
def lean_proofs() -> dict:
    """Compile lean/VsRegular.lean and read its axiom audit (standard axioms only, or this fails)."""
    p = subprocess.run(["lake", "env", "lean", "VsRegular.lean"], cwd=ROOT / "lean", capture_output=True, text=True,
                       encoding="utf-8")
    std = {"propext", "Classical.choice", "Quot.sound"}
    thms = {}
    for line in p.stdout.splitlines():
        if "depends on axioms" in line or "does not depend on any axioms" in line:
            name = line.split("'")[1].replace("CryoLean.Regular.", "")
            ax = line.split("[", 1)[1].rstrip("]").split(", ") if "[" in line else []
            thms[name] = ax
    ok = p.returncode == 0 and bool(thms) and all(set(a) <= std for a in thms.values()) and "sorry" not in p.stdout
    res = {"file": "lean/VsRegular.lean", "compiled": p.returncode == 0, "theorems": thms, "standard_axioms_only": ok,
           "errors": (p.stdout + p.stderr)[-2000:] if p.returncode else ""}
    save("lean_proofs", res)
    print(f"Lean proofs: {len(thms)} theorems, compiled={res['compiled']}, standard axioms only={ok}")
    return res


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if lean_runner.lean_binary() is None:
        sys.exit("Lean checker not built: run `cd lean && lake build` first")
    t = time.perf_counter()
    proofs = lean_proofs()
    cat = Catalog()
    cfgs = grid.configuration_documents(cat)
    t0, per_pair = t0_catalog(cat, cfgs)
    t1, t2 = t1_t2_hide_and_borrow(cat, cfgs, per_pair)
    t3 = t3_physics(cat, cfgs)
    t4 = t4_history()
    t5 = t5_faults()
    summary = {"lean_checker": lean_runner.source_hash(), "seconds": round(time.perf_counter() - t, 1),
               "lean_proofs": {"theorems": len(proofs["theorems"]), "standard_axioms_only": proofs["standard_axioms_only"]},
               "t0": {k: t0[k] for k in ("pairs", "counts", "yes_without_support", "yes_without_support_by_cause",
                                         "no_without_support")},
               "t1_one_line": t1["one"]["by_method"], "t1_cases": t1["one"]["cases"],
               "t1_named_hidden_line": t1["one"]["cryolean_need_info_names_the_hidden_line"],
               "t1_all_lines": t1["all"]["by_method"], "t1_all_cases": t1["all"]["cases"],
               "t2": t2["by_method"], "t2_cases": t2["cases"],
               "t3": t3["by_method"], "t3_cases": t3["cases"],
               "t4": t4 and {k: t4[k] for k in ("revision", "pairs_same_question", "later_documented_NO",
                                                "later_documented_YES", "by_method")},
               "t5": t5["by_method"], "t5_cases": t5["cases"]}
    save("summary", summary)
    print(f"done in {summary['seconds']}s -> bench/results/")


if __name__ == "__main__":
    main()
