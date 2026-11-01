#!/usr/bin/env python
"""Cryogenic-physics 2D figures for the CryoLean paper.

    python paper/scripts/fig_physics2d.py              (uses cached paper/data/fig_*.json when present)
    python paper/scripts/fig_physics2d.py --recompute  (re-runs every Lean batch, about 10 minutes)

Every feasible / infeasible classification below comes from the compiled Lean 4 checker
(cryolean.lean_runner.check_batch). Python only builds the input documents (exact rationals), draws, and
overlays analytic boundaries that are labelled as such.

fig_cooling_curves      sourced cooling-power points + the step rule the checker uses (Lean rhs vs T_op)
fig_heat_budget         Demo B budget, Krinner et al. per-line loads, before / after the Z3 repair
fig_boundary_2d         exact Lean feasibility region in the (n_flux_lines, n_drive_lines) plane
fig_sensitivity         per-parameter relative change that flips the Lean verdict (Lean k-section)
fig_uncertainty         Monte Carlo robustness to per-line load uncertainty, every sample decided by Lean
fig_cryostat_schematic  ILLUSTRATIVE dilution-refrigerator stack with CryoLean data for bluefors_ld400_hdw
fig_contraction         sourced integrated thermal contraction of the 14 materials in data/physics/materials.json
"""
from __future__ import annotations

import copy
import json
import math
import random
import sys
import time
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import *  # noqa: E402,F401,F403
from style import ROOT, DATA_DIR  # noqa: E402

import numpy as np  # noqa: E402
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from cryolean import lean_runner, serialize, units, verifier  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

RECOMPUTE = "--recompute" in sys.argv
CAT = Catalog()
EXP_ID = "quantum_mxc_wiring_heat_budget"
CFG_ID = "bluefors_ld400_hdw"
MODEL = "mxc_wiring_heat_budget"
SCRIPT = "paper/scripts/fig_physics2d.py"
MET, NOT, NEED = "REQUIREMENTS_MET", "DOES_NOT_MEET_REQUIREMENTS", "NEED_MORE_INFORMATION"
NW = F(1, 10**9)
LOAD_PARAMS = ["q_drive_line", "q_flux_line", "p_flux_dc", "q_output_line"]


# ------------------------------------------------------------------------------------------------ helpers
def cached(name, fn):
    path = DATA_DIR / f"{name}.json"
    if path.exists() and not RECOMPUTE:
        print(f"  {name}: using cached {path.relative_to(ROOT).as_posix()}")
        return load(name)
    t0 = time.perf_counter()
    obj = fn()
    obj["_generated_by"] = SCRIPT
    obj["_seconds"] = round(time.perf_counter() - t0, 2)
    dump(name, obj)
    print(f"  {name}: computed in {obj['_seconds']} s")
    return obj


def batch(pairs, chunk=3000):
    """Lean check_batch over any iterable of (cfg_doc, exp_doc), built lazily chunk by chunk (keeps memory flat)."""
    out, buf = [], []
    for pr in pairs:
        buf.append(pr)
        if len(buf) == chunk:
            out += lean_runner.check_batch(buf)
            buf = []
    if buf:
        out += lean_runner.check_batch(buf)
    return out


def fq(q):
    return F(q["num"], q["den"])


def coupled(r):
    return next(c for c in r["coupled_checks"] if c["model"] == MODEL)


def side(c, s):
    v = (c.get(s) or {}).get("value")
    return fq(v) if v else None


def base_docs():
    ex = serialize.working_experiment(CAT, EXP_ID, None, None, True)
    cd, ed, info, _ = verifier.build_documents(CAT, ex, CFG_ID)
    return ex, cd, ed, info


def params_of(ed):
    return {p["name"]: fq(p["value"]) for p in ed["params"] if p.get("value")}


def with_params(ed, **vals):
    e2 = copy.deepcopy(ed)
    for p in e2["params"]:
        if p["name"] in vals:
            v = F(vals[p["name"]])
            p["value"] = {"num": v.numerator, "den": v.denominator, "dim": p["value"]["dim"]}
            p["origin"] = "user_entered"
    return e2


def with_cooling(cd, key, watts):
    c2 = copy.deepcopy(cd)
    cap = next(c for c in c2["capabilities"] if c["key"] == key)
    w = F(watts)
    cap["value"] = {"kind": cap["value"]["kind"], "q": {"num": w.numerator, "den": w.denominator, "dim": cap["value"]["q"]["dim"]}}
    return c2


def lhs_exact(p):
    """Analytic left-hand side of the model equation (used ONLY for overlays / cross-checks, never to classify)."""
    return p["design_margin"] * (p["n_drive_lines"] * p["q_drive_line"] + p["n_flux_lines"] * (p["q_flux_line"] + p["p_flux_dc"])
                                 + p["n_output_lines"] * p["q_output_line"])


def fstr(x: F) -> str:
    return f"{x.numerator}/{x.denominator}" if x.denominator != 1 else str(x.numerator)


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


DARKER = {MET: "#087a08", NOT: "#9e2a2a", NEED: "#c48a0f", "BUILD_ERROR": "#5f5e5a"}


def verdict_box(ax, x, y, verdict, text, ha="left", va="center", fs=6.5, transform=None):
    """Verdict tag: status colour + hatch + text label (never colour alone)."""
    kw = dict(transform=transform) if transform is not None else {}
    t = ax.text(x, y, text, ha=ha, va=va, fontsize=fs, color="white" if verdict != NEED else INK, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", facecolor=VERDICT_COLOR[verdict], edgecolor=DARKER[verdict],
                          hatch=VERDICT_HATCH[verdict], linewidth=0.6), zorder=6, **kw)
    return t


# ================================================================================================ 1 cooling curves
SHORT = {"bluefors_ld250_manual_v2": "Bluefors LD250", "bluefors_ld400_hdw": "Bluefors LD400 (HDW)",
         "bluefors_ld450_current": "Bluefors LD450", "lakeshore_ccs_100": "CCS-100", "lakeshore_ccs_300s": "CCS-300S",
         "lakeshore_ccs_400": "CCS-400", "lakeshore_ccs_400h": "CCS-400H", "lakeshore_crx_4k": "CRX-4K",
         "lakeshore_crx_vf": "CRX-VF", "oxford_optistatdry_blv": "OptistatDry BLV",
         "oxford_optistatdry_tlex": "OptistatDry TLEX"}


def cooling_points():
    rows, unknown = [], []
    for cid, cfg in sorted(CAT.configurations.items()):
        for c in cfg["capabilities"]:
            if not c["key"].startswith("cooling_power.at_"):
                continue
            at = CAT.vocabulary.get(c["key"], {}).get("at_temperature")
            if c["value"].get("kind") == "unknown":
                unknown.append({"configuration": cid, "key": c["key"]})
                continue
            q = c["value"]["q"]
            rows.append({"configuration": cid, "key": c["key"], "T_K": str(units.to_si(at["value"], at["unit"])),
                         "P_W": str(units.to_si(q["value"], q["unit"])), "evidence_status": c["evidence_status"],
                         "install": c["install"], "evidence_ids": c.get("evidence_ids", [])})
    return rows, unknown


def compute_cooling():
    rows, unknown = cooling_points()
    cfgs = sorted({r["configuration"] for r in rows})
    doc_T = sorted({F(r["T_K"]) for r in rows})
    # T_op grid in microkelvin (exact integers): log grid + every documented temperature and its neighbours
    grid = {int(round(x)) for x in np.geomspace(5_000, 40_000_000, 140)}
    for t in doc_T:
        uk = int(t * 10**6)
        grid |= {uk - 1, uk, uk + 1}
    grid = sorted(g for g in grid if g > 0)
    ex0 = serialize.working_experiment(CAT, EXP_ID, None, None, True)
    pairs, index = [], []
    for cid in cfgs:
        for uk in grid:
            ex = copy.deepcopy(ex0)
            for p in ex["params"]:
                if p["name"] == "operating_temperature":
                    p["value"] = {"unit": "uK", "value": uk}
            cd, ed, info, _ = verifier.build_documents(CAT, ex, cid)
            slot = next(i for i in info if i["model"] == MODEL)["slots"].get("cooling")
            pairs.append((cd, ed))
            index.append((cid, uk, slot))
    res = batch(pairs)
    steps = defaultdict(list)
    for (cid, uk, slot), r in zip(index, res):
        c = coupled(r)
        rhs = side(c, "rhs")
        steps[cid].append({"T_op_uK": uk, "slot": slot, "rhs_W": fstr(rhs) if rhs is not None else None,
                           "coupled_outcome": c["outcome"]})
    return {"points": rows, "unknown_values": unknown, "steps": steps, "n_lean_checks": len(pairs),
            "note": "steps[cfg][i].rhs_W is the cooling power the Lean checker compared against (rhs of the "
                    "mxc_wiring_heat_budget coupled check) at operating temperature T_op; slot resolution rule: highest "
                    "documented, installed, known cooling_power.at_* temperature not above T_op."}


