#!/usr/bin/env python
"""Baselines and robustness figures for the CryoLean paper.

    python paper/scripts/fig_baselines.py              (about 1 minute; reuses paper/data/fig_incomplete_info.json)
    python paper/scripts/fig_baselines.py --recompute  (re-runs the 188,760-check deletion study, about 9 minutes)

fig_baseline_comparison    CryoLean (Lean verdicts) vs two Python baselines on the 11 x 26 = 286-pair grid.
fig_independent_vs_coupled Demo B: every single-capability requirement passes, the coupled heat budget fails, Z3
                           proposes a repair that Lean re-checks; coupled-check outcomes across the grid.
fig_incomplete_info        random deletion of k % of each configuration's documented capabilities, re-checked by Lean.
fig_fault_injection        the 2750 fault-injection cases of paper/data/e4_faults.json.

Every verdict labelled "CryoLean" or "Lean" comes from the compiled Lean checker (lean_runner.check_batch / check).
The baselines B1/B2 are deliberately simple Python re-implementations of a datasheet comparison; they are NOT
verified and exist only to show what an independent-property check misses.
"""
from __future__ import annotations

import copy
import random
import re
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

import numpy as np
from matplotlib.patches import Patch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import (COL2, DATA_DIR, GRID, INK, INK2, LAVENDER, MUTED, NAVY, ORANGE, SEQ_CMAP, VERDICT_COLOR,  # noqa: E402
                   VERDICT_HATCH, VERDICT_LABEL, VERDICT_ORDER, VERDICT_SHORT, apply, dump, load, plt, save,
                   verdict_legend)

from cryolean import lean_runner, serialize, verifier  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

MET, NI, NOT = "REQUIREMENTS_MET", "NEED_MORE_INFORMATION", "DOES_NOT_MEET_REQUIREMENTS"
SEED = 20261031
UNTRUSTED = ("inferred_estimate", "unknown")


# ============================================================== grid
def build_grid(cat: Catalog):
    ids, pairs = [], []
    for eid in sorted(cat.experiments):
        ex = serialize.working_experiment(cat, eid, None, None, True)
        for cid in sorted(cat.configurations):
            cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
            ids.append((eid, cid))
            pairs.append((cd, ed))
    return ids, pairs


def batched(pairs, chunk=4000):
    out = []
    for i in range(0, len(pairs), chunk):
        out.extend(lean_runner.check_batch(pairs[i:i + chunk]))
    return out


# ============================================================== baselines (Python, NOT verified)
def _q(x):
    return Fraction(int(x["num"]), int(x["den"])), tuple(sorted((k, v) for k, v in (x.get("dim") or {}).items() if v))


def _value_outcome(con, val):
    """Compare a constraint with a documented value (exact rationals, dimensions must match)."""
    k, vk = con["kind"], val["kind"]
    if vk == "unknown":
        return "unknown"
    if k in ("present", "absent", "flag_is"):
        want = True if k == "present" else False if k == "absent" else bool(con["b"])
        return ("pass" if val["b"] == want else "fail") if vk == "flag" else "unsupported"
    if k == "count_at_least":
        return ("pass" if con["n"] <= val["n"] else "fail") if vk == "count" else "unsupported"
    if k == "count_equals":
        return ("pass" if con["n"] == val["n"] else "fail") if vk == "count" else "unsupported"
    if k == "enum_in":
        return ("pass" if val["s"] in con["allowed"] else "fail") if vk == "enum" else "unsupported"
    if k == "set_contains":
        return ("pass" if set(con["needed"]) <= set(val["xs"]) else "fail") if vk == "set" else "unsupported"
    if k == "point_within" and vk == "range":
        (q, d), (lo, dl), (hi, dh) = _q(con["q"]), _q(val["lo"]), _q(val["hi"])
        return ("pass" if lo <= q <= hi else "fail") if d == dl == dh else "unsupported"
    if k == "range_within" and vk == "range":
        (rl, d1), (rh, d2), (lo, dl), (hi, dh) = _q(con["lo"]), _q(con["hi"]), _q(val["lo"]), _q(val["hi"])
        return ("pass" if lo <= rl and rh <= hi else "fail") if d1 == d2 == dl == dh and rl <= rh else "unsupported"
    if k == "at_least" and vk in ("max", "range"):
        (q, d), (m, dm) = _q(con["q"]), _q(val["q"] if vk == "max" else val["hi"])
        return ("pass" if q <= m else "fail") if d == dm else "unsupported"
    if k == "at_most" and vk in ("min", "range"):
        (q, d), (m, dm) = _q(con["q"]), _q(val["q"] if vk == "min" else val["lo"])
        return ("pass" if m <= q else "fail") if d == dm else "unsupported"
    return "unsupported"


def _cap(cfg, key):
    return next((c for c in cfg["capabilities"] if c["key"] == key), None)


def _key_outcome(cfg, con, key):
    """Baseline per-key outcome: install status is respected, evidence status (provenance) is IGNORED."""
    cap = _cap(cfg, key)
    if cap is None or cap["install"] == "unknown":
        return "unknown"
    if cap["install"] == "optional_not_installed":
        return "pass" if con["kind"] == "absent" or (con["kind"] == "flag_is" and not con["b"]) else "fail"
    return _value_outcome(con, cap["value"])


def _cond(cfg, exp, c):
    if c["kind"] == "cap_flag":
        cap = _cap(cfg, c["key"])
        if cap is None or cap["install"] == "unknown":
            return "unknown"
        if cap["install"] == "optional_not_installed":
            return "holds" if c["b"] is False else "fails"
        return ("holds" if cap["value"]["b"] == c["b"] else "fails") if cap["value"]["kind"] == "flag" else "unknown"
    p = next((p for p in exp["params"] if p["name"] == c["name"]), None)   # parameter origin ignored
    if p is None or p.get("value") is None:
        return "unknown"
    (v, dv), (q, dq) = _q(p["value"]), _q(c["q"])
    if dv != dq:
        return "unknown"
    ok = v <= q if c["kind"] == "param_at_most" else q <= v
    return "holds" if ok else "fails"


