#!/usr/bin/env python
"""Lean 4 formal-verification figures for the CryoLean paper.

    python paper/scripts/fig_formal.py               (about 1-2 minutes; runs Lean in batch and the fast test suite)
    python paper/scripts/fig_formal.py --use-cache   (re-draw from paper/data/fig_*.json without re-running anything)

Figures
  fig_proof_graph        dependency graph of the trusted core (docs/forensics/cryolean-forensics.json)
  fig_verdict_flow       per-check outcomes -> verdicts over the 11 x 26 grid (Lean, batch, re-run here)
  fig_guarantees         guarantee coverage matrix (VERIFICATION_SCOPE.md, audit-axioms.json, tests, forensics)
  fig_rejection_margins  mat_magnetoresistance_10T against all 26 configurations (Lean, batch, re-run here)
  fig_proof_stats        size of the Lean core and axiom usage (e8_proofs.json, audit-axioms.json, forensics)

Every verdict and every per-check outcome drawn here is produced by the compiled Lean checker
(lean/.lake/build/bin/cryolean.exe via cryolean.lean_runner.check_batch). Python only counts and draws.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import textwrap
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import *  # noqa: F401,F403,E402
from style import ROOT, DATA_DIR  # noqa: E402

import numpy as np  # noqa: E402
from matplotlib.patches import PathPatch, Rectangle  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

FORENSICS = ROOT / "docs" / "forensics" / "cryolean-forensics.json"
FORENSICS_SUMMARY = ROOT / "docs" / "forensics" / "summary.json"
AUDIT = ROOT / "lean" / "audit-axioms.json"
SCOPE = ROOT / "VERIFICATION_SCOPE.md"

MODULE_ORDER = ["CryoLean.Model", "CryoLean.Num", "CryoLean.Checker", "CryoLean.Spec", "CryoLean.Soundness",
                "CryoLean.Schedule"]
MODULE_COLOR = {"CryoLean.Model": MUTED, "CryoLean.Num": INK2, "CryoLean.Checker": NAVY, "CryoLean.Spec": LAVENDER,
                "CryoLean.Soundness": ICY, "CryoLean.Schedule": ORANGE}
OUTCOMES = ["pass", "fail", "unknown", "unsupported", "not_applicable"]
OUTCOME_COLOR = {"pass": NAVY, "fail": ORANGE, "unknown": LAVENDER, "unsupported": ICY, "not_applicable": MUTED}
OUTCOME_LABEL = {"pass": "pass", "fail": "fail", "unknown": "unknown", "unsupported": "unsupported",
                 "not_applicable": "not applicable"}


def short(name: str) -> str:
    return name[len("CryoLean."):] if name.startswith("CryoLean.") else name


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


# =====================================================================================================================
# Lean runs (shared by fig_verdict_flow and fig_rejection_margins)
# =====================================================================================================================
def lean_grid():
    """Every experiment x every configuration, confirmed and unconfirmed, through the compiled Lean checker."""
    from cryolean import lean_runner, serialize, verifier
    from cryolean.catalog import Catalog
    cat = Catalog()
    exps, cfgs = sorted(cat.experiments), sorted(cat.configurations)
    keys, pairs_c, pairs_u, build_errors = [], [], [], []
    for eid in exps:
        ex = serialize.working_experiment(cat, eid, None, None, True)
        for cid in cfgs:
            try:
                cd, ed, _, _ = verifier.build_documents(cat, ex, cid)
            except Exception as e:  # noqa: BLE001
                build_errors.append({"experiment": eid, "configuration": cid, "error": str(e)})
                continue
            eu = dict(ed)
            eu["confirmed"] = False
            keys.append((eid, cid, cat.configurations[cid].get("family")))
            pairs_c.append((cd, ed))
            pairs_u.append((cd, eu))
    t0 = time.perf_counter()
    res_c = lean_runner.check_batch(pairs_c)
    t1 = time.perf_counter()
    res_u = lean_runner.check_batch(pairs_u)
    t2 = time.perf_counter()
    return {"exps": exps, "cfgs": cfgs, "keys": keys, "confirmed": res_c, "unconfirmed": res_u,
            "build_errors": build_errors, "seconds_confirmed": t1 - t0, "seconds_unconfirmed": t2 - t1,
            "lean_version": lean_runner.version()}


def relevant_outcomes(r):
    """Outcomes of the mandatory + applicable checks, i.e. Lean's `outcomes cfg e` (relevantReqs ++ relevantCoupled)."""
    out = [c["outcome"] for c in r["checks"] if c["mandatory"] and c["applicable"]]
    out += [c["outcome"] for c in r["coupled_checks"] if c["mandatory"] and c["applicable"]]
    return out


def rule_branch(confirmed: bool, outs):
    """Which branch of Checker.lean `verdict` a pair falls in (used only to label the flow and to cross-check)."""
    if not confirmed:
        return "unconfirmed"
    if "fail" in outs:
        return "fail"
    if all(o in ("pass", "not_applicable") for o in outs) and "pass" in outs:
        return "allpass"
    if any(o in ("unknown", "unsupported") for o in outs):
        return "gap"
    return "nopass"


BRANCH_VERDICT = {"unconfirmed": "NEED_MORE_INFORMATION", "fail": "DOES_NOT_MEET_REQUIREMENTS",
                  "allpass": "REQUIREMENTS_MET", "gap": "NEED_MORE_INFORMATION", "nopass": "NEED_MORE_INFORMATION"}


def compute_verdict_flow(G):
    e1 = load("e1_grid")
    e1v = {(r["experiment"], r["configuration"]): r["verdict"] for r in e1["rows"]}
    cross = Counter()               # (outcome, verdict) over mandatory applicable checks, confirmed run
    optional = Counter()
    pairs, branch_cnt, branch_vs = [], Counter(), Counter()
    agree_rule = agree_e1 = 0
    for (eid, cid, fam), r in zip(G["keys"], G["confirmed"]):
        outs = relevant_outcomes(r)
        for o in outs:
            cross[(o, r["verdict"])] += 1
        for c in r["checks"] + r["coupled_checks"]:
            if not (c["mandatory"] and c["applicable"]):
                optional[c["outcome"]] += 1
        b = rule_branch(True, outs)
        branch_cnt[b] += 1
        branch_vs[(b, r["verdict"])] += 1
        agree_rule += BRANCH_VERDICT[b] == r["verdict"]
        agree_e1 += e1v.get((eid, cid)) == r["verdict"]
        pairs.append({"experiment": eid, "configuration": cid, "verdict": r["verdict"], "relevant_outcomes": dict(Counter(outs))})
    for r in G["unconfirmed"]:
        b = rule_branch(False, relevant_outcomes(r))
        branch_cnt[b] += 1
        branch_vs[(b, r["verdict"])] += 1
        agree_rule += BRANCH_VERDICT[b] == r["verdict"]
    n_pairs = len(G["confirmed"])
    return {
        "source": "Lean check_batch over every experiment x configuration (serialize.working_experiment confirmed=True, "
                  "verifier.build_documents); unconfirmed run sets experiment.confirmed=false on the same documents",
        "lean_version": G["lean_version"], "pairs_confirmed": n_pairs, "pairs_unconfirmed": len(G["unconfirmed"]),
        "build_errors": G["build_errors"], "seconds_confirmed_batch": G["seconds_confirmed"],
        "seconds_unconfirmed_batch": G["seconds_unconfirmed"],
        "verdicts_confirmed": dict(Counter(r["verdict"] for r in G["confirmed"])),
        "verdicts_unconfirmed": dict(Counter(r["verdict"] for r in G["unconfirmed"])),
        "relevant_checks": sum(cross.values()),
        "relevant_outcomes": dict(Counter({o: sum(v for (oo, _), v in cross.items() if oo == o) for o in OUTCOMES})),
        "outcome_by_verdict": [{"outcome": o, "verdict": v, "n": n} for (o, v), n in sorted(cross.items())],
        "non_relevant_checks_by_outcome": dict(optional),
        "branch_counts": dict(branch_cnt),
        "branch_by_verdict": [{"branch": b, "verdict": v, "n": n} for (b, v), n in sorted(branch_vs.items())],
        "rule_agrees_with_lean": agree_rule, "rule_total": n_pairs + len(G["unconfirmed"]),
        "confirmed_agrees_with_e1_grid": agree_e1,
        "pairs": pairs,
    }


# ---------------------------------------------------------------------------------------------- rejection margins
EXP_MR = "mat_magnetoresistance_10T"


def qv(q):
    return Fraction(q["num"], q["den"])


def margin_of(constraint, value):
    """Normalised margin from the numbers Lean reports (>= 1 means the documented value covers the requirement).
    at_least q vs max m: m/q;  at_least q vs range [lo,hi]: hi/q;  point_within q vs [lo,hi]: min(q/lo, hi/q)."""
    if value is None or value.get("kind") == "unknown":
        return None
    k = constraint["kind"]
    if k == "at_least":
        q = qv(constraint["q"])
        if value["kind"] == "max":
            return qv(value["q"]) / q
        if value["kind"] == "range":
            return qv(value["hi"]) / q
    if k == "at_most":
        q = qv(constraint["q"])
        if value["kind"] == "min":
            return q / qv(value["q"])
        if value["kind"] == "range":
            return q / qv(value["lo"])
    if k == "point_within" and value["kind"] == "range":
        q, lo, hi = qv(constraint["q"]), qv(value["lo"]), qv(value["hi"])
        a = q / lo if lo > 0 else None
        b = hi / q
        return min(b, a) if a is not None else b
    return None