def fig_cooling_curves():
    print("fig_cooling_curves")
    d = cached("fig_cooling_curves", compute_cooling)
    pts = d["points"]
    by_cfg = defaultdict(list)
    for r in pts:
        by_cfg[r["configuration"]].append(r)
    # group configurations with identical documented point sets AND identical Lean step functions
    groups = {}
    for cid in sorted(by_cfg):
        sig = (tuple(sorted((r["T_K"], r["P_W"], r["evidence_status"], r["install"]) for r in by_cfg[cid])),
               tuple((s["T_op_uK"], s["rhs_W"], s["coupled_outcome"]) for s in d["steps"][cid]))
        groups.setdefault(sig, []).append(cid)
    # merge groups whose INSTALLED points and Lean steps coincide (the CCS optional points are drawn separately)
    merged = {}
    for sig, cids in groups.items():
        inst = (tuple(x for x in sig[0] if x[3] == "installed"), sig[1])
        merged.setdefault(inst, []).extend(cids)
    series = sorted(merged.values(), key=lambda cids: cids[0])

    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.9), gridspec_kw=dict(wspace=0.32))
    panels = [("a  Dilution refrigerators (mixing chamber)", lambda T: T < 1, (8e-3, 0.4), (3e-6, 1e-3)),
              ("b  4 K-class cryocoolers (cold head)", lambda T: T >= 1, (2.0, 40.0), (5e-2, 2e1))]
    markers = ["o", "s", "D", "^"]
    facts = {}
    for ax, (title, sel, xl, yl) in zip(axes, panels):
        k = 0
        for cids in series:
            mine = [r for c in cids for r in by_cfg[c] if sel(float(F(r["T_K"])))]
            if not mine:
                continue
            col, mk = CATEGORICAL[k % 4], markers[k % 4]
            k += 1
            label = ", ".join(SHORT.get(c, c) for c in cids)
            if len(cids) >= 4:
                label = "Lake Shore " + ", ".join(SHORT.get(c, c) for c in cids[:3]) + ",\n" + ", ".join(SHORT.get(c, c) for c in cids[3:])
            # Lean step: rhs as a function of T_op
            st = d["steps"][cids[0]]
            xs = np.array([s["T_op_uK"] * 1e-6 for s in st])
            ys = np.array([float(F(s["rhs_W"])) if s["rhs_W"] else np.nan for s in st])
            est = np.array([s["coupled_outcome"] == "unknown" and s["rhs_W"] is not None for s in st])
            m = (xs >= xl[0]) & (xs <= xl[1])
            lw = 3.0 - 1.0 * (k - 1)
            ax.step(xs[m], ys[m], where="post", color=col, lw=lw, zorder=2 + k * 0.1, solid_capstyle="butt")
            # spans where the slot resolves to a value Lean will not use (estimate): Lean reports unknown, no value
            pvals = {r["key"]: float(F(r["P_W"])) for r in mine}
            run = [s for s in st if s["slot"] and s["rhs_W"] is None and s["slot"] in pvals]
            if run:
                x0, x1 = run[0]["T_op_uK"] * 1e-6, run[-1]["T_op_uK"] * 1e-6
                yv = pvals[run[0]["slot"]]
                ax.add_patch(Rectangle((x0, yv / 1.12), x1 - x0, yv * (1.12 - 1 / 1.12), facecolor=VERDICT_COLOR[NEED],
                                       hatch=VERDICT_HATCH[NEED], edgecolor=DARKER[NEED], lw=0.4, zorder=3))
                ax.annotate("estimate only:\nLean reports unknown\n(NEED INFO)", xy=(x0 * 1.04, yv / 1.12),
                            xytext=(x0 * 1.45, yv / 2.4), fontsize=5.6, color=INK, ha="left", va="center",
                            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.5))
            # start of the step (no documented point at or below T_op before this)
            first = next((s for s in st if s["rhs_W"]), None)
            for r in mine:
                T, P = float(F(r["T_K"])), float(F(r["P_W"]))
                if r["install"] != "installed":
                    ax.plot(T, P, marker="x", ms=4.5, mew=1.0, color=MUTED, ls="none", zorder=4)
                elif r["evidence_status"] == "manufacturer_specification":
                    ax.plot(T, P, marker=mk, ms=4.6, color=col, mec="white", mew=0.5, ls="none", zorder=5)
                else:
                    ax.plot(T, P, marker=mk, ms=4.6, mfc="white", mec=col, mew=1.1, ls="none", zorder=5)
            ax.plot([], [], marker=mk, color=col, ls="-", lw=1.1, ms=4, label=label)
            uniq = {}
            for r in mine:
                kk = (r["T_K"], r["P_W"], r["evidence_status"], r["install"])
                u = uniq.setdefault(kk, {"T_K": r["T_K"], "P_W": r["P_W"], "status": r["evidence_status"],
                                         "install": r["install"], "evidence_ids": [], "configurations": []})
                u["evidence_ids"] = sorted(set(u["evidence_ids"]) | set(r["evidence_ids"]))
                u["configurations"].append(r["configuration"])
            facts[label] = list(uniq.values())
            if first is not None:
                facts[label + " | Lean step starts at T_op (uK)"] = first["T_op_uK"]
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(*xl)
        ax.set_ylim(*yl)
        ax.set_xlabel("Temperature, operating temperature $T_{op}$ (K)")
        ax.set_ylabel("Cooling power (W)")
        ax.set_title(title, loc="left", fontsize=8)
        ax.grid(True, which="major")
        ax.grid(False, which="minor")
        from matplotlib.ticker import FixedLocator, NullFormatter, FuncFormatter
        ticks = [0.01, 0.02, 0.05, 0.1, 0.2] if xl[1] < 1 else [2, 4, 5, 10, 20, 40]
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.legend(loc="upper left", fontsize=6, handlelength=1.8, borderaxespad=0.3)
    # shared key for marker semantics
    key = [Line2D([], [], marker="o", color=INK2, mec="white", ls="none", ms=4.5, label="sourced point, manufacturer specification"),
           Line2D([], [], marker="o", mfc="white", mec=INK2, mew=1.1, ls="none", ms=4.5, label="sourced point, inferred estimate"),
           Line2D([], [], marker="x", color=MUTED, ls="none", ms=4.5, mew=1.0, label="option not installed (ignored by the rule)"),
           Line2D([], [], color=INK2, lw=1.1, label="value Lean compares against at $T_{op}$ (checker rule)"),
           Patch(facecolor=VERDICT_COLOR[NEED], hatch=VERDICT_HATCH[NEED], edgecolor=DARKER[NEED],
                 label="rule picks an estimate: Lean uses no value")]
    fig.legend(handles=key, loc="lower center", ncol=3, fontsize=6, bbox_to_anchor=(0.5, -0.13), handlelength=2.0,
               columnspacing=1.2)
    for ax, ypos in zip(axes, (0.03, 0.40)):
        ax.text(0.98, ypos, "left of each step: no documented point $\\leq T_{op}$\n$\\rightarrow$ missing $\\rightarrow$ NEED INFO",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=5.6, color=INK2,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9))
    n_cfg = len(by_cfg)
    n_pts = len(pts)
    n_unknown_cfg = len({u["configuration"] for u in d["unknown_values"]} - set(by_cfg))
    dump_facts = {"configurations_with_points": sorted(by_cfg), "n_points": n_pts,
                  "configurations_with_only_unknown_cooling_power": sorted({u["configuration"] for u in d["unknown_values"]} - set(by_cfg)),
                  "series": facts}
    save(fig, "fig_cooling_curves", meta=dict(
        title="Sourced cooling-power points and the checker's step rule",
        question="Which cooling-power number does CryoLean compare a heat load against at a given operating temperature, and what is documented?",
        model="P_cool(T_op) := documented, installed, known cooling_power.at_T with the largest T <= T_op (conservative step; "
              "no interpolation, no extrapolation). Below the lowest documented T the value is missing.",
        data=f"{n_pts} sourced cooling_power.at_* points from data/cryostats/*.json for {n_cfg} configurations (evidence ids in "
             f"paper/data/fig_cooling_curves.json); step = rhs of the Lean mxc_wiring_heat_budget coupled check over "
             f"{d['n_lean_checks']} Lean runs (T_op grid x configurations, check_batch). {n_unknown_cfg} further configurations "
             f"document cooling power only as unknown and are not plotted.",
        claim="SOURCED+COMPUTED",
        caption="Markers are sourced cooling-power specifications (filled: manufacturer specification; open: inferred estimate; "
                "grey crosses: ratings of an optional cold head that is not installed, which the rule ignores); configurations "
                "with identical installed points and identical Lean output share one series. Lines are the cooling power the "
                "Lean checker actually compares against at each operating temperature, read from its output over a T_op sweep: "
                "the value at the highest documented temperature not above T_op; where that value is an estimate (OptistatDry "
                "TLEX, 4.2-5 K) Lean uses no value and reports the constraint as unknown. The step is the checker's rule, not a "
                "physical load curve; it is conservative under the model's stated assumption that cooling capacity does not "
                "decrease above a documented temperature.",
        section="supplement"))
    return dump_facts