def baseline_req_outcomes(cfg, exp):
    """Per mandatory+applicable requirement: (keys, three-valued outcome). Coupled constraints are ignored."""
    out = []
    for r in exp["requirements"]:
        if not (r.get("mandatory", True) and r.get("applicable", True)):
            continue
        cs = [_cond(cfg, exp, c) for c in r.get("conditions", [])]
        if "fails" in cs:
            out.append(("/".join(r["keys"]), "not_applicable"))
            continue
        if "unknown" in cs:
            out.append(("/".join(r["keys"]), "unknown"))
            continue
        os_ = [_key_outcome(cfg, r["constraint"], k) for k in r["keys"]]
        if "pass" in os_:
            o = "pass"
        elif os_ and all(o == "fail" for o in os_):
            o = "fail"
        elif "unknown" in os_:
            o = "unknown"
        else:
            o = "unsupported"
        out.append(("/".join(r["keys"]), o))
    return out


def b1_verdict(outs):
    """B1 optimistic: only a documented violation blocks; unknown/unsupported/missing never block."""
    return NOT if any(o == "fail" for _, o in outs) else MET


def b2_verdict(outs):
    """B2 conservative: CryoLean's three-valued verdict rule, but over single-capability requirements only."""
    os_ = [o for _, o in outs]
    if "fail" in os_:
        return NOT
    if all(o in ("pass", "not_applicable") for o in os_) and "pass" in os_:
        return MET
    return NI


def lean_coupled_blockers(r):
    return [(c["model"], c["outcome"]) for c in r["coupled_checks"]
            if c["mandatory"] and c["applicable"] and c["outcome"] not in ("pass", "not_applicable")]


def lean_req_map(r):
    return {"/".join(c["keys"]): c["outcome"] for c in r["checks"] if c["mandatory"] and c["applicable"]}


OKISH = ("pass", "not_applicable")


def causes(b_outs, r, which, bverdict):
    """Why a baseline verdict differs from Lean, read from the per-check outcomes.
    coupled:    Lean has a mandatory coupled constraint that does not pass (the baseline never evaluates it)
    provenance: the baseline decided a requirement from a value Lean does not trust (estimate / unsourced)
    missing:    (B1 only) a requirement without usable data that B1 lets pass"""
    cs, lm = set(), lean_req_map(r)
    if bverdict == MET:
        if lean_coupled_blockers(r):
            cs.add("coupled")
        for k, o in b_outs:
            if o in OKISH and lm.get(k) not in OKISH:
                cs.add("provenance")
            if which == "B1" and o in ("unknown", "unsupported"):
                cs.add("missing")
    elif bverdict == NOT:
        for k, o in b_outs:
            if o == "fail" and lm.get(k) != "fail":
                cs.add("provenance")
    else:                                      # baseline NEED INFO
        if any(o == "fail" for _, o in lean_coupled_blockers(r)):
            cs.add("coupled")
        for k, o in b_outs:
            if o != lm.get(k):
                cs.add("provenance")
    return cs


CAUSE_NAMES = {"missing": "missing data", "provenance": "provenance", "coupled": "coupled constraint"}


def cause_label(cs):
    return " + ".join(CAUSE_NAMES[c] for c in ("missing", "provenance", "coupled") if c in cs) or "other"


def explain_requirement_differences(pairs, ids, res):
    """Every requirement where the B2 outcome differs from Lean's should involve untrusted evidence."""
    n, explained, examples = 0, 0, []
    for (eid, cid), (cd, ed), r in zip(ids, pairs, res):
        lm = lean_req_map(r)
        reqs = {"/".join(q["keys"]): q for q in ed["requirements"] if q.get("mandatory", True) and q.get("applicable", True)}
        for k, o in baseline_req_outcomes(cd, ed):
            if o == lm.get(k):
                continue
            n += 1
            q = reqs[k]
            caps = [_cap(cd, kk) for kk in q["keys"]]
            ev_untrusted = any(c is not None and c["evidence_status"] in UNTRUSTED for c in caps)
            par_untrusted = any(c["kind"] != "cap_flag" and next((p for p in ed["params"] if p["name"] == c["name"]), {}).get("origin") in UNTRUSTED
                                for c in q.get("conditions", []))
            cap_cond = any(c["kind"] == "cap_flag" and (_cap(cd, c["key"]) or {}).get("evidence_status") in UNTRUSTED
                           for c in q.get("conditions", []))
            ok = ev_untrusted or par_untrusted or cap_cond
            explained += ok
            if len(examples) < 40:
                examples.append({"experiment": eid, "configuration": cid, "requirement": k, "baseline": o, "lean": lm.get(k),
                                 "evidence_status": [c["evidence_status"] if c else None for c in caps], "explained": bool(ok)})
    return n, explained, examples


