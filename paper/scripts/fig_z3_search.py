#!/usr/bin/env python
"""Figures: Z3 (untrusted proposer) vs the Lean checker (the only source of verdicts), equipment search, and
campaign scheduling.

    python paper/scripts/fig_z3_search.py              (computes missing data, then plots; ~10 min the first time)
    python paper/scripts/fig_z3_search.py --recompute  (re-runs every Z3 / Lean computation)

fig_z3_lean_agreement  Demo B heat-budget grid (n_flux x n_drive) on three Bluefors refrigerators: smt.evaluate
                       (Z3) and the Lean checker (check_batch) on the SAME documents, point by point.
fig_conflict_graph     smt.all_conflicts (Z3 unsat cores) on every DOES_NOT_MEET pair of the 11 x 26 grid.
fig_search_funnel      26 configurations -> Z3 status -> candidates -> Lean verdicts (api.find_compatible_equipment,
                       re-run), plus the full-grid Z3-vs-Lean crosstab.
fig_schedule           Demo D campaign (re-run), the run-length sweep (paper/data/e6_schedule.json + Lean on the
                       back-to-back packing), and the tamper study (e6_schedule.json).

Every classification shown as a verdict comes from the compiled Lean checker; Z3 results are labelled as Z3.
"""
from __future__ import annotations

import argparse
import copy
import time
from collections import Counter, defaultdict
from fractions import Fraction

import networkx as nx
import numpy as np
from matplotlib.lines import Line2D

from style import *  # noqa: F401,F403  (also puts the repo root on sys.path)

from cryolean import lean_runner, schedule, serialize, smt, verifier  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

HEAT_EXP = "quantum_mxc_wiring_heat_budget"
HEAT_MODEL = "mxc_wiring_heat_budget"
FRIDGES = ["bluefors_ld250_manual_v2", "bluefors_ld400_hdw", "bluefors_ld450_current"]
FRIDGE_SHORT = {"bluefors_ld250_manual_v2": "Bluefors LD250 (standard)", "bluefors_ld400_hdw": "Bluefors LD400 + HDW",
                "bluefors_ld450_current": "Bluefors LD450 (2026 spec.)"}
N_FLUX = list(range(0, 65))                 # 0..64 flux lines
N_DRIVE = list(range(0, 162, 2))            # 0..160 drive lines, step 2
KRINNER = (50, 58)                          # (n_flux, n_drive) of Krinner et al.'s 50-qubit design

EXP_SHORT = {
    "bio_cryo_fluorescence_vitrified": "Cryo-fluorescence (vitrified)",
    "bio_cryosection_frozen_tissue": "Cryosectioning (tissue)",
    "chem_low_temperature_raman": "Low-T Raman",
    "chem_phase_transition_pom": "Phase transition (POM)",
    "chem_temperature_dependent_photoluminescence": "T-dependent PL",
    "mat_electrical_resistance_low_temperature": "Resistivity 2-300 K",
    "mat_magnetometry_vsm": "VSM magnetometry",
    "mat_magnetoresistance_10T": "Magnetoresistance 10 T",
    "quantum_mk_vector_field_transport": "mK vector-field transport",
    "quantum_mxc_wiring_heat_budget": "MXC wiring heat budget",
    "quantum_transmon_characterization": "Transmon characterization",
}
Z3_TO_VERDICT = {"satisfiable": "REQUIREMENTS_MET", "conflict": "DOES_NOT_MEET_REQUIREMENTS",
                 "pending_information": "NEED_MORE_INFORMATION"}
Z3_LABEL = {"satisfiable": "Z3: satisfiable", "conflict": "Z3: conflict", "pending_information": "Z3: pending information",
            "needs_options": "Z3: needs documented options"}


def F(q):
    return Fraction(int(q["num"]), int(q["den"]))


def qd(x: Fraction, dim=None):
    return {"num": x.numerator, "den": x.denominator, "dim": dim or {}}


def set_param(exp_doc, name, value: Fraction):
    for p in exp_doc["params"]:
        if p["name"] == name:
            p["value"] = qd(value, p["value"].get("dim", {}))
            p["origin"] = "user_entered"
            return
    raise KeyError(name)