# ================================================================================================ 2 heat budget
def compute_heat_budget():
    _, cd, ed, info = base_docs()
    p0 = params_of(ed)
    e5 = load("e5_heat")
    sugg = next(s for s in e5["z3_suggestion"] if s["parameter"] == "n_flux_lines")
    n_rep = F(sugg["suggested_exact"])
    states = [("Demo B", p0), ("Z3 repair", {**p0, "n_flux_lines": n_rep})]
    res = batch([(cd, with_params(ed, **{k: v for k, v in p.items() if k == "n_flux_lines"})) for _, p in states])
    out = []
    for (name, p), r in zip(states, res):
        c = coupled(r)
        lhs, rhs = side(c, "lhs"), side(c, "rhs")
        m = p["design_margin"]
        parts = {"drive": m * p["n_drive_lines"] * p["q_drive_line"],
                 "flux": m * p["n_flux_lines"] * (p["q_flux_line"] + p["p_flux_dc"]),
                 "output": m * p["n_output_lines"] * p["q_output_line"]}
        assert sum(parts.values()) == lhs, "contribution split must sum exactly to Lean's lhs"
        out.append({"state": name, "n_flux_lines": fstr(p["n_flux_lines"]), "verdict": r["verdict"],
                    "coupled_outcome": c["outcome"], "lhs_W": fstr(lhs), "rhs_W": fstr(rhs),
                    "lhs_display": c["lhs"]["display"], "rhs_display": c["rhs"]["display"],
                    "explanation": c["explanation"], "parts_W": {k: fstr(v) for k, v in parts.items()},
                    "raw_parts_W": {k: fstr(v / m) for k, v in parts.items()}})
    return {"states": out, "params": {k: fstr(v) for k, v in p0.items()}, "slot": info[0]["slots"],
            "z3_suggestion_source": "paper/data/e5_heat.json", "e5_lhs_uW_at": {str(pt["n_flux_lines"]): pt["lhs_uW"] for pt in e5["points"] if pt["n_flux_lines"] in (39, 50)}}


def fig_heat_budget():
    print("fig_heat_budget")
    d = cached("fig_heat_budget", compute_heat_budget)
    p = {k: F(v) for k, v in d["params"].items()}
    fig, ax = plt.subplots(figsize=(COL1, 2.35))
    names = {"drive": f"drive  {int(p['n_drive_lines'])} x {p['q_drive_line'] / NW} nW",
             "flux": f"flux  n x ({p['q_flux_line'] / NW} + {p['p_flux_dc'] / NW}) nW",
             "output": f"output  {int(p['n_output_lines'])} x {p['q_output_line'] / NW} nW"}
    cols = {"drive": NAVY, "flux": LAVENDER, "output": ICY}
    ys = [1, 0]
    rhs_uW = float(F(d["states"][0]["rhs_W"]) * 10**6)
    for y, st in zip(ys, d["states"]):
        left = 0.0
        for part in ("drive", "flux", "output"):
            w = float(F(st["parts_W"][part]) * 10**6)
            ax.barh(y, w, left=left, height=0.52, color=cols[part], edgecolor="white", linewidth=0.6, zorder=3)
            if w > 1.5:
                ax.text(left + w / 2, y, f"{w:.3f}".rstrip("0").rstrip("."), ha="center", va="center", fontsize=6.3,
                        color="white", zorder=4)
            left += w
        tot = float(F(st["lhs_W"]) * 10**6)
        short = VERDICT_SHORT[st["verdict"]]
        verdict_box(ax, tot + 0.35, y, st["verdict"], f"{short}\n{st['lhs_display']}", fs=6)
    ax.axvline(rhs_uW, color=INK, lw=0.9, ls=(0, (3, 2)), zorder=5)
    ax.text(rhs_uW + 0.3, 1.5, f"documented cooling power\nat 20 mK: {d['states'][0]['rhs_display']} (LD400)",
            ha="left", va="bottom", fontsize=6.2, color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"Demo B\n{d['states'][0]['n_flux_lines']} flux lines",
                        f"after Z3 repair\n{d['states'][1]['n_flux_lines']} flux lines"], fontsize=6.8)
    ax.set_xlim(0, 19.8)
    ax.set_ylim(-0.55, 1.95)
    ax.set_xlabel("Heat load at mixing chamber x design margin 3 (µW)")
    ax.grid(axis="y", visible=False)
    handles = [Patch(facecolor=cols[k], edgecolor="white", label=names[k]) for k in ("drive", "flux", "output")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, -0.24), ncol=1, fontsize=6, handlelength=1.2,
              title="contribution (per-line loads from Krinner et al. 2019)", title_fontsize=6)
    s0, s1 = d["states"]
    save(fig, "fig_heat_budget", meta=dict(
        title="Demo B mixing-chamber heat budget before and after the Z3 repair",
        question="Why does the 50-qubit wiring plan fail on a Bluefors LD400, and what single change repairs it?",
        model="margin x (n_drive q_drive + n_flux (q_flux + p_flux_dc) + n_out q_out) <= P_cool(20 mK); coupled model "
              "mxc_wiring_heat_budget (data/physics/coupled_models.json), exact rationals.",
        data=f"Parameters from data/experiments/quantum_mxc_wiring_heat_budget.json (Krinner et al., EPJ Quantum Technology 2019, "
             f"evidence hl_010, hl_011, hl_017, hl_019, hl_029, hl_033); cooling power 12 µW at 20 mK from "
             f"bluefors_ld400_hdw (ev_bf_0006). Totals and verdicts from 2 Lean runs now (lhs {s0['lhs_display']} / "
             f"{s1['lhs_display']}, identical to paper/data/e5_heat.json); Z3 suggestion n_flux_lines = {s1['n_flux_lines']} "
             f"from e5_heat.json. Per-contribution split computed with exact rationals and asserted to sum to Lean's lhs.",
        claim="COMPUTED+SOURCED",
        caption=f"Stacked mixing-chamber heat load (each contribution multiplied by the design margin 3) for the sourced "
                f"50-qubit wiring plan on bluefors_ld400_hdw. With {s0['n_flux_lines']} flux lines the Lean checker computes "
                f"{s0['lhs_display']} against the documented {s0['rhs_display']} and returns {VERDICT_LABEL[s0['verdict']].lower()}; "
                f"the Z3-proposed reduction to {s1['n_flux_lines']} flux lines gives {s1['lhs_display']}, which Lean accepts. "
                f"Per-line loads are measured central values from Krinner et al. (2019); their uncertainties are not propagated here.",
        section="main"))
    return d


# ================================================================================================ 3 boundary 2D
NF_MAX, ND_MAX = 80, 300


def compute_boundary():
    _, cd, ed, _ = base_docs()
    idx = [(nf, nd) for nd in range(ND_MAX + 1) for nf in range(NF_MAX + 1)]
    t0 = time.perf_counter()
    res = batch((cd, with_params(ed, n_drive_lines=nd, n_flux_lines=nf)) for nf, nd in idx)
    dt = time.perf_counter() - t0
    grid = [[None] * (NF_MAX + 1) for _ in range(ND_MAX + 1)]
    outcomes = Counter()
    for (nf, nd), r in zip(idx, res):
        grid[nd][nf] = {MET: 1, NOT: 0}.get(r["verdict"], -1)
        outcomes[(r["verdict"], coupled(r)["outcome"])] += 1
    return {"n_flux_max": NF_MAX, "n_drive_max": ND_MAX, "met_grid_rows_n_drive": grid,
            "verdict_x_coupled_outcome": [{"verdict": k[0], "coupled": k[1], "n": v} for k, v in outcomes.items()],
            "n_lean_checks": len(res), "lean_seconds": round(dt, 2),
            "fixed": "n_output_lines=8, q_drive=13 nW, q_flux=29 nW, p_flux_dc=50 nW, q_output=20 nW, margin=3, P_cool(20 mK)=12 uW"}