# ============================================================== figure 1
def fig_baseline_comparison(cat, ids, pairs, res):
    rows = []
    for (eid, cid), (cd, ed), r in zip(ids, pairs, res):
        outs = baseline_req_outcomes(cd, ed)
        v1, v2 = b1_verdict(outs), b2_verdict(outs)
        rows.append({"experiment": eid, "configuration": cid, "lean": r["verdict"], "B1": v1, "B2": v2,
                     "baseline_requirement_outcomes": outs, "lean_requirement_outcomes": lean_req_map(r),
                     "lean_coupled_blockers": lean_coupled_blockers(r),
                     "causes_B1": sorted(causes(outs, r, "B1", v1)) if v1 != r["verdict"] else [],
                     "causes_B2": sorted(causes(outs, r, "B2", v2)) if v2 != r["verdict"] else []})
    order = [MET, NI, NOT]
    conf = {b: [[sum(1 for x in rows if x[b] == bv and x["lean"] == lv) for lv in order] for bv in order] for b in ("B1", "B2")}
    dis = {b: [x for x in rows if x[b] != x["lean"]] for b in ("B1", "B2")}
    unsafe = {b: [x for x in rows if x[b] == MET and x["lean"] != MET] for b in ("B1", "B2")}
    demo_key = ("quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw")
    demo = next(x for x in rows if (x["experiment"], x["configuration"]) == demo_key)
    groups = {}
    for b in ("B1", "B2"):
        for x in dis[b]:
            groups.setdefault((x[b], x["lean"], cause_label(x["causes_" + b])), {"B1": [], "B2": []})[b].append(
                (x["experiment"], x["configuration"]))
    nreq, nexpl, ex_req = explain_requirement_differences(pairs, ids, res)

    dump("fig_baseline_comparison", {
        "description": "B1/B2 Python baselines vs Lean verdicts on the 286-pair grid (fresh Lean batch run).",
        "baseline_definitions": {
            "B1": "single-capability requirements only, each in isolation; coupled constraints ignored; evidence status ignored "
                  "(estimates and unsourced values taken at face value); missing/unknown values, unknown install status, "
                  "unsupported comparisons and undecidable conditions never block; verdict NOT MET iff a documented value violates "
                  "a requirement, else MET (B1 never answers NEED INFO).",
            "B2": "same per-requirement comparison as B1 (provenance ignored, coupled constraints ignored) but missing/unknown "
                  "gives NEED INFO under CryoLean's three-valued verdict rule."},
        "cause_definitions": {"coupled": "Lean has a mandatory coupled constraint that does not pass",
                              "provenance": "the baseline decided a requirement from a value Lean does not trust",
                              "missing": "B1 let a requirement without usable data pass"},
        "order": order, "confusion": conf, "lean_counts": Counter(x["lean"] for x in rows),
        "B1_counts": Counter(x["B1"] for x in rows), "B2_counts": Counter(x["B2"] for x in rows),
        "agreement": {b: len(rows) - len(dis[b]) for b in ("B1", "B2")},
        "accepts_not_accepted_by_lean": {b: len(unsafe[b]) for b in ("B1", "B2")},
        "disagreement_groups": [{"baseline_verdict": k[0], "lean_verdict": k[1], "cause": k[2],
                                 "B1": len(v["B1"]), "B2": len(v["B2"]), "B1_pairs": v["B1"], "B2_pairs": v["B2"]}
                                for k, v in sorted(groups.items())],
        "requirement_level_differences_B2_vs_lean": nreq, "explained_by_untrusted_evidence_or_origin": nexpl,
        "requirement_level_difference_examples": ex_req, "demo_b": demo, "rows": rows})

    # ---------------------------------------------------------------- plot
    fig = plt.figure(figsize=(COL2, 3.25))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.45], wspace=0.6, left=0.075, right=0.985, top=0.80, bottom=0.15)
    vmax = max(max(max(r_) for r_ in conf[b]) for b in conf)
    cmap = SEQ_CMAP.copy()
    cmap.set_bad("white")
    tick = {MET: "MET", NI: "NEED\nINFO", NOT: "NOT\nMET"}
    for i, b in enumerate(("B1", "B2")):
        ax = fig.add_subplot(gs[0, i])
        m = np.array(conf[b])
        ax.imshow(np.ma.masked_where(m == 0, m), cmap=cmap, vmin=0, vmax=vmax * 1.1)
        ax.grid(False)
        for r_ in range(3):
            for c_ in range(3):
                v = m[r_, c_]
                ax.add_patch(Rectangle((c_ - .5, r_ - .5), 1, 1, fill=False, ec=INK if r_ == c_ else GRID, lw=0.9 if r_ == c_ else 0.5))
                ax.text(c_, r_, str(v), ha="center", va="center", fontsize=8, fontweight="bold" if r_ == c_ else "normal",
                        color="white" if v > vmax * 0.5 else (MUTED if v == 0 else INK))
        ax.set_xticks(range(3), [tick[v] for v in order], fontsize=6.5)
        ax.set_yticks(range(3), [tick[v] for v in order], fontsize=6.5)
        ax.set_xlim(-.5, 2.5)
        ax.set_ylim(2.5, -.5)
        ax.set_xlabel("CryoLean (Lean) verdict")
        ax.set_ylabel(f"{b} verdict", labelpad=1)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.tick_params(length=0)
        ax.set_anchor("N")
        agree = len(rows) - len(dis[b])
        ax.set_title(f"({'ab'[i]}) {b}: {'optimistic' if b == 'B1' else 'conservative'}", loc="left", fontsize=8.5, pad=22)
        ax.text(0.0, 1.03, f"agrees with Lean on {agree}/{len(rows)}\naccepts {len(unsafe[b])} pairs Lean does not",
                transform=ax.transAxes, ha="left", va="bottom", fontsize=6.3, color=INK2)

    # (c) disagreements grouped by (baseline verdict, Lean verdict), one row per cause, B1 and B2 side by side
    ax = fig.add_subplot(gs[0, 2])
    trans = sorted({(k[0], k[1]) for k in groups}, key=lambda t: -sum(len(v["B1"]) + len(v["B2"]) for k, v in groups.items() if k[:2] == t))
    short = {"missing data": "missing", "provenance": "provenance", "coupled constraint": "coupled"}
    y, ys, labels = 0.0, [], []
    ytx = ax.get_yaxis_transform()
    for t in trans:
        ax.text(-0.02, y, f"baseline {VERDICT_SHORT[t[0]]}  /  Lean {VERDICT_SHORT[t[1]]}", transform=ytx, ha="left", va="center",
                fontsize=6.4, fontweight="bold", color=INK)
        y += 0.95
        items = sorted([(k[2], v) for k, v in groups.items() if k[:2] == t], key=lambda kv: -(len(kv[1]["B1"]) + len(kv[1]["B2"])))
        for cause, v in items:
            lab = " + ".join(short[c] for c in cause.split(" + "))
            lab += " (Demo B)" if demo_key in v["B1"] + v["B2"] and cause == "coupled constraint" else ""
            for j, (b, col) in enumerate((("B1", NAVY), ("B2", LAVENDER))):
                n = len(v[b])
                yy = y + (j - 0.5) * 0.4
                if n:
                    ax.barh(yy, n, height=0.38, color=col, edgecolor="white", lw=0.3)
                ax.text(n * 1.12 if n else 0.78, yy, str(n), va="center", ha="left", fontsize=5.9, color=INK if n else MUTED)
            ys.append(y)
            labels.append(lab)
            y += 1
        y += 0.35
    ax.set_xscale("log")
    ax.set_xlim(0.7, 900)
    ax.set_ylim(y - 0.2, -0.6)
    ax.set_yticks(ys, labels, fontsize=6.2)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("disagreeing pairs (log scale)")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=NAVY, label="B1 optimistic"), Patch(color=LAVENDER, label="B2 conservative")],
              loc="lower right", fontsize=6.2, handlelength=1.2)
    ax.set_title("(c) disagreements with Lean, by cause", loc="left", fontsize=8.5, pad=22)
    ax.text(0.0, 1.03, "cause read from the per-check outcomes", transform=ax.transAxes, ha="left", va="bottom", fontsize=6.3,
            color=INK2)

    n_un1, n_un2 = len(unsafe["B1"]), len(unsafe["B2"])
    save(fig, "fig_baseline_comparison", meta=dict(
        title="CryoLean versus independent-property baselines",
        question="How often does a datasheet-style check of each requirement in isolation (ignoring coupled physics and "
                 "provenance) disagree with the verified CryoLean verdict on real configurations, and why?",
        model="B1: per-requirement comparison of the documented value, coupled constraints and evidence status ignored, "
              "missing/unknown never blocks (MET unless a documented violation). B2: same comparison, missing/unknown -> NEED INFO "
              "with CryoLean's three-valued rule. CryoLean: compiled Lean 4 checker verdict (requirements + coupled constraints + "
              "trusted-provenance rule). Causes are read from per-check outcomes: a mandatory Lean coupled check that does not pass; "
              "a requirement decided by the baseline from a value Lean does not trust (provenance); a requirement without usable "
              "data that B1 lets pass (missing data).",
        data=f"11 experiment profiles x 26 configurations = {len(rows)} pairs built with verifier.build_documents from data/experiments "
             "and data/cryostats; one fresh lean_runner.check_batch run (verdicts identical, pair by pair, to paper/data/e1_grid.json); "
             f"baselines implemented in paper/scripts/fig_baselines.py; all {nreq} requirement-level B2/Lean differences involve "
             f"untrusted evidence ({nexpl}/{nreq}); per-pair results in paper/data/fig_baseline_comparison.json.",
        claim="COMPUTED",
        caption=(f"Verdicts of two unverified baselines against CryoLean on all {len(rows)} experiment-configuration pairs. "
                 f"(a) The optimistic baseline B1 checks each requirement in isolation and lets missing data pass; it agrees with "
                 f"Lean on {len(rows) - len(dis['B1'])} pairs and accepts {n_un1} pairs that Lean does not accept. (b) The conservative "
                 f"baseline B2 differs from CryoLean only by ignoring coupled constraints and provenance; it agrees on "
                 f"{len(rows) - len(dis['B2'])} pairs and still accepts {n_un2}. (c) Disagreements by cause, read from the per-check "
                 f"outcomes; the single coupled-constraint acceptance is Demo B (Bluefors LD400 HDW, 50-qubit wiring heat budget). "
                 f"CryoLean verdicts are computed by the Lean checker; the baselines are Python and not verified."),
        section="main"))
    return rows, conf, dis, unsafe, demo, groups, (nreq, nexpl)


