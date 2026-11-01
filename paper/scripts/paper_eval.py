#!/usr/bin/env python
"""Evaluation for the CryoLean paper. Every number in paper/ comes from this script's real runs of the
compiled Lean checker and Z3 on this machine; results are written to paper/data/*.json.

    python paper/scripts/paper_eval.py            (about 10-20 minutes)

E1 verdict grid: every experiment profile x every cryostat configuration (Lean, batch).
E2 latency: one Lean check per pair (subprocess) and the full pipeline with Z3 suggestions.
E3 Z3 vs Lean: equipment search, Z3 status of each candidate against the Lean verdict.
E4 fault injection: random single and multiple defects in synthetic configurations; Lean must never accept.
E5 heat-budget sweep (Demo B): Lean verdict for every flux-line count 0..60.
E6 scheduling: run-length sweep, and random tampering of a valid schedule judged by Lean and by an
   independent Python re-implementation of ScheduleOK.
E7 coverage and evidence.  E8 proof statistics.  E9 Gatekeeper corpus.
"""
from __future__ import annotations

import copy
import json
import platform
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cryolean import config, coverage, gatekeeper, lean_runner, schedule, serialize, units, verifier  # noqa: E402
from cryolean.bridge import CryoLeanAPI  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

OUT = ROOT / "paper" / "data"


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {name}.json")


