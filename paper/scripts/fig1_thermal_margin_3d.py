#!/usr/bin/env python
"""Figure 1 variant: cooling margin M = P_cool(T_doc) - Q as an explicit axis and colour, with Lean verdict markers.

    python paper/scripts/fig1_thermal_margin_3d.py

Same (T_op, Q) grid and configurations as fig_thermal_feasibility_3d. Every verdict is re-computed here by the
compiled Lean checker (lean_runner.check_batch via fig_physics3d.run_lean). P_cool is the value Lean itself used
(the rhs of the joule_heating_vs_cooling_power check), which the script asserts equals the sourced catalog value.
Where Lean used no cooling power (NEED_MORE_INFORMATION) the margin is undefined and is not drawn on the margin axis.
"""
from __future__ import annotations

import sys
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fig_physics3d as P  # noqa: E402
from style import *  # noqa: E402,F403

import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

NAME = "fig1_thermal_margin_3d"
LIN = 1e-9   # symlog linear threshold (W); smallest grid heat load is 1e-8 W


def symlog(m):
    return np.sign(m) * np.log10(1 + np.abs(m) / LIN)


def cfg_name(cid):
    return {"bluefors_ld400_hdw": "Bluefors LD400", "oxford_optistatdry_tlex": "Oxford OptistatDry TLEX",
            "lakeshore_ccs_400": "Lake Shore CCS-400"}.get(cid, cid)