# ============================================================== figure 2
def _rel_margin_req(check):
    """Relative slack of a single requirement from the Lean result (positive = passes)."""
    con = check["constraint"]
    cap = next((pk["capability"] for pk in check["per_key"] if pk["capability"]), None)
    v = cap["value"]
    if con["kind"] == "at_most":
        q = Fraction(con["q"]["num"], con["q"]["den"])
        a = Fraction(v["q"]["num"], v["q"]["den"])
        return float((q - a) / q), a, q
    if con["kind"] == "count_at_least":
        return (v["n"] - con["n"]) / con["n"], v["n"], con["n"]
    raise ValueError(con["kind"])


def _short_cfg(cid):
    """Short display name of a Bluefors configuration id (e.g. bluefors_ld400_hdw -> LD400 HDW)."""
    m = re.search(r"ld(\d+)", cid)
    return (f"LD{m.group(1)}" + (" HDW" if "hdw" in cid else "")) if m else cid


MODEL_NAME = {"mxc_wiring_heat_budget": "MXC wiring heat budget", "joule_heating_vs_cooling_power": "Joule heating vs\ncooling power",
              "magnet_ramp_time": "Magnet ramp time"}


def fig_independent_vs_coupled(cat, ids, pairs, res):
    i = ids.index(("quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw"))
    cd, ed = pairs[i]
    r = res[i]
    rows = []
    for c in r["checks"]:
        m, avail, req = _rel_margin_req(c)
        rows.append({"label": c["keys"][0], "outcome": c["outcome"], "margin": m, "documented": str(avail), "required": str(req),
                     "explanation": c["explanation"]})
    cc = next(c for c in r["coupled_checks"] if c["model"] == "mxc_wiring_heat_budget")
    lhs = Fraction(cc["lhs"]["value"]["num"], cc["lhs"]["value"]["den"])
    rhs = Fraction(cc["rhs"]["value"]["num"], cc["rhs"]["value"]["den"])
    rows.append({"label": "heat budget", "outcome": cc["outcome"], "margin": float((rhs - lhs) / rhs),
                 "cooling_power_W": str(rhs), "heat_load_W": str(lhs), "explanation": cc["explanation"]})
    # Z3 proposes, Lean re-checks
    ex = serialize.working_experiment(cat, "quantum_mxc_wiring_heat_budget", None, None, True)
    full = verifier.check(cat, ex, "bluefors_ld400_hdw", suggestions=True, max_alternatives=3)
    rep = next(p for p in full["suggestions"]["parameter_changes"] if p.get("status") == "found")
    ed2 = copy.deepcopy(ed)
    for p in ed2["params"]:
        if p["name"] == rep["parameter"]:
            p["value"] = rep["suggested_quantity"]
            p["origin"] = "user_entered"
    r2 = lean_runner.check(cd, ed2)
    cc2 = next(c for c in r2["coupled_checks"] if c["model"] == "mxc_wiring_heat_budget")
    lhs2 = Fraction(cc2["lhs"]["value"]["num"], cc2["lhs"]["value"]["den"])
    after_margin = float((rhs - lhs2) / rhs)

    # grid-wide: pairs whose single-capability requirements all pass (or are not applicable), and coupled outcomes
    allpass = []
    for (eid, cid), rr in zip(ids, res):
        req = [c["outcome"] for c in rr["checks"] if c["mandatory"] and c["applicable"]]
        if req and all(o in OKISH for o in req):
            cp = [(c["model"], c["outcome"], c["mandatory"]) for c in rr["coupled_checks"] if c["applicable"]]
            allpass.append({"experiment": eid, "configuration": cid, "verdict": rr["verdict"], "coupled": cp})
    grp = Counter()
    for a in allpass:
        mc = [o for _, o, mand in a["coupled"] if mand]
        grp["no mandatory coupled constraint" if not mc else "coupled passes" if all(o == "pass" for o in mc)
            else "coupled fails" if "fail" in mc else "coupled not evaluable"] += 1
    model_out = {}
    fails = []
    for (eid, cid), rr in zip(ids, res):
        for c in rr["coupled_checks"]:
            if c["applicable"]:
                d = model_out.setdefault(c["model"], {"mandatory": c["mandatory"], "outcomes": Counter(), "experiment": eid})
                d["outcomes"][c["outcome"]] += 1
                if c["outcome"] == "fail":
                    fails.append({"configuration": cid, "model": c["model"], "lhs": c["lhs"]["display"], "rhs": c["rhs"]["display"],
                                  "rhs_W": float(Fraction(c["rhs"]["value"]["num"], c["rhs"]["value"]["den"])),
                                  "verdict": rr["verdict"]})
    dump("fig_independent_vs_coupled", {
        "demo_b": {"configuration": "bluefors_ld400_hdw", "experiment": "quantum_mxc_wiring_heat_budget", "verdict": r["verdict"],
                   "checks": rows, "coupled_lhs_W": str(lhs), "coupled_rhs_W": str(rhs)},
        "z3_repair": {k: rep.get(k) for k in ("parameter", "current", "suggested", "direction", "lean_verdict", "verified", "coupled_after")},
        "after_repair": {"verdict": r2["verdict"], "coupled_outcome": cc2["outcome"], "coupled_lhs_W": str(lhs2), "margin": after_margin},
        "grid_all_single_pass": allpass, "grid_all_single_pass_breakdown": dict(grp),
        "grid_coupled_outcomes": {m: {"mandatory": d["mandatory"], "experiment": d["experiment"], "outcomes": dict(d["outcomes"])}
                                  for m, d in model_out.items()},
        "grid_coupled_failures": fails,
        "note_joule": "joule_heating_vs_cooling_power is an advisory (non-mandatory) check of mat_electrical_resistance_low_temperature; "
                      "measurement_current and sample_resistance are left for the user, so its left-hand side is missing in every pair."})

    # ---------------------------------------------------------------- plot
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.75), gridspec_kw=dict(width_ratios=[1.3, 1], wspace=0.62))
    ax = axs[0]
    labels = ["Base temperature ≤ 20 mK\n(documented 10 mK)", "RF/coax lines ≥ 124\n(documented 168)",
              f"Coupled: wiring heat load\n≤ cooling power at 20 mK\n({float(lhs) * 1e6:.3f} µW vs {float(rhs) * 1e6:g} µW)",
              f"Coupled, after Z3 repair\nn_flux_lines {rep['current']} → {rep['suggested']}\n"
              f"({float(lhs2) * 1e6:.3f} µW vs {float(rhs) * 1e6:g} µW)"]
    ms = [rows[0]["margin"] * 100, rows[1]["margin"] * 100, rows[2]["margin"] * 100, after_margin * 100]
    outs = [rows[0]["outcome"], rows[1]["outcome"], rows[2]["outcome"], cc2["outcome"]]
    y = np.array([0, 1, 2.25, 3.45])
    for yy, m, o in zip(y, ms, outs):
        v = MET if o == "pass" else NOT
        ax.barh(yy, m, color=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white", lw=0.3, height=0.6)
        if abs(m) < 1:
            ax.plot([m], [yy], marker="D", ms=3.5, color=VERDICT_COLOR[v], mec=INK, mew=0.4)
        txt = f"{'pass' if o == 'pass' else 'FAIL'}  {m:+.1f} %" if abs(m) >= 1 else f"{'pass' if o == 'pass' else 'FAIL'}  {m:+.3f} %"
        ax.text(max(m, 0) + 2.5, yy, txt, va="center", ha="left", fontsize=6.3, color=INK)
    ax.text(84, 2.25, f"Lean: {VERDICT_SHORT[r['verdict']]}", ha="right", va="center", fontsize=6.3, color=INK, fontweight="bold")
    ax.text(84, 3.45, f"Lean: {VERDICT_SHORT[r2['verdict']]}", ha="right", va="center", fontsize=6.3, color=INK, fontweight="bold")
    ax.axvline(0, color=INK2, lw=0.7)
    for yy in (1.62, 2.85):
        ax.axhline(yy, color=AXIS_DASH, lw=0.7, ls="--")
    ax.set_yticks(y, labels, fontsize=6.0)
    ax.set_ylim(3.95, -0.5)
    ax.set_xlim(-30, 85)
    ax.set_xlabel("relative margin (slack / limit), %")
    ax.grid(axis="y", visible=False)
    ax.set_title("(a) Demo B: Bluefors LD400 HDW", loc="left", fontsize=8.5)

    # (b) coupled-check outcomes per model across the grid
    ax = axs[1]
    seg = [("pass", ("pass",), MET), ("fail", ("fail",), NOT), ("not evaluable", ("unknown", "unsupported"), NI)]
    models = sorted(model_out, key=lambda m: (not model_out[m]["mandatory"], m))
    yb = [0.9 + (0 if j == 0 else 0.65 + j) for j in range(len(models))]
    for yy, mdl in zip(yb, models):
        left = 0
        oc = model_out[mdl]["outcomes"]
        for name, keys, v in seg:
            n = sum(oc.get(k, 0) for k in keys)
            if n:
                ax.barh(yy, n, left=left, color=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white", lw=0.3, height=0.6)
                ax.text(left + n / 2, yy, str(n), ha="center", va="center", fontsize=6.2, color=INK,
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.85))
                left += n
    ax.set_yticks(yb, [MODEL_NAME.get(m, m) + ("\n(mandatory)" if model_out[m]["mandatory"] else "\n(advisory)") for m in models],
                  fontsize=6.3)
    ax.set_ylim(yb[-1] + 0.5, -0.95)
    ax.set_xlim(0, 27)
    ax.set_xticks([0, 5, 10, 15, 20, 25])
    ax.set_xlabel("configurations (26 per experiment)")
    ax.grid(axis="y", visible=False)
    ax.set_title("(b) coupled checks in the 286-pair grid", loc="left", fontsize=8.5)
    ax.legend(handles=[Patch(facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white", label=n) for n, _, v in seg],
              loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=6.2, handlelength=1.4, columnspacing=1.0)
    fl = sorted(fails, key=lambda f: f["rhs_W"])
    if fl:
        load_disp = fl[0]["lhs"]
        parts = [f"{f['rhs']} ({_short_cfg(f['configuration'])})" for f in fl]
        ax.text(0.3, yb[0] + 0.36, f"fail: load {load_disp} > cooling power\n"
                + ",\n".join(", ".join(parts[i:i + 2]) for i in range(0, len(parts), 2)),
                ha="left", va="top", fontsize=5.6, color=INK2, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    n_all = len(allpass)
    ax.text(0.98, 0.985, f"{n_all} grid pairs pass every single\nrequirement; {grp.get('coupled fails', 0)} of them fails a\n"
                         f"coupled constraint (Demo B)", transform=ax.transAxes, ha="right", va="top", fontsize=5.9, color=INK,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GRID, lw=0.5))

    nfail = grp.get("coupled fails", 0)
    jo = model_out.get("joule_heating_vs_cooling_power", {"outcomes": Counter(), "mandatory": None})
    save(fig, "fig_independent_vs_coupled", meta=dict(
        title="Independent requirements pass, coupled physics fails",
        question="Can every requirement be met individually while the combined physics is violated, how often does that happen "
                 "on the real grid, and can the solver repair it under the verified checker?",
        model="Margins: (limit - documented)/limit for at_most, (documented - required)/required for counts, (P_cool - Q_load)/P_cool "
              "for the coupled relation margin*(n_drive q_drive + n_flux (q_flux + p_flux_dc) + n_out q_out) <= P_cool(20 mK) "
              "(model mxc_wiring_heat_budget, status validated). Repair: Z3 parameter search (verifier.check with suggestions), "
              "re-checked by Lean.",
        data="Lean batch run over the 286-pair grid (verifier.build_documents); Demo B lhs/rhs are the exact rationals returned by "
             "Lean; Z3 repair from verifier.check(..., suggestions=True) and an explicit Lean re-check of the repaired document; "
             "sourced parameters from data/experiments/quantum_mxc_wiring_heat_budget.json and cooling power from "
             "data/cryostats (Bluefors evidence ev_bf_0006). Saved in paper/data/fig_independent_vs_coupled.json.",
        claim="COMPUTED+SOURCED",
        caption=(f"(a) Demo B: the base-temperature and line-count requirements pass with {ms[0]:.1f} % and {ms[1]:.1f} % slack, "
                 f"but the coupled mixing-chamber heat budget fails ({float(lhs) * 1e6:.3f} µW > {float(rhs) * 1e6:g} µW, "
                 f"{ms[2]:.1f} %); Z3 proposes reducing n_flux_lines from {rep['current']} to {rep['suggested']} and Lean accepts "
                 f"the repaired profile with {after_margin * 100:.3f} % slack. (b) Coupled-check outcomes over the grid: the heat "
                 f"budget can be evaluated for the three configurations with a sourced 20 mK cooling power and fails for all three; "
                 f"of the {n_all} pairs that pass every single-capability requirement, {nfail} fails a coupled constraint. The "
                 f"Joule-heating check is advisory and not evaluable in "
                 f"{sum(jo['outcomes'].get(k, 0) for k in ('unknown', 'unsupported'))}/{sum(jo['outcomes'].values())} pairs "
                 f"(current and resistance are user inputs), so the grid contains no Joule-heating example. Verdicts and margins "
                 f"are computed by the Lean checker from sourced specifications."),
        section="main"))
    return rows, rep, after_margin, allpass, grp, model_out, r2, fails


# ============================================================== figure 3
K = list(range(0, 101, 10))
REPS = 30


def compute_incomplete_info(ids, pairs, res):
    rng = random.Random(SEED)
    jobs, docs_remove, docs_unknown = [], [], []
    for pi, (cd, ed) in enumerate(pairs):
        doc_idx = [j for j, c in enumerate(cd["capabilities"]) if c["value"]["kind"] != "unknown"]
        for k in K:
            m = round(k / 100 * len(doc_idx))
            for rep in range(REPS):
                sel = set(rng.sample(doc_idx, m))
                cr = copy.copy(cd)
                cr["capabilities"] = [c for j, c in enumerate(cd["capabilities"]) if j not in sel]
                cu = copy.copy(cd)
                cu["capabilities"] = [({**c, "install": "unknown"} if j in sel else c) for j, c in enumerate(cd["capabilities"])]
                docs_remove.append((cr, ed))
                docs_unknown.append((cu, ed))
                jobs.append((pi, k, rep))
    t0 = time.perf_counter()
    vr = [r["verdict"] for r in batched(docs_remove)]
    vu = [r["verdict"] for r in batched(docs_unknown)]
    secs = time.perf_counter() - t0
    base = [r["verdict"] for r in res]
    trans = {"remove": Counter(), "install_unknown": Counter()}
    for (pi, k, rep), a, b in zip(jobs, vr, vu):
        trans["remove"][(base[pi], a)] += 1
        trans["install_unknown"][(base[pi], b)] += 1
    became_met = {mode: sum(v for (b0, b1), v in t.items() if b0 != MET and b1 == MET) for mode, t in trans.items()}
    nonmono = {mode: sum(v for (b0, b1), v in t.items() if b1 != b0 and b1 != NI) for mode, t in trans.items()}
    met_set = {i for i, v in enumerate(base) if v == MET}

    def dist(subset, verd):
        arr = np.zeros((len(K), REPS, 3))
        cnt = np.zeros((len(K), REPS))
        for (pi, k, rep), v in zip(jobs, verd):
            if pi in subset:
                arr[K.index(k), rep, VERDICT_ORDER.index(v)] += 1
                cnt[K.index(k), rep] += 1
        return arr / cnt[..., None]
    summary = {}
    for name, a in (("met", dist(met_set, vr)), ("all", dist(set(range(len(pairs))), vr))):
        cum = np.cumsum(a, axis=2)
        summary[name] = {"k": K, "order": VERDICT_ORDER, "mean": a.mean(axis=1).tolist(),
                         "lo": np.percentile(a, 2.5, axis=1).tolist(), "hi": np.percentile(a, 97.5, axis=1).tolist(),
                         "cum_mean": cum.mean(axis=1).tolist(), "cum_lo": np.percentile(cum, 2.5, axis=1).tolist(),
                         "cum_hi": np.percentile(cum, 97.5, axis=1).tolist()}
    data = {"description": "Random deletion of k% of each configuration's documented capabilities (value kind != unknown); "
                           "the same random selection evaluated in two modes: record removed, or install set to 'unknown'. Lean batch.",
            "seed": SEED, "k_percent": K, "repeats": REPS, "pairs": len(pairs), "met_pairs": len(met_set),
            "baseline_counts": dict(Counter(base)),
            "lean_checks": len(vr) + len(vu), "lean_seconds": secs, "checks_per_mode": len(vr),
            "transitions": {mode: [{"from": k[0], "to": k[1], "n": v} for k, v in sorted(t.items())] for mode, t in trans.items()},
            "non_met_became_met": became_met, "non_monotone_transitions": nonmono,
            "modes_identical_verdicts": sum(a == b for a, b in zip(vr, vu)), "summary_remove_mode": summary}
    dump("fig_incomplete_info", data)
    return data


def fig_incomplete_info(ids, pairs, res, recompute: bool):
    path = DATA_DIR / "fig_incomplete_info.json"
    data = None
    if path.exists() and not recompute:
        data = load("fig_incomplete_info")
        base = dict(Counter(r["verdict"] for r in res))
        if (data.get("seed"), data.get("k_percent"), data.get("repeats"), data.get("pairs"), data.get("baseline_counts")) != \
                (SEED, K, REPS, len(pairs), base) or "checks_per_mode" not in data:
            data = None
        else:
            print("  fig_incomplete_info: reusing paper/data/fig_incomplete_info.json (pass --recompute to re-run Lean)")
    if data is None:
        data = compute_incomplete_info(ids, pairs, res)
    summ = data["summary_remove_mode"]
    tot = data["checks_per_mode"]
    bm, nm = data["non_met_became_met"], data["non_monotone_transitions"]
    n_nonmet = sum(t["n"] for t in data["transitions"]["remove"] if t["from"] != MET)      # checks of non-accepted pairs, per mode
    n_k0 = data["pairs"] * data["repeats"]                                                  # k = 0 draws (nothing deleted)

    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.6), sharey=True, gridspec_kw=dict(wspace=0.1))
    for ax, name, title in ((axs[0], "met", f"(a) the {data['met_pairs']} pairs Lean accepts"),
                            (axs[1], "all", f"(b) all {data['pairs']} pairs")):
        s = summ[name]
        cm, lo, hi = np.array(s["cum_mean"]), np.array(s["cum_lo"]), np.array(s["cum_hi"])
        prev = np.zeros(len(K))
        for j, v in enumerate(VERDICT_ORDER):
            ax.fill_between(K, prev, cm[:, j], facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white", lw=0,
                            alpha=0.9)
            prev = cm[:, j]
        for j in range(2):
            ax.fill_between(K, lo[:, j], hi[:, j], color="white", alpha=0.5, lw=0)
            ax.plot(K, lo[:, j], color=INK, lw=0.4, ls=":")
            ax.plot(K, hi[:, j], color=INK, lw=0.4, ls=":")
            ax.plot(K, cm[:, j], color=INK, lw=0.8)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 1)
        ax.set_xlabel("documented capabilities deleted, k (%)")
        ax.set_title(title, loc="left", fontsize=8.5)
        ax.grid(False)
        ax.set_xticks(K[::2])
    axs[0].set_ylabel("fraction of pairs (mean, 95 % band)")
    box = dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85)
    cmA = np.array(summ["met"]["cum_mean"])
    axs[0].text(3, cmA[K.index(10), 0] * 0.35, VERDICT_LABEL[MET], ha="left", va="center", fontsize=6.3, color=INK, bbox=box)
    axs[0].text(65, 0.55, VERDICT_LABEL[NI], ha="center", va="center", fontsize=6.3, color=INK, bbox=box)
    cmB = np.array(summ["all"]["cum_mean"])
    kk = K.index(30)
    axs[1].text(30, (cmB[kk, 1] + 1) / 2 + 0.03, VERDICT_LABEL[NOT], ha="center", va="center", fontsize=6.3, color=INK, bbox=box)
    axs[1].text(25, 0.30, VERDICT_LABEL[NI], ha="center", va="center", fontsize=6.3, color=INK, bbox=box)
    axs[1].annotate(VERDICT_LABEL[MET], xy=(3, cmB[0, 0] * 0.4), xytext=(6, 0.16), fontsize=6.3, color=INK, va="center",
                    bbox=box, arrowprops=dict(arrowstyle="-", color=INK, lw=0.5))
    axs[1].text(0.97, 0.42, f"non-accepted → MET: {bm['remove']} of {n_nonmet} (removed)\n"
                            f"{bm['install_unknown']} of {n_nonmet} (install = unknown)\n"
                            f"changes not to NEED INFO: {nm['remove'] + nm['install_unknown']} of {2 * tot}",
                transform=axs[1].transAxes, ha="right", va="bottom", fontsize=6.0, color=INK,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GRID, lw=0.5))
    save(fig, "fig_incomplete_info", meta=dict(
        title="Robustness to incomplete information",
        question="When documented specifications are deleted at random, does CryoLean degrade only towards NEED MORE INFORMATION "
                 "and never towards an unwarranted acceptance?",
        model="For each pair and k in {0,10,...,100} %, 30 random draws remove round(k/100 * n_doc) of the configuration's "
              "documented capabilities (value kind != unknown); the same draw is evaluated with the records removed and with "
              "install set to 'unknown'. Coloured areas: mean verdict fractions over draws (removal mode); white bands with dotted "
              "edges: 2.5-97.5 percentile of the cumulative boundaries over the 30 draws.",
        data=f"{data['lean_checks']} Lean checks (lean_runner.check_batch, {data['lean_seconds']:.0f} s) on documents built from "
             f"the 286-pair grid; seed {SEED}; results in paper/data/fig_incomplete_info.json.",
        claim="COMPUTED",
        caption=(f"Verdict distribution as a growing fraction k of each configuration's documented capabilities is deleted "
                 f"(30 random draws per k; bands are 95 % percentile intervals over draws). (a) The {data['met_pairs']} accepted pairs "
                 f"move from REQUIREMENTS MET to NEED MORE INFORMATION only; (b) over all {data['pairs']} pairs, rejections also turn "
                 f"into requests for information. Each deletion mode ran {tot} checks ({n_k0} of them the k = 0 controls); among the "
                 f"{n_nonmet} checks of non-accepted pairs per mode, none became REQUIREMENTS MET ({bm['remove']} with records removed, "
                 f"{bm['install_unknown']} with install unknown), no verdict changed to anything other than NEED MORE INFORMATION "
                 f"({nm['remove'] + nm['install_unknown']} of {2 * tot}), and removing a record or marking it install-unknown gave the "
                 f"same verdict in {data['modes_identical_verdicts']}/{tot} draws. All verdicts are computed by the Lean checker."),
        section="main"))
    return data