def compute_margins(G):
    from cryolean.catalog import Catalog
    cat = Catalog()
    rows = []
    for (eid, cid, fam), r in zip(G["keys"], G["confirmed"]):
        if eid != EXP_MR:
            continue
        cells = []
        for c in r["checks"]:
            if not (c["mandatory"] and c["applicable"]):
                continue
            key = "/".join(c["keys"])
            pk = c["per_key"][0] if c.get("per_key") else {}
            cap = pk.get("capability")
            val = cap.get("value") if cap else None
            m = margin_of(c["constraint"], val) if val else None
            cells.append({"key": key, "outcome": c["outcome"], "constraint": c["constraint"],
                          "documented": val, "evidence_status": cap.get("evidence_status") if cap else None,
                          "install": cap.get("install") if cap else None,
                          "margin": None if m is None else [m.numerator, m.denominator],
                          "margin_float": None if m is None else float(m),
                          "available_display": pk.get("available_display"), "required_display": c.get("required_display"),
                          "explanation": c.get("explanation")})
        for c in r["coupled_checks"]:
            if c["mandatory"] and c["applicable"]:
                cells.append({"key": c["model"], "outcome": c["outcome"], "coupled": True})
        rows.append({"configuration": cid, "family": fam,
                     "name": cat.configurations[cid].get("name") or cid, "verdict": r["verdict"], "cells": cells})
    # consistency of the drawn margin with Lean's own outcome (only where a trusted value was compared)
    consistent = inconsistent = 0
    for row in rows:
        for c in row["cells"]:
            if c.get("margin_float") is not None and c["outcome"] in ("pass", "fail"):
                if (c["margin_float"] >= 1) == (c["outcome"] == "pass"):
                    consistent += 1
                else:
                    inconsistent += 1
    return {"experiment": EXP_MR, "source": "Lean check_batch (same run as fig_verdict_flow), per_key capability values",
            "margin_definition": "at_least q vs documented max m: m/q; at_least q vs range [lo,hi]: hi/q; "
                                 "point_within q vs [lo,hi]: min(q/lo, hi/q); flags have no ratio",
            "rows": rows, "verdicts": dict(Counter(r["verdict"] for r in rows)),
            "margin_consistent_with_lean_outcome": consistent, "margin_inconsistent": inconsistent}


# =====================================================================================================================
# Figure 1: proof dependency graph
# =====================================================================================================================
KEY_DEFS = ["Q.le", "Q.scale", "Q.add", "Q.mul",
            "lookup", "trustedB", "usable", "checkValue", "checkCapability", "keyOutcome", "combineAny", "evalCond",
            "condsResult", "checkRequirement", "evalExpr", "checkLe", "validityOutcome", "checkCoupled", "relevantReqs",
            "relevantCoupled", "outcomes", "verdict", "run", "checkCandidates",
            "TrustedEvidence", "ValueMeets", "ValueFails", "SatisfiesKey", "ViolatesKey", "CondHolds", "CondFails", "Denotes",
            "LeHolds", "LeFails", "ReqPasses", "ReqOK", "ReqViolated", "CoupledPasses", "CoupledOK", "CoupledViolated",
            "AcceptSpec", "RejectSpec",
            "dropOptional", "dropNonApplicable", "comparedDims", "Constraint.dims",
            "cooldownOf", "durationOf", "resolve", "Disjoint", "ScheduleOK", "validSchedule"]
MAIN_THEOREMS = {"verdict_accept_sound", "verdict_accept_complete", "verdict_accept_iff", "verdict_reject_sound",
                 "verdict_reject_complete", "accept_no_unknown", "fail_needs_trusted", "satisfies_spec_exclusive",
                 "candidates_accept_sound", "validSchedule_sound", "validSchedule_complete", "evalExpr_sound",
                 "pass_dims_all_match", "verdict_industry_irrelevant", "violation_prevents_accept"}


def compute_graph():
    F = jload(FORENSICS)
    A = jload(AUDIT)
    N = {d["name"]: d for d in F["decls"]}
    thms = ["CryoLean." + t for t in A["theorems"]]
    defs = [n for n in ("CryoLean." + k for k in KEY_DEFS) if n in N]
    nodes = thms + defs
    S = set(nodes)
    stmt = set()
    for t in nodes:
        for dep in N[t]["typeDeps"]:
            if dep in S and dep != t:
                stmt.add((t, dep))
    # proof / definitional dependencies: direct valueDeps restricted to the drawn nodes (statement edges excluded)
    proof = {(t, d) for t in nodes for d in N[t]["valueDeps"] if d in S and d != t and (t, d) not in stmt}
    # for reference: the same, followed transitively through helper lemmas/defs that are not drawn
    trans = set()
    for t in nodes:
        seen, stack = set(), list(N[t]["valueDeps"])
        while stack:
            d = stack.pop()
            if d in seen or d == t:
                continue
            seen.add(d)
            if d in S:
                if (t, d) not in stmt:
                    trans.add((t, d))
                continue
            x = N.get(d)
            if x and x["kind"] in ("theorem", "def") and x["module"] in MODULE_ORDER[1:]:
                stack.extend(x["valueDeps"])
    out = []
    for n in nodes:
        d = N[n]
        out.append({"name": n, "short": short(n), "kind": d["kind"], "module": d["module"],
                    "signature": d["signature"], "doc": d.get("doc"), "axioms": d["axioms"],
                    "audited": n in thms, "line": d["range"]["pos"][0]})
    return {"source": "docs/forensics/cryolean-forensics.json (for-all-dev/forensics extractor, toolchain "
                      f"{F['toolchain']}), lean/audit-axioms.json (44 audited theorems)",
            "nodes": out, "statement_edges": sorted(stmt), "proof_edges": sorted(proof),
            "proof_edges_transitive": len(trans), "n_theorems": len(thms), "n_defs": len(defs),
            "n_decls_total": len(F["decls"])}


COLS = {"num": 0.0, "chk": 1.25, "spec": 2.5, "snd": 2.8, "schd": 5.75, "scht": 5.95}
LABEL_SIDE = {"num": "left", "chk": "left", "spec": "left", "snd": "right", "schd": "left", "scht": "right"}


def layer_of(n):
    """Column group used for ordering: 0 Num, 1 Checker, 2 Spec (+ Soundness helper defs), 3 Soundness theorems,
    4 Schedule defs, 5 Schedule theorems."""
    m, k = n["module"], n["kind"]
    if m in ("CryoLean.Num", "CryoLean.Model"):
        return 0
    if m == "CryoLean.Checker":
        return 1
    if m == "CryoLean.Spec" or (m == "CryoLean.Soundness" and k != "theorem"):
        return 2
    if m == "CryoLean.Soundness":
        return 3
    if m == "CryoLean.Schedule":
        return 4 if k != "theorem" else 5
    return 0


def graph_layout(G):
    """Layered layout: columns by module, order inside a column by barycentre sweeps (fewer crossings).
    Returns {name: (x, y, column)}."""
    nodes = {n["name"]: n for n in G["nodes"]}
    order = defaultdict(list)
    for n in sorted(G["nodes"], key=lambda n: n["line"]):
        order[layer_of(n)].append(n["name"])
    nbr = defaultdict(set)
    for a, b in G["statement_edges"] + G["proof_edges"]:
        nbr[a].add(b)
        nbr[b].add(a)
    ypos = {}

    def assign():
        for L, v in order.items():
            for i, x in enumerate(v):
                ypos[x] = 1 - (i + 0.5) / len(v)

    assign()
    for _ in range(40):
        for L in sorted(order):
            def bc(x):
                ys = [ypos[y] for y in nbr[x] if layer_of(nodes[y]) != L]
                return float(np.mean(ys)) if ys else ypos[x]
            order[L] = sorted(order[L], key=lambda x: -bc(x))
            assign()
    colname = {0: "num", 1: "chk", 2: "spec", 3: "snd", 4: "schd", 5: "scht"}
    pos = {}
    for L, v in order.items():
        cols = {colname[L]: v}
        for c, vv in cols.items():
            for i, x in enumerate(vv):
                pos[x] = (COLS[c], 1 - (i + 0.5) / len(vv), c)
    return pos


def _edge(ax, p0, p1, color, lw, alpha, z):
    (x0, y0), (x1, y1) = p0, p1
    if abs(x0 - x1) < 0.05:                         # same column: arc to the side instead of a vertical overlap
        bulge = 0.18 + 0.25 * abs(y0 - y1)
        verts = [(x0, y0), (x0 - bulge, (y0 + y1) / 2), (x1, y1)]
        ax.add_patch(PathPatch(MPath(verts, [MPath.MOVETO, MPath.CURVE3, MPath.CURVE3]), facecolor="none",
                               edgecolor=color, lw=lw, alpha=alpha, zorder=z))
    else:
        ax.plot([x0, x1], [y0, y1], color=color, lw=lw, alpha=alpha, zorder=z, solid_capstyle="round")


