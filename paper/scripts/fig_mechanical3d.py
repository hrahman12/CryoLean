#!/usr/bin/env python
"""Figure 2: 3D mechanical (sample-space) compatibility.

    CRYOLEAN_LEAN_BIN=... python paper/scripts/fig_mechanical3d.py [catalog.db]

A synthetic experiment family asks for a sample of lateral size D (requirement sample.diameter.max >= D) and
height H (requirement sample.height.max >= H), both user_entered, over a D x H grid. Every verdict drawn is the
output of the compiled Lean 4 checker (cryolean.grid.check_parallel -> lean_runner.check_batch) on the real
configuration documents built by cryolean.grid.configuration_documents / serialize.experiment_doc.
The surface is the binding remaining clearance min(D_max - D, H_max - H) computed from the sourced limits only;
it is an arithmetic overlay, not a verdict. A configuration whose limits are not documented has no surface and
its Lean verdicts are drawn on the zero plane exactly as Lean returned them.

Outputs: paper/figures/fig_mechanical_clearance_3d.{png,svg,pdf}, paper/figures/meta/fig_mechanical_clearance_3d.json,
paper/interactive/fig_mechanical_clearance_3d.html, paper/data/fig_mechanical_clearance_3d.json
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
from plotly.subplots import make_subplots  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from cryolean import grid, lean_runner, serialize, units  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

NAME = "fig_mechanical_clearance_3d"
DB = sys.argv[1] if len(sys.argv) > 1 else None
CAT = Catalog(DB) if DB else Catalog()
SIZE_KEYS = ["sample.diameter.max", "sample.width.max", "sample.length.max", "sample.height.max", "sample.bore_diameter"]
LAT, VERT = "sample.diameter.max", "sample.height.max"
# low-temperature sample-space configurations with both limits documented as manufacturer specifications,
# spanning 20-55 mm lateral and 50-117 mm vertical; the last one lists both keys with unknown values.
SHOWN = ["oxford_optistatdry_blv", "qd_ppms_classic_14T", "mi_6800c_cfms_9t_30_h3",
         "montana_instruments_cryoadvance50_standard", "kiutra_l_type_rapid_3p55", "bluefors_ld400_hdw"]
D_MM = [F(x) for x in (2, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80)]
H_MM = [F(x) for x in (2, 10, 20, 30, 40, 50, 60, 70, 80, 100, 120, 140)]
MARK = {"REQUIREMENTS_MET": "o", "NEED_MORE_INFORMATION": "^", "DOES_NOT_MEET_REQUIREMENTS": "x"}
PSYM = {"REQUIREMENTS_MET": "circle", "NEED_MORE_INFORMATION": "diamond", "DOES_NOT_MEET_REQUIREMENTS": "x"}


def cap(cid, key):
    return next((c for c in CAT.configurations[cid]["capabilities"] if c["key"] == key), None)


def limit_mm(cid, key):
    c = cap(cid, key)
    if not c or c["value"].get("kind") != "max":
        return None
    return float(units.to_si(c["value"]["q"]["value"], c["value"]["q"]["unit"])) * 1e3


def survey():
    """Documentation status of every sample-size key over all configurations."""
    out = {}
    for k in SIZE_KEYS:
        st = Counter()
        for cid in CAT.configurations:
            c = cap(cid, k)
            st["absent" if c is None else ("numeric_max" if c["value"].get("kind") == "max" else c["value"].get("kind", "?"))] += 1
        out[k] = dict(st)
    both = sum(1 for cid in CAT.configurations if limit_mm(cid, LAT) is not None and limit_mm(cid, VERT) is not None)
    return out, both


def experiment(D, H):
    def q(v):
        return {"kind": "at_least", "q": {"value": v * 1000, "unit": "um"}}
    return {"id": "paper_fig_mechanical3d", "name": "synthetic sample-size probe", "industry": "materials_and_nanotechnology",
            "confirmed": True, "params": [], "coupled": [],
            "requirements": [{"key": LAT, "constraint": q(D), "mandatory": True, "origin": "user_entered", "evidence_ids": []},
                             {"key": VERT, "constraint": q(H), "mandatory": True, "origin": "user_entered", "evidence_ids": []}]}


def run():
    cfgs = grid.configuration_documents(CAT, SHOWN)
    pairs, idx = [], []
    for cid in SHOWN:
        cfg_mod, cfg_doc = cfgs[cid]
        for D in D_MM:
            for H in H_MM:
                pairs.append((cfg_doc, serialize.experiment_doc(CAT, experiment(D, H), cfg_mod)[0]))
                idx.append((cid, float(D), float(H)))
    t0 = time.perf_counter()
    res = grid.check_parallel(pairs)
    dt = time.perf_counter() - t0
    print(f"Lean: {len(pairs)} checks in {dt:.1f} s")
    rows = []
    for (cid, D, H), r in zip(idx, res):
        o = grid.outcome(r)
        Ld, Lh = limit_mm(cid, LAT), limit_mm(cid, VERT)
        clr = None if Ld is None or Lh is None else min(Ld - D, Lh - H)
        rows.append({"configuration_id": cid, "D_mm": D, "H_mm": H, "verdict": o["verdict"], "failing": o["failing"],
                     "missing": o["missing"], "lateral_clearance_mm": None if Ld is None else Ld - D,
                     "vertical_clearance_mm": None if Lh is None else Lh - H, "binding_clearance_mm": clr})
    return rows, dt


def consistency(rows):
    """Lean verdict vs the sign of the sourced clearance (both limits documented)."""
    agree = disagree = 0
    for r in rows:
        if r["binding_clearance_mm"] is None:
            continue
        expect = "REQUIREMENTS_MET" if r["binding_clearance_mm"] >= 0 else "DOES_NOT_MEET_REQUIREMENTS"
        agree += r["verdict"] == expect
        disagree += r["verdict"] != expect
    return agree, disagree


SHORT = {"oxford_optistatdry_blv": "Oxford OptistatDry BLV", "qd_ppms_classic_14T": "QD PPMS 14 T",
         "mi_6800c_cfms_9t_30_h3": "MI 6800C CFMS 9 T", "montana_instruments_cryoadvance50_standard": "Montana CryoAdvance 50",
         "kiutra_l_type_rapid_3p55": "kiutra L-Type Rapid", "bluefors_ld400_hdw": "Bluefors LD400 (HDW)"}


def label(cid):
    return SHORT.get(cid) or CAT.configurations[cid].get("name") or cid


def main():
    apply()
    stats, both = survey()
    rows, dt = run()
    agree, disagree = consistency(rows)
    vcount = {cid: dict(Counter(r["verdict"] for r in rows if r["configuration_id"] == cid)) for cid in SHOWN}
    print(vcount, "agree", agree, "disagree", disagree)

    docz = [r["binding_clearance_mm"] for r in rows if r["binding_clearance_mm"] is not None]
    zabs = max(abs(min(docz)), max(docz))
    DD, HH = np.meshgrid([float(d) for d in D_MM], [float(h) for h in H_MM], indexing="ij")

    fig = plt.figure(figsize=(COL2, 5.0))
    for i, cid in enumerate(SHOWN):
        ax = fig.add_subplot(2, 3, i + 1, projection="3d")
        sub = [r for r in rows if r["configuration_id"] == cid]
        Ld, Lh = limit_mm(cid, LAT), limit_mm(cid, VERT)
        documented = Ld is not None and Lh is not None
        if documented:
            ZZ = np.minimum(Ld - DD, Lh - HH)
            ax.plot_surface(DD, HH, ZZ, cmap=DIV_CMAP, vmin=-zabs, vmax=zabs, alpha=0.55, linewidth=0, antialiased=True)
            ax.contour(DD, HH, ZZ, levels=[0], colors=INK, linewidths=0.9)
            sub_t = f"D_max {Ld:g} mm, H_max {Lh:g} mm (sourced)"
        else:
            sub_t = "size limits not documented"
        for v in VERDICT_ORDER:
            pts = [r for r in sub if r["verdict"] == v]
            if pts:
                ax.scatter([p["D_mm"] for p in pts], [p["H_mm"] for p in pts],
                           [p["binding_clearance_mm"] if documented else 0.0 for p in pts], marker=MARK[v],
                           s=9, color=VERDICT_COLOR[v], depthshade=False, linewidths=0.8)
        ax.set_title(f"{label(cid)}\n{sub_t}", fontsize=6.5, pad=0)
        ax.set_xlabel("width/diameter D (mm)", fontsize=6, labelpad=-4)
        ax.set_ylabel("height H (mm)", fontsize=6, labelpad=-4)
        ax.set_zlabel("clearance (mm)" if documented else "no clearance: limits undocumented" + chr(10) + "(markers placed at z = 0)", fontsize=6, labelpad=-4)
        for a in (ax.xaxis, ax.yaxis, ax.zaxis):
            a.pane.set_facecolor((1, 1, 1, 0))
            a.pane.set_edgecolor(AXIS)
        ax.tick_params(labelsize=5.5, pad=-2)
        ax.set_zlim(-zabs, zabs)
        if not documented:
            ax.set_zticks([])
        ax.view_init(elev=24, azim=-58)
    handles = [Line2D([], [], marker=MARK[v], ls="", color=VERDICT_COLOR[v], label=f"Lean: {VERDICT_LABEL[v]}")
               for v in VERDICT_ORDER] + [Line2D([], [], color=INK, lw=0.9, label="zero clearance (sourced limits)")]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=6.5)
    fig.subplots_adjust(left=0.0, right=1.0, top=0.93, bottom=0.07, wspace=0.05, hspace=0.2)

    pf = make_subplots(rows=2, cols=3, specs=[[{"type": "scene"}] * 3] * 2, subplot_titles=[label(c) for c in SHOWN])
    shown_legend = set()
    for i, cid in enumerate(SHOWN):
        rr, cc = i // 3 + 1, i % 3 + 1
        sub = [r for r in rows if r["configuration_id"] == cid]
        Ld, Lh = limit_mm(cid, LAT), limit_mm(cid, VERT)
        if Ld is not None and Lh is not None:
            pf.add_trace(go.Surface(x=DD, y=HH, z=np.minimum(Ld - DD, Lh - HH), opacity=0.5, showscale=False, cmin=-zabs,
                                    cmax=zabs, colorscale=[[0, "#d9663a"], [0.5, "#f0efec"], [1, "#2a4d8f"]],
                                    name="clearance from sourced limits"), row=rr, col=cc)
        for v in VERDICT_ORDER:
            pts = [r for r in sub if r["verdict"] == v]
            if not pts:
                continue
            pf.add_trace(go.Scatter3d(
                x=[p["D_mm"] for p in pts], y=[p["H_mm"] for p in pts],
                z=[p["binding_clearance_mm"] if p["binding_clearance_mm"] is not None else 0 for p in pts],
                mode="markers", marker=dict(size=3, color=VERDICT_COLOR[v], symbol=PSYM[v]),
                name=f"Lean: {VERDICT_LABEL[v]}", legendgroup=v, showlegend=v not in shown_legend,
                text=[f"{cid}<br>D={p['D_mm']:g} mm, H={p['H_mm']:g} mm<br>Lean: {p['verdict']}" for p in pts],
                hoverinfo="text"), row=rr, col=cc)
            shown_legend.add(v)
    for k in range(1, 7):
        pf.layout[f"scene{'' if k == 1 else k}"].update(xaxis_title="D (mm)", yaxis_title="H (mm)", zaxis_title="clearance (mm)")
    pf.update_layout(title="Sample-space clearance with Lean verdicts", height=900)
    html = save_html(pf, NAME)

    n = len(CAT.configurations)
    dump(NAME, {"catalog_db": DB or "default", "lean_binary": str(lean_runner.lean_binary()),
                "lean_version": lean_runner.version(), "lean_checks": len(rows), "lean_seconds": round(dt, 2),
                "requirement_keys": [LAT, VERT], "D_mm": [float(d) for d in D_MM], "H_mm": [float(h) for h in H_MM],
                "configurations": {cid: {"name": label(cid), "D_max_mm": limit_mm(cid, LAT), "H_max_mm": limit_mm(cid, VERT),
                                         "lateral_capability": cap(cid, LAT), "vertical_capability": cap(cid, VERT),
                                         "verdict_counts": vcount[cid]} for cid in SHOWN},
                "catalog_size_key_status": stats, "configurations_total": n,
                "configurations_with_numeric_diameter_and_height": both,
                "lean_vs_sourced_clearance": {"agree": agree, "disagree": disagree}, "rows": rows})

    caption = (f"Mechanical compatibility in three dimensions. A synthetic experiment family requests a sample of width/diameter D "
               f"and height H ({len(D_MM)} x {len(H_MM)} grid; user_entered requirements sample.diameter.max >= D and "
               f"sample.height.max >= H). Markers are verdicts of the compiled Lean 4 checker ({len(rows)} checks over "
               f"{len(SHOWN)} configurations); surfaces are the binding remaining clearance min(D_max - D, H_max - H) computed from "
               f"manufacturer-documented limits, zero contour in black. Lean verdicts and the sign of the sourced clearance agree "
               f"on {agree} of {agree + disagree} documented points. {CAT.configurations[SHOWN[-1]].get('name') or SHOWN[-1]} lists both size keys with unknown values, "
               f"so every request is Need more information, never a pass. Across the catalog only {both} of {n} configurations "
               f"document a numeric diameter and height limit; sample.width.max is numeric for "
               f"{stats['sample.width.max'].get('numeric_max', 0)} and sample.length.max for "
               f"{stats['sample.length.max'].get('numeric_max', 0)}, so full width x length x height footprints cannot be "
               f"checked for most configurations.")
    save(fig, NAME, interactive=html, meta=dict(
        title="3D mechanical compatibility: sample size vs documented clearance", section="main",
        question="Does a sample of a given width/diameter and height fit the documented sample space, and how much clearance remains?",
        model="Requirements sample.diameter.max >= D and sample.height.max >= H decided by the Lean checker; clearance = documented limit - requested size",
        data=f"paper/data/{NAME}.json; catalog sample-space capabilities (manufacturer specifications)",
        claim="COMPUTED+SOURCED", caption=caption,
        notes=("Diameter is the lateral limit because sample.width.max is numeric for very few configurations; the fit of a "
               "rectangular sample's diagonal in a circular bore is not modeled. The clearance surface is arithmetic on sourced "
               "values, not a verdict.")))


if __name__ == "__main__":
    main()