def fig_boundary_2d():
    print("fig_boundary_2d")
    d = cached("fig_boundary_2d", compute_boundary)
    g = np.array(d["met_grid_rows_n_drive"])
    assert (g >= 0).all(), "every grid point must have a MET / NOT MET verdict"
    _, _, ed, _ = base_docs()
    p = params_of(ed)
    # per row: largest feasible n_flux (Lean); verify the MET set is a prefix in every row (monotone)
    fmax = []
    for nd in range(g.shape[0]):
        row = g[nd]
        k = int(row.sum())
        assert (row[:k] == 1).all() and (row[k:] == 0).all(), "MET cells must form a prefix in each row"
        fmax.append(k - 1)  # -1 means none feasible
    fmax = np.array(fmax)
    # analytic boundary (overlay only) and exact agreement count against Lean
    agree = 0
    for nd in range(g.shape[0]):
        for nf in range(g.shape[1]):
            ok = lhs_exact({**p, "n_drive_lines": F(nd), "n_flux_lines": F(nf)}) <= F(12, 10**6)
            agree += int(ok == bool(g[nd, nf]))
    n_total = g.size
    n_met = int(g.sum())
    # staircase polygons (exact cell edges) for the two regions
    stairs = []
    for nd in range(g.shape[0]):
        stairs += [(fmax[nd] + 0.5, nd - 0.5), (fmax[nd] + 0.5, nd + 0.5)]
    met_poly = [(-0.5, -0.5)] + stairs + [(-0.5, g.shape[0] - 0.5)]
    not_poly = stairs + [(NF_MAX + 0.5, g.shape[0] - 0.5), (NF_MAX + 0.5, -0.5)]
    fig, ax = plt.subplots(figsize=(COL1, 3.35))
    ax.add_patch(Polygon(met_poly, closed=True, facecolor=VERDICT_COLOR[MET], edgecolor="none", alpha=0.85, zorder=1))
    ax.add_patch(Polygon(not_poly, closed=True, facecolor=VERDICT_COLOR[NOT], edgecolor="white", hatch=VERDICT_HATCH[NOT],
                         linewidth=0, alpha=0.85, zorder=1))
    # analytic line 3 (13 n_d + 79 n_f + 160) nW = 12 uW
    nf_line = np.linspace(-0.5, NF_MAX + 0.5, 200)
    P = F(12, 10**6)
    a = float(p["design_margin"] * p["q_drive_line"])
    b = float(p["design_margin"] * (p["q_flux_line"] + p["p_flux_dc"]))
    c0 = float(p["design_margin"] * p["n_output_lines"] * p["q_output_line"])
    nd_line = (float(P) - c0 - b * nf_line) / a
    ax.plot(nf_line, nd_line, color=INK, lw=1.0, ls=(0, (4, 2)), zorder=3,
            label="analytic: 3(13$n_d$ + 79$n_f$ + 160) nW = 12 µW")
    n0d, n0f = int(p["n_drive_lines"]), int(p["n_flux_lines"])
    e5 = load("e5_heat")
    n_rep = int(F(next(s for s in e5["z3_suggestion"] if s["parameter"] == "n_flux_lines")["suggested_exact"]))
    ax.annotate("", xy=(n_rep, n0d), xytext=(n0f, n0d), arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9), zorder=4)
    ax.plot(n0f, n0d, marker="o", ms=6, mfc="white", mec=INK, mew=1.2, ls="none", zorder=5)
    ax.plot(n_rep, n0d, marker="D", ms=5, mfc=INK, mec="white", mew=0.8, ls="none", zorder=5)
    ax.text(n0f + 1.5, n0d - 9, f"Demo B ({n0f}, {n0d})\nNOT MET", fontsize=6.2, color=INK, ha="left", va="top",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85), zorder=6)
    ax.text(n_rep - 1.5, n0d - 12, f"Z3 repair ({n_rep}, {n0d})\nMET", fontsize=6.2, color=INK, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85), zorder=6)
    ax.set_xlim(-0.5, NF_MAX + 0.5)
    ax.set_ylim(-0.5, ND_MAX + 0.5)
    ax.set_xlabel("Flux lines $n_f$ (count)")
    ax.set_ylabel("Drive lines $n_d$ (count)")
    ax.grid(False)
    h = [Patch(facecolor=VERDICT_COLOR[MET], label=f"Lean: requirements met ({n_met})"),
         Patch(facecolor=VERDICT_COLOR[NOT], hatch=VERDICT_HATCH[NOT], edgecolor="white",
               label=f"Lean: does not meet ({n_total - n_met})"),
         Line2D([], [], color=INK, lw=1.0, ls=(0, (4, 2)), label="analytic boundary (model equation)")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.45, -0.17), fontsize=6, ncol=1)
    # zoom inset: the integer staircase the Lean checker produces, against the analytic line
    ins = ax.inset_axes([0.6, 0.53, 0.37, 0.4])
    ax.add_patch(Rectangle((0.52, 0.46), 0.475, 0.535, transform=ax.transAxes, facecolor="white", edgecolor="none",
                           zorder=4))
    ins.add_patch(Polygon(met_poly, closed=True, facecolor=VERDICT_COLOR[MET], edgecolor="none", alpha=0.85, zorder=1))
    ins.add_patch(Polygon(not_poly, closed=True, facecolor=VERDICT_COLOR[NOT], edgecolor="white", hatch=VERDICT_HATCH[NOT],
                          linewidth=0, alpha=0.85, zorder=1))
    zx, zy = (33.5, 51.5), (44.5, 72.5)
    for xv in np.arange(zx[0], zx[1] + 1):
        ins.axvline(xv, color="white", lw=0.25, zorder=2)
    for yv in np.arange(zy[0], zy[1] + 1):
        ins.axhline(yv, color="white", lw=0.25, zorder=2)
    ins.plot(nf_line, nd_line, color=INK, lw=0.9, ls=(0, (4, 2)), zorder=3)
    ins.plot(n0f, n0d, marker="o", ms=4, mfc="white", mec=INK, mew=1.0, ls="none", zorder=5)
    ins.plot(n_rep, n0d, marker="D", ms=3.5, mfc=INK, mec="white", mew=0.6, ls="none", zorder=5)
    ins.set_xlim(*zx)
    ins.set_ylim(*zy)
    ins.set_xticks([35, 40, 45, 50])
    ins.set_yticks([50, 60, 70])
    ins.tick_params(labelsize=5.2, length=1.5, pad=1)
    ins.grid(False)
    for sp in ins.spines.values():
        sp.set_visible(True)
        sp.set_color(INK2)
        sp.set_linewidth(0.6)
    ins.set_title("zoom: one cell per Lean run", fontsize=5.4, pad=2, color=INK, fontweight="normal")
    ax.indicate_inset_zoom(ins, edgecolor=INK2, alpha=0.9, linewidth=0.6)
    nf_none = int(np.argmax(g[0] == 0))  # first n_flux infeasible even with zero drive lines
    facts = {"n_points": n_total, "n_met": n_met, "n_not_met": n_total - n_met, "lean_vs_analytic_agreement": agree,
             "max_n_flux_with_58_drive": int(fmax[n0d]), "max_n_flux_with_0_drive": int(fmax[0]),
             "max_n_drive_with_0_flux": int(max(nd for nd in range(g.shape[0]) if g[nd, 0] == 1)),
             "max_n_drive_with_50_flux": int(max([nd for nd in range(g.shape[0]) if g[nd, n0f] == 1], default=-1)),
             "first_n_flux_infeasible_with_0_drive": nf_none, "lean_seconds": d.get("lean_seconds")}
    save(fig, "fig_boundary_2d", meta=dict(
        title="Exact Lean feasibility region of the heat budget in the wiring plane",
        question="For which combinations of drive and flux lines does the LD400 meet the Demo B heat budget?",
        model="Lean verdict for margin x (n_d q_d + n_f (q_f + p_dc) + n_out q_out) <= P_cool(20 mK) at every integer "
              "(n_f, n_d); analytic line 3(13 n_d + 79 n_f + 160) nW = 12 µW overlaid (not used to classify).",
        data=f"{d['n_lean_checks']} Lean runs (check_batch, n_f = 0..{NF_MAX}, n_d = 0..{ND_MAX}) on documents built by "
             f"verifier.build_documents for {EXP_ID} on {CFG_ID} with n_drive_lines and n_flux_lines edited (origin "
             f"user_entered); all other parameters as sourced. Grid in paper/data/fig_boundary_2d.json.",
        claim="COMPUTED+MODELED",
        caption=f"Every integer point of the (flux lines, drive lines) plane classified by the Lean checker ({n_met} met, "
                f"{n_total - n_met} not met); the dashed line is the analytic boundary of the model equation, which agrees "
                f"with Lean at {agree} of {n_total} points. With 58 drive lines at most {int(fmax[n0d])} flux lines fit, "
                f"and with 50 flux lines no number of drive lines (not even zero) meets the budget. Output lines (8), per-line "
                f"loads, margin 3 and the 12 µW cooling power at 20 mK are held at their sourced values.",
        section="main"))
    return facts


# ================================================================================================ 4 sensitivity
SENS_PARAMS = ["n_drive_lines", "n_flux_lines", "n_output_lines", "q_drive_line", "q_flux_line", "p_flux_dc",
               "q_output_line", "design_margin", "cooling_power"]
INTEGER = {"n_drive_lines", "n_flux_lines", "n_output_lines"}