def lean_fail_set(r):
    """Mandatory, applicable failing items of a Lean result (same rule as paper_eval.e1_grid)."""
    return sorted({"/".join(c["keys"]) for c in r["checks"] if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"}
                  | {c["model"] for c in r["coupled_checks"] if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"})


# =============================================================================================== 1. agreement grid
def compute_agreement(cat):
    print("fig_z3_lean_agreement: building documents")
    ex = serialize.working_experiment(cat, HEAT_EXP, None, None, True)
    out = {"experiment": HEAT_EXP, "model": HEAT_MODEL, "n_flux": N_FLUX, "n_drive": N_DRIVE, "fridges": {}}
    for cid in FRIDGES:
        cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
        params = {p["name"]: F(p["value"]) for p in ed["params"]}
        docs, keys = [], []
        for nd in N_DRIVE:
            for nf in N_FLUX:
                e2 = copy.deepcopy(ed)
                set_param(e2, "n_drive_lines", Fraction(nd))
                set_param(e2, "n_flux_lines", Fraction(nf))
                docs.append(e2)
                keys.append((nd, nf))
        t0 = time.perf_counter()
        lean = lean_runner.check_batch([(cd, e) for e in docs])
        t_lean = time.perf_counter() - t0
        t0 = time.perf_counter()
        z3s, z3c = [], []
        for e in docs:
            ev = smt.evaluate(cd, e, allow_options=False)
            z3s.append(ev.status)
            lab = next((x for x in ev.failing_items + ev.unknown_items if x.startswith("coupled#")), None)
            z3c.append("pass" if lab is None else ("fail" if lab in ev.failing_items else "unknown"))
        t_z3 = time.perf_counter() - t0
        verdicts, lcoup, lhs, rhs = [], [], [], []
        for r in lean:
            c = next(c for c in r["coupled_checks"] if c["model"] == HEAT_MODEL)
            verdicts.append(r["verdict"])
            lcoup.append(c["outcome"])
            lhs.append(str(F(c["lhs"]["value"])) if c.get("lhs") and c["lhs"].get("value") else None)
            rhs.append(str(F(c["rhs"]["value"])) if c.get("rhs") and c["rhs"].get("value") else None)
        p_cool = Fraction(next(x for x in rhs if x))
        out["fridges"][cid] = {
            "lean_verdict": verdicts, "lean_coupled": lcoup, "z3_status": z3s, "z3_coupled": z3c,
            "lhs_W": lhs, "rhs_W": rhs, "cooling_power_W": str(p_cool),
            "cooling_power_display": next(c["rhs"]["display"] for r in lean[:1] for c in r["coupled_checks"] if c["model"] == HEAT_MODEL),
            "params": {k: str(v) for k, v in params.items()},
            "lean_seconds": t_lean, "z3_seconds": t_z3, "points": len(docs),
            "requirements_lean": {"/".join(c["keys"]): c["outcome"] for c in lean[0]["checks"]},
        }
        print(f"  {cid}: {len(docs)} points, Lean batch {t_lean:.1f} s, Z3 evaluate {t_z3:.1f} s")
    out["order"] = "row-major: for n_drive in n_drive: for n_flux in n_flux"
    out["z3_function"] = "cryolean.smt.evaluate(cfg_doc, exp_doc, allow_options=False)"
    dump("fig_z3_lean_agreement", out)
    return out


def boundary_nd(params, p_cool, nf):
    """Analytic boundary of the model equation solved for n_drive: margin*(nd*qd + nf*(qf+pdc) + no*qo) = P."""
    P = {k: Fraction(v) for k, v in params.items()}
    return (p_cool / P["design_margin"] - nf * (P["q_flux_line"] + P["p_flux_dc"]) - P["n_output_lines"] * P["q_output_line"]) / P["q_drive_line"]


def plot_agreement(d):
    nf, nd = np.array(d["n_flux"]), np.array(d["n_drive"])
    fig, axes = plt.subplots(2, 3, figsize=(COL2, 4.9), sharex=True, sharey=True)
    plt.rcParams["hatch.linewidth"] = 0.5
    plt.rcParams["hatch.color"] = "white"     # used by every figure in this script
    conf_total = Counter()
    stats = {}
    for j, cid in enumerate(FRIDGES):
        f = d["fridges"][cid]
        lean = np.array([VERDICT_INDEX[v] for v in f["lean_verdict"]]).reshape(len(nd), len(nf))
        z3 = np.array([VERDICT_INDEX[Z3_TO_VERDICT[s]] for s in f["z3_status"]]).reshape(len(nd), len(nf))
        conf = Counter(zip(f["z3_status"], f["lean_verdict"]))
        conf_total.update(conf)
        coup = Counter(zip(f["z3_coupled"], f["lean_coupled"]))
        agree = sum(n for (s, v), n in conf.items() if Z3_TO_VERDICT.get(s) == v)
        stats[cid] = {"agree": agree, "n": len(f["z3_status"]), "conf": conf, "coupled": coup}
        p_cool = Fraction(f["cooling_power_W"])
        xs = np.linspace(nf.min() - 0.5, nf.max() + 0.5, 200)
        yb = np.array([float(boundary_nd(f["params"], p_cool, Fraction(x).limit_denominator(1000))) for x in xs])
        for i, (grid, row) in enumerate(((z3, "Z3"), (lean, "Lean"))):
            ax = axes[i, j]
            ax.pcolormesh(nf, nd, grid, cmap=VERDICT_CMAP, vmin=-0.5, vmax=2.5, shading="nearest", rasterized=True)
            ax.contourf(nf, nd, grid, levels=[-0.5, 0.5, 1.5, 2.5], colors="none",
                        hatches=[VERDICT_HATCH[v] for v in VERDICT_ORDER])
            ax.plot(xs, yb, color=INK, lw=0.9, ls=(0, (4, 2)))
            ax.plot(*KRINNER, marker="*", ms=8, mfc="white", mec=INK, mew=0.8, ls="none", zorder=5)
            ax.set_xlim(nf.min() - 0.5, nf.max() + 0.5)
            ax.set_ylim(nd.min() - 1, nd.max() + 1)
            ax.grid(False)
            # direct region labels at the region centroid
            for v in VERDICT_ORDER:
                mask = grid == VERDICT_INDEX[v]
                if mask.sum() < 40:
                    continue
                yy, xx = np.nonzero(mask)
                cx, cy = nf[int(np.median(xx))], nd[int(np.median(yy))]
                txt = VERDICT_SHORT[v] if row == "Lean" else {"REQUIREMENTS_MET": "satisfiable", "DOES_NOT_MEET_REQUIREMENTS": "conflict",
                                                              "NEED_MORE_INFORMATION": "pending info"}[v]
                ax.text(cx, cy, txt, ha="center", va="center", fontsize=6.5, color=INK,
                        bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.9))
            failing = [k for k, o in f["requirements_lean"].items() if o == "fail"]
            if failing and i == 1:
                npass = f["lean_coupled"].count("pass")
                ax.text(0.03, 0.03, f"{', '.join(failing)}: option not installed\n-> NOT MET at every point; the heat\n"
                        f"relation alone passes on {npass} points\n(left of the dashed line)", transform=ax.transAxes, ha="left",
                        va="bottom", fontsize=5.6, color=INK, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=AXIS, lw=0.5))
            if i == 0:
                ax.set_title(f"{FRIDGE_SHORT[cid]}\n$P_{{cool}}$(20 mK) = {f['cooling_power_display']}", fontsize=7.5)
            if i == 1:
                ax.set_xlabel("flux lines $n_{flux}$")
                ax.text(0.97, 0.97, f"Z3 = Lean on\n{agree}/{len(f['z3_status'])} points", transform=ax.transAxes,
                        ha="right", va="top", fontsize=6.5, color=INK,
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=AXIS, lw=0.5))
            if j == 0:
                ax.set_ylabel(("Z3 status (proposal)\n" if i == 0 else "Lean verdict (decision)\n") + "drive lines $n_{drive}$")
    handles = [Patch(facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white",
                     label=f"{VERDICT_LABEL[v]} / {Z3_LABEL[{'REQUIREMENTS_MET': 'satisfiable', 'DOES_NOT_MEET_REQUIREMENTS': 'conflict', 'NEED_MORE_INFORMATION': 'pending_information'}[v]][4:]}")
               for v in VERDICT_ORDER]
    handles += [Line2D([], [], color=INK, lw=0.9, ls=(0, (4, 2)), label="analytic boundary of the model equation (overlay)"),
                Line2D([], [], marker="*", ms=8, mfc="white", mec=INK, ls="none", label="Krinner et al. design: 58 drive, 50 flux")]
    fig.legend(handles=handles, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.075), fontsize=6.5)
    fig.tight_layout(h_pad=0.6, w_pad=0.6)
    return fig, stats, conf_total