def pct(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p / 100
    f, c = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


# ---------------------------------------------------------------- E1 + E2a
def e1_grid(cat: Catalog):
    print("E1 verdict grid + E2 Lean latency")
    exps, cfgs = sorted(cat.experiments), sorted(cat.configurations)
    rows, lat = [], []
    for eid in exps:
        ex = serialize.working_experiment(cat, eid, None, None, True)
        for cid in cfgs:
            try:
                cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
            except Exception as e:  # noqa: BLE001
                rows.append({"experiment": eid, "configuration": cid, "verdict": "BUILD_ERROR", "error": str(e)})
                continue
            t0 = time.perf_counter()
            r = lean_runner.check(cd, ed)
            lat.append(time.perf_counter() - t0)
            fails = sorted({"/".join(c["keys"]) for c in r["checks"] if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"}
                           | {c["model"] for c in r["coupled_checks"] if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"})
            missing = sorted({"/".join(c["keys"]) for c in r["checks"] if c["mandatory"] and c["applicable"] and c["outcome"] in ("unknown", "unsupported")}
                             | {c["model"] for c in r["coupled_checks"] if c["mandatory"] and c["applicable"] and c["outcome"] in ("unknown", "unsupported")})
            rows.append({"experiment": eid, "configuration": cid, "family": cat.configurations[cid].get("family"),
                         "verdict": r["verdict"], "failed": fails, "missing": missing,
                         "n_checks": len(r["checks"]) + len(r["coupled_checks"])})
    # batch timing: the whole grid in one Lean process
    pairs = []
    for eid in exps:
        ex = serialize.working_experiment(cat, eid, None, None, True)
        for cid in cfgs:
            try:
                cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
                pairs.append((cd, ed))
            except Exception:  # noqa: BLE001
                pass
    t0 = time.perf_counter()
    batch = lean_runner.check_batch(pairs)
    tb = time.perf_counter() - t0
    agree = sum(1 for (row, b) in zip([r for r in rows if r["verdict"] != "BUILD_ERROR"], batch) if row["verdict"] == b["verdict"])
    save("e1_grid", {"experiments": exps, "configurations": cfgs, "rows": rows,
                     "counts": Counter(r["verdict"] for r in rows),
                     "batch_agrees_with_single": agree, "pairs": len(pairs)})
    return rows, lat, tb, len(pairs)


def e2_pipeline(cat: Catalog, rows):
    print("E2 full pipeline latency (Lean + Z3 suggestions + Lean re-checks)")
    by_exp = defaultdict(list)
    for r in rows:
        if r["verdict"] != "BUILD_ERROR":
            by_exp[r["experiment"]].append(r)
    times, z3_alts = [], []
    for eid, rs in by_exp.items():
        for r in rs[:4]:
            ex = serialize.working_experiment(cat, eid, None, None, True)
            t0 = time.perf_counter()
            res = verifier.check(cat, ex, r["configuration"], suggestions=True, max_alternatives=3)
            times.append({"experiment": eid, "configuration": r["configuration"], "verdict": res["verdict"],
                          "seconds": time.perf_counter() - t0})
            alts = (res.get("suggestions") or {}).get("alternatives") or []
            z3_alts.append(len(alts))
    return times


# ---------------------------------------------------------------- E3
def e3_search(api: CryoLeanAPI, cat: Catalog):
    print("E3 Z3 search vs Lean verdicts")
    out, cross = [], Counter()
    for eid in sorted(cat.experiments):
        t0 = time.perf_counter()
        r = api.find_compatible_equipment(eid, confirmed=True)
        dt = time.perf_counter() - t0
        if not r["ok"]:
            out.append({"experiment": eid, "error": r["error"]})
            continue
        cands = r["data"]["candidates"]
        for c in cands:
            cross[(c["z3_status"], c["lean_verdict"])] += 1
        out.append({"experiment": eid, "seconds": dt, "candidates": [{k: c.get(k) for k in ("configuration_id", "z3_status", "lean_verdict")} for c in cands]})
    save("e3_search", {"per_experiment": out, "crosstab": [{"z3": k[0], "lean": k[1], "n": v} for k, v in sorted(cross.items())]})
    return cross


# ---------------------------------------------------------------- E4
def Q(v, u):
    return units.lean_quantity(v, u)


KEYS = ["temperature.range", "magnetic_field.max", "optical_access", "electrical.dc_lines", "sample.width.max"]
GOOD = {"temperature.range": {"kind": "range", "lo": None, "hi": None}}


def _good(k):
    return {"temperature.range": {"kind": "range", "lo": Q(1, "K"), "hi": Q(400, "K")},
            "magnetic_field.max": {"kind": "max", "q": Q(20, "T")}, "optical_access": {"kind": "flag", "b": True},
            "electrical.dc_lines": {"kind": "count", "n": 48}, "sample.width.max": {"kind": "max", "q": Q(50, "mm")}}[k]


REQS = [{"keys": ["temperature.range"], "constraint": {"kind": "point_within", "q": Q(4, "K")}},
        {"keys": ["magnetic_field.max"], "constraint": {"kind": "at_least", "q": Q(9, "T")}},
        {"keys": ["optical_access"], "constraint": {"kind": "present"}},
        {"keys": ["electrical.dc_lines"], "constraint": {"kind": "count_at_least", "n": 8}},
        {"keys": ["sample.width.max"], "constraint": {"kind": "at_least", "q": Q(3, "mm")}}]
DEFECTS = ["unknown_value", "estimate", "no_provenance", "install_unknown", "optional_trusted", "optional_untrusted",
           "wrong_dimension", "missing", "below_limit"]


def _cap(k, defect):
    c = {"key": k, "value": _good(k), "install": "installed", "evidence_status": "manufacturer_specification", "evidence_ids": []}
    if defect == "unknown_value":
        c.update(value={"kind": "unknown"}, evidence_status="unknown")
    elif defect == "estimate":
        c["evidence_status"] = "inferred_estimate"
    elif defect == "no_provenance":
        c["evidence_status"] = "unknown"
    elif defect == "install_unknown":
        c["install"] = "unknown"
    elif defect == "optional_trusted":
        c["install"] = "optional_not_installed"
    elif defect == "optional_untrusted":
        c.update(install="optional_not_installed", evidence_status="inferred_estimate")
    elif defect == "wrong_dimension":
        v = c["value"]
        if v["kind"] in ("flag", "count"):
            c["value"] = {"kind": "max", "q": Q(1, "K")}
        else:
            for side in ("q", "lo", "hi"):
                if side in v:
                    v[side] = {**v[side], "dim": {"kg": 1, "A": 3}}
    elif defect == "below_limit":
        c["value"] = {"temperature.range": {"kind": "range", "lo": Q(10, "K"), "hi": Q(400, "K")},
                      "magnetic_field.max": {"kind": "max", "q": Q(5, "T")}, "optical_access": {"kind": "flag", "b": False},
                      "electrical.dc_lines": {"kind": "count", "n": 4}, "sample.width.max": {"kind": "max", "q": Q(2, "mm")}}[k]
    return c


EXPECT = {"unknown_value": "NEED_MORE_INFORMATION", "estimate": "NEED_MORE_INFORMATION", "no_provenance": "NEED_MORE_INFORMATION",
          "install_unknown": "NEED_MORE_INFORMATION", "optional_trusted": "DOES_NOT_MEET_REQUIREMENTS",
          "optional_untrusted": "NEED_MORE_INFORMATION", "wrong_dimension": "NEED_MORE_INFORMATION",
          "missing": "NEED_MORE_INFORMATION", "below_limit": "DOES_NOT_MEET_REQUIREMENTS"}
RANK = {"DOES_NOT_MEET_REQUIREMENTS": 2, "NEED_MORE_INFORMATION": 1, "REQUIREMENTS_MET": 0}


def e4_faults(n_single=1800, n_multi=900, seed=7):
    print("E4 fault injection")
    rng = random.Random(seed)
    cases = []
    for i in range(n_single + n_multi + 50):
        if i < n_single:
            d = {rng.choice(KEYS): rng.choice(DEFECTS)}
        elif i < n_single + n_multi:
            ks = rng.sample(KEYS, rng.randint(2, 4))
            d = {k: rng.choice(DEFECTS) for k in ks}
        else:
            d = {}                                     # controls: all documented
        caps = [_cap(k, d.get(k)) for k in KEYS if d.get(k) != "missing"]
        cfg = {"id": f"f{i}", "equipment_id": "synthetic", "name": "synthetic", "capabilities": caps}
        exp = {"id": "e", "name": "e", "industry": rng.choice(["x", "any", "new industry"]), "params": [], "coupled": [],
               "requirements": [{**r, "mandatory": True, "origin": "user_entered"} for r in REQS], "confirmed": True}
        # expected verdict from an independent rule: any trusted violation -> reject; else any defect -> need info
        exp_v = "REQUIREMENTS_MET" if not d else max((EXPECT[x] for x in d.values()), key=lambda v: RANK[v])
        cases.append((cfg, exp, d, exp_v))
    t0 = time.perf_counter()
    res = lean_runner.check_batch([(c, e) for c, e, _, _ in cases])
    dt = time.perf_counter() - t0
    by_defect = defaultdict(Counter)
    agree, accepted_with_defect = 0, 0
    for (cfg, exp, d, exp_v), r in zip(cases, res):
        kind = "control" if not d else ("single:" + next(iter(d.values())) if len(d) == 1 else "multiple")
        by_defect[kind][r["verdict"]] += 1
        agree += r["verdict"] == exp_v
        accepted_with_defect += bool(d) and r["verdict"] == "REQUIREMENTS_MET"
    save("e4_faults", {"cases": len(cases), "seconds": dt, "agree_with_independent_rule": agree,
                       "accepted_with_a_defect": accepted_with_defect,
                       "by_defect": {k: dict(v) for k, v in sorted(by_defect.items())}})


# ---------------------------------------------------------------- E5
def e5_heat(cat: Catalog):
    print("E5 heat-budget sweep")
    ex = serialize.working_experiment(cat, "quantum_mxc_wiring_heat_budget", None, None, True)
    cd, ed, _, _ = verifier.build_documents(cat, ex, "bluefors_ld400_hdw")
    pts = []
    pairs = []
    for n in range(0, 61):
        e2 = copy.deepcopy(ed)
        for p in e2["params"]:
            if p["name"] == "n_flux_lines":
                p["value"] = {"num": n, "den": 1, "dim": {}}
                p["origin"] = "user_entered"
        pairs.append((cd, e2))
    for n, r in zip(range(0, 61), lean_runner.check_batch(pairs)):
        c = next(c for c in r["coupled_checks"] if c["model"] == "mxc_wiring_heat_budget")
        def val(side):
            v = (c.get(side) or {}).get("value")
            return Fraction(v["num"], v["den"]) if v else None
        lhs, rhs = val("lhs"), val("rhs")
        pts.append({"n_flux_lines": n, "verdict": r["verdict"], "coupled_outcome": c["outcome"],
                    "lhs_uW": float(lhs * 10**6) if lhs is not None else None, "rhs_uW": float(rhs * 10**6) if rhs is not None else None})
    res = verifier.check(cat, ex, "bluefors_ld400_hdw", suggestions=True)
    pc = [p for p in res["suggestions"]["parameter_changes"] if p.get("status") == "found"]
    save("e5_heat", {"points": pts, "z3_suggestion": pc, "configuration": "bluefors_ld400_hdw",
                     "params": {p["name"]: p.get("display") for p in res["experiment"]["parameters"]}})


# ---------------------------------------------------------------- E6
def _ok_python(doc):
    """Independent re-implementation of Lean's ScheduleOK on the JSON document (for the tamper study)."""
    cd = doc["configuration"]
    cap = next((c for c in cd["capabilities"] if c["key"] == "cooldown_time.max"), None)
    if cap is None:
        return False
    cool = Fraction(cap["value"]["q"]["num"], cap["value"]["q"]["den"])
    L = Fraction(doc["run_length"]["num"], doc["run_length"]["den"])
    exps = {e["id"]: e for e in doc["experiments"]}
    if [s["experiment_id"] for s in doc["slots"]] != [e["id"] for e in doc["experiments"]]:
        return False
    iv = []
    for s in doc["slots"]:
        e = exps[s["experiment_id"]]
        d = next(p for p in e["params"] if p["name"] == "run_duration")["value"]
        st = Fraction(s["start"]["num"], s["start"]["den"])
        du = Fraction(d["num"], d["den"])
        if st < cool or st + du > L:
            return False
        iv.append((st, st + du))
    for i in range(len(iv)):
        for j in range(i + 1, len(iv)):
            a, b = iv[i], iv[j]
            if not (a[1] <= b[0] or b[1] <= a[0]):
                return False
    return True


def e6_schedule(cat: Catalog, n_tamper=400, seed=11):
    print("E6 scheduling")
    exps = ["bio_cryo_fluorescence_vitrified", "chem_low_temperature_raman", "chem_phase_transition_pom"]
    durs = {exps[0]: {"value": 6, "unit": "h"}, exps[1]: {"value": 8, "unit": "h"}, exps[2]: {"value": 4, "unit": "h"}}
    sweep = []
    for half in range(32, 61):                         # 16 h .. 30 h in 0.5 h steps
        L = half / 2
        t0 = time.perf_counter()
        r = schedule.schedule_campaign(cat, "lakeshore_crx_vf", exps, {"value": str(L), "unit": "h"}, durs, confirmed=True)
        sweep.append({"run_length_h": L, "z3": r["z3"]["status"], "lean_valid": (r["lean"] or {}).get("valid"),
                      "makespan": r["z3"].get("makespan"), "seconds": time.perf_counter() - t0})
    base = schedule.schedule_campaign(cat, "lakeshore_crx_vf", exps, {"value": 48, "unit": "h"}, durs, confirmed=True)
    doc = base["lean_input"]
    rng = random.Random(seed)
    tamper, conf = [], Counter()
    docs = []
    for i in range(n_tamper):
        d = copy.deepcopy(doc)
        kind = rng.choice(["shift_one", "shift_all", "swap_ids", "noop", "drop_slot_id", "early", "late"])
        if kind == "shift_one":
            s = rng.choice(d["slots"])
            s["start"] = {"num": int(Fraction(s["start"]["num"], s["start"]["den"]) + rng.randint(-8, 8) * 1800), "den": 1, "dim": {"s": 1}}
        elif kind == "shift_all":
            k = rng.randint(-6, 60) * 1800
            for s in d["slots"]:
                s["start"] = {"num": int(Fraction(s["start"]["num"], s["start"]["den"]) + k), "den": 1, "dim": {"s": 1}}
        elif kind == "swap_ids":
            a, b = rng.sample(range(len(d["slots"])), 2)
            d["slots"][a]["experiment_id"], d["slots"][b]["experiment_id"] = d["slots"][b]["experiment_id"], d["slots"][a]["experiment_id"]
        elif kind == "drop_slot_id":
            d["slots"][rng.randrange(len(d["slots"]))]["experiment_id"] = "unknown_experiment"
        elif kind == "early":
            d["slots"][rng.randrange(len(d["slots"]))]["start"] = {"num": rng.randint(0, 17999), "den": 1, "dim": {"s": 1}}
        elif kind == "late":
            d["slots"][rng.randrange(len(d["slots"]))]["start"] = {"num": rng.randint(40, 47) * 3600, "den": 1, "dim": {"s": 1}}
        docs.append((kind, d))
    t0 = time.perf_counter()
    for kind, d in docs:
        lean_ok = bool(lean_runner.check_schedule(d).get("valid"))
        try:
            py_ok = _ok_python(d)
        except (KeyError, StopIteration):
            py_ok = False
        conf[(lean_ok, py_ok)] += 1
        tamper.append({"kind": kind, "lean": lean_ok, "python": py_ok})
    dt = time.perf_counter() - t0
    by_kind = defaultdict(Counter)
    for t in tamper:
        by_kind[t["kind"]]["valid" if t["lean"] else "rejected"] += 1
    save("e6_schedule", {"sweep": sweep, "timeline": base["timeline"], "cooldown": base["cooldown"],
                         "makespan": base["z3"]["makespan"], "tamper_cases": len(tamper), "tamper_seconds": dt,
                         "lean_vs_independent": [{"lean_valid": k[0], "python_valid": k[1], "n": v} for k, v in sorted(conf.items())],
                         "by_kind": {k: dict(v) for k, v in by_kind.items()}})


# ---------------------------------------------------------------- E7, E8, E9
def e7_coverage(cat: Catalog):
    print("E7 coverage")
    cov = coverage.build(cat)
    unknown_by_cfg = Counter(u.get("configuration_id") or u.get("configuration") for u in cov["missing_scientific_data"]["unknown_capabilities"])
    save("e7_coverage", {"evidence_by_status": cov["manufacturer_evidence"]["by_status"],
                         "evidence_records": cov["manufacturer_evidence"]["records"],
                         "properties_by_status": cov["physical_properties"]["by_status"],
                         "properties": [{k: p.get(k) for k in ("id", "name", "status", "category")} for p in cov["physical_properties"]["properties"]],
                         "unknown_by_configuration": dict(unknown_by_cfg),
                         "unknown_capabilities": len(cov["missing_scientific_data"]["unknown_capabilities"]),
                         "inferred_estimates": len(cov["missing_scientific_data"]["inferred_estimates"]),
                         "industries": cov["industries"]["registered_or_known"], "coupled_models": len(cov["coupled_constraints"]["models"]),
                         "source_validation": cov["source_validation"]})


def e8_proofs():
    print("E8 proof statistics")
    files = {}
    for p in sorted((config.LEAN_DIR / "CryoLean").glob("*.lean")):
        t = p.read_text(encoding="utf-8")
        files[p.stem] = {"lines": len(t.splitlines()),
                         "theorems": len(re.findall(r"^\s*(?:private\s+)?theorem\s", t, flags=re.M)),
                         "defs": len(re.findall(r"^\s*(?:private\s+|partial\s+|noncomputable\s+)?(?:def|inductive|structure|abbrev|instance)\s", t, flags=re.M))}
    audit = lean_runner.axiom_audit()
    ax = Counter(a for v in audit["theorems"].values() for a in v)
    fx = json.loads((ROOT / "docs" / "forensics" / "summary.json").read_text(encoding="utf-8"))
    save("e8_proofs", {"files": files, "audited": len(audit["theorems"]), "axiom_use": dict(ax),
                       "theorems_axioms": audit["theorems"], "audit_status": audit["status"], "forensics": fx})


def e9_gatekeeper():
    print("E9 Gatekeeper corpus")
    corpus = [
        ("clean proof", "import CryoLean\nopen CryoLean\ntheorem gk_le_refl (a : Q) : Q.le a a := Q.le_refl a\n"),
        ("uses sorry", "theorem gk_sorry : 1 = 2 := by sorry\n"),
        ("native_decide", "theorem gk_native : 2 + 2 = 4 := by native_decide\n"),
        ("custom axiom", "axiom cheat : False\ntheorem gk_axiom : 1 = 2 := cheat.elim\n"),
        ("false statement", "theorem gk_false : (1 : Nat) = 2 := rfl\n"),
        ("clean, about the checker", "import CryoLean\nopen CryoLean\ntheorem gk_untrusted (k : Constraint) (c : Capability)\n"
                                     "    (h : c.evidence = .inferredEstimate) : checkCapability k c ≠ .pass :=\n  estimate_never_passes h\n"),
    ]
    lanyon = next((ROOT / "docs" / "lanyon").rglob("proof-*.lean"), None)
    if lanyon:
        corpus.append(("Lanyon exported proof (Mathlib)", lanyon.read_text(encoding="utf-8")))
    out = []
    for name, src in corpus:
        t0 = time.perf_counter()
        r = gatekeeper.check(src)
        out.append({"case": name, "admitted": r["admissible"], "escape_hatches": r["escape_hatches"],
                    "compiled": r["compiled"], "compile_errors": r.get("compile_errors", 0),
                    "nonstandard": r["nonstandard"], "reason": r.get("reason"), "seconds": time.perf_counter() - t0})
    save("e9_gatekeeper", {"cases": out})


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cat = Catalog()
    api = CryoLeanAPI()
    env = {"machine": platform.processor() or platform.machine(), "python": platform.python_version(),
           "os": platform.platform(), "lean": lean_runner.version(), "date": time.strftime("%Y-%m-%d")}
    rows, lat, tb, npairs = e1_grid(cat)
    pipe = e2_pipeline(cat, rows)
    save("e2_latency", {"env": env, "lean_single_seconds": lat, "lean_single_median": statistics.median(lat),
                        "lean_single_p95": pct(lat, 95), "batch_seconds": tb, "batch_pairs": npairs,
                        "pipeline": pipe, "pipeline_median": statistics.median(p["seconds"] for p in pipe),
                        "pipeline_p95": pct([p["seconds"] for p in pipe], 95)})
    e3_search(api, cat)
    e4_faults()
    e5_heat(cat)
    e6_schedule(cat)
    e7_coverage(cat)
    e8_proofs()
    e9_gatekeeper()
    save("env", env)


if __name__ == "__main__":
    main()