def compute_sensitivity():
    _, cd, ed, info = base_docs()
    slot = info[0]["slots"]["cooling"]
    p0 = params_of(ed)
    P0 = fq(next(c for c in cd["capabilities"] if c["key"] == slot)["value"]["q"])
    e5 = load("e5_heat")
    n_rep = F(next(s for s in e5["z3_suggestion"] if s["parameter"] == "n_flux_lines")["suggested_exact"])
    scenarios = {"demo_b": {"n_flux_lines": p0["n_flux_lines"]}, "z3_repair": {"n_flux_lines": n_rep}}
    n_checks = 0

    def doc(sc, name, lam):
        base = {**p0, **scenarios[sc]}
        if name == "cooling_power":
            return (with_cooling(cd, slot, P0 * lam), with_params(ed, **scenarios[sc]))
        return (cd, with_params(ed, **{**scenarios[sc], name: base[name] * lam}))

    out = {}
    for sc in scenarios:
        base_r = batch([doc(sc, "design_margin", F(1))])[0]
        n_checks += 1
        base_v = base_r["verdict"]
        out[sc] = {"baseline_verdict": base_v, "baseline_lhs_W": fstr(side(coupled(base_r), "lhs")), "params": {}}
        # direction that can flip: from NOT MET decrease loads / increase cooling; from MET the opposite
        for name in SENS_PARAMS:
            up_helps = name == "cooling_power"
            towards = (base_v == NOT) == up_helps  # True -> search lam > 1, False -> lam < 1
            base_val = P0 if name == "cooling_power" else {**p0, **scenarios[sc]}[name]
            rec = {"baseline_value": fstr(base_val), "direction": "increase" if towards else "decrease"}
            if name in INTEGER:
                n0 = int(base_val)
                cand = list(range(n0 + 1, n0 + 400)) if towards else list(range(n0 - 1, -1, -1))
                rs = batch([doc(sc, name, F(n, n0)) for n in cand])
                n_checks += len(rs)
                flip = next((n for n, r in zip(cand, rs) if r["verdict"] != base_v), None)
                rec.update(flip_value=flip, flip_relative=None if flip is None else fstr(F(flip - n0, n0)),
                           note="first integer count (scanning away from the baseline) at which the Lean verdict differs")
            else:
                # bracket: lam in [0, 1] (decrease) or [1, hi] (increase)
                if towards:
                    lo, hi = F(1), F(2)
                    while batch([doc(sc, name, hi)])[0]["verdict"] == base_v and hi < 2**20:
                        hi *= 2
                        n_checks += 1
                    n_checks += 1
                    a, b = lo, hi
                else:
                    a, b = F(0), F(1)
                end = batch([doc(sc, name, a if not towards else b)])[0]["verdict"]
                n_checks += 1
                if end == base_v:
                    rec.update(flip_relative=None, note="no flip over the whole search interval (parameter cannot repair/break "
                                                       "the budget alone)")
                    out[sc]["params"][name] = rec
                    continue
                # k-section with Lean: invariant verdict(lam=base side) == base_v, other side flipped
                # keep [x_base, x_flip] with x_base the endpoint nearer to 1
                x_base, x_flip = (a, b) if towards else (b, a)
                for _ in range(8):
                    pts = [x_base + (x_flip - x_base) * F(i, 32) for i in range(1, 32)]
                    rs = batch([doc(sc, name, x) for x in pts])
                    n_checks += len(rs)
                    flips = [x for x, r in zip(pts, rs) if r["verdict"] != base_v]
                    stays = [x for x, r in zip(pts, rs) if r["verdict"] == base_v]
                    if flips:
                        x_flip = min(flips, key=lambda x: abs(x - x_base))
                        nearer = [x for x in stays if abs(x - x_base) < abs(x_flip - x_base)]
                        if nearer:
                            x_base = max(nearer, key=lambda x: abs(x - x_base))
                    else:
                        x_base = pts[-1]
                # analytic exact threshold (overlay / cross-check only)
                q = {**p0, **scenarios[sc]}
                L = lhs_exact(q)
                if name == "cooling_power":
                    lam_star = L / P0
                elif name == "design_margin":
                    lam_star = P0 / L
                else:
                    coef = {"q_drive_line": q["n_drive_lines"], "q_flux_line": q["n_flux_lines"], "p_flux_dc": q["n_flux_lines"],
                            "q_output_line": q["n_output_lines"]}[name] * q["design_margin"]
                    lam_star = (P0 - (L - coef * q[name])) / (coef * q[name])
                # Lean at the exact analytic threshold (equality -> '<=' holds -> MET) and just beyond it
                eps = F(1, 10**12)
                beyond = lam_star - eps if towards is False else lam_star + eps
                inside = lam_star + eps if towards is False else lam_star - eps
                r_star, r_beyond, r_inside = batch([doc(sc, name, lam_star), doc(sc, name, beyond), doc(sc, name, inside)])
                n_checks += 3
                lo_b, hi_b = sorted([x_base, x_flip])
                rec.update(bracket_lo=fstr(lo_b), bracket_hi=fstr(hi_b), bracket_width=float(hi_b - lo_b),
                           flip_relative_float=float(((lo_b + hi_b) / 2) - 1),
                           analytic_threshold=fstr(lam_star), analytic_threshold_float=float(lam_star),
                           analytic_relative=float(lam_star - 1), analytic_in_lean_bracket=lo_b <= lam_star <= hi_b,
                           lean_at_threshold=r_star["verdict"], lean_beyond_threshold_by_1e12th=r_beyond["verdict"],
                           lean_inside_threshold_by_1e12th=r_inside["verdict"])
                rec["flip_relative"] = fstr(lam_star - 1)
            out[sc]["params"][name] = rec
    # analytic elasticities d ln(lhs)/d ln(p) at both scenarios (overlay data, not plotted as verdicts)
    for sc in scenarios:
        q = {**p0, **scenarios[sc]}
        L = lhs_exact(q)
        m = q["design_margin"]
        el = {"n_drive_lines": m * q["n_drive_lines"] * q["q_drive_line"] / L,
              "q_drive_line": m * q["n_drive_lines"] * q["q_drive_line"] / L,
              "n_flux_lines": m * q["n_flux_lines"] * (q["q_flux_line"] + q["p_flux_dc"]) / L,
              "q_flux_line": m * q["n_flux_lines"] * q["q_flux_line"] / L,
              "p_flux_dc": m * q["n_flux_lines"] * q["p_flux_dc"] / L,
              "n_output_lines": m * q["n_output_lines"] * q["q_output_line"] / L,
              "q_output_line": m * q["n_output_lines"] * q["q_output_line"] / L, "design_margin": F(1)}
        out[sc]["analytic_elasticity_of_lhs"] = {k: fstr(v) for k, v in el.items()}
        out[sc]["analytic_partial_derivatives_W_per_unit"] = {
            "n_drive_lines": fstr(m * q["q_drive_line"]), "n_flux_lines": fstr(m * (q["q_flux_line"] + q["p_flux_dc"])),
            "n_output_lines": fstr(m * q["q_output_line"]), "q_drive_line": fstr(m * q["n_drive_lines"]),
            "q_flux_line": fstr(m * q["n_flux_lines"]), "p_flux_dc": fstr(m * q["n_flux_lines"]),
            "q_output_line": fstr(m * q["n_output_lines"]), "design_margin": fstr(L / m), "cooling_power_rhs": "1"}
    out["n_lean_checks"] = n_checks
    out["cooling_slot"] = slot
    return out


PRETTY = {"n_drive_lines": "drive lines $n_d$", "n_flux_lines": "flux lines $n_f$", "n_output_lines": "output lines $n_{out}$",
          "q_drive_line": "load per drive line", "q_flux_line": "load per flux line", "p_flux_dc": "DC flux-bias power",
          "q_output_line": "load per output line", "design_margin": "design margin", "cooling_power": "cooling power at 20 mK"}


def fig_sensitivity():
    print("fig_sensitivity")
    d = cached("fig_sensitivity", compute_sensitivity)
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.75), gridspec_kw=dict(wspace=0.95))
    titles = {"demo_b": "a  Demo B (50 flux lines, NOT MET):\n    single change that makes it MET",
              "z3_repair": "b  Z3-repaired design (39 flux lines, MET):\n    single change that breaks it"}
    facts = {}
    for ax, sc in zip(axes, ("demo_b", "z3_repair")):
        rows = d[sc]["params"]
        order = sorted(SENS_PARAMS, key=lambda n: (rows[n]["flip_relative"] is None,
                                                  abs(float(F(rows[n]["flip_relative"]))) if rows[n]["flip_relative"] else 0))
        ys = np.arange(len(order))[::-1]
        for y, n in zip(ys, order):
            r = rows[n]
            if r["flip_relative"] is None:
                ax.text(0.012, y, "no flip, even at zero", va="center", ha="left", fontsize=6, color=MUTED, style="italic")
                continue
            rel = float(F(r["flip_relative"])) * 100
            col = NAVY if rel < 0 else ORANGE
            ax.barh(y, abs(rel), color=col, height=0.62, zorder=3)
            if n in INTEGER:
                lab = f"{'+' if rel > 0 else '−'}{abs(rel):.3g}%  ({int(F(r['baseline_value']))}→{r['flip_value']})"
            else:
                lab = f"{'+' if rel > 0 else '−'}{abs(rel):.3g}%"
            ax.text(abs(rel) * 1.12, y, lab, va="center", ha="left", fontsize=6, color=INK)
            facts[f"{sc}:{n}"] = lab
        ax.set_xscale("log")
        ax.set_xlim(0.01, 1000)
        ax.set_yticks(ys)
        ax.set_yticklabels([PRETTY[n] for n in order], fontsize=6.6)
        ax.set_xlabel("|relative change| at which the Lean verdict flips (%)")
        ax.set_title(titles[sc], loc="left", fontsize=7.4)
        ax.grid(axis="y", visible=False)
        ax.set_xticks([0.01, 0.1, 1, 10, 100, 1000])
        ax.set_xticklabels(["0.01", "0.1", "1", "10", "100", "1000"])
        ax.set_ylim(-0.6, len(order) - 0.4)
    h = [Patch(facecolor=NAVY, label="decrease"), Patch(facecolor=ORANGE, label="increase")]
    axes[0].legend(handles=h, loc="lower right", bbox_to_anchor=(1.03, 0.0), fontsize=6.5, title="direction of change",
                   title_fontsize=6.3)
    cont = [r for sc in ("demo_b", "z3_repair") for n, r in d[sc]["params"].items() if "analytic_in_lean_bracket" in r]
    all_in = all(r["analytic_in_lean_bracket"] for r in cont)
    at_thr = Counter(r["lean_at_threshold"] for r in cont)
    widths = max(r["bracket_width"] for r in cont)
    facts.update(n_lean_checks=d["n_lean_checks"], continuous_thresholds=len(cont), analytic_in_lean_bracket_all=all_in,
                 lean_at_exact_threshold=dict(at_thr), max_bracket_width=widths)
    save(fig, "fig_sensitivity", meta=dict(
        title="One-at-a-time sensitivity of the Demo B heat budget",
        question="How far must each input of the heat budget move, alone, before the Lean verdict changes?",
        model="For each parameter p, the factor lambda with verdict(p x lambda) != verdict(p): continuous parameters by 8 "
              "rounds of 32-point k-section on exact rationals (Lean decides every point), then the analytic threshold "
              "lambda* = (P - L_other)/L_p is checked with Lean at lambda* and lambda* +- 1e-12; counts by integer scan.",
        data=f"{d['n_lean_checks']} Lean runs (check_batch) on documents for {EXP_ID} on {CFG_ID}; the cooling power is "
             f"edited in the configuration document ({d['cooling_slot']}). Results, brackets and analytic elasticities in "
             f"paper/data/fig_sensitivity.json.",
        claim="COMPUTED",
        caption="Relative change of a single input (others at their sourced values) at which the Lean checker's verdict flips, "
                "on a log axis. (a) From the failing Demo B plan, only the flux-line count, the per-flux-line loads, the design "
                "margin or the cooling power can repair the budget on their own; drive and output lines cannot, even at zero. "
                "(b) The Z3-repaired design has only 15 nW of margin-weighted slack, so a 0.125% change of the margin or the "
                f"cooling power, or one extra drive or flux line, breaks it. Lean brackets contain the exact analytic threshold "
                f"in every continuous case and Lean returns MET exactly at the threshold (the constraint is <=).",
        section="main"))
    return facts