# ============================================================== figure 4
FAULT_LABEL = {"control": "control (no defect)", "single:below_limit": "value below requirement",
               "single:optional_trusted": "option not fitted (sourced)", "single:estimate": "inferred estimate",
               "single:no_provenance": "no provenance", "single:unknown_value": "value unknown",
               "single:install_unknown": "install status unknown", "single:missing": "capability missing",
               "single:optional_untrusted": "option not fitted (unsourced)", "single:wrong_dimension": "wrong SI dimension",
               "multiple": "2-4 defects at once"}
FAULT_EXPECT = {"control": MET, "single:below_limit": NOT, "single:optional_trusted": NOT, "single:estimate": NI,
                "single:no_provenance": NI, "single:unknown_value": NI, "single:install_unknown": NI, "single:missing": NI,
                "single:optional_untrusted": NI, "single:wrong_dimension": NI, "multiple": "worst defect"}


def fig_fault_injection():
    d = load("e4_faults")
    order = ["control", "single:below_limit", "single:optional_trusted", "single:estimate", "single:no_provenance",
             "single:unknown_value", "single:install_unknown", "single:missing", "single:optional_untrusted",
             "single:wrong_dimension", "multiple"]
    assert set(order) == set(d["by_defect"]), d["by_defect"].keys()
    fig, ax = plt.subplots(figsize=(COL2, 2.75))
    y = np.arange(len(order))
    for yy, k in zip(y, order):
        left = 0
        for v in VERDICT_ORDER:
            n = d["by_defect"][k].get(v, 0)
            if n:
                ax.barh(yy, n, left=left, color=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white", lw=0.3, height=0.66)
                ax.text(left + n / 2, yy, str(n), ha="center", va="center", fontsize=6.2, color=INK,
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.85))
                left += n
        exp = FAULT_EXPECT[k]
        ax.text(left + 12, yy, "expected: " + (VERDICT_SHORT[exp] if exp in VERDICT_SHORT else exp), va="center", fontsize=6.2,
                color=INK2)
    ax.set_yticks(y, [FAULT_LABEL[k] for k in order], fontsize=6.6)
    ax.set_ylim(len(order) - 0.4, -0.6)
    ax.set_xlim(0, 1100)
    ax.set_xlabel("synthetic cases (Lean verdict)")
    ax.grid(axis="y", visible=False)
    verdict_legend(ax, loc="upper right", fontsize=6.3)
    n_def = d["cases"] - sum(d["by_defect"]["control"].values())
    ax.set_title(f"Fault injection, {d['cases']} cases: {d['accepted_with_a_defect']} of {n_def} defective cases accepted; "
                 f"Lean agrees with the independent rule in {d['agree_with_independent_rule']}/{d['cases']}", loc="left", fontsize=8)
    save(fig, "fig_fault_injection", meta=dict(
        title="Fault injection by defect type",
        question="Does any single or combined data defect ever lead the checker to accept, and does each defect produce the "
                 "verdict an independent rule predicts?",
        model="Synthetic configuration with five capabilities against five mandatory requirements; one defect (1800 cases), "
              "2-4 defects (900) or none (50 controls) injected at random (seed 7). Independent rule: any trusted violation -> "
              "DOES NOT MEET; otherwise any defect -> NEED MORE INFORMATION; for multiple defects the worst outcome wins.",
        data=f"paper/data/e4_faults.json (paper/scripts/paper_eval.py e4_faults: one lean_runner.check_batch run of {d['cases']} "
             f"cases in {d['seconds']:.2f} s).",
        claim="COMPUTED",
        caption=(f"Lean verdicts for {d['cases']} synthetic configurations grouped by injected defect. Only documented, trusted "
                 f"violations (value below the requirement, option documented as not fitted) are rejected; every provenance, "
                 f"completeness or dimension defect yields NEED MORE INFORMATION. {d['accepted_with_a_defect']} of {n_def} defective "
                 f"cases were accepted, all {sum(d['by_defect']['control'].values())} controls were accepted, and the Lean verdict "
                 f"matched the independent rule in {d['agree_with_independent_rule']} of {d['cases']} cases."),
        section="supplement"))
    return d