def fig_proof_graph(G):
    pos = graph_layout(G)
    nodes = {n["name"]: n for n in G["nodes"]}
    fig, ax = plt.subplots(figsize=(COL2, 7.8))
    ax.set_axis_off()
    ax.grid(False)
    for a, b in G["proof_edges"]:
        _edge(ax, pos[a][:2], pos[b][:2], "#b9b8ad", 0.3, 0.6, 1)
    for a, b in G["statement_edges"]:
        _edge(ax, pos[a][:2], pos[b][:2], MODULE_COLOR[nodes[b]["module"]], 0.6, 0.75, 2)
    for name, (x, y, c) in pos.items():
        n = nodes[name]
        col = MODULE_COLOR[n["module"]]
        lab = short(name)
        bold = lab in MAIN_THEOREMS
        ax.scatter([x], [y], s=24 if bold else 12, marker="o" if n["kind"] == "theorem" else "s", color=col,
                   edgecolor="white", linewidth=0.5, zorder=4)
        side = LABEL_SIDE[c]
        ax.text(x + (0.045 if side == "right" else -0.045), y, lab, fontsize=4.9,
                ha="left" if side == "right" else "right", va="center", color=INK,
                fontweight="bold" if bold else "normal", zorder=5,
                bbox=dict(boxstyle="square,pad=0.02", facecolor="white", edgecolor="none", alpha=0.75))
    heads = [(COLS["num"] - 0.3, "Num"), (COLS["chk"] - 0.35, "Checker\n(executable)"),
             (COLS["spec"] - 0.35, "Spec\n(meaning)"), (COLS["snd"] + 0.85, "Soundness\n(theorems)"),
             ((COLS["schd"] + COLS["scht"]) / 2, "Schedule")]
    for x, t in heads:
        ax.text(x, 1.03, t, ha="center", va="bottom", fontsize=6.4, color=INK, fontweight="bold")
    ax.set_xlim(-1.0, 8.05)
    ax.set_ylim(-0.02, 1.08)
    handles = [Line2D([], [], marker="o", ls="", color=INK2, markersize=4, label="theorem (axiom-audited)"),
               Line2D([], [], marker="s", ls="", color=INK2, markersize=3.5, label="definition"),
               Line2D([], [], color=INK2, lw=0.9, label="used in statement (typeDeps)"),
               Line2D([], [], color="#b9b8ad", lw=0.6, label="used in proof / body (valueDeps)")]
    handles += [Line2D([], [], marker="s", ls="", color=MODULE_COLOR[m], markersize=4, label=short(m))
                for m in ["CryoLean.Num", "CryoLean.Checker", "CryoLean.Spec", "CryoLean.Soundness", "CryoLean.Schedule"]]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=5, fontsize=5.6,
              handletextpad=0.4, columnspacing=1.0)
    nT, nD = G["n_theorems"], G["n_defs"]
    save(fig, "fig_proof_graph", meta=dict(
        title="Proof dependency graph of the trusted Lean core",
        question="Which executable definitions and which specifications does each audited theorem talk about, and how "
                 "do the proofs build on each other?",
        model="Directed graph extracted statically from the elaborated Lean environment: an edge T->D is drawn solid "
              "when D occurs in the statement (type) of T and thin when D occurs only in its proof term or definition "
              "body (direct valueDeps restricted to the drawn nodes). Columns follow the module structure; order within "
              "a column minimises crossings (barycentre heuristic).",
        data=f"docs/forensics/cryolean-forensics.json ({G['n_decls_total']} declarations, for-all-dev/forensics "
             f"extractor); nodes = the {nT} theorems in lean/audit-axioms.json + {nD} key definitions; "
             f"{len(G['statement_edges'])} statement edges, {len(G['proof_edges'])} direct proof/definition edges "
             f"({G['proof_edges_transitive']} if followed through undrawn helper lemmas). "
             "Data: paper/data/fig_proof_graph.json.",
        claim="PROVEN+COMPUTED",
        caption=(f"Dependency structure of CryoLean's trusted Lean 4 core: the {nT} axiom-audited theorems (circles) and "
                 f"{nD} definitions they build on (squares), coloured by module. Solid edges are statement dependencies, "
                 "thin grey edges direct proof or definitional dependencies; both are extracted from the elaborated "
                 "environment by the forensics tool, not drawn by hand. The soundness theorems connect the executable "
                 "checker (Checker) to an independent specification (Spec: AcceptSpec, RejectSpec), and the schedule "
                 "theorems reuse the verdict. Bold labels mark headline theorems."),
        section="main"), interactive="fig_proof_graph.html")


def html_proof_graph(G):
    import plotly.graph_objects as go
    pos = graph_layout(G)
    nodes = {n["name"]: n for n in G["nodes"]}
    traces = []
    for edges, col, w, nm in [(G["proof_edges"], "#c3c2b7", 0.6, "proof / definition dependency"),
                              (G["statement_edges"], "#52514e", 1.0, "statement dependency")]:
        xs, ys = [], []
        for a, b in edges:
            xs += [pos[a][0], pos[b][0], None]
            ys += [pos[a][1], pos[b][1], None]
        traces.append(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=col, width=w), hoverinfo="skip", name=nm,
                                 opacity=0.6))
    for m in MODULE_ORDER:
        ns = [n for n in G["nodes"] if n["module"] == m]
        if not ns:
            continue
        hover = []
        for n in ns:
            doc = (n["doc"] or "").strip().replace("\n", " ")
            sig = "<br>".join(textwrap.wrap(n["signature"], 90))
            ax = ", ".join(n["axioms"]) or "none"
            hover.append(f"<b>{n['short']}</b> ({n['kind']}, {short(n['module'])})<br>{sig}<br><i>"
                         f"{'<br>'.join(textwrap.wrap(doc, 90))}</i><br>axioms: {ax}")
        traces.append(go.Scatter(
            x=[pos[n["name"]][0] for n in ns], y=[pos[n["name"]][1] for n in ns], mode="markers+text",
            marker=dict(color=MODULE_COLOR[m], size=[11 if n["kind"] == "theorem" else 9 for n in ns],
                        symbol=["circle" if n["kind"] == "theorem" else "square" for n in ns],
                        line=dict(color="white", width=1)),
            text=[n["short"] for n in ns], textfont=dict(size=9, color="#0b0b0b"),
            textposition=["middle right" if LABEL_SIDE[pos[n["name"]][2]] == "right" else "middle left" for n in ns],
            hovertext=hover, hoverinfo="text", name=short(m)))
    fig = go.Figure(traces)
    fig.update_layout(title="CryoLean trusted core: proof dependency graph (hover for signatures and axioms)",
                      xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor="white", height=1100,
                      width=1400, legend=dict(orientation="h"))
    return save_html(fig, "fig_proof_graph")


# =====================================================================================================================
# Figure 2: verdict flow (alluvial)
# =====================================================================================================================
def _band(ax, x0, x1, y0a, y0b, y1a, y1b, color, alpha, hatch=None):
    """Smooth band from [y0a,y0b] at x0 to [y1a,y1b] at x1 (cubic Bezier edges)."""
    xm = (x0 + x1) / 2
    verts = [(x0, y0a), (xm, y0a), (xm, y1a), (x1, y1a), (x1, y1b), (xm, y1b), (xm, y0b), (x0, y0b), (x0, y0a)]
    codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO, MPath.CURVE4, MPath.CURVE4,
             MPath.CURVE4, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color, edgecolor="none", alpha=alpha, zorder=1))


def alluvial(ax, left, right, flows, left_style, right_style, gap=0.025, w=0.035, xl=0.0, xr=1.0, unit=""):
    """left/right: ordered lists of node ids; flows: {(l, r): n}. Heights are proportional to n."""
    total = sum(flows.values())
    lt = {l: sum(n for (a, _), n in flows.items() if a == l) for l in left}
    rt = {r: sum(n for (_, b), n in flows.items() if b == r) for r in right}
    left = [l for l in left if lt[l] > 0]
    right = [r for r in right if rt[r] > 0]
    avail = 1 - gap * (max(len(left), len(right)) - 1)
    scale = avail / total

    def stack(ids, tot):
        used = sum(tot[i] for i in ids) * scale + gap * (len(ids) - 1)
        y = 1 - (1 - used) / 2
        pos = {}
        for i in ids:
            h = tot[i] * scale
            pos[i] = (y - h, y)
            y -= h + gap
        return pos

    lp, rp = stack(left, lt), stack(right, rt)
    loff = {l: lp[l][1] for l in left}
    roff = {r: rp[r][1] for r in right}
    for l in left:
        for r in right:
            n = flows.get((l, r), 0)
            if not n:
                continue
            h = n * scale
            ya, yb = loff[l], loff[l] - h
            za, zb = roff[r], roff[r] - h
            loff[l] -= h
            roff[r] -= h
            _band(ax, xl + w, xr - w, ya, yb, za, zb, right_style[r]["color"], 0.32)
    for side, ids, pp, tot, st, x in [("l", left, lp, lt, left_style, xl), ("r", right, rp, rt, right_style, xr - w)]:
        for i in ids:
            y0, y1 = pp[i]
            ax.add_patch(Rectangle((x, y0), w, y1 - y0, facecolor=st[i]["color"], hatch=st[i].get("hatch", ""),
                                   edgecolor="white", lw=0.4, zorder=3))
            lab = f"{st[i]['label']}  ({tot[i]:,}{unit})"
            if side == "l":
                ax.text(x - 0.01, (y0 + y1) / 2, lab, ha="right", va="center", fontsize=6.4, color=INK)
            else:
                ax.text(x + w + 0.01, (y0 + y1) / 2, lab, ha="left", va="center", fontsize=6.4, color=INK)
    ax.set_xlim(-0.36, 1.36)
    ax.set_ylim(-0.02, 1.02)
    ax.set_axis_off()
    return lp, rp


