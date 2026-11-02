"""Figure 4: cross-industry compatibility heatmaps from the stored Lean grid.

Every cell is a verdict produced by the compiled Lean checker (cryolean grid build, table "grid").
Nothing is re-decided here; this script only reads, orders and draws.

Usage: python paper/scripts/fig_cross_industry.py [path/to/catalog.db]
(default: environment variable CRYOLEAN_GRID_DB)
"""
from __future__ import annotations

import textwrap
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict

import numpy as np

from style import *  # noqa: F401,F403
from matplotlib.colors import ListedColormap

apply()
from cryolean.catalog import Catalog  # noqa: E402

DB = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CRYOLEAN_GRID_DB")
if not DB:
    sys.exit("pass the catalog database path (or set CRYOLEAN_GRID_DB)")
cat = Catalog(DB)
con = sqlite3.connect(DB)
meta = dict(con.execute("SELECT key, value FROM grid_meta").fetchall())
grid = {(e, c): v for e, c, v in con.execute("SELECT experiment_id, configuration_id, verdict FROM grid")}

IND = list(cat.industries)  # catalog order
IND_NAME = {i: cat.industries[i]["name"] for i in IND}
exps = sorted(cat.experiments, key=lambda e: (IND.index(cat.experiments[e].get("industry")), e))
cfgs_all = sorted(cat.configurations)

# Column grouping: configurations carry no industry in the catalog, so each one is placed in the industry where it
# has the most Lean REQUIREMENTS_MET pairs ("home industry"); configurations with no MET pair go to a final block.
met_by = defaultdict(Counter)
for (e, c), v in grid.items():
    if v == "REQUIREMENTS_MET":
        met_by[c][cat.experiments[e].get("industry")] += 1
home = {c: (min(met_by[c].items(), key=lambda kv: (-kv[1], IND.index(kv[0])))[0] if met_by[c] else None)
        for c in cfgs_all}
COL_GROUPS = IND + [None]
cfgs = sorted(cfgs_all, key=lambda c: (COL_GROUPS.index(home[c]), cat.configurations[c].get("family") or "", c))
missing_pairs = sum(1 for e in exps for c in cfgs if (e, c) not in grid)

M = np.full((len(exps), len(cfgs)), np.nan)
for i, e in enumerate(exps):
    for j, c in enumerate(cfgs):
        v = grid.get((e, c))
        if v in VERDICT_INDEX:
            M[i, j] = VERDICT_INDEX[v]

row_counts = {}
for ind in IND:
    cnt = Counter(grid[(e, c)] for e in exps if cat.experiments[e].get("industry") == ind for c in cfgs if (e, c) in grid)
    row_counts[ind] = {v: cnt.get(v, 0) for v in VERDICT_ORDER}
col_sizes = Counter(home[c] for c in cfgs)


def blocks(keys):
    out, start = [], 0
    for k in range(1, len(keys) + 1):
        if k == len(keys) or keys[k] != keys[start]:
            out.append((keys[start], start, k))
            start = k
    return out


row_blocks = blocks([cat.experiments[e].get("industry") for e in exps])
col_blocks = blocks([home[c] for c in cfgs])
cmap = ListedColormap([VERDICT_COLOR[v] for v in VERDICT_ORDER])

# ------------------------------------------------------------------------------------------- full heatmap
fig = plt.figure(figsize=(COL2, 8.0))
ax = fig.add_axes([0.25, 0.25, 0.53, 0.67])
axc = fig.add_axes([0.80, 0.25, 0.12, 0.67], sharey=ax)
ax.imshow(M, cmap=cmap, vmin=-0.5, vmax=2.5, aspect="auto", interpolation="nearest")
ax.grid(False)
for _, a, b in row_blocks[1:]:
    ax.axhline(a - 0.5, color=INK, lw=0.6)
for _, a, b in col_blocks[1:]:
    ax.axvline(a - 0.5, color=INK, lw=0.6)