# =============================================================================================== 2. conflict graph
def constraint_label(item):
    return "/".join(item["keys"]) if item["kind"] == "requirement" else item["model"]


def compute_conflicts(cat):
    print("fig_conflict_graph: Z3 all_conflicts on DOES_NOT_MEET pairs")
    g = load("e1_grid")
    rows = [r for r in g["rows"] if r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"]
    exs, docs = {}, []
    for r in rows:
        ex = exs.setdefault(r["experiment"], serialize.working_experiment(cat, r["experiment"], None, None, True))
        cd, ed, _, _ = verifier.build_documents(cat, ex, r["configuration"])
        docs.append((cd, ed))
    lean = lean_runner.check_batch(docs)                       # re-check now: the verdict being explained
    out = []
    t0 = time.perf_counter()
    for r, (cd, ed), lr in zip(rows, docs, lean):
        res = smt.all_conflicts(cd, ed)
        cores = []
        for c in res["conflicts"]:
            cores.append({"constraints": [constraint_label(i) for i in c["requirements"]],
                          "constraint_kinds": [i["kind"] for i in c["requirements"]],
                          "facts": [{"label": i["label"], "text": i["text"], "evidence_ids": i.get("evidence_ids", [])} for i in c["facts"]],
                          "explanation": c["explanation"]})
        z3_set = sorted({x for c in cores for x in c["constraints"]})
        out.append({"experiment": r["experiment"], "configuration": r["configuration"], "lean_verdict_now": lr["verdict"],
                    "lean_failed": lean_fail_set(lr), "e1_failed": r["failed"], "z3_status": res["status"],
                    "z3_core_constraints": z3_set, "cores": cores, "not_encoded": res["not_encoded"]})
    dt = time.perf_counter() - t0
    dump("fig_conflict_graph", {"pairs": out, "z3_seconds": dt, "source_grid": "paper/data/e1_grid.json",
                                "z3_function": "cryolean.smt.all_conflicts(cfg_doc, exp_doc, max_cores=8)"})
    return load("fig_conflict_graph")


def plot_conflicts(d):
    pairs = d["pairs"]
    block = Counter()            # constraint -> number of pairs in which it appears in a core
    kind = {}
    co = Counter()               # pair-level co-blocking edges
    within = Counter()           # within-core co-occurrence edges
    core_sizes = Counter()
    for p in pairs:
        labs = sorted(set(p["z3_core_constraints"]))
        for c in p["cores"]:
            core_sizes[len(c["constraints"])] += 1
            for lab, k in zip(c["constraints"], c["constraint_kinds"]):
                kind[lab] = k
            cs = sorted(set(c["constraints"]))
            for a in range(len(cs)):
                for b in range(a + 1, len(cs)):
                    within[(cs[a], cs[b])] += 1
        for lab in labs:
            block[lab] += 1
        for a in range(len(labs)):
            for b in range(a + 1, len(labs)):
                co[(labs[a], labs[b])] += 1
    G = nx.Graph()
    for lab, n in block.items():
        G.add_node(lab, n=n, kind=kind[lab])
    for (a, b), w in co.items():
        G.add_edge(a, b, w=w)
    fig = plt.figure(figsize=(COL2, 3.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.9, 1], wspace=0.04)
    ax = fig.add_subplot(gs[0])
    order, seen = [], set()
    for comp in sorted(nx.connected_components(G), key=lambda c: (-len(c), -max(block[x] for x in c))):
        start = max(comp, key=lambda x: block[x])
        for x in nx.dfs_preorder_nodes(G.subgraph(comp), start):
            if x not in seen:
                seen.add(x)
                order.append(x)
    ang = {lab: np.pi / 2 - 2 * np.pi * i / len(order) for i, lab in enumerate(order)}
    pos = {lab: np.array([np.cos(a), np.sin(a)]) for lab, a in ang.items()}
    wmax = max([e[2]["w"] for e in G.edges(data=True)] or [1])
    for a, b, e in G.edges(data=True):
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color=MUTED, lw=0.6 + 3.0 * e["w"] / wmax, alpha=0.75,
                solid_capstyle="round", zorder=1)
        mx, my = (pos[a] + pos[b]) / 2
        ax.text(mx, my, str(e["w"]), fontsize=5.5, color=INK2, ha="center", va="center", zorder=2,
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))
    nmax = max(block.values())
    for lab, (x, y) in pos.items():
        n = block[lab]
        col = NAVY if kind[lab] == "requirement" else ORANGE
        ax.scatter([x], [y], s=25 + 520 * n / nmax, color=col, edgecolor="white", lw=0.8, zorder=3)
    # labels: the most frequent ones always, others small
    for lab, (x, y) in pos.items():
        n = block[lab]
        a = ang[lab]
        r = 1.13 + 0.07 * np.sqrt(n / nmax)
        ca = np.cos(a)
        ax.text(r * np.cos(a), r * np.sin(a), f"{lab} ({n})", ha="left" if ca > 0.15 else ("right" if ca < -0.15 else "center"),
                va="center", fontsize=6.0, color=INK, zorder=4)
    ax.set_axis_off()
    ax.set_xlim(-2.75, 2.75)
    ax.set_ylim(-1.35, 1.3)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_anchor("N")
    ax.set_title("(a) Constraints in Z3 unsat cores (node area = pairs blocked)", loc="left", fontsize=8)
    leg = [Line2D([], [], marker="o", ls="none", color=NAVY, ms=6, label="requirement key"),
           Line2D([], [], marker="o", ls="none", color=ORANGE, ms=6, label="coupled physics model"),
           Line2D([], [], color=MUTED, lw=2, label="both block the same pair")]
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=3, fontsize=6, borderaxespad=0,
              handletextpad=0.4, columnspacing=1.0)
    # bar chart
    ax2 = fig.add_subplot(gs[1])
    top = block.most_common()[::-1]
    ys = np.arange(len(top))
    ax2.barh(ys, [n for _, n in top], color=[NAVY if kind[l] == "requirement" else ORANGE for l, _ in top], height=0.36)
    for y, (l, n) in zip(ys, top):
        ax2.text(n + 0.6, y, str(n), va="center", fontsize=6.3, color=INK)
        ax2.text(0, y + 0.27, l, va="bottom", ha="left", fontsize=6.2, color=INK)     # direct label above each bar
    ax2.set_yticks([])
    ax2.set_ylim(-0.5, len(top) - 0.1)
    ax2.spines["left"].set_visible(True)
    ax2.set_xlabel(f"DOES_NOT_MEET pairs blocked (of {len(pairs)})")
    ax2.set_xlim(0, max(n for _, n in top) * 1.15)
    ax2.grid(axis="y", visible=False)
    ax2.set_title("(b) Pairs blocked per constraint", loc="left", fontsize=8)
    fig.subplots_adjust(left=0.0, right=0.99, bottom=0.13, top=0.9)
    return fig, block, co, within, core_sizes, G