def main():
    apply()
    T_grid = sorted(set(P.nice(range(-2, 3), (1, 2, 5)) + [F(21, 5), F(300)]))
    Q_grid = P.nice(range(-8, 2), (1, 3))
    cases, keys = [], []
    for cid in P.FIG1_CFGS:
        for T in T_grid:
            for Q in Q_grid:
                cases.append((cid, P.experiment(T, Q)))
                keys.append((cid, T, Q))
    res, dt = P.run_lean(cases, "fig1_margin")
    src = {cid: {p["key"]: p for p in P.cooling_points(cid)} for cid in P.FIG1_CFGS}
    rows, incons = [], 0
    for (cid, T, Q), r in zip(keys, res):
        M = None
        if r["p_cool_used_exact"] is not None:
            pc = F(r["p_cool_used_exact"])
            assert pc == F(src[cid][r["slot"]]["P_W"]), (cid, T, Q)
            M = pc - Q
            if (M >= 0) != (r["verdict"] == "REQUIREMENTS_MET"):
                incons += 1
        rows.append({"configuration": cid, "T_op_exact": str(T), "T_op_K": float(T), "Q_exact": str(Q), "Q_W": float(Q),
                     "verdict": r["verdict"], "slot": r["slot"], "p_cool_used_exact": r["p_cool_used_exact"],
                     "margin_exact_W": str(M) if M is not None else None,
                     "margin_W": float(M) if M is not None else None})
    summ = {cid: dict(Counter(r["verdict"] for r in rows if r["configuration"] == cid)) for cid in P.FIG1_CFGS}
    n_undef = sum(r["margin_W"] is None for r in rows)
    dump(NAME, {"description": "Cooling margin M = P_cool(T_doc) - Q (exact rationals; P_cool is the value the Lean "
                               "checker used) and Lean verdicts over (T_op, Q); I = 1 mA, R = Q/I^2.",
                "configurations": P.FIG1_CFGS, "lean_checks": len(rows), "lean_seconds": dt,
                "margin_sign_vs_verdict_inconsistencies": incons, "margin_undefined_points": n_undef,
                "verdicts": summ, "rows": rows})

    zlim = float(np.ceil(symlog(np.array([30.0]))[0]))
    norm = Normalize(-zlim, zlim)
    zt = [-9, -6, -3, 0, 3, 6, 9]
    zlab = {}
    for k in zt:
        if k == 0:
            zlab[k] = "0"
        else:
            v = LIN * (10 ** abs(k) - 1)
            zlab[k] = ("-" if k < 0 else "+") + f"$10^{{{int(round(np.log10(v)))}}}$"
    fig = plt.figure(figsize=(COL2, 2.9))
    for lane, cid in enumerate(P.FIG1_CFGS):
        ax = fig.add_subplot(1, 3, lane + 1, projection="3d", computed_zorder=False)
        P.style3d(ax)
        rr = [r for r in rows if r["configuration"] == cid]
        x = np.log10([r["T_op_K"] for r in rr])
        y = np.log10([r["Q_W"] for r in rr])
        gx, gy = np.meshgrid([x.min(), x.max()], [y.min(), y.max()])
        ax.plot_surface(gx, gy, np.zeros((2, 2)), color=MUTED, alpha=0.12, linewidth=0, shade=False, zorder=1)
        for v in P.VERDICT_ORDER:
            m = np.array([r["verdict"] == v for r in rr])
            if not m.any():
                continue
            if v == "NEED_MORE_INFORMATION":   # margin undefined: marker on the floor, no margin height
                ax.scatter(x[m], y[m], np.full(m.sum(), -zlim), marker="^", c=VERDICT_COLOR[v], s=9, edgecolors=INK,
                           linewidths=0.25, depthshade=False, zorder=3)
                continue
            z = symlog(np.array([r["margin_W"] for r, k in zip(rr, m) if k]))
            col = DIV_CMAP(norm(z))
            if v == "DOES_NOT_MEET_REQUIREMENTS":
                ax.scatter(x[m], y[m], z, marker="x", c=col, s=10, linewidths=0.9, depthshade=False, zorder=5)
            else:
                ax.scatter(x[m], y[m], z, marker="o", c=col, s=10, edgecolors=VERDICT_COLOR[v], linewidths=0.6,
                           depthshade=False, zorder=5)
        ax.set_zlim(-zlim, zlim)
        ax.set_zticks(zt)
        ax.set_zticklabels([zlab[k] for k in zt])
        P.temp_ticks(ax, "x", x.min(), x.max())
        P.pow_ticks(ax, "y", y.min(), y.max(), step=3)
        ax.set_xlabel("Operating temp. $T_{op}$", labelpad=-4)
        ax.set_ylabel("Heat load $Q$ (W)", labelpad=-5)
        ax.set_zlabel("Margin $P_{cool}-Q$ (W)" if lane == 2 else "", labelpad=-3)
        ax.set_title(cfg_name(cid), fontsize=7, pad=0)
        ax.view_init(22, -58)
        ax.tick_params(labelsize=5.5, pad=-2)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=DIV_CMAP)
    cax = fig.add_axes([0.30, 0.07, 0.40, 0.025])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_ticks(zt)
    cb.set_ticklabels([zlab[k] for k in zt])
    cb.ax.tick_params(labelsize=5.5)
    cb.set_label("Cooling margin $P_{cool}(T_{doc})-Q$ (W, symmetric log)", fontsize=6.5)
    hs = [Line2D([], [], ls="none", marker="o", mfc=MUTED, mec=VERDICT_COLOR["REQUIREMENTS_MET"], ms=5,
                 label="Lean: Requirements met"),
          Line2D([], [], ls="none", marker="x", mec=INK, ms=5, label="Lean: Does not meet requirements"),
          Line2D([], [], ls="none", marker="^", mfc=VERDICT_COLOR["NEED_MORE_INFORMATION"], mec=INK, ms=5,
                 label="Lean: Need more information (no margin, on floor)")]
    fig.legend(handles=hs, loc="upper center", ncol=3, fontsize=6, frameon=False)
    fig.subplots_adjust(left=0.0, right=0.97, top=0.88, bottom=0.14, wspace=0.05)

    pf = go.Figure()
    groups = []
    for i, cid in enumerate(P.FIG1_CFGS):
        a = len(pf.data)
        rr = [r for r in rows if r["configuration"] == cid]
        for v in P.VERDICT_ORDER:
            sel = [r for r in rr if r["verdict"] == v]
            if not sel:
                continue
            z = [float(symlog(np.array([r["margin_W"]]))[0]) if r["margin_W"] is not None else -zlim for r in sel]
            pf.add_trace(go.Scatter3d(
                x=[float(np.log10(r["T_op_K"])) for r in sel], y=[float(np.log10(r["Q_W"])) for r in sel], z=z,
                mode="markers", visible=i == 0, name=f"Lean: {VERDICT_LABEL[v]}",
                marker=dict(size=4, symbol=P.PLOTLY_SYM[v],
                            color=z if v != "NEED_MORE_INFORMATION" else VERDICT_COLOR[v],
                            colorscale=[[0, ORANGE], [0.5, "#f0efec"], [1, NAVY]], cmin=-zlim, cmax=zlim,
                            line=dict(width=1, color=VERDICT_COLOR[v])),
                text=[f"T_op={r['T_op_exact']} K, Q={r['Q_exact']} W, P_cool={r['p_cool_used_exact']} W, "
                      f"margin={r['margin_exact_W']} W, Lean: {r['verdict']}" for r in sel], hoverinfo="text"))
        groups.append((a, len(pf.data)))
    pf.update_layout(title="Cooling margin P_cool(T_doc) - Q with Lean verdicts", scene=dict(
        xaxis_title="log10 T_op (K)", yaxis_title="log10 Q (W)", zaxis_title="symlog margin (W, linear within 1 nW)"),
        updatemenus=[dict(buttons=[dict(label=cid, method="update",
                                        args=[{"visible": [a <= j < b for j in range(len(pf.data))]}])
                                   for cid, (a, b) in zip(P.FIG1_CFGS, groups)])])
    html = save_html(pf, NAME)
    save(fig, NAME, interactive=html, meta=dict(
        title="Cooling margin of a Joule-heated measurement over operating temperature and heat load",
        question="How much documented cooling power is left (or missing) at each operating temperature and heat load, "
                 "and does the Lean verdict agree with the sign of that margin?",
        model="M = P_cool(T_doc) - Q with Q = I^2 R; joule_heating_vs_cooling_power passes iff M >= 0. T_doc is the highest "
              "documented, installed, non-estimate cooling-power temperature not above T_op (serialize.resolve_slots).",
        data=f"{len(rows)} Lean checks (check_batch, {dt:.1f} s), 3 configurations x {len(T_grid)} T_op x {len(Q_grid)} Q, "
             "same grid as fig_thermal_feasibility_3d; P_cool is the rhs Lean used, asserted equal to the sourced catalog "
             f"value; margin sign vs verdict inconsistencies: {incons}; {n_undef} points have no usable cooling power "
             f"(margin undefined). paper/data/{NAME}.json.",
        claim="COMPUTED+SOURCED",
        caption="Height and colour give the cooling margin P_cool(T_doc) - Q (symmetric log, linear within 1 nW), with "
                "P_cool the sourced cooling power the Lean checker used; marker shape is the Lean verdict. Circles "
                "(met) lie above the zero plane and crosses (not met) below it. Where no documented, non-estimate "
                "cooling power applies (below the lowest documented temperature; OptistatDry TLEX at 4.2-5 K, "
                "documented only as an estimate) the margin is undefined, Lean answers Need more information, and "
                "those points are drawn as triangles on the floor rather than given an invented margin.",
        section="main"))
    print({"lean": len(rows), "seconds": round(dt, 2), "inconsistent": incons, "undefined": n_undef, "verdicts": summ})


if __name__ == "__main__":
    main()