def fig_verdict_flow(D):
    vstyle = {v: {"color": VERDICT_COLOR[v], "hatch": VERDICT_HATCH[v], "label": VERDICT_SHORT[v]} for v in VERDICT_ORDER}
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(COL2, 5.8), gridspec_kw=dict(height_ratios=[1, 1], hspace=0.42))
    flows = {(x["outcome"], x["verdict"]): x["n"] for x in D["outcome_by_verdict"]}
    ostyle = {o: {"color": OUTCOME_COLOR[o], "label": OUTCOME_LABEL[o]} for o in OUTCOMES}
    alluvial(a1, OUTCOMES, VERDICT_ORDER, flows, ostyle, vstyle, unit="")
    a1.set_title(f"(a) Lean check outcome -> verdict of its pair ({D['relevant_checks']:,} mandatory checks, "
                 f"{D['pairs_confirmed']} pairs; width = checks)", loc="left", fontsize=7.2)
    ro = D["relevant_outcomes"]
    zero = [OUTCOME_LABEL[o] for o in OUTCOMES if not ro.get(o)]
    nr = D["non_relevant_checks_by_outcome"]
    note = (("Outcomes that never occur here: " + ", ".join(zero) + "." + chr(10)) if zero else "") + \
        f"Not drawn: {sum(nr.values())} optional or flagged-inapplicable checks (they never affect the verdict)."
    a1.text(0.5, -0.02, note, ha="center", va="top", fontsize=5.8, color=INK2, transform=a1.transAxes)
    bflows = {(x["branch"], x["verdict"]): x["n"] for x in D["branch_by_verdict"]}
    bl = {"fail": "confirmed, >=1 mandatory fail", "gap": "confirmed, no fail,\n>=1 unknown / unsupported",
          "allpass": "confirmed, all pass or N/A,\n>=1 pass", "nopass": "confirmed, no pass at all",
          "unconfirmed": "same pairs, profile\nnot confirmed"}
    bc = {"fail": ORANGE, "gap": LAVENDER, "allpass": NAVY, "nopass": MUTED, "unconfirmed": INK2}
    bstyle = {b: {"color": bc[b], "label": bl[b]} for b in bl}
    alluvial(a2, ["fail", "gap", "allpass", "nopass", "unconfirmed"], VERDICT_ORDER, bflows, bstyle, vstyle, unit=" pairs")
    a2.set_title(f"(b) Branch of `verdict` (Checker.lean) -> Lean verdict ({D['rule_total']} pair "
                 f"evaluations; width = pairs)", loc="left", fontsize=7.2)
    rule = ("verdict cfg e :=\n"
            "  if not e.confirmed            -> NEED INFO\n"
            "  elif fail in outcomes         -> NOT MET\n"
            "  elif all pass/N/A, >=1 pass   -> MET\n"
            "  else                          -> NEED INFO")
    a2.text(0.5, -0.03, rule, ha="center", va="top", fontsize=5.6, family="DejaVu Sans Mono", color=INK,
            multialignment="left",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f4f3ef", edgecolor=AXIS, lw=0.5),
            transform=a2.transAxes)
    vc = D["verdicts_confirmed"]
    unk_rej = sum(x["n"] for x in D["outcome_by_verdict"] if x["outcome"] == "unknown"
                  and x["verdict"] == "DOES_NOT_MEET_REQUIREMENTS")
    save(fig, "fig_verdict_flow", meta=dict(
        title="How check outcomes become verdicts",
        question="How do the per-check outcomes produced by the Lean checker combine into the three verdicts over the "
                 "real catalogue, and does every verdict follow the stated combination rule?",
        model="Combination rule of `verdict` in lean/CryoLean/Checker.lean: unconfirmed -> NEED_MORE_INFORMATION; any "
              "mandatory applicable fail -> DOES_NOT_MEET; all pass or not-applicable with at least one pass -> MET; "
              "otherwise NEED_MORE_INFORMATION. Outcomes are those of relevantReqs and relevantCoupled.",
        data=f"Two Lean check_batch runs over all {D['pairs_confirmed']} experiment x configuration pairs "
             f"(11 experiments x 26 configurations), confirmed and unconfirmed; {D['relevant_checks']} mandatory "
             "applicable checks. Script paper/scripts/fig_formal.py; data paper/data/fig_verdict_flow.json; verdicts "
             f"agree with paper/data/e1_grid.json for {D['confirmed_agrees_with_e1_grid']}/{D['pairs_confirmed']} pairs.",
        claim="COMPUTED+PROVEN",
        caption=(f"(a) Every mandatory, applicable check outcome produced by the Lean checker over the "
                 f"{D['pairs_confirmed']}-pair grid, routed to the verdict of its pair (band width = number of checks). "
                 f"(b) The same pairs grouped by the branch of the `verdict` definition they reach, plus the same pairs "
                 f"with unconfirmed profiles. All {D['rule_total']} Lean verdicts match the branch, and confirmed "
                 f"verdicts are {vc.get('REQUIREMENTS_MET', 0)} MET, {vc.get('NEED_MORE_INFORMATION', 0)} NEED INFO and "
                 f"{vc.get('DOES_NOT_MEET_REQUIREMENTS', 0)} NOT MET; {unk_rej} of the checks inside NOT MET pairs are "
                 "themselves unknown, because one trusted failure suffices to reject. Verdicts and outcomes are computed "
                 "by Lean; the rule is the definition proven correct by verdict_accept_iff and "
                 "verdict_reject_sound/complete."),
        section="main"))


# =====================================================================================================================
# Figure 3: guarantee coverage matrix
# =====================================================================================================================
GUARANTEE_TESTS = {
    "1": ["test_control_all_documented_accepts", "test_01_temperature_compatibility", "test_15_lean_accepts_valid_candidate",
          "test_lean1_absent_requirement_met_by_option_not_installed"],
    "2": ["test_unknown_capabilities_never_supported", "test_11_missing_mandatory_manufacturer_data",
          "test_unconfirmed_profile_never_accepted", "test_f2_confirmation_is_strict"],
    "3": ["test_12_unsupported_physical_requirements", "test_lean2_3_4_decoder_fails_closed", "test_exact_units_no_floats",
          "test_f5_internal_num_den_and_floats_refused_from_users"],
    "4": ["test_04_magnetic_field_incompatibility", "test_05_missing_measurement_accessory",
          "test_10_vacuum_incompatibility", "test_untrusted_not_installed_record_never_rejects"],
    "5": ["test_03_insufficient_cooling_power", "test_07_thermal_load_exceeds_cooling_capacity",
          "test_17_independent_checks_pass_coupled_fails", "test_09_thermal_contraction_constraint"],
    "6": ["test_optional_requirement_does_not_block", "test_smt2_optional_unknown_value_agrees_with_lean"],
    "7": ["test_conditional_requirement_not_applicable_is_not_a_failure"],
    "8": ["test_installed_documented_vs_proposed_modifications", "test_05_missing_measurement_accessory",
          "test_lean1_absent_requirement_met_by_option_not_installed", "test_f8_cooling_slot_uses_installed_capabilities_only"],
    "9": ["test_16_equipment_switching_invalidates_results", "test_16b_stored_result_refused_after_catalog_change",
          "test_f1_alternatives_and_search_respect_modifications"],
    "10": ["test_ai_cannot_weaken_or_invent", "test_injected_verdict_in_document_is_ignored", "test_ai_matching_examples"],
    "11": ["test_13_14_z3_proposes_invalid_configuration_lean_rejects", "test_15_lean_accepts_valid_candidate"],
    "12": ["test_18_register_previously_unknown_industry", "test_19_same_lean_core_across_industries",
           "test_19b_industry_label_cannot_change_verdict"],
    "13": ["test_schedule_packs_only_accepted_and_lean_validates", "test_lean_rejects_tampered_schedules",
           "test_schedule_refuses_rejected_experiment_in_lean", "test_schedule_too_long_gives_unsat_core"],
    "A": ["test_smt6_inverted_range_is_not_satisfiable_in_z3"],
    "B": ["test_exact_units_no_floats"],
}
# evaluation experiments in paper/data that exercise a guarantee at scale (read, not recomputed)
GUARANTEE_EVAL = {"2": "e4_faults", "4": "e4_faults", "8": "e4_faults", "11": "e3_search", "13": "e6_schedule"}
SHORT_G = {"1": "ACCEPT => every applicable mandatory requirement passes",
           "2": "Missing mandatory information cannot give ACCEPT",
           "3": "Unsupported requirements (dimension/shape/model) cannot give ACCEPT",
           "4": "A confirmed mandatory failure prevents ACCEPT; REJECT rests on trusted evidence",
           "5": "Every applicable mandatory coupled constraint passes before ACCEPT",
           "6": "Optional requirements do not block acceptance",
           "7": "Non-applicable requirements cause no false failures",
           "8": "Installed accessories are distinguished from optional ones",
           "9": "A verdict applies only to the exact configuration and experiment",
           "10": "AI cannot bypass the gate",
           "11": "Z3 cannot override a Lean rejection",
           "12": "New industries cannot bypass mandatory checking",
           "13": "A campaign schedule is accepted only if bounds, disjointness and acceptance hold",
           "A": "ACCEPT/REJECT specs exclusive; coupled-expression evaluation sound and complete",
           "B": "The rational order is independent of representation"}


def parse_scope():
    rows = []
    for line in SCOPE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+|—)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        num, text, thm = m.groups()
        names = re.findall(r"`([A-Za-z_.]+)`", thm)
        rows.append({"num": num, "text": text, "theorem_cell": thm, "theorems": [n for n in names if n not in ("CoupledOK", '"verdict"')]})
    aux = iter("AB")
    for r in rows:
        if r["num"] == "—":
            r["num"] = next(aux)
    return rows