# ================================================================================================ 5 uncertainty
N_SAMPLES = 2000
NF_RANGE = list(range(20, 61))
SOURCED_SIGMA_NW = {"q_drive_line": F(6), "q_flux_line": F(5), "p_flux_dc": F(3), "q_output_line": F(16)}  # hl_011/017/029/019


def compute_uncertainty():
    _, cd, ed, _ = base_docs()
    p0 = params_of(ed)
    rng = random.Random(20261031)
    # model U: independent uniform +-20 % multipliers on the 4 per-line loads (ASSUMED tolerance), exact grid 1e-4
    uni = [{k: p0[k] * (1 + F(rng.randint(-2000, 2000), 10000)) for k in LOAD_PARAMS} for _ in range(N_SAMPLES)]
    # model G: independent Gaussian with the sourced 1-sigma of Krinner et al. Table 2, truncated at 0 (distribution ASSUMED)
    gau = []
    for _ in range(N_SAMPLES):
        s = {}
        for k in LOAD_PARAMS:
            while True:
                x = rng.gauss(float(p0[k] / NW), float(SOURCED_SIGMA_NW[k]))
                if x >= 0:
                    break
            s[k] = F(round(x * 1000), 1000) * NW
        gau.append(s)
    out = {}
    n_checks = 0
    for tag, samples in (("uniform_20pct", uni), ("gaussian_sourced_sigma", gau)):
        res = batch((cd, with_params(ed, n_flux_lines=nf, **s)) for nf in NF_RANGE for s in samples)
        n_checks += len(res)
        rows = []
        for i, nf in enumerate(NF_RANGE):
            vs = Counter(r["verdict"] for r in res[i * N_SAMPLES:(i + 1) * N_SAMPLES])
            k = vs.get(MET, 0)
            pm, lo, hi = wilson(k, N_SAMPLES)
            rows.append({"n_flux_lines": nf, "n": N_SAMPLES, "met": k, "verdicts": dict(vs), "p_met": pm, "wilson_lo": lo,
                         "wilson_hi": hi})
        out[tag] = rows
    nominal = batch([(cd, with_params(ed, n_flux_lines=nf)) for nf in NF_RANGE])
    n_checks += len(nominal)
    return {"models": out, "nominal": [{"n_flux_lines": nf, "verdict": r["verdict"]} for nf, r in zip(NF_RANGE, nominal)],
            "n_samples_per_point": N_SAMPLES, "seed": 20261031, "n_lean_checks": n_checks,
            "assumptions": {"uniform_20pct": "q_drive, q_flux, p_flux_dc, q_output each multiplied by an independent "
                                             "uniform factor in [0.8, 1.2] (exact grid 1e-4); +-20 % is an ASSUMED tolerance, "
                                             "not sourced. One factor per load type, shared by all lines of that type.",
                            "gaussian_sourced_sigma": "independent Gaussian per load type with mean = sourced central value "
                                                      "and sigma = sourced 1-sigma of Krinner et al. Table 2 (13(6), 29(5), "
                                                      "20(16), 50(3) nW; hl_011, hl_017, hl_019, hl_029), truncated at 0, "
                                                      "rounded to 1e-3 nW; the Gaussian shape and independence are ASSUMED.",
                            "common_random_numbers": "the same samples are reused for every n_flux value"}}


def fig_uncertainty():
    print("fig_uncertainty")
    d = cached("fig_uncertainty", compute_uncertainty)
    fig, ax = plt.subplots(figsize=(COL1, 2.65))
    styles = {"uniform_20pct": (NAVY, "o", "uniform ±20%\n(tolerance assumed)"),
              "gaussian_sourced_sigma": (LAVENDER, "s", "Gaussian, sourced 1σ\n(shape assumed)")}
    facts = {}
    for tag, (col, mk, lab) in styles.items():
        rows = d["models"][tag]
        x = np.array([r["n_flux_lines"] for r in rows])
        pm = np.array([r["p_met"] for r in rows])
        lo = np.array([r["wilson_lo"] for r in rows])
        hi = np.array([r["wilson_hi"] for r in rows])
        ax.fill_between(x, lo, hi, color=col, alpha=0.25, lw=0, zorder=2)
        ax.plot(x, pm, color=col, lw=1.2, marker=mk, ms=2.4, zorder=3, label=lab)
        byn = {r["n_flux_lines"]: r for r in rows}
        facts[tag] = {str(n): f"{byn[n]['met']}/{byn[n]['n']} = {byn[n]['p_met']:.3f} [{byn[n]['wilson_lo']:.3f}, {byn[n]['wilson_hi']:.3f}]"
                      for n in (30, 35, 39, 40, 45, 50) if n in byn}
        # n_flux at which P(MET) first drops below 0.95 / 0.5
        facts[tag]["largest_n_with_p_met_ge_0.95"] = max([r["n_flux_lines"] for r in rows if r["p_met"] >= 0.95], default=None)
        facts[tag]["largest_n_with_p_met_ge_0.5"] = max([r["n_flux_lines"] for r in rows if r["p_met"] >= 0.5], default=None)
    nom = d["nominal"]
    last_met = max(r["n_flux_lines"] for r in nom if r["verdict"] == MET)
    um = {r["n_flux_lines"]: r for r in d["models"]["uniform_20pct"]}
    ax.axvline(last_met + 0.5, color=INK, lw=0.9, ls=(0, (3, 2)), zorder=4)
    ax.text(last_met - 0.1, 0.2, f"nominal Lean boundary\n{last_met} MET | {last_met + 1} NOT MET", fontsize=6, color=INK,
            ha="right", va="center")
    # nominal verdict strip (colour + hatch + text), below the data
    for r in nom:
        v = r["verdict"]
        ax.add_patch(Rectangle((r["n_flux_lines"] - 0.5, -0.15), 1, 0.08, facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v],
                               edgecolor=DARKER[v], lw=0.3, zorder=3, clip_on=False))
    ax.text(NF_RANGE[0] + 0.5, -0.11, "nominal: MET", fontsize=5.6, color="white", va="center",
            fontweight="bold", zorder=4)
    ax.text(NF_RANGE[-1] - 0.5, -0.11, "NOT MET", fontsize=5.6, color="white", va="center", ha="right", fontweight="bold",
            zorder=4, bbox=dict(boxstyle="square,pad=0.1", facecolor=VERDICT_COLOR[NOT], edgecolor="none"))
    ax.set_xlim(NF_RANGE[0] - 0.5, NF_RANGE[-1] + 0.5)
    ax.set_ylim(-0.2, 1.04)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.spines["left"].set_bounds(0, 1.04)
    ax.set_xlabel("Flux lines $n_f$ (count)")
    ax.set_ylabel("P(Lean: requirements met)")
    ax.legend(loc="center right", bbox_to_anchor=(1.03, 0.7), fontsize=6, handlelength=1.6,
              title="input model\n(each sample decided by Lean)", title_fontsize=5.8)
    save(fig, "fig_uncertainty", meta=dict(
        title="Robustness of the heat-budget verdict to uncertain per-line loads",
        question="How likely is the LD400 heat budget to hold for a given number of flux lines when the per-line loads are uncertain?",
        model="Monte Carlo over the four per-line loads (q_drive, q_flux, p_flux_dc, q_output), one value per load type shared "
              "by all lines of that type; each sample decided by the Lean checker; P(MET) with Wilson 95% intervals. "
              "Two input models: uniform +-20% (ASSUMED tolerance) and Gaussian with the sourced 1-sigma (shape ASSUMED).",
        data=f"{d['n_lean_checks']} Lean runs (check_batch): {N_SAMPLES} samples x {len(NF_RANGE)} flux-line counts "
             f"({NF_RANGE[0]}..{NF_RANGE[-1]}) x 2 input models + {len(NF_RANGE)} nominal runs; seed {d['seed']}, common random "
             f"numbers across n_f. Sourced sigmas from Krinner et al. 2019 Table 2 (hl_011, hl_017, hl_019, hl_029). "
             f"paper/data/fig_uncertainty.json.",
        claim="COMPUTED+MODELED",
        caption=f"Fraction of Monte Carlo samples that the Lean checker accepts, with Wilson 95% intervals, against the number "
                f"of flux lines on bluefors_ld400_hdw. The nominal boundary between {last_met} and {last_met + 1} flux lines "
                f"becomes a transition band: under an assumed independent ±20% tolerance on each per-line load (navy) the "
                f"Z3-repaired design with {last_met} flux lines is accepted in {um[last_met]['met']}/{N_SAMPLES} samples "
                f"(P = {um[last_met]['p_met']:.3f}, 95% CI {um[last_met]['wilson_lo']:.3f}-{um[last_met]['wilson_hi']:.3f}) "
                f"and P(MET) >= 0.95 requires at most {facts['uniform_20pct']['largest_n_with_p_met_ge_0.95']} flux lines; "
                f"with the sourced 1-sigma uncertainties of Krinner et al. (lavender; Gaussian shape assumed) the band is "
                f"wider (P(MET) >= 0.95 up to {facts['gaussian_sourced_sigma']['largest_n_with_p_met_ge_0.95']} flux lines). "
                f"The strip shows the Lean verdict at the central (sourced) loads. The input distributions are modelling "
                f"assumptions; every accept/reject decision is a Lean run.",
        section="main"))
    return facts