# =============================================================================================== 3. search funnel
def compute_search(cat):
    print("fig_search_funnel: Z3 evaluate on all pairs, Lean batch, api.find_compatible_equipment")
    from cryolean.bridge import CryoLeanAPI
    api = CryoLeanAPI()
    exps, cfgs = sorted(cat.experiments), sorted(cat.configurations)
    pairs, keys = [], []
    for eid in exps:
        ex = serialize.working_experiment(cat, eid, None, None, True)
        for cid in cfgs:
            cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
            pairs.append((cd, ed))
            keys.append((eid, cid))
    lean = lean_runner.check_batch(pairs)
    grid = []
    for (eid, cid), (cd, ed), lr in zip(keys, pairs, lean):
        ev0 = smt.evaluate(cd, ed, allow_options=False)
        ev1 = smt.evaluate(cd, ed, allow_options=True)
        grid.append({"experiment": eid, "configuration": cid, "lean_verdict": lr["verdict"], "z3_no_options": ev0.status,
                     "z3_with_options": ev1.status, "added_options": ev1.added_options})
    search = []
    for eid in exps:
        t0 = time.perf_counter()
        r = api.find_compatible_equipment(eid, confirmed=True)
        dt = time.perf_counter() - t0
        if not r["ok"]:
            search.append({"experiment": eid, "error": r["error"], "seconds": dt})
            continue
        dd = r["data"]
        search.append({"experiment": eid, "seconds": dt, "rejected_by_z3": len(dd["rejected_by_z3"]),
                       "candidates": [{k: c.get(k) for k in ("configuration_id", "z3_status", "lean_verdict", "added_options", "hypothetical")}
                                      for c in dd["candidates"]]})
    e3 = load("e3_search")
    dump("fig_search_funnel", {"grid": grid, "search": search, "n_configurations": len(cfgs), "n_experiments": len(exps),
                               "e3_crosstab_previous_run": e3["crosstab"]})
    return load("fig_search_funnel")


def plot_search(d):
    grid, search = d["grid"], {s["experiment"]: s for s in d["search"]}
    exps = sorted({g["experiment"] for g in grid})
    ncfg = d["n_configurations"]
    stages = []
    for eid in exps:
        gs_ = [g for g in grid if g["experiment"] == eid]
        nonconf = sum(g["z3_with_options"] != "conflict" for g in gs_)
        cands = search[eid].get("candidates", [])
        met = sum(c["lean_verdict"] == "REQUIREMENTS_MET" for c in cands)
        stages.append((eid, ncfg, nonconf, len(cands), met))
    order = sorted(stages, key=lambda s: (s[4], s[3], s[2]))
    fig = plt.figure(figsize=(COL2, 3.5))
    gsp = fig.add_gridspec(2, 2, width_ratios=[1.55, 1], height_ratios=[1, 1], wspace=0.55, hspace=0.75)
    ax = fig.add_subplot(gsp[:, 0])
    cols = [SEQ_BLUE[0], SEQ_BLUE[2], SEQ_BLUE[4], SEQ_BLUE[7]]
    names = [f"catalog configurations ({ncfg})", "Z3 not in conflict (incl. documented options)",
             "candidates returned (top 10)", "Lean: REQUIREMENTS_MET"]
    hs = [0.78, 0.6, 0.42, 0.24]
    for y, (eid, a, b, c, m) in enumerate(order):
        for val, col, h in zip((a, b, c, m), cols, hs):
            ax.barh(y, val, height=h, color=col, edgecolor="white", lw=0.4)
        ax.text(a + 0.4, y, f"{b} → {c} → {m}", va="center", fontsize=6.3, color=INK)
    ax.set_yticks(range(len(order)), [EXP_SHORT[s[0]] for s in order], fontsize=6.5)
    ax.set_xlim(0, ncfg + 6.5)
    ax.set_ylim(-0.6, len(order) - 0.05)
    ax.text(ncfg + 0.4, len(order) - 0.45, "Z3 → cand. → MET", va="bottom", fontsize=6.0, color=INK2)
    ax.set_xticks([0, 5, 10, 15, 20, 26])
    ax.set_xlabel("configurations")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=c, label=n) for c, n in zip(cols, names)], loc="upper center", bbox_to_anchor=(0.42, -0.13),
              ncol=2, fontsize=6, handlelength=1.2, columnspacing=0.8)
    ax.set_title("(a) Search-space reduction per experiment", loc="left", fontsize=8)
    # (b) candidates crosstab
    z_rows = ["satisfiable", "needs_options", "pending_information", "conflict"]
    v_cols = ["REQUIREMENTS_MET", "NEED_MORE_INFORMATION", "DOES_NOT_MEET_REQUIREMENTS"]
    cand = Counter((c["z3_status"], c["lean_verdict"]) for s in d["search"] for c in s.get("candidates", []))
    full = Counter((g["z3_no_options"], g["lean_verdict"]) for g in grid)

    def heat(axh, cnt, rows, title):
        M = np.array([[cnt.get((r, v), 0) for v in v_cols] for r in rows])
        axh.imshow(M > 0, cmap=ListedColormap(["#f6f6f3", "#dfe9f8"]), aspect="auto", vmin=0, vmax=1)
        for i in range(len(rows)):
            for j in range(len(v_cols)):
                n = M[i, j]
                axh.text(j, i, str(n), ha="center", va="center", fontsize=7, color=INK if n else MUTED,
                         fontweight="bold" if n else "normal")
        axh.set_xticks(range(len(v_cols)), [VERDICT_SHORT[v] for v in v_cols], fontsize=6.3)
        axh.set_yticks(range(len(rows)), [r.replace("_", " ").replace("pending information", "pending info") for r in rows], fontsize=6.3)
        axh.tick_params(length=0)
        axh.grid(False)
        for s in axh.spines.values():
            s.set_visible(False)
        axh.set_xticks(np.arange(-0.5, len(v_cols)), minor=True)
        axh.set_yticks(np.arange(-0.5, len(rows)), minor=True)
        axh.grid(which="minor", color="white", lw=1.5)
        axh.tick_params(which="minor", length=0)
        axh.set_title(title, loc="left", fontsize=7.5)
        axh.set_xlabel("Lean verdict", fontsize=6.8, labelpad=2)
        axh.set_ylabel("Z3 status", fontsize=6.8, labelpad=2)
        return M
    axb = fig.add_subplot(gsp[0, 1])
    Mb = heat(axb, cand, z_rows[:3], f"(b) Returned candidates (n = {sum(cand.values())})")
    axc = fig.add_subplot(gsp[1, 1])
    Mc = heat(axc, full, ["satisfiable", "pending_information", "conflict"], f"(c) All pairs, no options (n = {len(grid)})")
    fig.subplots_adjust(left=0.2, right=0.985, top=0.93, bottom=0.2)
    return fig, stages, cand, full