def run_tests():
    with tempfile.TemporaryDirectory() as td:
        xmlp = Path(td) / "junit.xml"
        t0 = time.perf_counter()
        p = subprocess.run([sys.executable, "-m", "pytest", "-m", "not slow", "-q", "-p", "no:cacheprovider",
                            f"--junitxml={xmlp}"], cwd=ROOT, capture_output=True, text=True)
        dt = time.perf_counter() - t0
        tree = ET.parse(xmlp)
    res = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0, "file": None})
    for tc in tree.iter("testcase"):
        base = tc.get("name").split("[")[0]
        st = "failed" if (tc.find("failure") is not None or tc.find("error") is not None) else \
             "skipped" if tc.find("skipped") is not None else "passed"
        res[base][st] += 1
        res[base]["file"] = tc.get("classname")
    suite = tree.getroot().find("testsuite") if tree.getroot().tag == "testsuites" else tree.getroot()
    return {"command": "python -m pytest -m 'not slow'", "returncode": p.returncode, "seconds": dt,
            "tests": int(suite.get("tests")), "failures": int(suite.get("failures")), "errors": int(suite.get("errors")),
            "skipped": int(suite.get("skipped")), "deselected_slow": re.findall(r"(\d+) deselected", p.stdout),
            "by_test": dict(res)}


def compute_guarantees(tests):
    A = jload(AUDIT)
    F = jload(FORENSICS)
    FS = jload(FORENSICS_SUMMARY)
    N = {d["name"]: d for d in F["decls"]}
    std = set(A["standard_axioms"])
    rows = []
    for g in parse_scope():
        # names in back-ticks that are definitions (e.g. `verdict`, `CoupledOK`) are context, not theorems
        thms = [t for t in g["theorems"] if N.get("CryoLean." + t, {"kind": "theorem"})["kind"] == "theorem"]
        present = [t for t in thms if "CryoLean." + t in N]
        audited = [t for t in thms if t in A["theorems"]]
        std_ok = [t for t in audited if set(A["theorems"][t]) <= std]
        clean = [t for t in present if not N["CryoLean." + t]["smells"] and not N["CryoLean." + t]["flags"]
                 and set(N["CryoLean." + t]["axioms"]) <= std]
        ax_union = [a for a in ("propext", "Quot.sound", "Classical.choice") if any(a in A["theorems"][t] for t in audited)]
        tnames = GUARANTEE_TESTS.get(g["num"], [])
        tres = {t: tests["by_test"].get(t) for t in tnames}
        t_pass = sum(1 for v in tres.values() if v and v["failed"] == 0 and v["passed"] > 0)
        t_cases = sum(v["passed"] + v["failed"] for v in tres.values() if v)
        rows.append({"num": g["num"], "text": g["text"], "short": SHORT_G[g["num"]], "theorems": thms,
                     "theorems_in_lean": present, "audited": audited, "standard_axioms_only": std_ok, "axioms_union": ax_union,
                     "forensics_clean": clean, "tests": tnames, "tests_passed": t_pass, "test_cases_run": t_cases,
                     "test_cases": {t: v for t, v in tres.items()}, "evaluation": GUARANTEE_EVAL.get(g["num"])})
    rows = [r for r in rows if r["num"].isdigit()] + [r for r in rows if not r["num"].isdigit()]
    return {"rows": rows, "tests": {k: v for k, v in tests.items() if k != "by_test"}, "forensics_summary": FS,
            "failing_tests": sorted(k for k, v in tests["by_test"].items() if v["failed"]),
            "audit_count": A["count"], "audit_all_standard": A["all_standard"], "audit_source_hash": A["source_hash"],
            "audit_freshness": audit_freshness()}


def audit_freshness():
    """Is lean/audit-axioms.json current for the working tree (cryolean.lean_runner.axiom_audit), and if not, could
    the edits reach the audited theorems?  Lean declarations can only depend on imported modules, so an edited file
    outside the import closure of the theorem modules cannot change their axioms."""
    from cryolean import lean_runner
    status = lean_runner.axiom_audit()["status"]
    t_audit = AUDIT.stat().st_mtime
    src = ROOT / "lean" / "CryoLean"
    files = sorted(src.glob("*.lean")) + [ROOT / "lean" / "Main.lean"]
    modified = [p.name for p in files if p.stat().st_mtime > t_audit]
    b = lean_runner.lean_binary()
    binary_modified = bool(b and b.stat().st_mtime > t_audit)
    imports = {p.stem: re.findall(r"^import CryoLean\.(\w+)", p.read_text(encoding="utf-8"), flags=re.M)
               for p in src.glob("*.lean")}
    closure, stack = set(), ["Num", "Soundness", "Schedule"]          # modules that hold the 44 audited theorems
    while stack:
        m = stack.pop()
        if m not in closure:
            closure.add(m)
            stack.extend(imports.get(m, []))
    reach = [f for f in modified if f.endswith(".lean") and f[:-5] in closure]
    return {"status": status, "modified_after_audit": modified, "binary_rebuilt_after_audit": binary_modified,
            "theorem_import_closure": sorted(closure), "modified_in_closure": reach}


STATUS_STYLE = {"covered": ("#d6e6f7", "", "covered"), "partial": ("#ece8fb", "////", "partial"),
                "none": ("#ffffff", "xx", "none")}


def _compact_names(names):
    """validSchedule_a, validSchedule_b -> validSchedule_{a, b} (only when all share the prefix)."""
    if len(names) > 3 and all(n.startswith("validSchedule_") for n in names):
        return "validSchedule_{" + ", ".join(n[len("validSchedule_"):] for n in names) + "}"
    return ", ".join(names)