# ================================================================================================ 6 schematic
def fig_cryostat_schematic():
    print("fig_cryostat_schematic")
    cfg = CAT.configurations[CFG_ID]
    caps = {c["key"]: c for c in cfg["capabilities"]}
    base_T = caps["temperature.base"]["value"]["q"]
    p20 = caps["cooling_power.at_20mK"]["value"]["q"]
    p100 = caps["cooling_power.at_100mK"]["value"]["q"]
    coax = caps["electrical.coax_lines"]["value"]["n"]
    hb = load("fig_heat_budget") if (DATA_DIR / "fig_heat_budget.json").exists() else compute_heat_budget()
    pr = {k: F(v) for k, v in hb["params"].items()}
    s0 = hb["states"][0]
    nd, nf, no = int(pr["n_drive_lines"]), int(pr["n_flux_lines"]), int(pr["n_output_lines"])
    qd, qf, pdc, qo = (pr[k] / NW for k in ("q_drive_line", "q_flux_line", "p_flux_dc", "q_output_line"))

    def nw_uw(q):
        return f"{F(q['value']) / 1000} µW" if q["unit"] == "nW" else f"{q['value']} {q['unit']}"

    plates = [("room-temperature top flange", 6.2, 1.25), ("first pulse-tube stage", 5.0, 1.15), ("second pulse-tube stage", 3.85, 1.05),
              ("still", 2.75, 0.95), ("cold plate", 1.75, 0.88), ("mixing chamber (MXC)", 0.7, 0.82)]
    fig, ax = plt.subplots(figsize=(COL2, 3.9))
    ax.set_xlim(-3.25, 4.6)
    ax.set_ylim(-0.3, 6.95)
    ax.set_aspect("equal")
    ax.axis("off")
    cx = 0.0
    tilt = 0.28
    # support rods (behind)
    for dx in (-0.62, 0.62):
        ax.plot([cx + dx, cx + dx], [0.7, 6.2], color=AXIS, lw=1.6, zorder=1, solid_capstyle="butt")
    # wiring lines: representative lines, colours = line type
    groups = [(NAVY, np.linspace(-0.42, -0.2, 4)), (LAVENDER, np.linspace(-0.08, 0.2, 4)), (ICY, np.linspace(0.32, 0.44, 2))]
    for col, xs in groups:
        for x in xs:
            ax.plot([cx + x, cx + x], [0.7, 6.2], color=col, lw=0.9, zorder=3)
    for i, (name, y, r) in enumerate(plates):
        is_mxc = i == len(plates) - 1
        ax.add_patch(Ellipse((cx, y), 2 * r, 2 * r * tilt, facecolor="#e8eef8" if not is_mxc else "#fbe3d8",
                             edgecolor=ORANGE if is_mxc else INK2, lw=1.4 if is_mxc else 0.8, zorder=2))
        # front lip to suggest thickness
        ax.add_patch(Rectangle((cx - r, y - 0.07), 2 * r, 0.07, facecolor="#d5deee" if not is_mxc else "#f6c9b5",
                               edgecolor="none", zorder=2))
        ax.add_patch(Ellipse((cx, y - 0.07), 2 * r, 2 * r * tilt, facecolor="none", edgecolor=INK2 if not is_mxc else ORANGE,
                             lw=0.5, zorder=2, ls="-"))
        ax.text(cx - r - 0.12, y, name, ha="right", va="center", fontsize=6.6, color=INK)
    # sample stage below MXC
    ax.add_patch(Rectangle((cx - 0.22, -0.1), 0.44, 0.36, facecolor="white", edgecolor=INK2, lw=0.7, zorder=2))
    ax.plot([cx, cx], [0.26, 0.58], color=INK2, lw=1.2, zorder=1)
    ax.text(cx - 0.3, 0.08, "sample / qubit chip", ha="right", va="center", fontsize=6.2, color=INK2)
    # annotations (all numbers from CryoLean data for bluefors_ld400_hdw and the heat-budget profile)
    xa = 1.55
    ax.annotate(f"High-Density Wiring: {coax} coax lines\n(one side-loading port; catalog assumption)",
                xy=(cx + 0.44, 5.55), xytext=(xa, 5.75), fontsize=6.4, color=INK, va="center",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax.text(xa, 4.6, "Heat-budget profile (Krinner et al. 2019):", fontsize=6.4, color=INK, fontweight="bold", va="center")
    leg = [(NAVY, f"{nd} drive lines, {qd} nW each at the MXC"),
           (LAVENDER, f"{nf} flux lines, ({qf} + {pdc} DC) nW each"),
           (ICY, f"{no} output lines, {qo} nW each")]
    for j, (col, txt) in enumerate(leg):
        yy = 4.25 - j * 0.3
        ax.plot([xa, xa + 0.28], [yy, yy], color=col, lw=1.6)
        ax.text(xa + 0.38, yy, txt, fontsize=6.3, color=INK, va="center")
    ax.text(xa, 3.2, "(representative lines drawn; not to scale)", fontsize=5.8, color=INK2, va="center", style="italic")
    box = (f"Heat-budget constraint applies at the MXC:\n"
           f"3 x ({nd}·{qd} + {nf}·({qf}+{pdc}) + {no}·{qo}) nW\n"
           f"= {s0['lhs_display']}  vs  P_cool(20 mK) = {nw_uw(p20)}")
    ax.annotate(box, xy=(cx + 0.82, 0.7), xytext=(xa, 1.85), fontsize=6.3, color=INK, va="center",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=ORANGE, lw=1.0),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.0))
    verdict_box(ax, xa + 2.1, 1.08, s0["verdict"], f"Lean: {VERDICT_SHORT[s0['verdict']]}", ha="left", fs=6.3)
    ax.text(xa, 0.55, f"MXC: base temperature ≤ {base_T['value']} {base_T['unit']}; cooling power {nw_uw(p20)} at 20 mK,\n"
                      f"{nw_uw(p100)} at 100 mK (manufacturer specification, LD400)", fontsize=6.1, color=INK2, va="center")
    ax.text(-3.2, 6.85, "ILLUSTRATIVE  -  schematic, not to scale; plate names generic", fontsize=6.6, color=INK2,
            fontweight="bold", va="top")
    save(fig, "fig_cryostat_schematic", meta=dict(
        title="Dilution-refrigerator stack and where the heat budget applies",
        question="Where in the refrigerator does the Demo B heat-budget constraint act, and which documented numbers enter it?",
        model="Schematic only (no physics computed); the boxed total and verdict are the Lean output for Demo B.",
        data=f"Numbers from data/cryostats/bluefors_ld.json ({CFG_ID}: temperature.base ev_bf_0003, cooling_power.at_20mK "
             f"ev_bf_0006, cooling_power.at_100mK ev_bf_0007, electrical.coax_lines) and data/experiments/{EXP_ID}.json "
             f"(line counts hl_033, per-line loads hl_011, hl_017, hl_019, hl_029); total and verdict from "
             f"paper/data/fig_heat_budget.json (Lean).",
        claim="ILLUSTRATIVE+SOURCED+COMPUTED",
        caption="Illustrative stack of a cryogen-free dilution refrigerator (plates drawn as discs, wiring as vertical lines; "
                "geometry, plate spacing and line positions are not to scale). Annotated numbers are the sourced LD400 "
                "specifications in CryoLean's catalog and the per-line loads of the Demo B heat-budget profile; the heat-budget "
                "constraint is evaluated at the mixing-chamber plate, where the Lean checker compares the margin-weighted "
                f"wiring load ({s0['lhs_display']}) with the documented cooling power at 20 mK ({nw_uw(p20)}).",
        section="supplement"), interactive=schematic_html(plates, groups, nd, nf, no, qd, qf, pdc, qo, s0, p20, p100, base_T, coax))
    return {"base_T": base_T, "P20": p20, "P100": p100, "coax_lines": coax}