# =============================================================================================== 4. schedule
CAMPAIGN = ["bio_cryo_fluorescence_vitrified", "chem_low_temperature_raman", "chem_phase_transition_pom", "mat_magnetoresistance_10T"]
DURS_H = {CAMPAIGN[0]: 6, CAMPAIGN[1]: 8, CAMPAIGN[2]: 4, CAMPAIGN[3]: 2}


def compute_schedule(cat):
    print("fig_schedule: Demo D campaign + Lean check of the back-to-back packing per run length")
    durs = {e: {"value": h, "unit": "h"} for e, h in DURS_H.items()}
    r = schedule.schedule_campaign(cat, "lakeshore_crx_vf", CAMPAIGN, {"value": 48, "unit": "h"}, durs, confirmed=True)
    doc = r["lean_input"]
    slots = [{"experiment_id": s["experiment_id"], "start_s": str(F(s["start"])),
              "duration_s": str(F(next(p for p in e["params"] if p["name"] == "run_duration")["value"]))}
             for s, e in zip(doc["slots"], doc["experiments"])]
    cool = next(c for c in doc["configuration"]["capabilities"] if c["key"] == "cooldown_time.max")
    # Lean validSchedule on the tightest possible packing (back-to-back from the end of cooldown) at each run length
    order = [s["experiment_id"] for s in doc["slots"]]
    t = F(cool["value"]["q"])
    tight = []
    for s in doc["slots"]:
        e = next(x for x in doc["experiments"] if x["id"] == s["experiment_id"])
        tight.append({"experiment_id": s["experiment_id"], "start": qd(t, {"s": 1})})
        t += F(next(p for p in e["params"] if p["name"] == "run_duration")["value"])
    b2b = []
    for half in range(32, 61):
        L = Fraction(half, 2) * 3600
        d2 = copy.deepcopy(doc)
        d2["slots"] = copy.deepcopy(tight)
        d2["run_length"] = qd(L, {"s": 1})
        lr = lean_runner.check_schedule(d2)
        b2b.append({"run_length_h": half / 2, "lean_valid": bool(lr.get("valid")), "reasons": lr.get("reasons", [])})
    dump("fig_schedule", {"configuration": "lakeshore_crx_vf", "run_length_h": 48, "durations_h": DURS_H,
                          "feasible": r["feasible_experiments"], "excluded": r["excluded_experiments"],
                          "cooldown_s": str(F(cool["value"]["q"])), "cooldown_evidence": cool.get("evidence_ids", []),
                          "z3": r["z3"], "slots": slots, "lean_valid": r["lean"]["valid"], "lean_theorems": r["lean"]["theorems"],
                          "lean_experiment_verdicts": r["lean"]["experiment_verdicts"],
                          "back_to_back_order": order, "back_to_back_end_h": float(t / 3600), "back_to_back_lean": b2b,
                          "sweep_and_tamper_source": "paper/data/e6_schedule.json"})
    return load("fig_schedule")