def fig_guarantees(D):
    rows = D["rows"]
    evals = {}
    for k in ("e4_faults", "e3_search", "e6_schedule"):
        try:
            evals[k] = load(k)
        except FileNotFoundError:
            pass

    def eval_text(name):
        if name == "e4_faults" and name in evals:
            e = evals[name]
            nctl = sum(e["by_defect"].get("control", {}).values())
            return (f"E4: {e['accepted_with_a_defect']} of {e['cases'] - nctl:,} faulty configurations accepted "
                    f"(+{nctl} controls)")
        if name == "e3_search" and name in evals:
            ct = evals[name]["crosstab"]
            n = sum(x["n"] for x in ct)
            met = sum(x["n"] for x in ct if x["lean"] == "REQUIREMENTS_MET")
            return f"E3: {n} Z3 candidates, each verdict from Lean ({met} met)"
        if name == "e6_schedule" and name in evals:
            e = evals[name]
            agree = sum(x["n"] for x in e["lean_vs_independent"] if x["lean_valid"] == x["python_valid"])
            return f"E6: Lean matches an independent re-check on {agree}/{e['tamper_cases']} tampered schedules"
        return ""

    cols = [("Guarantee", 1.9), ("Lean theorem(s)", 1.95), ("Axiom audit", 0.92),
            ("Tests and evaluation", 1.48), ("Forensics", 0.8)]
    W = sum(w for _, w in cols)
    rh = 0.47
    head = 0.3
    foot = 0.62 if D["audit_freshness"]["status"] != "current" else 0.46
    H = rh * len(rows) + head + foot
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(-len(rows) * rh - foot, head)
    ax.set_axis_off()
    xs, x = [], 0.0
    for name, w in cols:
        xs.append(x)
        ax.text(x + 0.05, head / 2, name, fontsize=6.3, fontweight="bold", va="center", color=INK)
        x += w
    statuses = []
    for i, r in enumerate(rows):
        y = -(i + 1) * rh
        lab = r["num"] if r["num"].isdigit() else f"aux {r['num']}"
        ax.text(0.05, y + rh / 2, lab, fontsize=6.2, fontweight="bold", va="center", color=INK)
        ax.text(0.40, y + rh / 2, "\n".join(textwrap.wrap(r["short"], 34)), fontsize=5.4, va="center", color=INK)
        n_t = len(r["theorems"])
        # column 1: theorems
        if n_t == 0:
            s1, t1 = "none", "no theorem: holds by construction\n(the Lean input type has no AI field)"
        elif len(r["theorems_in_lean"]) == n_t:
            s1 = "covered" if r["num"] != "9" else "partial"
            t1 = "\n".join(textwrap.wrap(_compact_names(r["theorems"]), 43))
            if r["num"] == "9":
                t1 += "\n(verdict_deterministic: congruence only)"
        else:
            s1, t1 = "partial", f"{len(r['theorems_in_lean'])}/{n_t} found in Lean"
        # column 2: axiom audit
        if n_t == 0:
            s2, t2 = "none", "n/a"
        elif len(r["standard_axioms_only"]) == n_t:
            s2 = "covered" if not D["audit_freshness"]["modified_in_closure"] else "partial"
            t2 = f"{n_t}/{n_t} standard only:\n" + "\n".join(textwrap.wrap(", ".join(r["axioms_union"]), 22))
        else:
            s2, t2 = "partial", f"{len(r['standard_axioms_only'])}/{n_t} audited"
        # column 3: tests and evaluation
        nt = len(r["tests"])
        s3 = "covered" if nt and r["tests_passed"] == nt else ("partial" if r["tests_passed"] else "none")
        nc = r["test_cases_run"]
        t3 = f"{r['tests_passed']}/{nt} mapped tests pass ({nc} case{'s' if nc != 1 else ''})"
        ev = eval_text(r["evaluation"]) if r["evaluation"] else ""
        if ev:
            t3 += "\n" + "\n".join(textwrap.wrap(ev, 36))
        # column 4: forensics
        if n_t == 0:
            s4, t4 = "none", "n/a"
        elif len(r["forensics_clean"]) == n_t:
            s4, t4 = "covered", f"{n_t}/{n_t} clean"
            if r["num"] == "4":
                t4 += "\n(gap found\nand fixed)"
            elif r["num"] == "3":
                t4 += "\n(statement\ngeneralised)"
            elif r["num"] == "9":
                s4, t4 = "partial", f"{n_t}/{n_t} clean;\n1 is congruence"
        else:
            s4, t4 = "partial", f"{len(r['forensics_clean'])}/{n_t} clean"
        statuses.append({"num": r["num"], "lean": s1, "audit": s2, "tests": s3, "forensics": s4})
        for j, (s, t) in enumerate([(s1, t1), (s2, t2), (s3, t3), (s4, t4)], start=1):
            fc, hatch, word = STATUS_STYLE[s]
            ax.add_patch(Rectangle((xs[j] + 0.02, y + 0.02), cols[j][1] - 0.04, rh - 0.04, facecolor=fc, hatch=hatch,
                                   edgecolor="#b9c7dd" if s != "none" else AXIS, lw=0.4, zorder=1))
            box = dict(boxstyle="square,pad=0.08", facecolor=fc, edgecolor="none") if hatch else None
            # status word on its own top line, content top-aligned below it: nothing can overlap
            ax.text(xs[j] + cols[j][1] - 0.06, y + rh - 0.045, word, fontsize=4.4, va="top", ha="right", color=INK2,
                    zorder=3, fontstyle="italic", bbox=box)
            ax.text(xs[j] + 0.07, y + rh - 0.12, t, fontsize=4.8 if j == 1 else 5.0, va="top", color=INK, zorder=3,
                    linespacing=1.15, family="DejaVu Sans Mono" if j == 1 else "DejaVu Sans", bbox=box)
        ax.plot([0, W], [y, y], color=GRID, lw=0.4, zorder=0)
    handles = [Patch(facecolor=STATUS_STYLE[s][0], hatch=STATUS_STYLE[s][1], edgecolor="#b9c7dd", label=s)
               for s in ("covered", "partial", "none")]
    ax.legend(handles=handles, loc="upper left", ncol=3, fontsize=6, bbox_to_anchor=(0.0, (foot - 0.02) / H),
              frameon=False)
    T = D["tests"]
    fs = D["forensics_summary"]
    AF = D["audit_freshness"]
    nf = T["failures"] + T["errors"]
    line1 = (f"tests: {T['tests']} fast tests run here, " + ("all pass" if not nf else
             f"{T['tests'] - nf} pass, {nf} fail ({', '.join(D['failing_tests'])})") +
             f"   |   forensics: {fs['declarations']} declarations, {len(fs['nonstandard_axioms'])} non-standard axioms, "
             f"{len(fs['statement_smells'])} smells, {len(fs['unsafe_flags'])} unsafe flags")
    line2 = ""
    if AF["status"] != "current":
        line2 = (f"axiom-audit cache {AF['status']}: {', '.join(AF['modified_after_audit']) or 'binary'} edited after "
                 "the audit; " + ("none is imported by the theorem modules (Num, Soundness, Schedule), so their axioms "
                                  "are unaffected" if not AF["modified_in_closure"] else
                                  "imported by the theorem modules: audit must be re-run"))
    ax.text(0.05, -len(rows) * rh - 0.36, line1, ha="left", va="center", fontsize=5.2, color=INK2)
    if line2:
        ax.text(0.05, -len(rows) * rh - 0.5, line2, ha="left", va="center", fontsize=5.2, color=INK2)
    D["statuses"] = statuses
    numbered = [s for s in statuses if s["num"].isdigit()]
    D["rows_fully_covered"] = sum(1 for s in numbered if all(s[k] == "covered" for k in ("lean", "audit", "tests", "forensics")))
    D["rows_numbered"] = len(numbered)
    save(fig, "fig_guarantees", meta=dict(
        title="Formal guarantee coverage",
        question="For each guarantee CryoLean claims, which Lean theorem states it, does that theorem use only standard "
                 "axioms, is it exercised by a runtime test, and did the independent forensics audit find it clean?",
        model="Coverage matrix. Theorem column: theorem names listed in VERIFICATION_SCOPE.md and found in the elaborated "
              "environment. Audit: axioms from lean/audit-axioms.json (#print axioms). Tests: tests mapped to each "
              "guarantee by reading tests/*.py, run now with pytest -m 'not slow'. Forensics: per-declaration axioms, "
              "smells and flags from the for-all-dev/forensics extractor.",
        data=f"VERIFICATION_SCOPE.md (13 guarantees + 2 auxiliary rows); lean/audit-axioms.json ({D['audit_count']} "
             f"theorems, source hash {D['audit_source_hash'][:12]}); tests/*.py run here ({T['tests']} tests, "
             f"{T['failures']} failures, {T['seconds']:.0f} s); docs/forensics/cryolean-forensics.json + summary.json; "
             "evaluation summaries read from paper/data/e3_search.json, e4_faults.json, e6_schedule.json. "
             "Data: paper/data/fig_guarantees.json.",
        claim="PROVEN+COMPUTED",
        caption=(f"Coverage of CryoLean's guarantees by four independent kinds of evidence. {D['rows_fully_covered']} of "
                 f"the {D['rows_numbered']} numbered guarantees are stated by named Lean theorems that the kernel checks, "
                 "use only the standard axioms (propext, Quot.sound, Classical.choice), are exercised by passing runtime "
                 "tests and were found clean by the forensics audit. Guarantee 10 (AI cannot bypass the gate) holds by "
                 "construction, since the checker's input type has no AI field, and is covered by tests only; guarantee 9 "
                 "is partial because verdict_deterministic is plain congruence. Theorem and axiom facts are PROVEN by the "
                 "Lean kernel; test outcomes were computed on this machine."),
        section="main"))


# =====================================================================================================================
# Figure 4: rejection margins
# =====================================================================================================================
REQ_ORDER = ["magnetic_field.max", "temperature.range", "module.electrical_transport", "sample.width.max",
             "sample.length.max", "sample.height.max"]
REQ_LABEL = {"magnetic_field.max": "field\n>= 10 T", "temperature.range": "operate\nat 2 K",
             "module.electrical_transport": "transport\nmodule", "sample.width.max": "width\n>= 3 mm",
             "sample.length.max": "length\n>= 3 mm", "sample.height.max": "height\n>= 3 mm"}


def unknown_reason(c, m=None):
    """Why Lean reported a check as unknown, read from the capability record Lean saw (no re-judging)."""
    doc = c.get("documented")
    if doc is None:
        return "not documented"
    if doc.get("kind") == "unknown":
        if c.get("install") == "unknown":
            return "fit unknown"
        if c.get("install") == "optional_not_installed":
            return "not fitted,|unsourced"
        return "value unknown"
    if c.get("evidence_status") in ("inferred_estimate", "unknown"):
        return f"estimate {m:.2f}" if m is not None else "estimate"
    if c.get("install") != "installed":
        return "install unknown"
    return c.get("outcome", "unknown")