AXIS_DASH = "#c3c2b7"


# ============================================================== main
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply()
    recompute = "--recompute" in sys.argv
    cat = Catalog()
    ids, pairs = build_grid(cat)
    res = batched(pairs)
    e1 = load("e1_grid")
    old = {(r["experiment"], r["configuration"]): r["verdict"] for r in e1["rows"]}
    same = sum(old.get(i) == r["verdict"] for i, r in zip(ids, res))
    print(f"grid: {len(pairs)} pairs, Lean verdicts identical to e1_grid for {same}")
    rows, conf, dis, unsafe, demo, groups, expl = fig_baseline_comparison(cat, ids, pairs, res)
    print("B1 confusion", conf["B1"], "B2", conf["B2"], "accepts-not-Lean", {k: len(v) for k, v in unsafe.items()},
          "req-level diffs explained", expl)
    for k, v in sorted(groups.items()):
        print("  ", k, "B1", len(v["B1"]), "B2", len(v["B2"]), v["B2"] if len(v["B2"]) < 10 else "")
    out2 = fig_independent_vs_coupled(cat, ids, pairs, res)
    print("all-single-pass breakdown", dict(out2[4]), "repair", out2[1]["current"], "->", out2[1]["suggested"], out2[6]["verdict"],
          f"after margin {out2[2]:.5f}", "fails", out2[7])
    d3 = fig_incomplete_info(ids, pairs, res, recompute)
    print("incomplete info: became_met", d3["non_met_became_met"], "nonmono", d3["non_monotone_transitions"],
          "same modes", d3["modes_identical_verdicts"], "checks", d3["lean_checks"])
    fig_fault_injection()


if __name__ == "__main__":
    main()