def plot_schedule(d, e6):
    fig = plt.figure(figsize=(COL2, 4.7))
    gsp = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], width_ratios=[1.05, 1], hspace=0.62, wspace=0.42)
    ax = fig.add_subplot(gsp[0, :])
    cool_h = float(Fraction(d["cooldown_s"]) / 3600)
    rows = ["Cooldown"] + [s["experiment_id"] for s in d["slots"]] + [x["experiment_id"] for x in d["excluded"]]
    ypos = {r: len(rows) - 1 - i for i, r in enumerate(rows)}
    ax.barh(ypos["Cooldown"], cool_h, left=0, height=0.6, color=GRID, edgecolor=MUTED, hatch="xx", lw=0.5)
    ax.text(cool_h + 0.4, ypos["Cooldown"], f"0–{cool_h:g} h  (documented cooldown_time.max)", va="center", fontsize=6.3, color=INK)
    for s, col in zip(d["slots"], [NAVY, LAVENDER, ICY]):
        st, du = float(Fraction(s["start_s"]) / 3600), float(Fraction(s["duration_s"]) / 3600)
        ax.barh(ypos[s["experiment_id"]], du, left=st, height=0.6, color=col, edgecolor="white")
        ax.text(st + du + 0.4, ypos[s["experiment_id"]], f"{st:g}–{st + du:g} h  (Lean: MET)", va="center", fontsize=6.3, color=INK)
    for x in d["excluded"]:
        y = ypos[x["experiment_id"]]
        ax.barh(y, DURS_H[x["experiment_id"]], left=cool_h, height=0.6, color=VERDICT_COLOR[x["lean_verdict"]], edgecolor="white",
                hatch=VERDICT_HATCH[x["lean_verdict"]], lw=0.4)
        why = x["reason"].split("conflicts with:")[-1].strip().rstrip(".").replace("'", "")
        ax.text(cool_h + DURS_H[x["experiment_id"]] + 0.4, y,
                f"not scheduled: Lean {VERDICT_SHORT[x['lean_verdict']]} on this configuration ({why})", va="center",
                fontsize=6.3, color=INK)
    mk = float(Fraction(d["z3"]["makespan"].split()[0]))
    ax.axvline(mk, color=INK, lw=0.8, ls=(0, (4, 2)))
    ax.axvline(d["run_length_h"], color=INK2, lw=0.8)
    ax.text(mk, len(rows) - 0.35, f"makespan {mk:g} h", ha="center", va="bottom", fontsize=6.3, color=INK)
    ax.text(d["run_length_h"], len(rows) - 0.35, f"run end {d['run_length_h']} h", ha="right", va="bottom", fontsize=6.3, color=INK)
    ax.set_yticks([ypos[r] for r in rows], [r if r == "Cooldown" else EXP_SHORT[r] for r in rows], fontsize=6.5)
    ax.set_xlim(0, 48.5)
    ax.set_ylim(-0.6, len(rows) - 0.1)
    ax.set_xticks(range(0, 49, 4))
    ax.set_xlabel("time since start of run (h)")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"(a) Z3 slots on the Lake Shore CRX-VF, 48 h run; Lean validSchedule: "
                 f"{'valid' if d['lean_valid'] else 'rejected'}", loc="left", fontsize=8)
    # (b) sweep
    axb = fig.add_subplot(gsp[1, 0])
    sw = e6["sweep"]
    L = [s["run_length_h"] for s in sw]
    b2b = {b["run_length_h"]: b["lean_valid"] for b in d["back_to_back_lean"]}
    rowsb = [("Z3 Optimize", 2), ("Lean on Z3 slots", 1), ("Lean on back-to-back\npacking", 0)]
    for s in sw:
        x = s["run_length_h"]
        sat = s["z3"] == "sat"
        axb.scatter(x, 2, s=22, marker="o", facecolor=NAVY if sat else "white", edgecolor=NAVY, lw=0.8, zorder=3)
        if s["lean_valid"] is None:
            axb.scatter(x, 1, s=14, marker="_", color=MUTED, lw=1.0, zorder=3)
        else:
            v = "REQUIREMENTS_MET" if s["lean_valid"] else "DOES_NOT_MEET_REQUIREMENTS"
            axb.scatter(x, 1, s=24, marker="s", color=VERDICT_COLOR[v], edgecolor="white", lw=0.4, zorder=3)
        v = "REQUIREMENTS_MET" if b2b[x] else "DOES_NOT_MEET_REQUIREMENTS"
        axb.scatter(x, 0, s=24, marker="s" if b2b[x] else "X", color=VERDICT_COLOR[v], edgecolor="white", lw=0.3, zorder=3)
    thr = cool_h + sum(DURS_H[e] for e in d["feasible"])
    axb.axvline(thr - 0.25, color=INK, lw=0.8, ls=(0, (4, 2)))
    axb.text(thr - 0.25, 2.55, f"feasible from {cool_h:g} + 6 + 8 + 4 = {thr:g} h", ha="center", va="bottom", fontsize=6.2, color=INK,
             bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
    axb.set_yticks([r[1] for r in rowsb], [r[0] for r in rowsb], fontsize=6.3)
    axb.set_ylim(-0.6, 3.0)
    axb.set_xlim(15.6, 30.4)
    axb.set_xticks(range(16, 31, 2))
    axb.set_xlabel("run length (h)")
    axb.grid(axis="y", visible=False)
    leg = [Line2D([], [], marker="o", ls="none", mfc=NAVY, mec=NAVY, ms=4.5, label="Z3 sat"),
           Line2D([], [], marker="o", ls="none", mfc="white", mec=NAVY, ms=4.5, label="Z3 unsat"),
           Line2D([], [], marker="s", ls="none", color=VERDICT_COLOR["REQUIREMENTS_MET"], ms=4.5, label="Lean valid"),
           Line2D([], [], marker="X", ls="none", color=VERDICT_COLOR["DOES_NOT_MEET_REQUIREMENTS"], ms=4.5, label="Lean rejected"),
           Line2D([], [], marker="_", ls="none", color=MUTED, ms=6, label="not run (no slots)")]
    axb.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.45, -0.3), ncol=3, fontsize=5.8, handletextpad=0.3,
               columnspacing=0.8)
    axb.set_title("(b) Run-length sweep", loc="left", fontsize=8)
    # (c) tamper
    axc = fig.add_subplot(gsp[1, 1])
    bk = e6["by_kind"]
    kinds = sorted(bk, key=lambda k: (bk[k].get("valid", 0) / sum(bk[k].values()), k))
    ys = np.arange(len(kinds))
    val = np.array([bk[k].get("valid", 0) for k in kinds])
    rej = np.array([bk[k].get("rejected", 0) for k in kinds])
    axc.barh(ys, val, color=VERDICT_COLOR["REQUIREMENTS_MET"], edgecolor="white", height=0.66, label="Lean: valid")
    axc.barh(ys, rej, left=val, color=VERDICT_COLOR["DOES_NOT_MEET_REQUIREMENTS"], hatch=VERDICT_HATCH["DOES_NOT_MEET_REQUIREMENTS"],
             edgecolor="white", height=0.66, label="Lean: rejected")
    for y, a, b in zip(ys, val, rej):
        axc.text(a + b + 1, y, f"{a} / {b}", va="center", fontsize=6.2, color=INK)
    axc.set_yticks(ys, [k.replace("_", " ") for k in kinds], fontsize=6.5)
    axc.set_xlim(0, max(val + rej) * 1.3)
    axc.set_xlabel("perturbed schedules (valid / rejected)")
    axc.grid(axis="y", visible=False)
    agree = sum(x["n"] for x in e6["lean_vs_independent"] if x["lean_valid"] == x["python_valid"])
    axc.legend(loc="upper center", bbox_to_anchor=(0.45, -0.3), ncol=2, fontsize=5.8)
    axc.set_title(f"(c) Tamper study: Lean = Python on {agree}/{e6['tamper_cases']}", loc="left", fontsize=8)
    fig.subplots_adjust(left=0.17, right=0.985, top=0.94, bottom=0.14)
    return fig, thr