def fig_rejection_margins(D):
    from matplotlib.colors import Normalize
    rows = D["rows"]
    vrank = {"REQUIREMENTS_MET": 0, "NEED_MORE_INFORMATION": 1, "DOES_NOT_MEET_REQUIREMENTS": 2}
    rows = sorted(rows, key=lambda r: (vrank[r["verdict"]], r["family"] or "", r["configuration"]))
    keys = [k for k in REQ_ORDER if any(c["key"] == k for r in rows for c in r["cells"])]
    extra = sorted({c["key"] for r in rows for c in r["cells"]} - set(keys))
    keys += extra
    nR, nC = len(rows), len(keys)
    fig, ax = plt.subplots(figsize=(COL2, 0.205 * nR + 1.25))
    ax.grid(False)
    norm = Normalize(-2, 2)
    vx = nC + 0.25
    for i, r in enumerate(rows):
        cells = {c["key"]: c for c in r["cells"]}
        for j, k in enumerate(keys):
            c = cells.get(k)
            if c is None:
                continue
            o = c["outcome"]
            m = c.get("margin_float")
            if o in ("pass", "fail") and m is not None:
                col = DIV_CMAP(norm(np.clip(np.log2(m), -2, 2)))
                txt, hatch = (f"{m:.2f}" if m < 10 else f"{m:.0f}"), ""
            elif o in ("pass", "fail"):
                col = DIV_CMAP(norm(1.2)) if o == "pass" else DIV_CMAP(norm(-1.2))
                txt, hatch = ("present" if o == "pass" else "absent"), ""
            else:
                col = VERDICT_COLOR["NEED_MORE_INFORMATION"]
                hatch = VERDICT_HATCH["NEED_MORE_INFORMATION"]
                txt = unknown_reason(c, m)
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=col, hatch=hatch, edgecolor="white", lw=0.8))
            two = "|" in txt
            txt = txt.replace("|", chr(10))
            ax.text(j + 0.5, i + 0.52, txt, ha="center", va="center", fontsize=4.9 if two else 5.4, color=INK,
                    linespacing=0.95,
                    bbox=dict(boxstyle="square,pad=0.06", facecolor=col, edgecolor="none", alpha=0.85) if hatch else None)
            if o == "fail":
                ax.text(j + 0.95, i + 0.5, "x", ha="right", va="center", fontsize=5.0, color=INK, fontweight="bold")
        v = r["verdict"]
        ax.add_patch(Rectangle((vx, i), 1.35, 1, facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white", lw=0.8))
        ax.text(vx + 0.675, i + 0.52, VERDICT_SHORT[v], ha="center", va="center", fontsize=5.4, color=INK,
                fontweight="bold", bbox=dict(boxstyle="square,pad=0.08", facecolor=VERDICT_COLOR[v], edgecolor="none"))
    ax.set_xlim(0, vx + 1.35)
    ax.set_ylim(nR, 0)
    ax.set_yticks(np.arange(nR) + 0.5)
    ax.set_yticklabels([r["configuration"] for r in rows], fontsize=5.6)
    ax.set_xticks(list(np.arange(nC) + 0.5) + [vx + 0.675])
    ax.set_xticklabels([REQ_LABEL.get(k, k) for k in keys] + ["Lean\nverdict"], fontsize=6)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    # boundaries between verdict groups
    for i in range(1, nR):
        if rows[i]["verdict"] != rows[i - 1]["verdict"]:
            ax.plot([0, vx + 1.35], [i, i], color=INK, lw=0.8)
    cax = fig.add_axes([0.16, 0.035, 0.36, 0.012])
    sm = plt.cm.ScalarMappable(norm=norm, cmap=DIV_CMAP)
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=[-2, -1, 0, 1, 2])
    cb.ax.set_xticklabels(["<=0.25", "0.5", "1 (limit)", "2", ">=4"], fontsize=5.6)
    cb.set_label("margin = documented / required (log scale; < 1 violates)", fontsize=6)
    cb.outline.set_linewidth(0.4)
    present = [v for v in VERDICT_ORDER if any(r["verdict"] == v for r in rows)]
    handles = [Patch(facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white",
                     label=VERDICT_LABEL[v] + (" (verdict) /\ncheck unknown to Lean (cell)" if v == "NEED_MORE_INFORMATION"
                                               else " (verdict)")) for v in present]
    handles.append(Line2D([], [], ls="", marker="$x$", color=INK, markersize=5, label="check fails in Lean"))
    fig.legend(handles=handles, loc="lower right", bbox_to_anchor=(0.995, 0.0), ncol=1, fontsize=5.6)
    fig.subplots_adjust(left=0.24, right=0.99, top=0.93, bottom=0.095)
    vc = D["verdicts"]
    n_fail = sum(1 for r in rows for c in r["cells"] if c["outcome"] == "fail")
    summ = {"outcomes_by_requirement": {k: dict(Counter(c["outcome"] for r in rows for c in r["cells"] if c["key"] == k))
                                        for k in keys},
            "unknown_reasons": dict(Counter(unknown_reason(c).split(" ")[0] if unknown_reason(c).startswith("estimate")
                                            else unknown_reason(c).replace("|", " ")
                                            for r in rows for c in r["cells"] if c["outcome"] not in ("pass", "fail"))),
            "fail_cells": n_fail,
            "rejected_with_unknown_checks": sum(1 for r in rows if r["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
                                                and any(c["outcome"] == "unknown" for c in r["cells"])),
            "rejected_by_single_failure": sum(1 for r in rows if sum(c["outcome"] == "fail" for c in r["cells"]) == 1),
            "need_info_with_no_failure": sum(1 for r in rows if r["verdict"] == "NEED_MORE_INFORMATION"
                                             and not any(c["outcome"] == "fail" for c in r["cells"])),
            "failing_margins": {r["configuration"]: {c["key"]: c.get("margin_float") for c in r["cells"]
                                                     if c["outcome"] == "fail"} for r in rows
                                if any(c["outcome"] == "fail" for c in r["cells"])}}
    D["summary"] = summ
    save(fig, "fig_rejection_margins", meta=dict(
        title="Why each configuration passes or fails the 10 T magnetoresistance experiment",
        question="For one real experiment, which mandatory requirement decides the verdict on each of the 26 catalogued "
                 "configurations, and by how much does the documented value clear or miss it?",
        model=D["margin_definition"] + ". Colour encodes log2(margin); the pass/fail/unknown status of each cell is "
              "Lean's outcome, not the ratio.",
        data=f"Lean check_batch of {EXP_MR} (confirmed) against all {len(rows)} configurations (same run as "
             "fig_verdict_flow); documented values from the Lean result's per_key capability (sourced from "
             f"data/cryostats/*.json). Margin sign agrees with Lean's outcome in {D['margin_consistent_with_lean_outcome']} "
             f"of {D['margin_consistent_with_lean_outcome'] + D['margin_inconsistent']} numeric cells. "
             "Data: paper/data/fig_rejection_margins.json.",
        claim="COMPUTED+SOURCED",
        caption=(f"Mandatory requirements of the 10 T magnetoresistance profile against all {len(rows)} configurations. "
                 "Numbers are the documented capability divided by the requirement (for the 2 K operating point, the "
                 "smaller of T/T_min and T_max/T), computed from the exact rationals in the Lean result; x marks a "
                 "check that Lean reports as failing. Dotted yellow cells are checks Lean reports as unknown; the cell "
                 "text gives the reason read from the capability record (not documented, value unknown, fitting unknown, "
                 "an unsourced not-fitted claim, or an inferred estimate, which never counts as evidence). Lean verdicts: "
                 f"{vc.get('REQUIREMENTS_MET', 0)} met, {vc.get('NEED_MORE_INFORMATION', 0)} need information, "
                 f"{vc.get('DOES_NOT_MEET_REQUIREMENTS', 0)} not met; all {summ['rejected_with_unknown_checks']} "
                 "rejected configurations also have unknown checks, because one trusted failure suffices to reject."),
        section="main"))
    return n_fail


# =====================================================================================================================
# Figure 5: proof statistics
# =====================================================================================================================
def compute_stats():
    e8 = load("e8_proofs")
    A = jload(AUDIT)
    F = jload(FORENSICS)
    FS = jload(FORENSICS_SUMMARY)
    sets = Counter(tuple(sorted(v)) for v in A["theorems"].values())
    by_set = defaultdict(list)
    for t, v in A["theorems"].items():
        by_set[tuple(sorted(v))].append(t)
    N = {d["name"]: d for d in F["decls"]}
    agree = sum(1 for t, v in A["theorems"].items() if set(N["CryoLean." + t]["axioms"]) == set(v))
    kinds = Counter(d["kind"] for d in F["decls"])
    # theorems written in the sources (regex over lean/CryoLean/*.lean) vs. generated by the elaborator
    src_thms = set()
    for p in sorted((ROOT / "lean" / "CryoLean").glob("*.lean")):
        src_thms |= set(re.findall(r"^\s*(?:private\s+)?theorem\s+([^\s(:{\[]+)", p.read_text(encoding="utf-8"), flags=re.M))
    fthms = [d["name"] for d in F["decls"] if d["kind"] == "theorem"]
    hand = [n for n in fthms if n[len("CryoLean."):] in src_thms]
    gen = [n for n in fthms if n not in set(hand)]
    gen_kinds = Counter(n.rsplit(".", 1)[-1] for n in gen)
    fx_axsets = Counter(tuple(sorted(d["axioms"])) for d in F["decls"])
    fx_thm_axsets = Counter(tuple(sorted(d["axioms"])) for d in F["decls"] if d["kind"] == "theorem")
    mod_kind = defaultdict(Counter)
    for d in F["decls"]:
        mod_kind[d["module"]][d["kind"]] += 1
    # per-file counts recomputed from the current sources with the same rules as paper_eval.py E8, so the figure follows
    # the working tree; differences from the stored e8_proofs.json snapshot are recorded
    files = {}
    for p in sorted((ROOT / "lean" / "CryoLean").glob("*.lean")):
        t = p.read_text(encoding="utf-8")
        files[p.stem] = {"lines": len(t.splitlines()),
                         "theorems": len(re.findall(r"^\s*(?:private\s+)?theorem\s", t, flags=re.M)),
                         "defs": len(re.findall(r"^\s*(?:private\s+|partial\s+|noncomputable\s+)?(?:def|inductive|structure|"
                                                r"abbrev|instance)\s", t, flags=re.M))}
    e8_diff = {f: {"e8": e8["files"].get(f), "now": v} for f, v in files.items() if e8["files"].get(f) != v}
    return {"files": files, "e8_snapshot_differs": e8_diff, "audit_source_hash": A["source_hash"],
            "audited": len(A["theorems"]), "axiom_sets": [{"axioms": list(k), "n": v, "theorems": by_set[k]}
                                                                              for k, v in sets.most_common()],
            "axiom_use": dict(Counter(a for v in A["theorems"].values() for a in v)),
            "audit_matches_forensics": agree, "forensics_summary": FS, "forensics_kinds": dict(kinds),
            "forensics_axiom_sets_all": [{"axioms": list(k), "n": v} for k, v in fx_axsets.most_common()],
            "forensics_axiom_sets_theorems": [{"axioms": list(k), "n": v} for k, v in fx_thm_axsets.most_common()],
            "forensics_by_module": {m: dict(c) for m, c in mod_kind.items()},
            "source_theorems": len(src_thms), "forensics_theorems_handwritten": len(hand),
            "forensics_theorems_generated": len(gen), "generated_theorem_kinds": dict(gen_kinds.most_common()),
            "totals_regex": {k: sum(f[k] for f in files.values()) for k in ("lines", "theorems", "defs")},
            "totals_e8": {k: sum(f[k] for f in e8["files"].values()) for k in ("lines", "theorems", "defs")}}


def fig_proof_stats(S):
    files = S["files"]
    order = sorted(files, key=lambda f: -files[f]["lines"])
    fig = plt.figure(figsize=(COL2, 4.4))
    gs = fig.add_gridspec(2, 2, hspace=0.62, wspace=0.42, height_ratios=[1, 1])
    a = fig.add_subplot(gs[0, 0])
    y = np.arange(len(order))
    a.barh(y, [files[f]["lines"] for f in order], color=NAVY, height=0.62)
    for i, f in enumerate(order):
        a.text(files[f]["lines"] + 15, i, f"{files[f]['lines']:,}", va="center", fontsize=6, color=INK)
    a.set_yticks(y)
    a.set_yticklabels([f + ".lean" for f in order])
    a.invert_yaxis()
    a.set_xlabel("lines of Lean")
    a.set_xlim(0, max(files[f]["lines"] for f in order) * 1.18)
    a.grid(axis="y", visible=False)
    T = S["totals_regex"]
    a.set_title(f"(a) Lean core: {T['lines']:,} lines in {len(files)} files", loc="left", fontsize=7.5)

    b = fig.add_subplot(gs[0, 1])
    h = 0.38
    b.barh(y - h / 2, [files[f]["defs"] for f in order], height=h, color=LAVENDER, label="definitions and types")
    b.barh(y + h / 2, [files[f]["theorems"] for f in order], height=h, color=NAVY, label="theorems")
    for i, f in enumerate(order):
        b.text(files[f]["defs"] + 1, i - h / 2, str(files[f]["defs"]), va="center", fontsize=5.5, color=INK)
        b.text(files[f]["theorems"] + 1, i + h / 2, str(files[f]["theorems"]), va="center", fontsize=5.5, color=INK)
    b.set_yticks(y)
    b.set_yticklabels([f + ".lean" for f in order])
    b.invert_yaxis()
    b.set_xlabel("source declarations (count)")
    b.set_xlim(0, max(max(files[f]["defs"], files[f]["theorems"]) for f in order) * 1.15)
    b.grid(axis="y", visible=False)
    b.legend(loc="lower right", fontsize=6)
    b.set_title(f"(b) {T['defs']} definitions/types, {T['theorems']} theorems", loc="left", fontsize=7.5)

    c = fig.add_subplot(gs[1, 0])
    label = {("propext",): "propext only", ("Quot.sound", "propext"): "propext + Quot.sound",
             ("Classical.choice", "Quot.sound", "propext"): "propext + Quot.sound\n+ Classical.choice", (): "none"}
    sets = S["axiom_sets"]
    allsets = [("propext",), ("Quot.sound", "propext"), ("Classical.choice", "Quot.sound", "propext"), ()]
    cnt = {tuple(x["axioms"]): x["n"] for x in sets}
    ys = np.arange(len(allsets))
    cols = [ICY, LAVENDER, NAVY, MUTED]
    c.barh(ys, [cnt.get(s, 0) for s in allsets], color=cols, height=0.62)
    for i, s in enumerate(allsets):
        c.text(cnt.get(s, 0) + 0.4, i, str(cnt.get(s, 0)), va="center", fontsize=6.2, color=INK)
    c.set_yticks(ys)
    c.set_yticklabels([label[s] for s in allsets], fontsize=6)
    c.invert_yaxis()
    c.set_xlabel("audited theorems (count)")
    c.set_xlim(0, max(cnt.values()) * 1.2)
    c.grid(axis="y", visible=False)
    cls = [x for x in sets if "Classical.choice" in x["axioms"]]
    names = ", ".join(t for x in cls for t in x["theorems"])
    c.set_title(f"(c) Axioms of the {S['audited']} audited theorems", loc="left", fontsize=7.5)
    c.text(0.0, -0.42, "Classical.choice: " + "\n".join(textwrap.wrap(names, 62)), transform=c.transAxes, fontsize=5.2,
           color=INK2, va="top")

    d = fig.add_subplot(gs[1, 1])
    kinds = dict(S["forensics_kinds"])
    th = kinds.pop("theorem", 0)
    kinds["theorem (in source)"] = S["forensics_theorems_handwritten"]
    kinds["theorem (generated)"] = S["forensics_theorems_generated"]
    assert kinds["theorem (in source)"] + kinds["theorem (generated)"] == th
    korder = sorted(kinds, key=lambda k: -kinds[k])
    yk = np.arange(len(korder))
    d.barh(yk, [kinds[k] for k in korder], height=0.62,
           color=[NAVY if k == "theorem (in source)" else INK2 for k in korder])
    for i, k in enumerate(korder):
        d.text(kinds[k] + 4, i, str(kinds[k]), va="center", fontsize=6, color=INK)
    d.set_yticks(yk)
    d.set_yticklabels(korder, fontsize=6)
    d.invert_yaxis()
    d.set_xlabel("elaborated declarations (count)")
    d.set_xlim(0, max(kinds.values()) * 1.2)
    d.grid(axis="y", visible=False)
    FS = S["forensics_summary"]
    d.set_title(f"(d) Forensics: {FS['declarations']} declarations", loc="left", fontsize=7.5)
    d.text(0.98, 0.04, f"non-standard axioms: {len(FS['nonstandard_axioms'])}\nstatement smells: "
           f"{len(FS['statement_smells'])}\nunsafe/partial flags: {len(FS['unsafe_flags'])}",
           transform=d.transAxes, ha="right", va="bottom", fontsize=6, color=INK,
           bbox=dict(boxstyle="round,pad=0.3", facecolor="#f4f3ef", edgecolor=AXIS, lw=0.5))
    save(fig, "fig_proof_stats", meta=dict(
        title="Size of the trusted Lean core and its axiom footprint",
        question="How large is the trusted Lean core, where do its theorems live, and which logical axioms do the "
                 "audited theorems rely on?",
        model="Counts. (a,b) source lines and top-level def/inductive/structure/abbrev/instance and theorem keywords per "
              "file (regex over lean/CryoLean/*.lean); (c) #print axioms of the 44 audited theorems; (d) declarations "
              "in the elaborated environment (including auto-generated constructors and instances).",
        data="(a,b) lean/CryoLean/*.lean recounted at run time with the E8 rules of paper_eval.py (differences from "
             "paper/data/e8_proofs.json recorded in the data file); lean/audit-axioms.json; "
             "docs/forensics/cryolean-forensics.json and summary.json. Data: paper/data/fig_proof_stats.json.",
        claim="PROVEN+COMPUTED",
        caption=(f"(a,b) The trusted core is {T['lines']:,} lines of Lean 4 in {len(files)} files; "
                 f"{files['Soundness']['theorems']} of the {T['theorems']} source theorems are in Soundness.lean. "
                 f"(c) All {S['audited']} audited theorems rely only on Lean's standard axioms; "
                 f"{cnt.get(('propext',), 0)} need only propext and {cnt.get(('Classical.choice', 'Quot.sound', 'propext'), 0)} "
                 f"use Classical.choice. (d) The forensics extractor sees {FS['declarations']} elaborated declarations, "
                 f"including all {S['forensics_theorems_handwritten']} source theorems and "
                 f"{S['forensics_theorems_generated']} theorems generated by the elaborator (sizeOf_spec, inj, injEq, ...), "
                 f"with no non-standard axiom, statement smell or unsafe flag. Audit and forensics axiom sets agree for "
                 f"{S['audit_matches_forensics']}/{S['audited']} audited theorems."),
        section="supplement"))


# =====================================================================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-cache", action="store_true", help="re-draw from paper/data/fig_*.json without Lean or pytest")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    apply()

    G = compute_graph()
    dump("fig_proof_graph", G)
    fig_proof_graph(G)
    html_proof_graph(G)

    if args.use_cache:
        VF, MG, GU = load("fig_verdict_flow"), load("fig_rejection_margins"), load("fig_guarantees")
        tests = GU["tests_raw"]
    else:
        print("running Lean over the grid (batch) ...")
        grid = lean_grid()
        VF = compute_verdict_flow(grid)
        MG = compute_margins(grid)
        dump("fig_verdict_flow", VF)
        dump("fig_rejection_margins", MG)
        print("running the fast test suite ...")
        tests = run_tests()
    fig_verdict_flow(VF)
    n_fail = fig_rejection_margins(MG)
    dump("fig_rejection_margins", MG)          # adds the derived summary computed while drawing
    GU = compute_guarantees(tests)
    GU["tests_raw"] = tests
    fig_guarantees(GU)
    dump("fig_guarantees", GU)
    S = compute_stats()
    dump("fig_proof_stats", S)
    fig_proof_stats(S)
    print(json.dumps({"verdict_flow": {k: VF[k] for k in ("verdicts_confirmed", "verdicts_unconfirmed", "relevant_checks",
                                                           "relevant_outcomes", "rule_agrees_with_lean", "rule_total",
                                                           "confirmed_agrees_with_e1_grid", "branch_counts",
                                                           "seconds_confirmed_batch")},
                      "margins": {"verdicts": MG["verdicts"], "consistent": MG["margin_consistent_with_lean_outcome"],
                                  "inconsistent": MG["margin_inconsistent"], "fail_cells": n_fail},
                      "graph": {"stmt": len(G["statement_edges"]), "proof": len(G["proof_edges"]), "nodes": len(G["nodes"])},
                      "guarantees_fully_covered": GU["rows_fully_covered"], "tests": GU["tests"],
                      "stats": {"audit_matches_forensics": S["audit_matches_forensics"], "axiom_sets": [(x["axioms"], x["n"]) for x in S["axiom_sets"]]}},
                     indent=1, default=str))


if __name__ == "__main__":
    main()