ax.set_yticks([(a + b - 1) / 2 for _, a, b in row_blocks])
ax.set_yticklabels([f"{IND_NAME[k]} ({b - a})" for k, a, b in row_blocks], fontsize=5.6)
wide = [(k, a, b) for k, a, b in col_blocks if b - a >= 5]
ax.set_xticks([(a + b - 1) / 2 for _, a, b in wide])
ax.set_xticklabels([(IND_NAME[k] if k else "no MET pair") + f" ({b - a})" for k, a, b in wide],
                   rotation=90, fontsize=4.6)
ax.tick_params(length=0)
ax.set_xlabel("Configurations by home industry (most MET pairs), then family; blocks under 5 columns unlabelled", fontsize=6.5, labelpad=4)
fig.suptitle(f"Lean verdicts: {len(exps)} experiments x {len(cfgs)} configurations ({len(exps) * len(cfgs):,} pairs)",
             fontsize=8, fontweight="bold", x=0.5, y=0.99)
axc.grid(False)
for k, a, b in row_blocks:
    tot_k = sum(row_counts[k].values())
    left = 0.0
    for v in VERDICT_ORDER:
        w = row_counts[k][v] / tot_k if tot_k else 0
        axc.barh((a + b - 1) / 2, w, left=left, height=(b - a) * 0.85, color=VERDICT_COLOR[v],
                 hatch=VERDICT_HATCH[v], edgecolor="white", lw=0.3)
        left += w
    rc = row_counts[k]
    axc.text(1.04, (a + b - 1) / 2, f"{rc['REQUIREMENTS_MET']}/{rc['NEED_MORE_INFORMATION']}/"
             f"{rc['DOES_NOT_MEET_REQUIREMENTS']}", va="center", fontsize=4.8, color=INK2, clip_on=False)
axc.set_xlim(0, 1)
axc.set_xticks([0, 0.5, 1])
axc.set_xticklabels(["0", "50%", "100%"])
axc.tick_params(axis="y", left=False, labelleft=False)
axc.set_title("Share per industry\nMET / INFO / NOT", fontsize=6.5)
fig.legend(handles=verdict_legend(ax).legend_handles, loc="lower center", ncol=3, fontsize=6.5, frameon=False,
           bbox_to_anchor=(0.55, -0.005))
ax.get_legend().remove()

tot = Counter(grid.values())
cap = (f"Every cell is a verdict of the compiled Lean 4 checker for one experiment-configuration pair of the full catalog "
       f"({len(exps)} experiments, {len(cfgs)} configurations, {len(grid):,} stored pairs; grid built "
       f"{json.loads(meta['built_at'])}). Rows are grouped by the experiment's industry (catalog order). The catalog assigns no "
       f"industry to configurations, so columns are grouped by each configuration's home industry, defined here as the "
       f"industry in which it has the most REQUIREMENTS_MET pairs (ties go to the earlier industry), with "
       f"{col_sizes[None]} configurations that meet no experiment in a final block; within a block columns are sorted by "
       f"equipment family. Black lines mark industry block boundaries. Totals: {tot['REQUIREMENTS_MET']:,} met, "
       f"{tot['NEED_MORE_INFORMATION']:,} need more information, {tot['DOES_NOT_MEET_REQUIREMENTS']:,} not met. Right "
       f"panel: verdict shares and counts (met/need info/not met) per experiment industry.")
save(fig, "fig_cross_industry_heatmap", meta=dict(
    title="Cross-industry compatibility heatmap (full catalog)",
    question="Which cryogenic configurations can run which experiments, across 20 industries?",
    model="Lean 4 checker verdicts (cryolean grid table); no re-evaluation, no Z3",
    data=f"catalog database table grid (lean_source_hash {json.loads(meta['lean_source_hash'])})",
    claim="COMPUTED", caption=cap, section="main",
    notes=f"Column home industry is a grouping derived from Lean MET counts, not catalog data. Pairs absent from grid: {missing_pairs}."))

