#!/usr/bin/env python
"""3D cryogenic multiphysics figures for the CryoLean paper.

    python paper/scripts/fig_physics3d.py

Every feasibility classification in these figures is a verdict of the compiled Lean 4 checker
(lean_runner.check_batch). Python only builds the documents (cryolean.verifier.build_documents, which also
resolves the cooling-power slot exactly as serialize.resolve_slots does) and draws. Analytic boundaries drawn on
top (I^2 R = P_cool, the box of documented ranges) are labelled as model overlays.

Figures (static PNG/SVG/PDF + interactive Plotly HTML):
  fig_thermal_feasibility_3d   Lean verdict of the Joule model over (T_op, Q) for three configurations
  fig_joule_surface_3d         P = I^2 R over (I, R) with the documented cooling-power plane, Lean verdicts
  fig_compat_region_3d         (T, B, Q) compatibility region for two configurations, Lean verdicts
  fig_operating_envelope_3d    sourced temperature-field envelopes of all configurations + experiment needs
Data: paper/data/fig_<name>.json
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import *  # noqa: E402,F403

import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from cryolean import lean_runner, units, verifier  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

CAT = Catalog()
JOULE = "joule_heating_vs_cooling_power"
I_FIXED = F(1, 1000)                     # 1 mA excitation; R = Q / I^2 makes I^2 R = Q exactly
MARK = {"REQUIREMENTS_MET": "o", "NEED_MORE_INFORMATION": "^", "DOES_NOT_MEET_REQUIREMENTS": "x"}
PLOTLY_SYM = {"REQUIREMENTS_MET": "circle", "NEED_MORE_INFORMATION": "diamond", "DOES_NOT_MEET_REQUIREMENTS": "x"}
LEAN_CALLS = Counter()


# ---------------------------------------------------------------------------------------------- helpers
def nice(decades, mults=(1, 3)):
    """Exact log-spaced grid: m * 10^k for k in decades, m in mults."""
    return [F(m) * F(10) ** k for k in decades for m in mults]


def fl(x):
    return float(x) if x is not None else None


def lg(x):
    return float(np.log10(float(x)))


def experiment(T_K, Q_W=None, reqs=(), I_A=None, R_ohm=None, joule=True):
    """Catalog-form experiment: optional mandatory requirements + the real Joule coupled model (mandatory)."""
    if Q_W is not None:
        I_A, R_ohm = I_FIXED, F(Q_W) / I_FIXED ** 2
    params = [{"name": "operating_temperature", "value": {"value": F(T_K), "unit": "K"}, "origin": "user_entered"}]
    if joule:
        params += [{"name": "measurement_current", "value": {"value": F(I_A), "unit": "A"}, "origin": "user_entered"},
                   {"name": "sample_resistance", "value": {"value": F(R_ohm), "unit": "Ohm"}, "origin": "user_entered"}]
    return {"id": "paper_fig_physics3d", "name": "synthetic multiphysics probe", "industry": "materials_and_nanotechnology",
            "confirmed": True, "params": params, "requirements": list(reqs),
            "coupled": [{"model": JOULE, "mandatory": True, "origin": "user_entered"}] if joule else []}


def run_lean(cases, tag):
    """cases: list of (configuration_id, catalog-form experiment). Returns list of result dicts (Lean)."""
    pairs, slots = [], []
    for cid, ex in cases:
        cd, ed, info, _ = verifier.build_documents(CAT, ex, cid)
        pairs.append((cd, ed))
        slots.append(next((i["slots"].get("cooling") for i in info if i["model"] == JOULE), None))
    t0 = time.perf_counter()
    res = lean_runner.check_batch(pairs)
    dt = time.perf_counter() - t0
    LEAN_CALLS[tag] += len(pairs)
    print(f"  Lean {tag}: {len(pairs)} checks in {dt:.1f} s")
    out = []
    for r, s in zip(res, slots):
        c = next((c for c in r["coupled_checks"] if c["model"] == JOULE), None)
        rhs = (c or {}).get("rhs") or {}
        rv = rhs.get("value")
        fails = sorted({"/".join(x["keys"]) for x in r["checks"] if x["mandatory"] and x["applicable"] and x["outcome"] == "fail"})
        unk = sorted({"/".join(x["keys"]) for x in r["checks"] if x["mandatory"] and x["applicable"] and x["outcome"] in ("unknown", "unsupported")})
        out.append({"verdict": r["verdict"], "joule_outcome": c["outcome"] if c else None, "slot": s,
                    "p_cool_used_W": fl(F(rv["num"], rv["den"])) if rv else None,
                    "p_cool_used_exact": str(F(rv["num"], rv["den"])) if rv else None,
                    "failed_requirements": fails, "missing_requirements": unk})
    return out, dt


def cap(cid, key):
    return next((c for c in CAT.configurations[cid]["capabilities"] if c["key"] == key), None)


def cooling_points(cid):
    """Sourced cooling-power capabilities of a configuration: (T_doc K, P W | None, install, evidence_status, ids)."""
    pts = []
    for c in CAT.configurations[cid]["capabilities"]:
        if not c["key"].startswith("cooling_power.at_"):
            continue
        at = CAT.vocabulary[c["key"]]["at_temperature"]
        T = units.to_si(at["value"], at["unit"])
        P = units.to_si(c["value"]["q"]["value"], c["value"]["q"]["unit"]) if c["value"].get("kind") == "max" else None
        pts.append({"key": c["key"], "T_K": T, "P_W": P, "install": c["install"], "evidence_status": c["evidence_status"],
                    "evidence_ids": c["evidence_ids"]})
    return sorted(pts, key=lambda p: p["T_K"])


def pow_ticks(ax, axis, lo, hi, step=1, unit=""):
    ks = list(range(int(np.ceil(lo)), int(np.floor(hi)) + 1, step))
    labels = [rf"$10^{{{k}}}$" for k in ks]
    getattr(ax, f"set_{axis}ticks")(ks)
    getattr(ax, f"set_{axis}ticklabels")(labels)


T_LABELS = {-2: "10 mK", -1: "100 mK", 0: "1 K", 1: "10 K", 2: "100 K", 3: "1000 K"}


def temp_ticks(ax, axis, lo, hi):
    ks = [k for k in sorted(T_LABELS) if lo - 1e-9 <= k <= hi + 1e-9]
    getattr(ax, f"set_{axis}ticks")(ks)
    getattr(ax, f"set_{axis}ticklabels")([T_LABELS[k] for k in ks])


def style3d(ax):
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.pane.set_facecolor((1, 1, 1, 0))
        a.pane.set_edgecolor(AXIS)
        a._axinfo["grid"].update(color=GRID, linewidth=0.4)
    ax.tick_params(axis="both", which="major", pad=0, labelsize=6.5)


def verdict_handles(verdicts=VERDICT_ORDER, markers=True):
    hs = []
    for v in verdicts:
        if markers:
            hs.append(Line2D([], [], ls="none", marker=MARK[v], mfc=VERDICT_COLOR[v] if MARK[v] != "x" else "none",
                             mec=VERDICT_COLOR[v] if MARK[v] == "x" else INK, mew=0.6 if MARK[v] != "x" else 1.1, ms=5,
                             label=f"Lean: {VERDICT_LABEL[v]}"))
        else:
            hs.append(Patch(facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white", label=f"Lean: {VERDICT_LABEL[v]}"))
    return hs


def scatter_verdicts(ax, xs, ys, zs, verdicts, s=10, alpha=None, only=None):
    xs, ys, zs = map(np.asarray, (xs, ys, zs))
    verdicts = np.asarray(verdicts)
    for v in VERDICT_ORDER:
        if only and v not in only:
            continue
        m = verdicts == v
        if not m.any():
            continue
        a = alpha.get(v, 1) if isinstance(alpha, dict) else (alpha or 1)
        if MARK[v] == "x":
            ax.scatter(xs[m], ys[m], zs[m], marker="x", c=VERDICT_COLOR[v], s=s * 0.8, linewidths=0.7, alpha=a, depthshade=False)
        else:
            ax.scatter(xs[m], ys[m], zs[m], marker=MARK[v], c=VERDICT_COLOR[v], s=s, edgecolors=INK, linewidths=0.25,
                       alpha=a, depthshade=False)


def plotly_verdict_traces(xs, ys, zs, verdicts, hover, size=4, opacity=None):
    traces = []
    verdicts = np.asarray(verdicts)
    for v in VERDICT_ORDER:
        m = np.where(verdicts == v)[0]
        if not len(m):
            continue
        traces.append(go.Scatter3d(x=np.asarray(xs)[m], y=np.asarray(ys)[m], z=np.asarray(zs)[m], mode="markers",
                                   name=f"Lean: {VERDICT_LABEL[v]}", text=[hover[i] for i in m], hoverinfo="text",
                                   marker=dict(size=size, color=VERDICT_COLOR[v], symbol=PLOTLY_SYM[v],
                                               opacity=(opacity or {}).get(v, 0.9), line=dict(width=0.5, color=INK))))
    return traces


def plotly_log_axis(title, lo, hi, kind="pow"):
    ks = list(range(int(np.ceil(lo)), int(np.floor(hi)) + 1))
    text = [T_LABELS.get(k, f"1e{k}") for k in ks] if kind == "temp" else [f"1e{k}" for k in ks]
    return dict(title=title, tickvals=ks, ticktext=text, range=[lo, hi], backgroundcolor="white", gridcolor=GRID)


# ---------------------------------------------------------------------------------------------- figure 1
FIG1_CFGS = ["bluefors_ld400_hdw", "oxford_optistatdry_tlex", "lakeshore_ccs_400"]
FIG1_SHORT = {"bluefors_ld400_hdw": "Bluefors LD400 (HDW)", "oxford_optistatdry_tlex": "OptistatDry TLEX",
              "lakeshore_ccs_400": "Lake Shore CCS-400"}


def fig_thermal_feasibility():
    print("fig_thermal_feasibility_3d")
    T_grid = nice(range(-2, 3), (1, 2, 5)) + [F(21, 5), F(300)]          # 10 mK .. 500 K, plus 4.2 K and 300 K
    T_grid = sorted(set(T_grid))
    Q_grid = nice(range(-8, 2), (1, 3))                                    # 10 nW .. 30 W
    cases, keys = [], []
    for cid in FIG1_CFGS:
        for T in T_grid:
            for Q in Q_grid:
                cases.append((cid, experiment(T, Q)))
                keys.append((cid, T, Q))
    res, dt = run_lean(cases, "fig1")
    rows = [{"configuration": cid, "T_op_K": fl(T), "T_op_exact": str(T), "Q_W": fl(Q), "Q_exact": str(Q), **r}
            for (cid, T, Q), r in zip(keys, res)]
    # consistency: the cooling power Lean used equals the sourced value of the resolved slot
    src = {cid: {p["key"]: p for p in cooling_points(cid)} for cid in FIG1_CFGS}
    for r in rows:
        if r["p_cool_used_W"] is not None:
            assert abs(r["p_cool_used_W"] - float(src[r["configuration"]][r["slot"]]["P_W"])) < 1e-15
    summary = {}
    for cid in FIG1_CFGS:
        rr = [r for r in rows if r["configuration"] == cid]
        need_T = [r["T_op_K"] for r in rr if r["verdict"] == "NEED_MORE_INFORMATION"]
        summary[cid] = {"verdicts": dict(Counter(r["verdict"] for r in rr)), "n": len(rr),
                        "max_T_need_info_K": max(need_T) if need_T else None,
                        "p_cool_by_T": {str(r["T_op_exact"]): r["p_cool_used_W"] for r in rr if r["Q_W"] == float(Q_grid[0])},
                        "sourced_cooling_points": [{**p, "T_K": str(p["T_K"]), "P_W": str(p["P_W"]) if p["P_W"] is not None else None}
                                                   for p in cooling_points(cid)]}
    dump("fig_thermal_feasibility_3d", {
        "description": "Lean verdicts for a synthetic experiment whose only requirement is the real coupled model "
                       "joule_heating_vs_cooling_power (mandatory), I = 1 mA, R = Q / I^2, swept over (T_op, Q).",
        "configurations": FIG1_CFGS, "T_grid_K": [str(t) for t in T_grid], "Q_grid_W": [str(q) for q in Q_grid],
        "lean_checks": len(rows), "lean_seconds": dt, "summary": summary, "rows": rows})

    # ---------------- static: per configuration, roof z = log10 P_cool(T_doc(T_op)) (sourced, = Lean's rhs),
    # Lean verdict points at height z = Q, Lean verdict map projected on the floor
    xT = np.log10([float(t) for t in T_grid])
    zQ = np.log10([float(q) for q in Q_grid])
    xe = np.r_[xT[0] - (xT[1] - xT[0]) / 2, (xT[:-1] + xT[1:]) / 2, xT[-1] + (xT[-1] - xT[-2]) / 2]
    ye = np.r_[zQ[0] - 0.25, (zQ[:-1] + zQ[1:]) / 2, zQ[-1] + 0.25]
    zfloor = ye[0]
    vmap = {(r["configuration"], r["T_op_exact"], r["Q_exact"]): r["verdict"] for r in rows}
    fig = plt.figure(figsize=(COL2, 2.75))
    for lane, cid in enumerate(FIG1_CFGS):
        ax = fig.add_subplot(1, 3, lane + 1, projection="3d", computed_zorder=False)
        style3d(ax)
        # floor: Lean verdict map (hatched tiles), the 2D projection of the decision
        for v in VERDICT_ORDER:
            sel = [[(xe[i], ye[j], zfloor), (xe[i + 1], ye[j], zfloor), (xe[i + 1], ye[j + 1], zfloor), (xe[i], ye[j + 1], zfloor)]
                   for i, T in enumerate(T_grid) for j, Q in enumerate(Q_grid) if vmap[(cid, str(T), str(Q))] == v]
            if sel:
                ax.add_collection3d(Poly3DCollection(sel, facecolor=VERDICT_COLOR[v], edgecolor="white", linewidths=0.1,
                                                     alpha=0.5, hatch=VERDICT_HATCH[v] or None, zorder=1))
        # roof: sourced cooling power used by the checker (installed, documented, not an estimate -> Lean's rhs)
        pts = cooling_points(cid)
        usable = [p for p in pts if p["install"] == "installed" and p["P_W"] is not None]
        roof_x, roof_z = [], []
        for k, p in enumerate(usable):
            x0 = lg(p["T_K"])
            x1 = lg(usable[k + 1]["T_K"]) if k + 1 < len(usable) else xe[-1]
            z = lg(p["P_W"])
            trusted = p["evidence_status"] != "inferred_estimate"
            quad = [(x0, ye[0], z), (x1, ye[0], z), (x1, ye[-1], z), (x0, ye[-1], z)]
            ax.add_collection3d(Poly3DCollection([quad], facecolor=ICY if trusted else "white", alpha=0.28 if trusted else 0.6,
                                                 edgecolor=NAVY, linewidths=0.7, linestyles="-" if trusted else (0, (2, 1.5)),
                                                 hatch=None if trusted else "....", zorder=3))
            # roof edge at the front (Q axis min) and intersection with the diagonal z = Q (boundary I^2R = P_cool)
            ax.plot([x0, x1], [z, z], [z, z], color=INK, lw=1.3 if trusted else 0.8, ls="-" if trusted else (0, (2, 1.5)), zorder=12)
            ax.plot([x0, x1], [z, z], [zfloor, zfloor], color=INK, lw=0.6, ls=(0, (3, 2)), zorder=4)
        # Lean verdict points at (T_op, Q, z = Q)
        rr = [r for r in rows if r["configuration"] == cid]
        scatter_verdicts(ax, np.log10([r["T_op_K"] for r in rr]), np.log10([r["Q_W"] for r in rr]), np.log10([r["Q_W"] for r in rr]),
                         [r["verdict"] for r in rr], s=4.5)
        ax.set_xlim(xe[0], xe[-1]); ax.set_ylim(ye[0], ye[-1]); ax.set_zlim(zfloor, ye[-1])
        temp_ticks(ax, "x", xe[0], xe[-1])
        ax.set_xticklabels(["10 mK", "", "1 K", "", "100 K"])
        pow_ticks(ax, "y", ye[0], ye[-1], step=3)
        pow_ticks(ax, "z", ye[0], ye[-1], step=3)
        ax.set_xlabel("$T_{op}$", labelpad=-4)
        ax.set_ylabel("$Q=I^2R$ (W)", labelpad=-3)
        ax.set_zlabel("Power (W)" if lane == len(FIG1_CFGS) - 1 else "", labelpad=-5)
        ax.tick_params(axis="both", pad=-2, labelsize=5.8)
        ax.view_init(elev=20, azim=-58)
        ax.set_box_aspect((1.25, 1, 1), zoom=0.98)
        ax.set_title(f"({'abc'[lane]}) {FIG1_SHORT[cid]}", fontsize=7.5, pad=-14)
    hs = verdict_handles() + [
        Patch(facecolor=ICY, alpha=0.4, edgecolor=NAVY, lw=0.7, label=r"Sourced $P_{cool}(T_{doc})$ used by Lean (roof)"),
        Patch(facecolor="white", edgecolor=NAVY, hatch="....", ls="--", lw=0.7, label="Documented only as an estimate (not used)"),
        Line2D([], [], color=INK, lw=0.6, ls=(0, (3, 2)), label=r"Boundary $Q=P_{cool}$ (floor projection)")]
    fig.legend(handles=hs, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0), fontsize=6.3, columnspacing=1.2)
    fig.subplots_adjust(left=0.0, right=0.985, bottom=0.13, top=1.02, wspace=0.08)
    # ---------------- interactive: one configuration at a time (buttons), roof + Lean points
    pf = go.Figure()
    groups = []
    for lane, cid in enumerate(FIG1_CFGS):
        start = len(pf.data)
        vis = lane == 0
        usable = [p for p in cooling_points(cid) if p["install"] == "installed" and p["P_W"] is not None]
        for k, p in enumerate(usable):
            x0 = lg(p["T_K"]); x1 = lg(usable[k + 1]["T_K"]) if k + 1 < len(usable) else xT[-1]
            z = lg(p["P_W"]); trusted = p["evidence_status"] != "inferred_estimate"
            pf.add_trace(go.Surface(x=[[x0, x1], [x0, x1]], y=[[ye[0], ye[0]], [ye[-1], ye[-1]]], z=[[z, z], [z, z]],
                                    showscale=False, opacity=0.35 if trusted else 0.15, visible=vis,
                                    colorscale=[[0, ICY if trusted else MUTED], [1, ICY if trusted else MUTED]],
                                    name=f"P_cool = {units.display(p['P_W'], units.WATT)} @ {units.display(p['T_K'], units.KELVIN)}"
                                         + ("" if trusted else " (estimate, not used)"),
                                    hovertext=f"{p['key']}: {units.display(p['P_W'], units.WATT)} ({p['evidence_status']})", hoverinfo="text"))
        rr = [r for r in rows if r["configuration"] == cid]
        hov = [f"{FIG1_SHORT[cid]}<br>T_op = {r['T_op_K']:g} K<br>Q = {r['Q_W']:g} W<br>Lean: {r['verdict']}<br>"
               f"slot: {r['slot']}<br>P_cool used: {r['p_cool_used_W']}" for r in rr]
        for tr in plotly_verdict_traces(np.log10([r["T_op_K"] for r in rr]), np.log10([r["Q_W"] for r in rr]),
                                        np.log10([r["Q_W"] for r in rr]), [r["verdict"] for r in rr], hov, size=3):
            tr.visible = vis
            pf.add_trace(tr)
        groups.append((start, len(pf.data)))
    pf.update_layout(title="Thermal feasibility of the Joule model: sourced P_cool(T_doc) roof and Lean verdicts at z = Q",
                     updatemenus=[dict(type="buttons", direction="right", x=0.0, y=1.08, buttons=[
                         dict(label=FIG1_SHORT[cid], method="update",
                              args=[{"visible": [a <= i < b for i in range(len(pf.data))]}]) for cid, (a, b) in zip(FIG1_CFGS, groups)])],
                     scene=dict(xaxis=plotly_log_axis("T_op", xT[0], xT[-1], "temp"),
                                yaxis=plotly_log_axis("Q = I^2 R (W)", ye[0], ye[-1]),
                                zaxis=plotly_log_axis("power (W)", ye[0], ye[-1])))
    html = save_html(pf, "fig_thermal_feasibility_3d")

    s = summary
    save(fig, "fig_thermal_feasibility_3d", interactive=html, meta=dict(
        title="Thermal feasibility of a Joule-heated measurement over operating temperature and heat load",
        question="For a given operating temperature and dissipated power, does the documented cooling power of a real "
                 "cryostat suffice, and where does the documentation not allow a decision?",
        model="joule_heating_vs_cooling_power: I^2 R <= P_cool(T_doc), valid when T_doc <= T_op, with T_doc the highest "
              "documented, installed, non-unknown cooling-power temperature not above T_op (serialize.resolve_slots).",
        data=f"{len(rows)} Lean checks (check_batch, {dt:.1f} s): 3 configurations x {len(T_grid)} T_op x {len(Q_grid)} Q; "
             "I = 1 mA, R = Q/I^2 (exact rationals). Cooling-power values from data/cryostats (bluefors_ld.json, "
             "oxford_optistatdry.json, lakeshore_janis_ccs.json) via the catalog. paper/data/fig_thermal_feasibility_3d.json.",
        claim="COMPUTED+SOURCED",
        caption="For each configuration the translucent roof is the sourced cooling power P_cool(T_doc) at the highest "
                "documented temperature not above T_op, the conservative value the checker uses; markers are Lean checker "
                "verdicts, placed at height Q, for a synthetic experiment whose only mandatory requirement is the "
                "Joule-heating coupled model, and the floor repeats the verdict map. Below the lowest documented "
                "temperature, and where the only value is an estimate (OptistatDry TLEX, 4.2-5 K), the checker answers "
                "Need more information. Verdicts are computed; cooling powers are sourced manufacturer specifications.",
        section="main"))
    return summary, rows


# ---------------------------------------------------------------------------------------------- figure 2
FIG2_CFG = "bluefors_ld400_hdw"
FIG2_TOPS = [F(20, 1000), F(100, 1000)]


def fig_joule_surface():
    print("fig_joule_surface_3d")
    I_grid = nice(range(-6, -1), (1, 3)) + [F(1, 100)]               # 1 uA .. 10 mA
    R_grid = nice(range(-2, 5), (1, 3)) + [F(10) ** 5]               # 10 mOhm .. 100 kOhm
    cases, keys = [], []
    for T in FIG2_TOPS:
        for I in I_grid:
            for R in R_grid:
                cases.append((FIG2_CFG, experiment(T, I_A=I, R_ohm=R)))
                keys.append((T, I, R))
    res, dt = run_lean(cases, "fig2")
    rows = [{"T_op_K": fl(T), "I_A": fl(I), "R_ohm": fl(R), "P_W": fl(I * I * R), "P_exact": str(I * I * R), **r}
            for (T, I, R), r in zip(keys, res)]
    pc = {str(T): next(r["p_cool_used_W"] for r in rows if r["T_op_K"] == float(T)) for T in FIG2_TOPS}
    # agreement of Lean verdicts with the analytic boundary (reported, not used to classify)
    pcx = {str(T): F(next(r["p_cool_used_exact"] for r in rows if r["T_op_K"] == float(T))) for T in FIG2_TOPS}
    agree = sum((r["verdict"] == "REQUIREMENTS_MET") == (F(r["P_exact"]) <= pcx[str(T)]) for (T, _, _), r in zip(keys, rows))
    summ = {str(T): dict(Counter(r["verdict"] for r in rows if r["T_op_K"] == float(T))) for T in FIG2_TOPS}
    global pcx_g
    pcx_g = pcx
    dump("fig_joule_surface_3d", {"configuration": FIG2_CFG, "T_op_K": [str(t) for t in FIG2_TOPS], "p_cool_used_W": pc,
                                  "I_grid_A": [str(x) for x in I_grid], "R_grid_ohm": [str(x) for x in R_grid],
                                  "lean_checks": len(rows), "lean_seconds": dt, "verdicts": summ,
                                  "lean_agrees_with_analytic_boundary": agree, "rows": rows})

    li = np.linspace(-6, -2, 60)
    lr = np.linspace(-2, 5, 60)
    LI, LR = np.meshgrid(li, lr)
    LP = 2 * LI + LR
    fig = plt.figure(figsize=(COL2, 3.5))
    norm = plt.Normalize(-6, 6)
    for k, T in enumerate(FIG2_TOPS):
        P = pc[str(T)]
        ax = fig.add_subplot(1, 2, k + 1, projection="3d", computed_zorder=False)
        style3d(ax)
        margin = np.log10(P) - LP                                         # decades of slack (+) / overload (-)
        ax.plot_surface(LI, LR, LP, facecolors=DIV_CMAP(norm(np.clip(margin, -6, 6))), rstride=2, cstride=2,
                        linewidth=0, antialiased=True, shade=False, alpha=0.75, zorder=1)
        # cooling-capacity plane
        gi, gr = np.meshgrid([li[0], li[-1]], [lr[0], lr[-1]])
        ax.plot_surface(gi, gr, np.full_like(gi, np.log10(P)), color=ICY, alpha=0.18, linewidth=0, shade=False, zorder=2)
        ax.plot([li[0], li[-1], li[-1], li[0], li[0]], [lr[0], lr[0], lr[-1], lr[-1], lr[0]], [np.log10(P)] * 5,
                color=NAVY, lw=0.5, zorder=3)
        # analytic intersection I^2 R = P_cool
        rr = np.linspace(lr[0], lr[-1], 200)
        ii = 0.5 * (np.log10(P) - rr)
        m = (ii >= li[0]) & (ii <= li[-1])
        ax.plot(ii[m], rr[m], np.full(m.sum(), np.log10(P)), color=INK, lw=1.6, zorder=10)
        ax.plot(ii[m], rr[m], np.full(m.sum(), -14), color=INK, lw=0.8, ls=(0, (3, 2)), zorder=4)   # floor projection
        # Lean verdicts at sampled grid points (on the surface)
        rk = [r for r in rows if r["T_op_K"] == float(T)]
        scatter_verdicts(ax, np.log10([r["I_A"] for r in rk]), np.log10([r["R_ohm"] for r in rk]),
                         np.log10([r["P_W"] for r in rk]), [r["verdict"] for r in rk], s=9)
        ax.set_xlim(li[0], li[-1]); ax.set_ylim(lr[0], lr[-1]); ax.set_zlim(-14, 1)
        ax.set_xticks(range(-6, -1)); ax.set_xticklabels(["1 µA", "10 µA", "100 µA", "1 mA", "10 mA"])
        ax.set_yticks(range(-2, 6)); ax.set_yticklabels(["", "", "1 Ω", "", "100 Ω", "", "10 kΩ", ""])
        pow_ticks(ax, "z", -14, 1, step=3)
        ax.set_xlabel("Current $I$", labelpad=0)
        ax.set_ylabel("Resistance $R$", labelpad=0)
        ax.set_zlabel("$P=I^2R$ (W)", labelpad=-1)
        ax.view_init(elev=18, azim=-128)
        ax.set_box_aspect((1, 1.1, 0.95), zoom=0.9)
        slot = next(r["slot"] for r in rk)
        ax.set_title(f"({'ab'[k]}) $T_{{op}}$ = {units.display(T, units.KELVIN)}: plane $P_{{cool}}$ = "
                     f"{units.display(pcx_g[str(T)], units.WATT)}\n(slot {slot})", fontsize=7.5, pad=-2)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=DIV_CMAP)
    cax = fig.add_axes([0.36, 0.06, 0.28, 0.025])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label(r"Margin $\log_{10}(P_{cool}/I^2R)$ (decades; < 0 overloaded)", fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    cb.outline.set_linewidth(0.4)
    hs = verdict_handles(["REQUIREMENTS_MET", "DOES_NOT_MEET_REQUIREMENTS"]) + [
        Line2D([], [], color=INK, lw=1.6, label=r"Analytic $I^2R = P_{cool}$"),
        Patch(facecolor=ICY, alpha=0.3, edgecolor=NAVY, lw=0.5, label="Documented cooling power plane")]
    fig.legend(handles=hs, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.11), fontsize=6.5)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.18, top=0.95, wspace=0.02)

    # interactive
    pf = go.Figure()
    for k, T in enumerate(FIG2_TOPS):
        P = pc[str(T)]
        vis = k == 1
        margin = np.log10(P) - LP
        pf.add_trace(go.Surface(x=LI, y=LR, z=LP, surfacecolor=np.clip(margin, -6, 6), cmin=-6, cmax=6,
                                colorscale=[[0, ORANGE], [0.5, "#f0efec"], [1, NAVY]], opacity=0.8, visible=vis,
                                colorbar=dict(title="margin (decades)", len=0.6), name=f"I^2R surface (T_op={units.display(T, units.KELVIN)})",
                                hovertemplate="log10 I=%{x:.2f}<br>log10 R=%{y:.2f}<br>log10 P=%{z:.2f}<extra></extra>"))
        pf.add_trace(go.Surface(x=[[li[0], li[-1]], [li[0], li[-1]]], y=[[lr[0], lr[0]], [lr[-1], lr[-1]]],
                                z=[[np.log10(P)] * 2] * 2, showscale=False, opacity=0.3, colorscale=[[0, ICY], [1, ICY]],
                                visible=vis, name=f"P_cool = {units.display(pcx_g[str(T)], units.WATT)}"))
        rr = np.linspace(lr[0], lr[-1], 200); ii = 0.5 * (np.log10(P) - rr); m = (ii >= li[0]) & (ii <= li[-1])
        pf.add_trace(go.Scatter3d(x=ii[m], y=rr[m], z=np.full(m.sum(), np.log10(P)), mode="lines", visible=vis,
                                  line=dict(color=INK, width=6), name="analytic I^2R = P_cool"))
        rk = [r for r in rows if r["T_op_K"] == float(T)]
        hov = [f"I = {units.display(F(str(r['I_A'])), units.AMPERE)}, R = {r['R_ohm']:g} Ohm<br>P = {r['P_W']:.3g} W<br>Lean: {r['verdict']}" for r in rk]
        for tr in plotly_verdict_traces(np.log10([r["I_A"] for r in rk]), np.log10([r["R_ohm"] for r in rk]),
                                        np.log10([r["P_W"] for r in rk]), [r["verdict"] for r in rk], hov):
            tr.visible = vis
            pf.add_trace(tr)
    ntr = len(pf.data) // 2
    pf.update_layout(
        title=f"Joule heating P = I^2 R vs documented cooling power, {FIG2_CFG}",
        updatemenus=[dict(type="buttons", direction="right", x=0.0, y=1.08, buttons=[
            dict(label=f"T_op = {units.display(T, units.KELVIN)}", method="update",
                 args=[{"visible": [i // ntr == k for i in range(len(pf.data))]}]) for k, T in enumerate(FIG2_TOPS)])],
        scene=dict(xaxis=plotly_log_axis("current I (A)", -6, -2), yaxis=plotly_log_axis("resistance R (Ohm)", -2, 5),
                   zaxis=plotly_log_axis("P = I^2 R (W)", -14, 1)))
    html = save_html(pf, "fig_joule_surface_3d")
    save(fig, "fig_joule_surface_3d", interactive=html, meta=dict(
        title="Joule heating surface against the documented cooling power of a dilution refrigerator",
        question="Which combinations of excitation current and sample resistance keep the Joule heating within the "
                 "documented mixing-chamber cooling power, and does the checker's verdict follow the physical boundary?",
        model="P = I^2 R (exact) against P_cool(T_doc) of the joule_heating_vs_cooling_power model; analytic boundary "
              "I = sqrt(P_cool / R).",
        data=f"{len(rows)} Lean checks (check_batch, {dt:.1f} s) for {FIG2_CFG} at T_op = 20 mK and 100 mK on a "
             f"{len(I_grid)} x {len(R_grid)} (I, R) grid; cooling power 12 uW @ 20 mK and 400 uW @ 100 mK from "
             "data/cryostats/bluefors_ld.json. paper/data/fig_joule_surface_3d.json.",
        claim="COMPUTED+MODELED+SOURCED",
        caption="The surface is the Joule power P = I^2R over current and sample resistance (log axes), coloured by the "
                "margin to the documented cooling power of a Bluefors LD400 at 20 mK (a) and 100 mK (b), which is drawn as "
                "a horizontal plane. The black curve is the analytic intersection I^2R = P_cool (model overlay, projected "
                "on the floor). Markers are Lean checker verdicts of the Joule coupled model at sampled (I, R) points; "
                f"all {agree} of {len(rows)} sampled verdicts agree with the analytic boundary.",
        section="supplement"))
    return pc, summ, agree, len(rows)


# ---------------------------------------------------------------------------------------------- figure 3
FIG3 = {"lakeshore_crx_vf": {"short": "Lake Shore CRX-VF", "B": [F(k, 2) for k in range(0, 9)]},
        "qd_dynacool_9T_eto_res": {"short": "QD PPMS DynaCool 9 T (ETO)", "B": [F(k) for k in range(0, 11)]}}


def fig_compat_region():
    print("fig_compat_region_3d")
    T_grid = sorted(set(nice(range(0, 3), (1, 2, 5)) + [F(9, 5), F(15), F(300), F(400), F(420), F(500)]))   # 1 K .. 500 K, incl. both envelope edges
    Q_grid = nice(range(-3, 1), (1, 2, 5)) + [F(2), F(5)]                                     # 1 mW .. 5 W
    cases, keys = [], []
    for cid, spec in FIG3.items():
        for T in T_grid:
            for B in spec["B"]:
                for Q in Q_grid:
                    reqs = [{"key": "temperature.range", "constraint": {"kind": "point_within", "q": {"value": T, "unit": "K"}},
                             "mandatory": True, "origin": "user_entered"},
                            {"key": "magnetic_field.max", "constraint": {"kind": "at_least", "q": {"value": B, "unit": "T"}},
                             "mandatory": True, "origin": "user_entered"}]
                    cases.append((cid, experiment(T, Q, reqs)))
                    keys.append((cid, T, B, Q))
    res, dt = run_lean(cases, "fig3")
    rows = [{"configuration": cid, "T_K": fl(T), "B_T": fl(B), "Q_W": fl(Q), **r} for (cid, T, B, Q), r in zip(keys, res)]
    summ = {}
    for cid in FIG3:
        rr = [r for r in rows if r["configuration"] == cid]
        met = [r for r in rr if r["verdict"] == "REQUIREMENTS_MET"]
        need = [r for r in rr if r["verdict"] == "NEED_MORE_INFORMATION"]
        summ[cid] = {"n": len(rr), "verdicts": dict(Counter(r["verdict"] for r in rr)),
                     "met_T_range_K": [min(r["T_K"] for r in met), max(r["T_K"] for r in met)] if met else None,
                     "met_B_max_T": max(r["B_T"] for r in met) if met else None,
                     "met_Q_max_W": max(r["Q_W"] for r in met) if met else None,
                     "need_info_reasons": dict(Counter(tuple(r["missing_requirements"]) + (("joule:" + str(r["joule_outcome"])),)
                                                       for r in need).most_common(4)) if need else {},
                     "need_T_range_K": [min(r["T_K"] for r in need), max(r["T_K"] for r in need)] if need else None,
                     "need_B_max_T": max(r["B_T"] for r in need) if need else None}
        summ[cid]["need_info_reasons"] = {" + ".join(k): v for k, v in summ[cid]["need_info_reasons"].items()}
    env = {}
    for cid in FIG3:
        tr, bm = cap(cid, "temperature.range"), cap(cid, "magnetic_field.max")
        cps = [p for p in cooling_points(cid) if p["install"] == "installed" and p["P_W"] is not None]
        env[cid] = {"T_lo_K": units.to_si(tr["value"]["lo"]["value"], tr["value"]["lo"]["unit"]),
                    "T_hi_K": units.to_si(tr["value"]["hi"]["value"], tr["value"]["hi"]["unit"]),
                    "B_max_T": units.to_si(bm["value"]["q"]["value"], bm["value"]["q"]["unit"]),
                    "cooling": [(p["T_K"], p["P_W"]) for p in cps],
                    "evidence_ids": sorted(set(tr["evidence_ids"] + bm["evidence_ids"] + [i for p in cps for i in p["evidence_ids"]]))}
    dump("fig_compat_region_3d", {
        "description": "Synthetic experiment: mandatory temperature.range point_within T, magnetic_field.max at_least B, "
                       "and the real joule_heating_vs_cooling_power model (mandatory, T_op = T, I = 1 mA, R = Q/I^2).",
        "T_grid_K": [str(t) for t in T_grid], "Q_grid_W": [str(q) for q in Q_grid],
        "B_grid_T": {cid: [str(b) for b in s["B"]] for cid, s in FIG3.items()},
        "envelopes_sourced": {cid: {k: (str(v) if isinstance(v, F) else [(str(a), str(b)) for a, b in v] if k == "cooling" else v)
                                    for k, v in e.items()} for cid, e in env.items()},
        "lean_checks": len(rows), "lean_seconds": dt, "summary": summ, "rows": rows})

    fig = plt.figure(figsize=(COL2, 3.2))
    qlo, qhi = lg(Q_grid[0]) - 0.15, lg(Q_grid[-1]) + 0.15
    tlo, thi = 0 - 0.08, lg(500) + 0.08
    for k, (cid, spec) in enumerate(FIG3.items()):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d", computed_zorder=False)
        style3d(ax)
        rr = [r for r in rows if r["configuration"] == cid]
        e = env[cid]
        bhi = float(spec["B"][-1])
        # analytic box from the sourced envelope (model overlay): T in [lo, hi], B <= Bmax, Q <= P_cool (if documented)
        x0, x1 = lg(e["T_lo_K"]), lg(e["T_hi_K"])
        y1 = float(e["B_max_T"])
        z1 = lg(e["cooling"][0][1]) if e["cooling"] else qhi
        col = VERDICT_COLOR["REQUIREMENTS_MET"] if e["cooling"] else VERDICT_COLOR["NEED_MORE_INFORMATION"]
        V = np.array([[x0, 0, qlo], [x1, 0, qlo], [x1, y1, qlo], [x0, y1, qlo], [x0, 0, z1], [x1, 0, z1], [x1, y1, z1], [x0, y1, z1]])
        faces = [[V[i] for i in f] for f in ([0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4])]
        ax.add_collection3d(Poly3DCollection(faces, facecolor=col, alpha=0.10, edgecolor="none", zorder=1))
        for a_, b_ in ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)):
            ax.plot(*zip(V[a_], V[b_]), color=INK, lw=0.8, zorder=15)
        # Lean verdicts: MET / NEED INFO prominent, NOT MET faint
        scatter_verdicts(ax, np.log10([r["T_K"] for r in rr]), [r["B_T"] for r in rr], np.log10([r["Q_W"] for r in rr]),
                         [r["verdict"] for r in rr], s=5,
                         alpha={"REQUIREMENTS_MET": 0.9, "NEED_MORE_INFORMATION": 0.75, "DOES_NOT_MEET_REQUIREMENTS": 0.12})
        ax.set_yticks([0, 1, 2.5, 4] if bhi < 5 else [0, 3, 6, 9])
        ax.set_xlim(tlo, thi); ax.set_ylim(0, bhi); ax.set_zlim(qlo, qhi)
        temp_ticks(ax, "x", tlo, thi)
        pow_ticks(ax, "z", qlo, qhi)
        ax.set_xlabel("Temperature $T$", labelpad=0)
        ax.set_ylabel("Field $B$ (T)", labelpad=0)
        ax.set_zlabel("Heat load $Q$ (W)", labelpad=-1)
        ax.view_init(elev=20, azim=-57)
        ax.set_box_aspect((1.25, 1, 0.9), zoom=0.98)
        cool = ", ".join(f"{units.display(p, units.WATT)} @ {units.display(t, units.KELVIN)}" for t, p in e["cooling"]) or "not documented"
        ax.set_title(f"({'ab'[k]}) {spec['short']}\n{units.display(e['T_lo_K'], units.KELVIN)}–{units.display(e['T_hi_K'], units.KELVIN)}, "
                     f"{units.display(e['B_max_T'], units.TESLA)}; cooling {cool}", fontsize=7.2, pad=-12)
    hs = verdict_handles() + [Patch(facecolor="none", edgecolor=INK, lw=0.6, label="Sourced envelope box (overlay)")]
    fig.legend(handles=hs, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.0), fontsize=6.5)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.07, top=1.0, wspace=0.0)

    pf = go.Figure()
    for k, (cid, spec) in enumerate(FIG3.items()):
        rr = [r for r in rows if r["configuration"] == cid]
        vis = k == 0
        hov = [f"{spec['short']}<br>T = {r['T_K']:g} K, B = {r['B_T']:g} T, Q = {r['Q_W']:g} W<br>Lean: {r['verdict']}"
               f"<br>failed: {', '.join(r['failed_requirements']) or '-'}<br>joule: {r['joule_outcome']}" for r in rr]
        for tr in plotly_verdict_traces(np.log10([r["T_K"] for r in rr]), [r["B_T"] for r in rr], np.log10([r["Q_W"] for r in rr]),
                                        [r["verdict"] for r in rr], hov, size=3,
                                        opacity={"REQUIREMENTS_MET": 0.9, "NEED_MORE_INFORMATION": 0.8, "DOES_NOT_MEET_REQUIREMENTS": 0.12}):
            tr.visible = vis
            pf.add_trace(tr)
    n_per = [len({r["verdict"] for r in rows if r["configuration"] == cid}) for cid in FIG3]
    vis_masks = []
    for k in range(len(FIG3)):
        vis_masks.append([i >= sum(n_per[:k]) and i < sum(n_per[:k + 1]) for i in range(sum(n_per))])
    pf.update_layout(title="Compatibility region over (T, B, Q): Lean verdicts",
                     updatemenus=[dict(type="buttons", direction="right", x=0.0, y=1.08, buttons=[
                         dict(label=spec["short"], method="update", args=[{"visible": vis_masks[k]}]) for k, spec in enumerate(FIG3.values())])],
                     scene=dict(xaxis=plotly_log_axis("temperature", 0, lg(500), "temp"), yaxis=dict(title="field B (T)"),
                                zaxis=plotly_log_axis("heat load Q (W)", qlo, qhi)))
    html = save_html(pf, "fig_compat_region_3d")
    save(fig, "fig_compat_region_3d", interactive=html, meta=dict(
        title="Three-dimensional compatibility region over temperature, magnetic field and heat load",
        question="What region of (temperature, field, heat load) can a real configuration certify, and where does missing "
                 "documentation turn the answer into Need more information rather than a pass or a fail?",
        model="Mandatory requirements temperature.range point_within T and magnetic_field.max at_least B, plus the "
              "joule_heating_vs_cooling_power coupled model (I^2 R = Q <= P_cool(T_doc), T_doc <= T_op = T).",
        data=f"{len(rows)} Lean checks (check_batch, {dt:.1f} s): {len(T_grid)} T x 9 or 11 B x {len(Q_grid)} Q for "
             "lakeshore_crx_vf and qd_dynacool_9T_eto_res; envelopes from data/cryostats/lakeshore_crx.json and "
             "qd_ppms_dynacool.json. paper/data/fig_compat_region_3d.json.",
        claim="COMPUTED+SOURCED",
        caption="Markers are Lean checker verdicts on a (T, B, Q) grid for a synthetic experiment requiring temperature T, "
                "field B and the Joule-heating model with heat load Q; non-passing points are drawn faint. The box is the "
                "sourced envelope (temperature range, maximum field and, where documented, cooling power), drawn as an "
                "overlay. For the CRX-VF (a) the certified volume is bounded by 10-420 K, 2.5 T and the 1 W cooling power at "
                "4.2 K; for the DynaCool (b), whose cooling power is not documented, every point inside the envelope is "
                "Need more information.",
        section="main"))
    return summ


# ---------------------------------------------------------------------------------------------- figure 4
FAMILY_SHORT = {"bluefors_ld": "Bluefors LD (dilution)", "lakeshore_janis_ccs": "Lake Shore CCS (optical CCR)",
                "lakeshore_crx": "Lake Shore CRX (probe station)", "linkam_thms600": "Linkam THMS600 (LN2 stage)",
                "oxford_optistatdry": "Oxford OptistatDry (optical)", "oxford_teslatronpt": "Oxford TeslatronPT (magnet)",
                "qd_ppms_dynacool": "QD PPMS DynaCool", "qd_ppms_classic": "QD PPMS classic (LHe)",
                "leica_cm1950": "Leica CM1950 (cryotome)"}
EXP_SHORT = {"bio_cryo_fluorescence_vitrified": "cryo-fluorescence", "bio_cryosection_frozen_tissue": "cryosection",
             "chem_low_temperature_raman": "LT Raman", "chem_phase_transition_pom": "phase transition POM",
             "chem_temperature_dependent_photoluminescence": "T-dependent PL",
             "mat_electrical_resistance_low_temperature": "resistance 2-300 K", "mat_magnetometry_vsm": "VSM magnetometry",
             "mat_magnetoresistance_10T": "magnetoresistance 10 T", "quantum_mk_vector_field_transport": "mK vector-field transport",
             "quantum_mxc_wiring_heat_budget": "MXC wiring budget", "quantum_transmon_characterization": "transmon"}


def _q(c):
    return units.to_si(c["value"], c["unit"])


def fig_operating_envelope():
    print("fig_operating_envelope_3d")
    e1 = load("e1_grid")
    met_by_cfg = Counter(r["configuration"] for r in e1["rows"] if r["verdict"] == "REQUIREMENTS_MET")
    cfgs, excluded = [], []
    for cid, cfg in sorted(CAT.configurations.items()):
        tr, bm = cap(cid, "temperature.range"), cap(cid, "magnetic_field.max")
        if not tr or tr["value"].get("kind") != "range":
            excluded.append({"configuration": cid, "reason": "temperature.range not documented"})
            continue
        b = None
        if bm and bm["value"].get("kind") == "max":
            b = _q(bm["value"]["q"])
        cfgs.append({"configuration": cid, "family": cfg["equipment_id"], "name": cfg.get("name"),
                     "T_lo_K": _q(tr["value"]["lo"]), "T_hi_K": _q(tr["value"]["hi"]), "T_evidence_status": tr["evidence_status"],
                     "B_max_T": b, "B_install": bm["install"] if bm else None, "B_evidence_status": bm["evidence_status"] if bm else None,
                     "evidence_ids": sorted(set(tr["evidence_ids"] + (bm["evidence_ids"] if bm else []))),
                     "e1_met_count": met_by_cfg.get(cid, 0)})
    fams = sorted({c["family"] for c in cfgs}, key=lambda f: (max(float(c["B_max_T"] or 0) for c in cfgs if c["family"] == f),
                                                             min(float(c["T_lo_K"]) for c in cfgs if c["family"] == f)))
    fam_z = {f: i for i, f in enumerate(fams)}
    # experiment needs (temperature + field) from the profiles' mandatory requirements
    needs = []
    for eid, ex in sorted(CAT.experiments.items()):
        t_lo = t_hi = None; tkind = tkey = None; b = F(0); bkind = "none"
        for r in ex["requirements"]:
            if not r.get("mandatory"):
                continue
            k = (r.get("keys") or [r["key"]])[0]
            c = r["constraint"]
            if k.startswith("temperature") and not k.startswith("temperature.sweep") and t_lo is None:
                tkey, tkind = k, c["kind"]
                if c["kind"] == "range_within":
                    t_lo, t_hi = _q(c["lo"]), _q(c["hi"])
                else:
                    t_lo = t_hi = _q(c["q"])
            if k == "magnetic_field.max" and c["kind"] == "at_least":
                b, bkind = _q(c["q"]), "at_least"
        if t_lo is not None:
            needs.append({"experiment": eid, "label": EXP_SHORT.get(eid, eid), "temperature_key": tkey, "temperature_kind": tkind,
                          "T_lo_K": t_lo, "T_hi_K": t_hi, "B_T": b, "field_kind": bkind,
                          "e1_met_count": sum(1 for r in e1["rows"] if r["experiment"] == eid and r["verdict"] == "REQUIREMENTS_MET")})
    dump("fig_operating_envelope_3d", {
        "configurations": [{k: (str(v) if isinstance(v, F) else v) for k, v in c.items()} for c in cfgs],
        "excluded": excluded, "families": fams,
        "experiment_needs": [{k: (str(v) if isinstance(v, F) else v) for k, v in n.items()} for n in needs],
        "note": "Geometry only (sourced values). e1_met_count is copied from paper/data/e1_grid.json (Lean verdicts)."})

    # upright walls: x = log10 T, y = family (depth), z = field. Families ordered front -> back by max field.
    fig = plt.figure(figsize=(COL2, 3.7))
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    style3d(ax)
    ref_unknown = 0.5         # height of the strip drawn when the field is not documented
    y_need = -1.2             # experiment needs on a front wall
    for c in cfgs:
        y = fam_z[c["family"]]
        x0, x1 = lg(c["T_lo_K"]), lg(c["T_hi_K"])
        est = c["T_evidence_status"] == "inferred_estimate"
        if c["B_max_T"] is not None:
            h = float(c["B_max_T"])
            installed = c["B_install"] == "installed"
            poly = [(x0, y, 0), (x1, y, 0), (x1, y, h), (x0, y, h)]
            ax.add_collection3d(Poly3DCollection([poly], facecolor=NAVY if installed else "none", alpha=0.13 if installed else 1,
                                                 edgecolor="none", zorder=2 + y))
            ax.plot([x0, x0, x1, x1], [y] * 4, [0, h, h, 0], color=NAVY, lw=0.8, zorder=3 + y,
                    ls="-" if installed else (0, (3, 2)))
            ax.text(x0 - 0.05, y, h, f"{h:g} T" + ("" if installed else " (option, not installed)"), fontsize=5.4,
                    color=INK2, ha="right", va="center", zorder=40)
        else:
            poly = [(x0, y, 0), (x1, y, 0), (x1, y, ref_unknown), (x0, y, ref_unknown)]
            ax.add_collection3d(Poly3DCollection([poly], facecolor="white", edgecolor=MUTED, hatch="//////", linewidths=0.5,
                                                 zorder=2 + y))
        ax.plot([x0, x1], [y, y], [0, 0], color=NAVY, lw=1.8, zorder=4 + y, ls=(0, (2, 1)) if est else "-")
    for n in needs:
        x0, x1 = lg(n["T_lo_K"]), lg(n["T_hi_K"])
        z = float(n["B_T"])
        if x1 > x0:
            ax.plot([x0, x1], [y_need, y_need], [z, z], color=ORANGE, lw=2.0, zorder=50, solid_capstyle="butt")
        mk = "<" if n["temperature_kind"] == "at_most" else "o"
        ax.scatter([x0], [y_need], [z], marker=mk, s=13, c=ORANGE, edgecolors=INK, linewidths=0.3, depthshade=False, zorder=51)
        if z > 0:
            if x1 > x0:     # range need: label after the segment's right end
                ax.text(x0 - 0.12, y_need, z - 0.4, f"{n['label']} (≥ {z:g} T)", fontsize=5.4, color=INK2, ha="right", va="top", zorder=60)
            else:           # point need: label to the left of the marker
                ax.text(x0 - 0.15, y_need, z + 0.6, f"{n['label']} (≥ {z:g} T)", fontsize=5.4, color=INK2, ha="right", va="bottom", zorder=60)
        ax.plot([x0, x0], [y_need, len(fams) - 0.5], [z, z], color=ORANGE, lw=0.5, alpha=0.45, ls=(0, (1, 2)), zorder=1)
    ax.set_xlim(-2.3, 3.1); ax.set_ylim(y_need - 0.3, len(fams) - 0.5); ax.set_zlim(0, 17)
    temp_ticks(ax, "x", -2.3, 3.1)
    ax.set_yticks([y_need] + list(range(len(fams))))
    ax.set_yticklabels(["experiment needs"] + [FAMILY_SHORT.get(f, f) for f in fams], fontsize=5.6)
    for lab in ax.get_yticklabels():
        lab.set_horizontalalignment("left")
    ax.set_zticks([0, 2.5, 6, 9, 12, 16])
    ax.set_zlabel("Maximum field $B_{max}$ (T)", labelpad=-2)
    ax.set_xlabel("Temperature range (log)", labelpad=0)
    ax.view_init(elev=16, azim=-56)
    ax.set_box_aspect((2.3, 2.0, 1.2), zoom=1.05)
    hs = [Patch(facecolor=NAVY, alpha=0.3, edgecolor=NAVY, label="Sourced T range x field (magnet installed)"),
          Patch(facecolor="none", edgecolor=NAVY, ls="--", label="Field of an optional magnet, not installed"),
          Patch(facecolor="white", edgecolor=MUTED, hatch="//////", label="Field not documented (strip)"),
          Line2D([], [], color=NAVY, lw=1.6, ls=(0, (2, 1)), label="T range documented only as an estimate"),
          Line2D([], [], color=ORANGE, lw=2.0, marker="o", mfc=ORANGE, mec=INK, mew=0.3, ms=4,
                 label="Experiment need: T range or point, at field (front wall)"),
          Line2D([], [], ls="none", marker="<", mfc=ORANGE, mec=INK, mew=0.3, ms=4, label="Experiment need: T at most (base temperature)")]
    fig.legend(handles=hs, loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=2, fontsize=6.3)
    fig.subplots_adjust(left=0.0, right=0.97, bottom=0.0, top=1.0)
    pf = go.Figure()
    for c in cfgs:
        y = fam_z[c["family"]]
        x0, x1 = lg(c["T_lo_K"]), lg(c["T_hi_K"])
        known = c["B_max_T"] is not None
        h = float(c["B_max_T"]) if known else ref_unknown
        inst = known and c["B_install"] == "installed"
        hov = (f"{c['configuration']}<br>{c['name']}<br>T: {units.display(c['T_lo_K'], units.KELVIN)} - {units.display(c['T_hi_K'], units.KELVIN)}"
               f" ({c['T_evidence_status']})<br>B max: {units.display(c['B_max_T'], units.TESLA) if known else 'not documented'}"
               f" ({c['B_install']})<br>experiments met (E1 grid, Lean): {c['e1_met_count']}")
        pf.add_trace(go.Mesh3d(x=[x0, x1, x1, x0], y=[y] * 4, z=[0, 0, h, h], i=[0, 0], j=[1, 2], k=[2, 3],
                               color=NAVY if inst else MUTED, opacity=0.22 if inst else 0.12,
                               hovertext=hov, hoverinfo="text", name=c["configuration"], showlegend=False))
        pf.add_trace(go.Scatter3d(x=[x0, x0, x1, x1, x0], y=[y] * 5, z=[0, h, h, 0, 0], mode="lines",
                                  line=dict(color=NAVY if known else MUTED, width=3, dash="solid" if inst else "dash"),
                                  hovertext=hov, hoverinfo="text", showlegend=False))
    for n in needs:
        x0, x1 = lg(n["T_lo_K"]), lg(n["T_hi_K"])
        z = float(n["B_T"])
        hov = (f"{n['experiment']}<br>T ({n['temperature_key']}, {n['temperature_kind']}): {units.display(n['T_lo_K'], units.KELVIN)}"
               f"{' - ' + units.display(n['T_hi_K'], units.KELVIN) if x1 > x0 else ''}<br>B at least: {units.display(n['B_T'], units.TESLA)}"
               f"<br>configurations met (E1 grid, Lean): {n['e1_met_count']}")
        xs = [x0, x1] if x1 > x0 else [x0]
        pf.add_trace(go.Scatter3d(x=xs, y=[y_need] * len(xs), z=[z] * len(xs), mode="lines+markers+text",
                                  text=[n["label"]] + [""] * (len(xs) - 1), textposition="top center",
                                  line=dict(color=ORANGE, width=7), marker=dict(size=4, color=ORANGE), hovertext=hov,
                                  hoverinfo="text", showlegend=False))
    pf.update_layout(title="Sourced temperature-field operating envelopes and experiment needs",
                     scene=dict(xaxis=plotly_log_axis("temperature", -2.3, 3.1, "temp"),
                                yaxis=dict(title="", tickvals=list(range(len(fams))) + [y_need],
                                           ticktext=[FAMILY_SHORT.get(f, f) for f in fams] + ["experiment needs"]),
                                zaxis=dict(title="B max (T)"), aspectmode="manual", aspectratio=dict(x=2, y=1.6, z=1)))
    html = save_html(pf, "fig_operating_envelope_3d")
    nB = sum(1 for c in cfgs if c["B_max_T"] is not None)
    save(fig, "fig_operating_envelope_3d", interactive=html, meta=dict(
        title="Sourced temperature-field operating envelopes of all catalogued configurations",
        question="How do the documented temperature ranges and maximum fields of the catalogued cryostats cover what the "
                 "experiment profiles need, and where is the field simply not documented?",
        model="Geometry only: rectangle [T_lo, T_hi] x [0, B_max] per configuration from its temperature.range and "
              "magnetic_field.max capabilities; experiment needs from the mandatory temperature and field requirements.",
        data=f"{len(cfgs)} configurations with a sourced temperature.range ({nB} with a documented field), "
             f"{len(excluded)} excluded (no temperature.range), {len(needs)} experiment profiles; data/cryostats/*.json and "
             "data/experiments/*.json via the catalog. Hover counts in the interactive version from paper/data/e1_grid.json. "
             "paper/data/fig_operating_envelope_3d.json.",
        claim="SOURCED",
        caption="Each upright rectangle is the sourced temperature range (log axis) times the documented maximum field of "
                "one configuration, with equipment families in depth; nested rectangles are configurations of one family "
                "with different magnets. Hatched strips mark configurations whose field capability is not documented, and the "
                "dashed outline a magnet that is only an uninstalled option. Orange segments on the front wall are the temperature "
                "and field needs of the experiment profiles. The figure shows sourced geometry only; feasibility verdicts "
                "are those of the Lean checker in the verdict grid.",
        section="supplement"))
    return cfgs, excluded, needs


def main():
    """Optional arguments 1 2 3 4 select figures (default: all)."""
    apply()
    sel = set(sys.argv[1:]) or {"1", "2", "3", "4"}
    out = {}
    if "1" in sel:
        out["fig1"] = {k: {kk: vv for kk, vv in v.items() if kk not in ("sourced_cooling_points", "p_cool_by_T")}
                       for k, v in fig_thermal_feasibility()[0].items()}
    if "2" in sel:
        out["fig2"] = fig_joule_surface()[1:]
    if "3" in sel:
        out["fig3"] = fig_compat_region()
    if "4" in sel:
        cfgs, excl, needs = fig_operating_envelope()
        out["fig4"] = {"n_cfg": len(cfgs), "n_with_field": sum(c["B_max_T"] is not None for c in cfgs),
                       "excluded": [e["configuration"] for e in excl], "n_needs": len(needs)}
    print("Lean checks:", dict(LEAN_CALLS), "total", sum(LEAN_CALLS.values()))
    import json
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