def schematic_html(plates, groups, nd, nf, no, qd, qf, pdc, qo, s0, p20, p100, base_T, coax):
    import plotly.graph_objects as go
    traces = []
    th = np.linspace(0, 2 * np.pi, 72)
    for i, (name, y, r) in enumerate(plates):
        is_mxc = i == len(plates) - 1
        rr = np.linspace(0, r, 2)
        T, R = np.meshgrid(th, rr)
        traces.append(go.Surface(x=R * np.cos(T), y=R * np.sin(T), z=np.full_like(T, y), showscale=False, opacity=0.85,
                                 colorscale=[[0, "#fbe3d8" if is_mxc else "#e8eef8"], [1, "#fbe3d8" if is_mxc else "#e8eef8"]],
                                 hoverinfo="text", text=name, name=name))
        traces.append(go.Scatter3d(x=r * np.cos(th), y=r * np.sin(th), z=np.full_like(th, y), mode="lines",
                                   line=dict(color=ORANGE if is_mxc else INK2, width=5 if is_mxc else 2), showlegend=False,
                                   hoverinfo="skip"))
        traces.append(go.Scatter3d(x=[-r - 0.15], y=[0], z=[y], mode="text", text=[name], textposition="middle left",
                                   showlegend=False, hoverinfo="skip"))
    labels = {NAVY: f"drive lines ({nd}, {qd} nW each at MXC)", LAVENDER: f"flux lines ({nf}, {qf}+{pdc} nW each)",
              ICY: f"output lines ({no}, {qo} nW each)"}
    for col, xs in groups:
        for j, x in enumerate(xs):
            traces.append(go.Scatter3d(x=[x, x], y=[0.1 * j - 0.1, 0.1 * j - 0.1], z=[0.7, 6.2], mode="lines",
                                       line=dict(color=col, width=4), name=labels[col], showlegend=j == 0, legendgroup=col))
    traces.append(go.Scatter3d(x=[1.2], y=[0], z=[0.7], mode="text", textposition="middle right",
                               text=[f"MXC heat budget: {s0['lhs_display']} vs {F(p20['value']) / 1000} µW at 20 mK -> "
                                     f"Lean: {VERDICT_SHORT[s0['verdict']]}"], showlegend=False))
    fig = go.Figure(traces)
    fig.update_layout(title=f"ILLUSTRATIVE dilution-refrigerator stack (bluefors_ld400_hdw data: base <= {base_T['value']} "
                            f"{base_T['unit']}, {F(p20['value']) / 1000} µW at 20 mK, {F(p100['value']) / 1000} µW at 100 mK, "
                            f"{coax} coax lines) - not to scale",
                      scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                                 aspectmode="data"), margin=dict(l=0, r=0, t=50, b=0), legend=dict(x=0.75, y=0.9))
    return save_html(fig, "fig_cryostat_schematic")


# ================================================================================================ 7 contraction
def fig_contraction():
    print("fig_contraction")
    mats = json.loads((ROOT / "data" / "physics" / "materials.json").read_text(encoding="utf-8"))["materials"]
    rows = []
    for m in mats:
        v4 = next((v for v in m["values"] if v["to_temperature"]["value"] <= 4000), None)
        v80 = next((v for v in m["values"] if 70000 <= v["to_temperature"]["value"] <= 80000), None)
        rows.append({"id": m["id"], "name": m["name"], "ref_K": m["reference_temperature_K"], "notes": m["notes"],
                     "c4": F(v4["contraction"]) if v4 else None, "c4_ids": v4["evidence_ids"] if v4 else [],
                     "c80": F(v80["contraction"]) if v80 else None, "T80_mK": v80["to_temperature"]["value"] if v80 else None,
                     "c80_ids": v80["evidence_ids"] if v80 else []})
    dump("fig_contraction", {"materials": [{**r, "c4": fstr(r["c4"]) if r["c4"] is not None else None,
                                            "c80": fstr(r["c80"]) if r["c80"] is not None else None} for r in rows],
                             "source": "data/physics/materials.json", "_generated_by": SCRIPT})
    rows.sort(key=lambda r: float(r["c4"] if r["c4"] is not None else r["c80"]))
    cu = next(r for r in rows if r["id"] == "copper")
    fig, ax = plt.subplots(figsize=(COL1, 3.3))
    XMAX = 7.4
    ys = np.arange(len(rows))
    for y, r in zip(ys, rows):
        vals = [float(v) * 1e3 for v in (r["c4"], r["c80"]) if v is not None]
        if len(vals) == 2:
            ax.plot([min(min(vals), XMAX), min(max(vals), XMAX)], [y, y], color=AXIS, lw=1.0, zorder=2)
        for v, mk, col in ((r["c80"], "s", LAVENDER), (r["c4"], "o", NAVY)):
            if v is None:
                continue
            x = float(v) * 1e3
            if x > XMAX:
                ax.annotate("", xy=(XMAX + 0.05, y), xytext=(XMAX - 0.45, y),
                            arrowprops=dict(arrowstyle="-|>", color=col, lw=1.0), zorder=3, annotation_clip=False)
                continue
            ax.plot(x, y, marker=mk, ms=4.2, color=col, mec="white", mew=0.5, ls="none", zorder=4)
        if any(v is not None and float(v) * 1e3 > XMAX for v in (r["c4"], r["c80"])):
            ax.text(XMAX - 0.6, y, f"off scale: 4 K {float(r['c4']) * 1e3:.1f}, 80 K {float(r['c80']) * 1e3:.1f}", fontsize=5.6,
                    color=INK, ha="right", va="center")
        if r["c4"] is None:
            x80 = float(r["c80"]) * 1e3
            right = x80 < 5
            ax.text(x80 + (0.25 if right else -0.25), y, "no 4 K value (fit not valid)" if right else "no 4 K value", fontsize=5.4, color=MUTED,
                    va="center", ha="left" if right else "right")
    ax.axvline(float(cu["c4"]) * 1e3, color=INK2, lw=0.7, ls=(0, (3, 2)), zorder=1)
    ax.text(float(cu["c4"]) * 1e3 + 0.08, len(rows) - 0.35, "copper, 4 K", fontsize=5.8, color=INK2, va="bottom")
    ax.axvline(0, color=AXIS, lw=0.6, zorder=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([r["name"] for r in rows], fontsize=6.2)
    ax.set_xlim(-0.6, XMAX + 0.1)
    ax.set_ylim(-0.7, len(rows) + 0.2)
    ax.set_xlabel("Integrated linear contraction from 293 K, $(L_{293}-L_T)/L_{293}$ ($10^{-3}$)")
    ax.grid(axis="y", visible=False)
    h = [Line2D([], [], marker="o", color=NAVY, mec="white", ls="none", ms=4.2, label="to 4 K"),
         Line2D([], [], marker="s", color=LAVENDER, mec="white", ls="none", ms=4.2, label="to 77-80 K")]
    ax.legend(handles=h, loc="lower right", fontsize=6.2, frameon=True, facecolor="white", edgecolor="none")
    n4 = sum(r["c4"] is not None for r in rows)
    facts = {"n_materials": len(rows), "n_with_4K": n4,
             "ptfe_4K": fstr(next(r for r in rows if r["id"] == "ptfe")["c4"]),
             "fused_silica_4K": fstr(next(r for r in rows if r["id"] == "fused_silica")["c4"]),
             "copper_4K": fstr(cu["c4"]), "invar_4K": fstr(next(r for r in rows if r["id"] == "invar_fe36ni")["c4"]),
             "ptfe_minus_copper_4K": fstr(next(r for r in rows if r["id"] == "ptfe")["c4"] - cu["c4"])}
    ids = sorted({i for r in rows for i in r["c4_ids"] + r["c80_ids"]})
    save(fig, "fig_contraction", meta=dict(
        title="Sourced integrated thermal contraction of 14 cryostat materials",
        question="How different are the thermal contractions that CryoLean's differential-contraction model can use?",
        model="None (reference data). CryoLean's differential_thermal_contraction model uses |L (eps_sample - eps_holder)| <= delta "
              "with these values.",
        data=f"data/physics/materials.json ({len(rows)} materials, {n4} with a 4 K value); evidence ids {', '.join(ids)} "
             f"(NBS Monograph 29 and NIST cryogenic material fits). The 77-80 K marker is the 80 K row, or 77 K where only that "
             f"is recorded. Copy in paper/data/fig_contraction.json.",
        claim="SOURCED",
        caption="Integrated linear thermal contraction from room temperature to 4 K (circles) and to 77-80 K (squares) for the "
                "14 materials in CryoLean's reference table, in units of 10^-3. PTFE (about 21 x 10^-3) is off scale and labelled; "
                "fused silica expands slightly on cooling; sapphire and the two G-10 directions have only 77 K values because the "
                "cited fits are not valid at 4 K. The dashed line marks copper at 4 K for reference.",
        section="supplement"))
    return facts


# ================================================================================================ main
def main():
    apply()
    t0 = time.perf_counter()
    facts = {}
    facts["fig_cooling_curves"] = fig_cooling_curves()
    facts["fig_heat_budget"] = fig_heat_budget()["states"]
    facts["fig_boundary_2d"] = fig_boundary_2d()
    facts["fig_sensitivity"] = fig_sensitivity()
    facts["fig_uncertainty"] = fig_uncertainty()
    facts["fig_cryostat_schematic"] = fig_cryostat_schematic()
    facts["fig_contraction"] = fig_contraction()
    (DATA_DIR / "fig_physics2d_facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False, default=str) + "\n",
                                                      encoding="utf-8")
    print(f"done in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