# ------------------------------------------------------------------------------------------- featured 180
sel = json.load(open(ROOT / "research" / "v4" / "site_selection.json", encoding="utf-8"))
inds = [i for i in IND if i in sel] + [i for i in sel if i not in IND]
fig, axes = plt.subplots(4, 5, figsize=(COL2, 6.4))
featured, mismatch = [], []
for ax, ind in zip(axes.flat, inds):
    s = sel[ind]
    sub = np.full((len(s["experiment_ids"]), len(s["configuration_ids"])), np.nan)
    for i, e in enumerate(s["experiment_ids"]):
        for j, c in enumerate(s["configuration_ids"]):
            v = grid.get((e, c))
            featured.append({"industry": ind, "experiment_id": e, "configuration_id": c, "verdict": v})
            if v in VERDICT_INDEX:
                sub[i, j] = VERDICT_INDEX[v]
                ax.text(j, i, VERDICT_SHORT[v].replace(" ", "\n"), ha="center", va="center", fontsize=4.2,
                        color="white" if v != "NEED_MORE_INFORMATION" else INK)
    ax.imshow(sub, cmap=cmap, vmin=-0.5, vmax=2.5, interpolation="nearest")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    cnt = Counter(f["verdict"] for f in featured if f["industry"] == ind)
    g, y, r = cnt["REQUIREMENTS_MET"], cnt["NEED_MORE_INFORMATION"], cnt["DOES_NOT_MEET_REQUIREMENTS"]
    if (g, r, y) != (s.get("green"), s.get("red"), s.get("yellow")):
        mismatch.append(ind)
    ax.set_title(textwrap.fill(IND_NAME.get(ind, ind), 26) + f"\n{g} met / {y} info / {r} not", fontsize=5.0, fontweight="normal")
for ax in axes.flat[len(inds):]:
    ax.axis("off")
fc = Counter(f["verdict"] for f in featured)
fig.legend(handles=verdict_legend(axes.flat[0]).legend_handles, loc="lower center", ncol=3, fontsize=6.5, frameon=False)
axes.flat[0].get_legend().remove()
fig.subplots_adjust(hspace=1.0, wspace=0.25, bottom=0.07, top=0.93)
cap2 = (f"The {len(featured)} featured pairings of research/v4/site_selection.json: per industry, 3 experiments (rows) x 3 "
        f"configurations (columns); each cell is the stored Lean verdict. Totals: {fc['REQUIREMENTS_MET']} met, "
        f"{fc['NEED_MORE_INFORMATION']} need more information, {fc['DOES_NOT_MEET_REQUIREMENTS']} not met"
        + (f", {fc[None]} pairs absent from the grid" if fc[None] else "") + ".")
save(fig, "fig_featured_180_heatmap", meta=dict(
    title="Featured 180 pairings, Lean verdicts",
    question="What does the checker say about the showcased pairings in each industry?",
    model="Lean 4 checker verdicts (cryolean grid table)",
    data="catalog database table grid; research/v4/site_selection.json",
    claim="COMPUTED", caption=cap2, section="supplement",
    notes=("Selection green/red/yellow counts agree with the grid for every industry." if not mismatch else
           f"Stored green/red/yellow counts in site_selection.json differ from the grid for: {mismatch}; the figure uses the grid.")))

dump("fig_cross_industry_heatmap", {
    "grid_meta": {k: json.loads(v) for k, v in meta.items()}, "experiments": exps, "configurations": cfgs,
    "experiment_industry": {e: cat.experiments[e].get("industry") for e in exps},
    "configuration_home_industry": {c: home[c] for c in cfgs},
    "configuration_family": {c: cat.configurations[c].get("family") for c in cfgs},
    "verdict_index": VERDICT_INDEX, "matrix": [[None if np.isnan(x) else int(x) for x in row] for row in M],
    "row_industry_counts": row_counts, "totals": dict(tot), "missing_pairs": missing_pairs})
dump("fig_featured_180_heatmap", {"pairs": featured, "totals": {str(k): v for k, v in fc.items()},
                                  "selection_count_mismatch": mismatch})
print(dict(tot), dict(fc), "mismatch", mismatch, "noMET", col_sizes[None], "missing", missing_pairs)