# =============================================================================================== main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recompute", action="store_true")
    args = ap.parse_args()
    apply()
    cat = Catalog()

    def get(name, fn):
        p = DATA_DIR / f"{name}.json"
        return fn(cat) if (args.recompute or not p.exists()) else load(name)

    # ---------------------------------------------------------------- 1
    d1 = get("fig_z3_lean_agreement", compute_agreement)
    fig, st, conf = plot_agreement(d1)
    n_all = sum(conf.values())
    agree_all = sum(n for (s, v), n in conf.items() if Z3_TO_VERDICT.get(s) == v)
    conf_txt = "; ".join(f"Z3 {s} / Lean {VERDICT_SHORT[v]}: {n}" for (s, v), n in sorted(conf.items()))
    coup = Counter()
    for cid in FRIDGES:
        coup.update(st[cid]["coupled"])
    coup_agree = sum(n for (a, b), n in coup.items() if a == b)
    lean_s = sum(d1["fridges"][c]["lean_seconds"] for c in FRIDGES)
    z3_s = sum(d1["fridges"][c]["z3_seconds"] for c in FRIDGES)
    per = {c: Counter(d1["fridges"][c]["lean_verdict"]) for c in FRIDGES}
    print("agreement", conf, coup)
    save(fig, "fig_z3_lean_agreement", meta=dict(
        title="Z3 feasibility classification vs Lean verdicts on the Demo B heat-budget grid",
        question="Does the untrusted Z3 encoding of the coupled heat-budget relation classify (n_flux, n_drive) designs the same way as the Lean checker, including the three-valued outcome?",
        model="mxc_wiring_heat_budget: margin*(n_drive*q_drive + n_flux*(q_flux+p_flux_dc) + n_out*q_out) <= P_cool(20 mK); "
              "margin 3, q_drive 13 nW, q_flux 29 nW, p_flux_dc 50 nW, n_out 8, q_out 20 nW (Krinner et al. 2019, data/experiments/quantum_mxc_wiring_heat_budget.json).",
        data=f"Real documents from verifier.build_documents for {HEAT_EXP} on {', '.join(FRIDGES)}; n_drive_lines in 0..160 step 2 and "
             f"n_flux_lines in 0..64 edited in exp_doc (origin user_entered); {n_all} pairs. Lean: lean_runner.check_batch "
             f"({lean_s:.1f} s total). Z3: smt.evaluate(allow_options=False) ({z3_s:.1f} s total). Data: paper/data/fig_z3_lean_agreement.json.",
        claim="COMPUTED+SOURCED",
        caption=(f"Z3 status (top) and Lean verdict (bottom) for every wiring design on three Bluefors refrigerators; each cell is one "
                 f"real experiment document with the drive- and flux-line counts edited. Z3 and Lean agree on {agree_all}/{n_all} points "
                 f"({conf_txt}); the coupled relation alone agrees on {coup_agree}/{sum(coup.values())}. Where the heat relation holds, the LD250 is NEED INFO "
                 f"because its coax-line count is UNKNOWN in the sourced record, and the LD450 is NOT MET everywhere because its documented "
                 f"coax wiring is an optional accessory that is not installed (the relation alone passes on "
                 f"{d1['fridges']['bluefors_ld450_current']['lean_coupled'].count('pass')} of its points). The dashed line is the analytic boundary of the model equation, overlaid "
                 f"for reference only; per-line loads and cooling powers are sourced, the classifications are computed."),
        section="main"))

    # ---------------------------------------------------------------- 2
    d2 = get("fig_conflict_graph", compute_conflicts)
    fig, block, co, within, core_sizes, G = plot_conflicts(d2)
    pairs = d2["pairs"]
    match = sum(sorted(p["z3_core_constraints"]) == sorted(p["lean_failed"]) for p in pairs)
    still = sum(p["lean_verdict_now"] == "DOES_NOT_MEET_REQUIREMENTS" for p in pairs)
    ncores = sum(len(p["cores"]) for p in pairs)
    multi = sum(len(p["cores"]) > 1 for p in pairs)
    top3 = ", ".join(f"{l} ({n})" for l, n in block.most_common(3))
    print("conflicts", match, len(pairs), core_sizes, block.most_common(5))
    save(fig, "fig_conflict_graph", meta=dict(
        title="Constraint conflict graph from Z3 unsat cores",
        question="Which requirements and coupled physics models are responsible for the DOES_NOT_MEET verdicts across the catalog, and which ones block the same experiment-configuration pairs together?",
        model="Z3 unsat cores (smt.all_conflicts): requirements and coupled relations are tracked constraints, documented capability values and parameters are tracked facts; independent minimal cores are enumerated by removing each core's constraints and re-solving (max 8).",
        data=f"All {len(pairs)} DOES_NOT_MEET pairs of paper/data/e1_grid.json (11 experiments x 26 configurations), documents rebuilt with verifier.build_documents; "
             f"Lean re-checked in one check_batch ({still}/{len(pairs)} still DOES_NOT_MEET); {ncores} cores. Raw cores with facts and evidence ids: paper/data/fig_conflict_graph.json.",
        claim="COMPUTED",
        caption=(f"(a) Nodes are requirement keys (navy) and coupled models (orange) that appear in a Z3 minimal unsat core; node area is the number of "
                 f"DOES_NOT_MEET pairs they block. Every core contained exactly one constraint plus the documented fact(s) it contradicts "
                 f"({dict(core_sizes)} cores by constraint count), so edges join constraints that block the same pair in independent cores "
                 f"({multi} pairs have more than one core); edge width and label count such pairs. (b) Pairs blocked per constraint; the most frequent are {top3}. "
                 f"The set of core constraints equals Lean's failing set on {match}/{len(pairs)} pairs; Lean, not Z3, issues each verdict."),
        section="main"))

    # ---------------------------------------------------------------- 3
    d3 = get("fig_search_funnel", compute_search)
    fig, stages, cand, full = plot_search(d3)
    tot = sum(s[1] for s in stages)
    nonconf = sum(s[2] for s in stages)
    ncand = sum(s[3] for s in stages)
    nmet = sum(s[4] for s in stages)
    grid_agree = sum(n for (s, v), n in full.items() if Z3_TO_VERDICT.get(s) == v)
    cand_txt = "; ".join(f"Z3 {s} -> Lean {VERDICT_SHORT[v]}: {n}" for (s, v), n in sorted(cand.items()))
    hyp_met = sum(1 for s in d3["search"] for c in s.get("candidates", []) if c["z3_status"] == "needs_options" and c["lean_verdict"] == "REQUIREMENTS_MET")
    opt_shift = sum(1 for g in d3["grid"] if g["z3_no_options"] == "conflict" and g["z3_with_options"] != "conflict")
    print("search", stages, cand, full, opt_shift)
    save(fig, "fig_search_funnel", meta=dict(
        title="Equipment search: Z3 narrows the catalog, Lean decides every candidate",
        question="How much of the 26-configuration catalog does the Z3 search eliminate per experiment, and does any Z3 status ever stand in for a Lean verdict?",
        model="smt.rank_alternatives / smt.evaluate (Z3; documented optional accessories allowed and minimised) proposes and ranks; every returned candidate is checked by the proven Lean checkCandidates entry point.",
        data=f"Re-run of CryoLeanAPI.find_compatible_equipment for all 11 experiments (confirmed=True, max_results=10); smt.evaluate on all {len(d3['grid'])} "
             f"experiment x configuration documents with and without options; Lean check_batch on the same {len(d3['grid'])} base documents. "
             f"Data: paper/data/fig_search_funnel.json (previous run: paper/data/e3_search.json).",
        claim="COMPUTED",
        caption=(f"(a) Per experiment: 26 catalog configurations, those Z3 does not put in conflict ({nonconf} of {tot} pairs in total), the candidates returned "
                 f"({ncand}) and those Lean accepts ({nmet}). (b) Z3 status of every returned candidate against its Lean verdict ({cand_txt}); "
                 f"{hyp_met} candidates are hypothetical configurations with documented options added, and Lean accepts them only on that "
                 f"exact document. With options allowed, {opt_shift} Lean-rejected base pairs leave Z3's conflict tier, and pending-information configurations that "
                 f"document none of an experiment's requirements are not returned (hence 0 candidates for the heat-budget profile). "
                 f"(c) Without options, Z3 status and Lean verdict coincide on {grid_agree}/{len(d3['grid'])} pairs. "
                 f"Every verdict shown is Lean's; Z3 only proposes and ranks."),
        section="main"))

    # ---------------------------------------------------------------- 4
    d4 = get("fig_schedule", compute_schedule)
    e6 = load("e6_schedule")
    fig, thr = plot_schedule(d4, e6)
    sat_min = min(s["run_length_h"] for s in e6["sweep"] if s["z3"] == "sat")
    b2b_min = min(b["run_length_h"] for b in d4["back_to_back_lean"] if b["lean_valid"])
    agree = sum(x["n"] for x in e6["lean_vs_independent"] if x["lean_valid"] == x["python_valid"])
    nvalid = sum(x["n"] for x in e6["lean_vs_independent"] if x["lean_valid"])
    print("schedule", thr, sat_min, b2b_min, agree)
    save(fig, "fig_schedule", meta=dict(
        title="Campaign scheduling: Z3 proposes slots, Lean validSchedule decides",
        question="Can several experiments be packed into one cooldown of a configuration, where exactly is the feasibility threshold, and does the Lean schedule check catch tampered schedules?",
        model="Z3 Optimize: start_i >= cooldown, start_i + d_i <= run length, pairwise disjoint, minimise makespan; Lean validSchedule (validSchedule_sound/_bounds/_disjoint/_only_accepted) checks the exact slot list. Durations are user-entered (6, 8, 4, 2 h); cooldown is the documented cooldown_time.max.",
        data=f"(a) schedule.schedule_campaign on lakeshore_crx_vf, 48 h, re-run now (paper/data/fig_schedule.json). (b) run-length sweep 16-30 h in 0.5 h steps from paper/data/e6_schedule.json, "
             f"plus {len(d4['back_to_back_lean'])} new Lean check_schedule runs on the back-to-back packing. (c) {e6['tamper_cases']} randomly perturbed schedules from paper/data/e6_schedule.json, "
             f"judged by Lean and by an independent Python re-implementation of ScheduleOK (paper_eval._ok_python).",
        claim="COMPUTED",
        caption=(f"(a) Lean accepts three experiments on the CRX-VF and Z3 packs them after the {d4['cooldown_s'] and float(Fraction(d4['cooldown_s'])/3600):g} h cooldown with a makespan of "
                 f"{d4['z3']['makespan']}; Lean validSchedule accepts the slot list, and the 10 T magnetoresistance experiment is never scheduled because Lean returns "
                 f"DOES NOT MEET for it on this configuration. (b) Z3 finds a schedule exactly from {sat_min:g} h = cooldown + sum of durations; Lean independently rejects "
                 f"the tightest packing below that and accepts it from {b2b_min:g} h. (c) Of {e6['tamper_cases']} perturbed schedules Lean accepts {nvalid}, and agrees with the "
                 f"independent re-implementation on {agree}/{e6['tamper_cases']}."),
        section="main"))


if __name__ == "__main__":
    main()
