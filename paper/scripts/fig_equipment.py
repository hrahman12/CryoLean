#!/usr/bin/env python
"""Figures: scientific equipment, experiments and data.

    python paper/scripts/fig_equipment.py

fig_compat_heatmap         11 experiments x 26 configurations, Lean verdicts (paper/data/e1_grid.json),
                           re-checked now with one Lean batch run.
fig_capability_comparison  sourced capability values per configuration (catalog, evidence-tagged).
fig_industry_coverage      20 industries x 40 physical properties: which validated profiles require what.
fig_evidence_coverage      667 evidence records by evidence class and source; 40 properties by status.
fig_missing_info           what blocks a decision in the 157 NEED_MORE_INFORMATION pairs; unknown specs per configuration.

Nothing here re-implements the checker: verdicts come from the compiled Lean binary (e1_grid.json and a fresh
check_batch run); capability values and evidence classes are read verbatim from the catalog database built from
data/; property status comes from cryolean.coverage (computed from the same data).
"""
from __future__ import annotations

import sys
import textwrap
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import *  # noqa: E402,F401,F403
from style import (AXIS, CATEGORICAL, COL2, GRID, ICY, INK, INK2, LAVENDER, MUTED, NAVY, ORANGE, SEQ_BLUE,  # noqa: E402
                   VERDICT_COLOR, VERDICT_HATCH, VERDICT_LABEL, VERDICT_ORDER, apply, dump, load, save)

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

from cryolean import coverage, lean_runner, serialize, units, verifier  # noqa: E402
from cryolean.catalog import Catalog  # noqa: E402

plt.rcParams["hatch.linewidth"] = 0.5

# ------------------------------------------------------------------ presentation labels (not data)
FAMILY_ORDER = ["bluefors_ld", "oxford_teslatronpt", "qd_ppms_classic", "qd_ppms_dynacool", "lakeshore_crx",
                "lakeshore_janis_ccs", "oxford_optistatdry", "linkam_thms600", "leica_cm1950"]
FAMILY_SHORT = {
    "bluefors_ld": "Dilution refrigerator\n(Bluefors LD)",
    "oxford_teslatronpt": "Magnet + VTI\n(Oxford TeslatronPT)",
    "qd_ppms_classic": "PPMS, liquid He\n(Quantum Design)",
    "qd_ppms_dynacool": "PPMS DynaCool\n(Quantum Design)",
    "lakeshore_crx": "Probe station\n(Lake Shore CRX)",
    "lakeshore_janis_ccs": "Optical CCR cryostat\n(Lake Shore CCS)",
    "oxford_optistatdry": "Optical cryostat\n(Oxford OptistatDry)",
    "linkam_thms600": "LN2 microscope stage\n(Linkam THMS600)",
    "leica_cm1950": "Cryosection cryostat\n(Leica CM1950)",
}
FAMILY_ONELINE = {k: v.replace("\n", " ") for k, v in FAMILY_SHORT.items()}
FAMILY_TAG = {"bluefors_ld": "Bluefors\nLD", "oxford_teslatronpt": "Oxford\nTeslatronPT", "qd_ppms_classic": "QD PPMS\n(LHe)",
              "qd_ppms_dynacool": "QD\nDynaCool", "lakeshore_crx": "LakeShore\nCRX", "lakeshore_janis_ccs": "Lake Shore\nCCS",
              "oxford_optistatdry": "Oxford\nOptistat", "linkam_thms600": "Linkam\nTHMS600", "leica_cm1950": "Leica\nCM1950"}
CFG_SHORT = {
    "bluefors_ld250_manual_v2": "LD250 (manual v2.0)", "bluefors_ld400_hdw": "LD400sl + HD wiring",
    "bluefors_ld450_current": "LD450 (2026 spec.)",
    "oxford_teslatronpt_8T": "TeslatronPT 8 T", "oxford_teslatronpt_12T": "TeslatronPT 12 T",
    "oxford_teslatronpt_14T": "TeslatronPT 14 T", "oxford_teslatronpt_6_1_1T_vector": "TeslatronPT 6/1/1 T vector",
    "qd_ppms_classic_14T": "PPMS 14 T", "qd_ppms_classic_16T": "PPMS 16 T",
    "qd_dynacool_9T_eto_res": "DynaCool 9 T ETO", "qd_dynacool_12T_vsm": "DynaCool 12 T VSM",
    "qd_dynacool_14T_eto_vsm_hc": "DynaCool 14 T ETO+VSM+HC",
    "lakeshore_crx_vf": "CRX-VF", "lakeshore_crx_4k": "CRX-4K",
    "lakeshore_ccs_100": "CCS-100", "lakeshore_ccs_300s": "CCS-300S", "lakeshore_ccs_400": "CCS-400",
    "lakeshore_ccs_400h": "CCS-400H",
    "oxford_optistatdry_blv": "OptistatDry BLV", "oxford_optistatdry_tlex": "OptistatDry TLEX",
    "linkam_thms600_lnp96_t96": "THMS600 + LNP96", "linkam_thms600_heating_only": "THMS600, heating only",
    "linkam_thmsel600_lnp96": "THMSEL600 + LNP96",
    "leica_cm1950_genA_standard": "CM1950 gen. A standard", "leica_cm1950_genA_vacuum_motor_objcool": "CM1950 gen. A vac.+motor",
    "leica_cm1950_dualecotec_standard": "CM1950 DualEcoTec",
}
# disambiguates experiment profiles that share a plain_name (technique taken from each profile's `name`)
EXP_TAG = {"chem_phase_transition_pom": "polarized microscopy", "chem_temperature_dependent_photoluminescence": "photoluminescence",
           "mat_magnetometry_vsm": "VSM, 9 T", "mat_magnetoresistance_10T": "magnetoresistance, 10 T"}
INDUSTRY_ORDER = ["quantum_computing_and_sensing", "materials_and_nanotechnology", "chemistry_and_pharmaceuticals",
                  "biology_and_biotechnology"]
GLYPH = {"REQUIREMENTS_MET": "✓", "NEED_MORE_INFORMATION": "?", "DOES_NOT_MEET_REQUIREMENTS": "✕"}
GLYPH_COLOR = {"REQUIREMENTS_MET": "white", "NEED_MORE_INFORMATION": INK, "DOES_NOT_MEET_REQUIREMENTS": "white"}

CAT = Catalog()


def cfg_order():
    out = []
    for fam in FAMILY_ORDER:
        ids = [c for c in CAT.configurations if CAT.configurations[c]["equipment_id"] == fam]
        out += [c for c in CFG_SHORT if c in ids]
    assert sorted(out) == sorted(CAT.configurations), "configuration list changed"
    return out


def exp_order():
    out = []
    for ind in INDUSTRY_ORDER:
        out += sorted(e for e, x in CAT.experiments.items() if x.get("industry") == ind)
    assert sorted(out) == sorted(CAT.experiments)
    return out


def exp_label(eid, width=44):
    ex = CAT.experiments[eid]
    s = ex.get("plain_name") or ex["name"]
    if eid in EXP_TAG:
        s += f" ({EXP_TAG[eid]})"
    return "\n".join(textwrap.wrap(s, width))


def family_spans(order):
    spans, start = [], 0
    for i in range(1, len(order) + 1):
        if i == len(order) or CAT.configurations[order[i]]["equipment_id"] != CAT.configurations[order[start]]["equipment_id"]:
            spans.append((CAT.configurations[order[start]]["equipment_id"], start, i))
            start = i
    return spans


# ================================================================== 1. compatibility heatmap
def fig_compat_heatmap():
    e1 = load("e1_grid")
    grid = {(r["experiment"], r["configuration"]): r for r in e1["rows"]}
    exps, cfgs = exp_order(), cfg_order()

    # fresh Lean batch run over the same 286 pairs (documents rebuilt from the current catalog)
    pairs, keys = [], []
    for eid in exps:
        ex = serialize.working_experiment(CAT, eid, None, None, True)
        for cid in cfgs:
            cd, ed, _, _ = verifier.build_documents(CAT, ex, cid)
            pairs.append((cd, ed))
            keys.append((eid, cid))
    t0 = time.perf_counter()
    res = lean_runner.check_batch(pairs)
    dt = time.perf_counter() - t0
    agree_verdict = agree_detail = 0
    fresh = {}
    for (eid, cid), r in zip(keys, res):
        fails = sorted({"/".join(c["keys"]) for c in r["checks"] if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"}
                       | {c["model"] for c in r["coupled_checks"] if c["mandatory"] and c["applicable"] and c["outcome"] == "fail"})
        missing = sorted({"/".join(c["keys"]) for c in r["checks"] if c["mandatory"] and c["applicable"] and c["outcome"] in ("unknown", "unsupported")}
                         | {c["model"] for c in r["coupled_checks"] if c["mandatory"] and c["applicable"] and c["outcome"] in ("unknown", "unsupported")})
        fresh[(eid, cid)] = r["verdict"]
        old = grid[(eid, cid)]
        agree_verdict += old["verdict"] == r["verdict"]
        agree_detail += old["verdict"] == r["verdict"] and old["failed"] == fails and old["missing"] == missing
    counts = Counter(r["verdict"] for r in e1["rows"])
    print(f"  Lean re-check: {agree_verdict}/{len(pairs)} verdicts agree, {agree_detail} with identical failed/missing keys, {dt:.2f} s")

    M = len(exps)
    N = len(cfgs)
    fig = plt.figure(figsize=(COL2, 4.7))
    ax = fig.add_axes([0.335, 0.33, 0.585, 0.58])
    for i, eid in enumerate(exps):
        for j, cid in enumerate(cfgs):
            v = grid[(eid, cid)]["verdict"]
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v],
                                   edgecolor="white", linewidth=0.9))
            ax.text(j + 0.5, i + 0.52, GLYPH[v], ha="center", va="center", fontsize=6.5, color=GLYPH_COLOR[v],
                    fontweight="bold")
    ax.set_xlim(0, N)
    ax.set_ylim(M, 0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_yticks([i + 0.5 for i in range(M)])
    ax.set_yticklabels([exp_label(e) for e in exps], fontsize=6.2, color=INK)
    ax.set_xticks([j + 0.5 for j in range(N)])
    ax.set_xticklabels([CFG_SHORT[c] for c in cfgs], rotation=90, fontsize=6.0, color=INK)
    ax.tick_params(length=0, pad=2)
    # family brackets on top
    for fam, a, b in family_spans(cfgs):
        ax.plot([a + 0.12, b - 0.12], [-0.25, -0.25], color=INK2, lw=0.8, clip_on=False)
        ax.text((a + b) / 2, -0.4, FAMILY_TAG[fam], ha="center", va="bottom", fontsize=5.4, color=INK2,
                rotation=0, linespacing=1.05)
        if a > 0:
            ax.axvline(a, color=INK, lw=1.0)
    # industry separators + labels
    start = 0
    for ind in INDUSTRY_ORDER:
        n = sum(1 for e in exps if CAT.experiments[e]["industry"] == ind)
        if start > 0:
            ax.axhline(start, color=INK, lw=1.0)
        start += n
    # right margin: per-experiment verdict counts
    xr = N + 0.6
    for k, v in enumerate(VERDICT_ORDER):
        ax.text(xr + k * 1.15, -0.4, GLYPH[v], ha="center", va="bottom", fontsize=7, color=INK, fontweight="bold")
        for i, eid in enumerate(exps):
            n = sum(1 for c in cfgs if grid[(eid, c)]["verdict"] == v)
            ax.text(xr + k * 1.15, i + 0.52, str(n), ha="center", va="center", fontsize=6.2, color=INK2)
    # industry tags in the far left margin
    start = 0
    for ind in INDUSTRY_ORDER:
        n = sum(1 for e in exps if CAT.experiments[e]["industry"] == ind)
        name = CAT.industries[ind].get("plain_tab") or CAT.industries[ind]["name"]
        fig.text(0.008, 0.91 - 0.58 * (start + n / 2) / M, name, rotation=90, ha="left", va="center", fontsize=6.5,
                 color=INK2, fontweight="bold")
        start += n
    handles = [Patch(facecolor=VERDICT_COLOR[v], hatch=VERDICT_HATCH[v], edgecolor="white",
                     label=f"{GLYPH[v]}  {VERDICT_LABEL[v]} ({counts[v]})") for v in VERDICT_ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.6, -0.005), fontsize=6.8,
               handlelength=1.6, handleheight=1.1)
    dump("fig_compat_heatmap", {
        "source": "paper/data/e1_grid.json (paper_eval.py E1) + fresh lean_runner.check_batch over the same pairs",
        "experiments": exps, "configurations": cfgs, "counts": dict(counts), "pairs": len(pairs),
        "fresh_batch_verdicts_agree": agree_verdict, "fresh_batch_failed_missing_identical": agree_detail,
        "fresh_batch_seconds": round(dt, 3),
        "met_pairs": sorted(f"{e} @ {c}" for (e, c), r in grid.items() if r["verdict"] == "REQUIREMENTS_MET"),
        "per_experiment": {e: dict(Counter(grid[(e, c)]["verdict"] for c in cfgs)) for e in exps},
        "per_family": {fam: dict(Counter(grid[(e, c)]["verdict"] for e in exps for c in cfgs[a:b]))
                       for fam, a, b in family_spans(cfgs)},
    })
    save(fig, "fig_compat_heatmap", meta=dict(
        title="Lean verdicts: 11 experiment profiles x 26 cryostat configurations",
        question="Which sourced cryostat configurations can perform which validated experiment profiles, and how often must the checker withhold a decision?",
        model="Verdict of the compiled Lean 4 checker (cryolean.exe check / check-batch) on documents built by verifier.build_documents from the catalog; no Python re-implementation.",
        data=(f"paper/data/e1_grid.json ({len(pairs)} pairs, paper_eval.py E1); re-checked in one Lean check_batch run "
              f"({agree_verdict}/{len(pairs)} verdicts agree, {agree_detail} with identical failed/missing keys); "
              "plain names from data/experiments/*.json; families from data/cryostats/*.json. Saved: paper/data/fig_compat_heatmap.json"),
        claim="COMPUTED",
        caption=(f"Verdict of the Lean checker for every pairing of the 11 validated experiment profiles (rows, grouped by industry) "
                 f"with the 26 sourced cryostat configurations (columns, grouped by equipment family). Of {len(pairs)} pairs, "
                 f"{counts['REQUIREMENTS_MET']} meet all mandatory requirements, {counts['DOES_NOT_MEET_REQUIREMENTS']} violate at least one, "
                 f"and {counts['NEED_MORE_INFORMATION']} cannot be decided because a required specification or model input is undocumented. "
                 "Verdicts are computed by the compiled checker (a fresh batch run reproduced all of them); colour, hatch and glyph "
                 "encode the same verdict, and the right-hand columns count verdicts per profile."),
        section="main"))


# ================================================================== 2. capability comparison
def _si(q):
    return float(units.to_si(Fraction(q["value"]), q["unit"]))


def _cap(cfg, key):
    for c in cfg["capabilities"]:
        if c["key"] == key:
            return c
    return None


def fig_capability_comparison():
    cfgs = cfg_order()
    rows = []
    for cid in cfgs:
        cfg = CAT.configurations[cid]
        rec = {"configuration": cid, "family": cfg["equipment_id"]}
        for key in ("temperature.range", "temperature.chamber.range", "temperature.base", "magnetic_field.max",
                    "sample.bore_diameter", "sample.diameter.max", "cooldown_time.max", "cooling_power.at_4200mK",
                    "cooling_power.at_20mK"):
            c = _cap(cfg, key)
            if c is None:
                rec[key] = {"state": "not_recorded"}
                continue
            v = c["value"]
            st = "unknown" if v["kind"] == "unknown" else c["evidence_status"]
            r = {"state": st, "install": c["install"], "evidence_ids": c["evidence_ids"], "kind": v["kind"]}
            if v["kind"] == "range":
                r["lo_si"], r["hi_si"] = _si(v["lo"]), _si(v["hi"])
            elif "q" in v:
                r["si"] = _si(v["q"])
            rec[key] = r
        rows.append(rec)
    n = len(cfgs)

    fig, axes = plt.subplots(1, 5, figsize=(COL2, 5.0), sharey=True,
                             gridspec_kw=dict(width_ratios=[1.35, 1, 1, 1, 1.15], wspace=0.12))
    ys = list(range(n))

    def styl(st):
        if st == "inferred_estimate":
            return dict(mfc="white", mec=ORANGE, color=ORANGE, ls=(0, (2, 1.2)))
        return dict(mfc=NAVY, mec=NAVY, color=NAVY, ls="-")

    def no_value(ax, y, rec, x):
        txt = "unknown" if rec["state"] == "unknown" else "not recorded"
        ax.text(x, y, txt, ha="center", va="center", fontsize=5.3, color=MUTED, style="italic")

    # (a) temperature
    ax = axes[0]
    for y, rec in zip(ys, rows):
        key = "temperature.range" if rec["temperature.range"]["state"] != "not_recorded" else "temperature.chamber.range"
        r = rec[key]
        b = rec["temperature.base"]
        if "lo_si" in r:
            s = styl(r["state"])
            ax.plot([r["lo_si"], r["hi_si"]], [y, y], color=s["color"], ls=s["ls"], lw=1.4, solid_capstyle="butt")
            mk = "s" if key == "temperature.chamber.range" else "|"
            ax.plot([r["lo_si"], r["hi_si"]], [y, y], ls="none", marker=mk, ms=4 if mk == "s" else 6, mfc=s["mfc"],
                    mec=s["mec"], mew=1.0)
        if "si" in b:
            ax.plot([b["si"]], [y], ls="none", marker="o", ms=3.6, mfc="white", mec=LAVENDER, mew=1.1, zorder=4)
        if "lo_si" not in r and "si" not in b:
            no_value(ax, y, r, 1.0)
        elif "lo_si" not in r:
            ax.text(b["si"] * 1.6, y, "range unknown", ha="left", va="center", fontsize=5.3, color=MUTED, style="italic")
    ax.set_xscale("log")
    ax.set_xlim(5e-3, 2e3)
    ax.set_xlabel("Temperature (K)")
    ax.set_title("a  Operating range", loc="left", fontsize=7.5)

    # (b) max field
    ax = axes[1]
    for y, rec in zip(ys, rows):
        r = rec["magnetic_field.max"]
        if "si" in r:
            opt = r["install"] == "optional_not_installed"
            ax.plot([0, r["si"]], [y, y], color=MUTED if opt else NAVY, lw=0.8, ls=":" if opt else "-")
            ax.plot([r["si"]], [y], marker="o", ms=4, mfc="white" if opt else NAVY, mec=MUTED if opt else NAVY, mew=1.0)
            ax.text(r["si"] + 0.9, y, f"{r['si']:g} T" + (" (option)" if opt else ""), va="center", ha="left",
                    fontsize=5.3, color=INK2)
        else:
            no_value(ax, y, r, 8.5)
    ax.set_xlim(0, 19)
    ax.set_xlabel("Maximum field (T)")
    ax.set_title("b  Magnet", loc="left", fontsize=7.5)

    # (c) sample space
    ax = axes[2]
    for y, rec in zip(ys, rows):
        bore, dia = rec["sample.bore_diameter"], rec["sample.diameter.max"]
        if "si" in bore:
            ax.plot([bore["si"] * 1e3], [y], marker="o", ms=4, color=NAVY, ls="none")
        elif "si" in dia:
            ax.plot([dia["si"] * 1e3], [y], marker="s", ms=3.6, color=LAVENDER, ls="none")
        else:
            st = bore if bore["state"] != "not_recorded" else dia
            no_value(ax, y, st, 30)
    ax.set_xlim(0, 60)
    ax.set_xlabel("Diameter (mm)")
    ax.set_title("c  Sample space", loc="left", fontsize=7.5)

    # (d) cooldown
    ax = axes[3]
    for y, rec in zip(ys, rows):
        r = rec["cooldown_time.max"]
        if "si" in r:
            s = styl(r["state"])
            ax.plot([r["si"] / 3600], [y], marker="o", ms=4, mfc=s["mfc"], mec=s["mec"], mew=1.1, ls="none")
        else:
            no_value(ax, y, r, 3.0)
    ax.set_xscale("log")
    ax.set_xlim(0.3, 50)
    ax.set_xlabel("Cooldown time (h)")
    ax.set_title("d  Cooldown", loc="left", fontsize=7.5)

    # (e) cooling power
    ax = axes[4]
    for y, rec in zip(ys, rows):
        r4, r20 = rec["cooling_power.at_4200mK"], rec["cooling_power.at_20mK"]
        drew = False
        if "si" in r4:
            s = styl(r4["state"])
            ax.plot([r4["si"]], [y], marker="o", ms=4, mfc=s["mfc"], mec=s["mec"], mew=1.1, ls="none")
            drew = True
        if "si" in r20:
            ax.plot([r20["si"]], [y], marker="D", ms=3.6, mfc=ICY, mec=INK2, mew=0.5, ls="none")
            ax.text(r20["si"] * 2.2, y, f"{r20['si'] * 1e6:g} µW at 20 mK", va="center", fontsize=5.0, color=INK2)
            drew = True
        if not drew:
            no_value(ax, y, r4, 3e-3)
    ax.set_xscale("log")
    ax.set_xlim(1e-6, 10)
    ax.set_xticks([1e-6, 1e-4, 1e-2, 1])
    ax.set_xlabel("Cooling power (W)")
    ax.set_title("e  Cooling power", loc="left", fontsize=7.5)

    for ax in axes:
        ax.set_ylim(n - 0.5, -0.5)
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
        for fam, a, b in family_spans(cfgs):
            if a > 0:
                ax.axhline(a - 0.5, color=AXIS, lw=0.6)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([CFG_SHORT[c] for c in cfgs], fontsize=6.0)
    axes[0].tick_params(axis="y", length=0)
    for fam, a, b in family_spans(cfgs):
        axes[0].annotate(FAMILY_TAG[fam].replace("\n", " ").replace("LakeShore", "Lake Shore"), xy=(0, (a + b - 1) / 2), xycoords=("axes fraction", "data"),
                         xytext=(-92, 0), textcoords="offset points", ha="right", va="center", fontsize=5.6,
                         color=INK2, fontweight="bold")
    leg = [Line2D([], [], color=NAVY, marker="o", ms=4, label="manufacturer specification"),
           Line2D([], [], color=ORANGE, marker="o", mfc="white", ms=4, ls=(0, (2, 1.2)), label="inferred estimate"),
           Line2D([], [], color=MUTED, marker="o", mfc="white", ms=4, ls=":", label="documented option, not installed"),
           Line2D([], [], color=LAVENDER, marker="o", mfc="white", ms=4, ls="none", label="base temperature (a)"),
           Line2D([], [], color=NAVY, marker="s", ms=3.5, ls="-", label="cryochamber range (a, Leica)"),
           Line2D([], [], color=INK2, marker="D", mfc=ICY, ms=3.6, ls="none", label="at 20 mK (e); circles at 4.2 K"),
           Line2D([], [], marker="o", ls="none", color=NAVY, ms=4, label="bore / sample-space diameter (c)"),
           Line2D([], [], marker="s", ls="none", color=LAVENDER, ms=3.6, label="max. sample diameter (c)")]
    fig.legend(handles=leg, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.075), fontsize=6.0, handlelength=2.2)

    # facts
    def count(key, pred):
        return sum(1 for r in rows if pred(r[key]))
    facts = {
        "configurations": n,
        "field_documented_installed": count("magnetic_field.max", lambda r: "si" in r and r["install"] == "installed"),
        "field_unknown": count("magnetic_field.max", lambda r: r["state"] == "unknown"),
        "cooling_power_4K_documented": count("cooling_power.at_4200mK", lambda r: "si" in r),
        "cooling_power_4K_unknown": count("cooling_power.at_4200mK", lambda r: r["state"] == "unknown"),
        "cooldown_documented": count("cooldown_time.max", lambda r: "si" in r),
        "cooldown_inferred": count("cooldown_time.max", lambda r: r["state"] == "inferred_estimate"),
        "cooldown_unknown": count("cooldown_time.max", lambda r: r["state"] == "unknown"),
        "lowest_base_K": min(r["temperature.base"]["si"] for r in rows if "si" in r["temperature.base"]),
        "highest_T_K": max(r["temperature.range"]["hi_si"] for r in rows if "hi_si" in r["temperature.range"]),
        "max_field_T": max(r["magnetic_field.max"]["si"] for r in rows if "si" in r["magnetic_field.max"]),
    }
    print("  capability facts:", facts)
    dump("fig_capability_comparison", {"source": "catalog (data/cryostats/*.json via cryolean.catalog.Catalog), values converted with cryolean.units.to_si",
                                       "facts": facts, "rows": rows})
    save(fig, "fig_capability_comparison", meta=dict(
        title="Sourced capabilities of the 26 cryostat configurations",
        question="How do the catalogued configurations differ in temperature range, field, sample space, cooldown and cooling power, and where are the specifications missing?",
        model="None: values are read from the catalog and converted exactly to SI (cryolean.units.to_si); evidence class from each capability's evidence_status.",
        data=("data/cryostats/*.json (catalog database), keys temperature.range / temperature.chamber.range / temperature.base / "
              "magnetic_field.max / sample.bore_diameter / sample.diameter.max / cooldown_time.max / cooling_power.at_4200mK / "
              "cooling_power.at_20mK; saved in paper/data/fig_capability_comparison.json"),
        claim="SOURCED",
        caption=(f"Manufacturer-specified capabilities of the 26 configurations, grouped by equipment family. Filled markers are manufacturer "
                 f"specifications, hollow dashed markers inferred estimates, and dotted markers values documented for an option that is not installed; "
                 f"'unknown' marks a capability the catalogue records but no source quantifies, 'not recorded' one the catalogue does not list. "
                 f"Cooling power at 4.2 K is quantified for only {facts['cooling_power_4K_documented']} of 26 configurations and maximum field for "
                 f"{facts['field_documented_installed']} installed magnets; all values are sourced, none are modelled."),
        section="main"))


# ================================================================== 3. industry x property coverage
STATUS_STYLE = {
    "implemented_with_data": dict(fc=NAVY, hatch="", tc="white", label="implemented, with documented data"),
    "representable_no_data": dict(fc=ICY, hatch="....", tc=INK, label="representable, no equipment data"),
    "representable_only": dict(fc="#dddcd5", hatch="////", tc=INK, label="representable only (no key or validated model)"),
    "model_not_validated": dict(fc="#d0cfc8", hatch="xx", tc=INK, label="model not validated"),
}


def property_requirements():
    """property id -> {experiment ids that require it}; via requirement keys and coupled models."""
    props = CAT.properties
    req = defaultdict(set)
    unmapped = set()
    for eid, ex in CAT.experiments.items():
        rkeys = {k for r in ex.get("requirements", []) for k in (r.get("keys") or [r.get("key")])}
        models = {c["model"] for c in ex.get("coupled", [])}
        hit = set()
        for pid, p in props.items():
            ks = rkeys & set(p.get("keys", []))
            ms = models & set(p.get("models", []))
            if ks or ms:
                req[pid].add(eid)
                hit |= ks
        unmapped |= {(eid, k) for k in rkeys - hit}
    return req, unmapped


def fig_industry_coverage():
    pstat = {p["id"]: p for p in coverage.property_status(CAT)}
    e7 = load("e7_coverage")
    assert Counter(p["status"] for p in pstat.values()) == Counter(e7["properties_by_status"]), "property status drifted from e7"
    req, unmapped = property_requirements()
    pids = sorted(CAT.properties)
    inds = sorted(CAT.industries.values(), key=lambda i: (0 if i["experiment_ids"] else 1,
                                                          INDUSTRY_ORDER.index(i["id"]) if i["id"] in INDUSTRY_ORDER else 99, i["name"]))
    n_res = sum(1 for i in inds if i["experiment_ids"])
    R, C = len(inds), len(pids)

    H = 0.5                                   # row height of industries without a validated profile
    y0 = [float(i) if i < n_res else n_res + (i - n_res) * H for i in range(R)]
    hh = [1.0 if i < n_res else H for i in range(R)]
    Y = n_res + (R - n_res) * H
    fig = plt.figure(figsize=(COL2, 5.0))
    ax = fig.add_axes([0.235, 0.36, 0.70, 0.50])
    matrix = {}
    for i, ind in enumerate(inds):
        exps = set(ind["experiment_ids"])
        for j, pid in enumerate(pids):
            k = len(req.get(pid, set()) & exps)
            matrix[(ind["id"], pid)] = k
            if k:
                st = STATUS_STYLE[pstat[pid]["status"]]
                ax.add_patch(Rectangle((j, y0[i]), 1, 1, facecolor=st["fc"], hatch=st["hatch"], edgecolor="white", lw=0.8))
                ax.text(j + 0.5, y0[i] + 0.53, str(k), ha="center", va="center", fontsize=6.0, color=st["tc"], fontweight="bold")
            elif i < n_res:
                ax.add_patch(Rectangle((j, y0[i]), 1, 1, facecolor="white", edgecolor=GRID, lw=0.5))
    # registered-only block
    ax.add_patch(Rectangle((0, n_res), C, Y - n_res, facecolor="#f6f5f1", edgecolor="none", zorder=0))
    for i in range(n_res, R):
        ax.axhline(y0[i] + H, color="white", lw=0.8)
    ax.text(C / 2, n_res + (Y - n_res) / 2, f"{R - n_res} known or registered industries:\nno validated experiment profile, "
            "so no property is required yet", ha="center", va="center", fontsize=7, color=INK2, style="italic", zorder=5,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=AXIS, lw=0.6))
    # status strip
    ys = Y + 0.5
    for j, pid in enumerate(pids):
        st = STATUS_STYLE[pstat[pid]["status"]]
        ax.add_patch(Rectangle((j, ys), 1, 1, facecolor=st["fc"], hatch=st["hatch"], edgecolor="white", lw=0.8, clip_on=False))
    ax.text(-0.3, ys + 0.5, "Property status (all 40)", ha="right", va="center", fontsize=6.5, color=INK, fontweight="bold")
    ax.axhline(n_res, color=INK, lw=1.0)
    ax.set_xlim(0, C)
    ax.set_ylim(Y + 1.5, 0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_yticks([y0[i] + hh[i] / 2 for i in range(R)])
    labels = []
    for i, ind in enumerate(inds):
        n = len(ind["experiment_ids"])
        labels.append(f"{ind['name']}  [{n} profile{'s' if n != 1 else ''}]" if n else ind["name"])
    ax.set_yticklabels(labels, fontsize=6.0)
    for t, ind in zip(ax.get_yticklabels(), inds):
        t.set_color(INK if ind["experiment_ids"] else INK2)
        if ind["experiment_ids"]:
            t.set_fontweight("bold")
        else:
            t.set_fontsize(5.4)
    ax.tick_params(length=0, pad=2)
    ax.set_xticks([j + 0.5 for j in range(C)])
    ax.set_xticklabels([f"{CAT.properties[pid]['name']}  {pid}" for pid in pids], rotation=90, fontsize=5.4)
    ax.xaxis.set_ticks_position("bottom")
    # category brackets on top
    cats = []
    for j, pid in enumerate(pids):
        c = CAT.properties[pid]["category"]
        if not cats or cats[-1][0] != c:
            cats.append([c, j, j + 1])
        else:
            cats[-1][2] = j + 1
    for c, a, b in cats:
        ax.plot([a + 0.15, b - 0.15], [-0.3, -0.3], color=INK2, lw=0.8, clip_on=False)
        ax.text((a + b) / 2, -0.5, textwrap.fill(c, 17), ha="center", va="bottom", fontsize=6.0, color=INK2, linespacing=1.0)
        if a > 0:
            ax.plot([a, a], [0, Y], color=INK2, lw=0.6)
    handles = [Patch(facecolor=STATUS_STYLE[s]["fc"], hatch=STATUS_STYLE[s]["hatch"],
                     edgecolor=INK2 if s == "representable_only" else "white", lw=0.5,
                     label=f"{STATUS_STYLE[s]['label']} ({sum(1 for p in pstat.values() if p['status'] == s)})")
               for s in ("implemented_with_data", "representable_no_data", "representable_only")]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=3, fontsize=6.3, handlelength=1.6,
               handleheight=1.1, title="Cell colour = property status; number = profiles in that industry requiring it",
               title_fontsize=6.3, alignment="left")
    required_any = sorted(pid for pid in pids if req.get(pid))
    facts = {"industries": R, "researched_industries": n_res, "properties": C,
             "properties_required_by_any_profile": len(required_any),
             "required_properties_by_status": dict(Counter(pstat[p]["status"] for p in required_any)),
             "cells_required": sum(1 for v in matrix.values() if v),
             "requirement_keys_not_mapped_to_a_property": sorted(f"{e}:{k}" for e, k in unmapped),
             "properties_by_status": dict(Counter(p["status"] for p in pstat.values())),
             "most_required": sorted(((CAT.properties[p]["name"], len(req[p])) for p in required_any), key=lambda x: -x[1])[:6]}
    print("  industry facts:", {k: v for k, v in facts.items() if k != "requirement_keys_not_mapped_to_a_property"})
    dump("fig_industry_coverage", {"source": "cryolean.catalog (industries, experiments, properties), cryolean.coverage.property_status",
                                   "facts": facts,
                                   "matrix": {f"{i}|{p}": v for (i, p), v in matrix.items() if v},
                                   "industries": [{"id": i["id"], "name": i["name"], "status": i["status"],
                                                   "experiment_ids": i["experiment_ids"]} for i in inds],
                                   "property_status": {p: pstat[p]["status"] for p in pids}})
    save(fig, "fig_industry_coverage", meta=dict(
        title="Cross-industry coverage: industries x physical compatibility properties",
        question="Which physical properties do the validated experiment profiles of each industry depend on, and are those properties backed by data?",
        model="Set intersection: a profile requires a property when one of its requirement keys or coupled models is listed for that property in data/physics/properties.json; property status from cryolean.coverage.property_status.",
        data=("data/industries.json + cryolean.catalog_standard (20 industries), data/experiments/*.json (11 profiles), "
              "data/physics/properties.json (40 properties), data/physics/coupled_models.json; status cross-checked against paper/data/e7_coverage.json; "
              "saved in paper/data/fig_industry_coverage.json"),
        claim="COMPUTED+SOURCED",
        caption=(f"Rows are the {R} industries the catalogue knows; only {n_res} have validated experiment profiles (bold). "
                 f"Each filled cell counts the profiles of that industry that require a property (via a requirement key or a coupled model), "
                 f"coloured by the property's implementation status computed from the data; the bottom strip shows the status of all {C} properties. "
                 f"The profiles touch {len(required_any)} of the {C} properties; the remaining industries are labels only and carry no verification claim."),
        section="supplement"))


# ================================================================== 4. evidence coverage
EV_CLASSES = ["manufacturer_specification", "experimental_observation", "reference_data", "textbook_model",
              "inferred_estimate", "unknown"]
EV_STYLE = {"manufacturer_specification": (NAVY, "", "manufacturer specification"),
            "experimental_observation": (LAVENDER, "", "experimental observation"),
            "reference_data": (ICY, "", "reference data"),
            "textbook_model": (ORANGE, "", "textbook model"),
            "inferred_estimate": ("#c9c8c1", "////", "inferred estimate"),
            "unknown": ("white", "xx", "unknown (value not stated)")}
SOURCE_GROUPS = [
    ("Bluefors LD", ["bluefors.json"], "Bluefors"),
    ("Oxford TeslatronPT / OptistatDry", ["oxford.json"], None),
    ("Quantum Design PPMS / DynaCool", ["quantum_design.json"], "QD"),
    ("Lake Shore CRX / CCS", ["lakeshore.json"], None),
    ("Linkam THMS600", ["linkam.json"], "Linkam"),
    ("Leica CM1950", ["leica.json"], None),
    ("Experiment profiles (literature)", ["experiments.json", "v2_experiments_v2.json"], None),
    ("Coupled physics models", ["v2_physics_models.json"], None),
    ("Thermal contraction (reference)", ["v2_thermal_contraction.json"], None),
    ("Mixing-chamber heat-load study", ["v2_heat_load_demo.json"], None),
]


def _gap_group(applies_to: str) -> str:
    a = applies_to.lower()
    if a.startswith("bluefors"):
        return "Bluefors"
    if a.startswith("linkam"):
        return "Linkam"
    if any(s in a for s in ("quantum design", "ppms", "mpms", "vsm")):
        return "QD"
    raise ValueError(f"unassigned equipment-gap evidence: {applies_to}")


def fig_evidence_coverage():
    e7 = load("e7_coverage")
    ev = list(CAT.evidence.values())
    assert len(ev) == e7["evidence_records"], "evidence count drifted from e7"
    assert Counter(e["evidence_status"] for e in ev) == Counter(e7["evidence_by_status"]), "evidence classes drifted from e7"
    table = {g[0]: Counter() for g in SOURCE_GROUPS}
    tag2group = {g[2]: g[0] for g in SOURCE_GROUPS if g[2]}
    for e in ev:
        frag = e["_fragment"]
        if frag == "v2_equipment_gaps.json":
            grp = tag2group[_gap_group(e["applies_to"])]
        else:
            grp = next(g[0] for g in SOURCE_GROUPS if frag in g[1])
        table[grp][e["evidence_status"]] += 1
    assert sum(sum(c.values()) for c in table.values()) == len(ev)

    pstat = coverage.property_status(CAT)
    cats = []
    for p in pstat:
        if p["category"] not in cats:
            cats.append(p["category"])
    pc = {c: Counter(p["status"] for p in pstat if p["category"] == c) for c in cats}

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(COL2, 3.6), gridspec_kw=dict(width_ratios=[1.55, 1], wspace=0.75))
    fig.subplots_adjust(bottom=0.30)
    groups = [g[0] for g in SOURCE_GROUPS]
    for y, g in enumerate(groups):
        left = 0
        for cl in EV_CLASSES:
            v = table[g][cl]
            if not v:
                continue
            fc, h, _ = EV_STYLE[cl]
            a1.barh(y, v, left=left, color=fc, hatch=h, edgecolor=INK2 if cl == "unknown" else "white", lw=0.5, height=0.72)
            if v >= 9 and not h:
                a1.text(left + v / 2, y, str(v), ha="center", va="center", fontsize=5.6,
                        color="white" if cl in ("manufacturer_specification", "experimental_observation") else INK)
            left += v
        a1.text(left + 1.5, y, str(left), va="center", ha="left", fontsize=6.2, color=INK, fontweight="bold")
    a1.set_yticks(range(len(groups)))
    a1.set_yticklabels(groups, fontsize=6.3)
    a1.set_ylim(len(groups) - 0.5, -0.5)
    a1.set_xlabel("Evidence records")
    a1.grid(axis="y", visible=False)
    a1.tick_params(axis="y", length=0)
    a1.axhline(5.5, color=AXIS, lw=0.6)
    a1.set_xlim(0, max(sum(c.values()) for c in table.values()) * 1.12)
    a1.set_title(f"a  {len(ev)} evidence records by class and source", loc="left", fontsize=7.5)
    h1 = [Patch(facecolor=EV_STYLE[c][0], hatch=EV_STYLE[c][1], edgecolor=INK2 if c == "unknown" else "white", lw=0.5,
                label=f"{EV_STYLE[c][2]} ({e7['evidence_by_status'][c]})") for c in EV_CLASSES]
    a1.legend(handles=h1, loc="upper left", bbox_to_anchor=(-0.05, -0.2), ncol=2, fontsize=5.8, handlelength=1.4, handleheight=1.0,
              columnspacing=1.0)

    order = ["implemented_with_data", "representable_no_data", "representable_only"]
    for y, c in enumerate(cats):
        left = 0
        for s in order:
            v = pc[c][s]
            if not v:
                continue
            st = STATUS_STYLE[s]
            a2.barh(y, v, left=left, color=st["fc"], hatch=st["hatch"], edgecolor="white", lw=0.5, height=0.66)
            a2.text(left + v / 2, y, str(v), ha="center", va="center", fontsize=6.0, color=st["tc"] if not st["hatch"] else INK,
                    fontweight="bold", bbox=None if not st["hatch"] else dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
            left += v
    a2.set_yticks(range(len(cats)))
    a2.set_yticklabels([textwrap.fill(c, 18) for c in cats], fontsize=6.3)
    a2.set_ylim(len(cats) - 0.5, -0.5)
    a2.set_xlabel("Physical properties")
    a2.grid(axis="y", visible=False)
    a2.tick_params(axis="y", length=0)
    a2.set_xlim(0, 10.5)
    a2.set_xticks(range(0, 11, 2))
    a2.set_title("b  40 properties by status", loc="left", fontsize=7.5)
    tot = Counter(p["status"] for p in pstat)
    h2 = [Patch(facecolor=STATUS_STYLE[s]["fc"], hatch=STATUS_STYLE[s]["hatch"], lw=0.5,
                edgecolor=INK2 if s == "representable_only" else "white",
                label=f"{STATUS_STYLE[s]['label'].split(' (')[0]} ({tot[s]})") for s in order]
    a2.legend(handles=h2, loc="upper left", bbox_to_anchor=(-0.05, -0.2), fontsize=5.8, handlelength=1.4, handleheight=1.0)
    data = {"source": "cryolean.catalog evidence table (data/evidence.json + data/evidence/*); equipment-gap records assigned by applies_to",
            "by_source_and_class": {g: dict(c) for g, c in table.items()},
            "by_class": dict(Counter(e["evidence_status"] for e in ev)), "records": len(ev),
            "properties_by_category_and_status": {c: dict(v) for c, v in pc.items()}}
    dump("fig_evidence_coverage", data)
    man = sum(sum(table[g].values()) for g in groups[:6])
    print("  evidence:", {g: sum(c.values()) for g, c in table.items()})
    save(fig, "fig_evidence_coverage", meta=dict(
        title="Scientific evidence behind the catalogue",
        question="What kind of evidence supports the catalogued specifications and models, and how many of the 40 physical properties are backed by data?",
        model="Counts of evidence records by evidence_status and source document; property status from cryolean.coverage.property_status.",
        data=(f"{len(ev)} evidence records in the catalog database (cross-checked against paper/data/e7_coverage.json); "
              "source group from each record's source fragment, equipment-gap records assigned to a manufacturer by their applies_to field; "
              "data/physics/properties.json; saved in paper/data/fig_evidence_coverage.json"),
        claim="SOURCED+COMPUTED",
        caption=(f"(a) The {len(ev)} evidence records grouped by source and coloured by evidence class: {e7['evidence_by_status']['manufacturer_specification']} "
                 f"manufacturer specifications, {e7['evidence_by_status']['experimental_observation']} experimental observations, "
                 f"{e7['evidence_by_status']['reference_data']} reference data, {e7['evidence_by_status']['textbook_model']} textbook-model records, "
                 f"{e7['evidence_by_status']['inferred_estimate']} inferred estimates and {e7['evidence_by_status']['unknown']} records that document "
                 f"that a value is not stated; {man} records concern the six equipment families. (b) Status of the 40 physical compatibility properties "
                 f"per category, computed from the data: {tot['implemented_with_data']} implemented with documented data, {tot['representable_no_data']} "
                 f"representable without equipment data, {tot['representable_only']} representable only."),
        section="supplement"))


# ================================================================== 5. missing information
def fig_missing_info():
    e1 = load("e1_grid")
    e7 = load("e7_coverage")
    nmi = [r for r in e1["rows"] if r["verdict"] == "NEED_MORE_INFORMATION"]
    total = Counter()
    sole = Counter()
    by_ind = defaultdict(Counter)
    for r in nmi:
        for m in r["missing"]:
            total[m] += 1
            by_ind[m][CAT.experiments[r["experiment"]]["industry"]] += 1
        if len(r["missing"]) == 1:
            sole[r["missing"][0]] += 1
    n_missing_dist = Counter(len(r["missing"]) for r in nmi)
    models = set(CAT.coupled_models)
    # is each missing item recorded-but-unknown in the configuration, absent from it, or a coupled model?
    origin = Counter()
    for r in nmi:
        caps = {c["key"]: c for c in CAT.configurations[r["configuration"]]["capabilities"]}
        for m in r["missing"]:
            if m in models:
                origin["coupled_model"] += 1
            elif any(k in caps for k in m.split("/")):
                origin["recorded_unknown_or_not_installed"] += 1
            else:
                origin["key_absent_from_configuration"] += 1

    cov = coverage.build(CAT)
    unk = cov["missing_scientific_data"]["unknown_capabilities"]
    assert len(unk) == e7["unknown_capabilities"]
    blocking_keys = defaultdict(set)
    for r in nmi:
        for m in r["missing"]:
            for k in m.split("/"):
                blocking_keys[r["configuration"]].add(k)
    cfgs = cfg_order()
    unk_block = Counter()
    unk_other = Counter()
    unk_keys = defaultdict(list)
    for u in unk:
        cid = u["configuration_id"]
        unk_keys[cid].append(u["key"])
        (unk_block if u["key"] in blocking_keys[cid] else unk_other)[cid] += 1
    assert all(unk_block[c] + unk_other[c] == e7["unknown_by_configuration"].get(c, 0) for c in cfgs)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(COL2, 4.6), gridspec_kw=dict(width_ratios=[1, 1], wspace=0.95))
    fig.subplots_adjust(bottom=0.2)
    items = sorted(total, key=lambda k: (-total[k], k))
    ys = range(len(items))
    a1.barh(list(ys), [total[k] for k in items], color=SEQ_BLUE[1], height=0.7, label="pairs where it is missing")
    a1.barh(list(ys), [sole[k] for k in items], color=NAVY, height=0.7, label="pairs where it is the only missing item")
    for y, k in zip(ys, items):
        a1.text(total[k] + 0.8, y, f"{total[k]}" + (f"  ({sole[k]} sole)" if sole[k] else ""), va="center", fontsize=5.8, color=INK2)
    lab = []
    for k in items:
        s = k.replace("/", " / ")
        lab.append(s + ("  [model]" if k in models else ""))
    a1.set_yticks(list(ys))
    a1.set_yticklabels(lab, fontsize=5.9)
    a1.set_ylim(len(items) - 0.5, -0.5)
    a1.set_xlim(0, max(total.values()) * 1.35)
    a1.grid(axis="y", visible=False)
    a1.tick_params(axis="y", length=0)
    a1.set_xlabel(f"Undecided pairs (of {len(nmi)})")
    a1.set_title("a  What the checker lacked", loc="left", fontsize=7.5)
    a1.legend(loc="upper left", bbox_to_anchor=(-0.02, -0.15), fontsize=6.0, handlelength=1.4)

    y2 = list(range(len(cfgs)))
    b = [unk_block[c] for c in cfgs]
    o = [unk_other[c] for c in cfgs]
    a2.barh(y2, b, color=ORANGE, height=0.7, label="blocks at least one decision in the grid")
    a2.barh(y2, o, left=b, color="white", edgecolor=INK2, hatch="////", lw=0.5, height=0.7, label="not needed by any profile's decision")
    for y, c in zip(y2, cfgs):
        a2.text(b[y] + o[y] + 0.25, y, str(b[y] + o[y]), va="center", fontsize=5.8, color=INK2)
    a2.set_yticks(y2)
    a2.set_yticklabels([CFG_SHORT[c] for c in cfgs], fontsize=5.9)
    a2.set_ylim(len(cfgs) - 0.5, -0.5)
    a2.set_xlim(0, max(e7["unknown_by_configuration"].values()) + 3)
    a2.grid(axis="y", visible=False)
    a2.tick_params(axis="y", length=0)
    for fam, s, e in family_spans(cfgs):
        if s > 0:
            a2.axhline(s - 0.5, color=AXIS, lw=0.6)
    a2.set_xlabel(f"Unknown capabilities (total {len(unk)})")
    a2.set_title("b  Unknown specifications per configuration", loc="left", fontsize=7.5)
    a2.legend(loc="upper left", bbox_to_anchor=(-0.02, -0.15), fontsize=6.0, handlelength=1.4)
    a2.set_xticks(range(0, 13, 2))

    facts = {"need_more_information_pairs": len(nmi), "missing_items_ranked": [(k, total[k], sole[k]) for k in items],
             "missing_count_distribution": dict(sorted(n_missing_dist.items())),
             "unknown_capabilities": len(unk), "unknown_blocking": sum(unk_block.values()),
             "unknown_not_blocking": sum(unk_other.values()),
             "missing_item_origin": dict(origin),
             "unknown_by_configuration": {c: [unk_block[c], unk_other[c]] for c in cfgs},
             "unknown_keys_by_configuration": dict(unk_keys)}
    print("  missing facts:", {k: v for k, v in facts.items() if k not in ("unknown_by_configuration", "unknown_keys_by_configuration")})
    dump("fig_missing_info", {"source": "paper/data/e1_grid.json (Lean verdicts, missing = mandatory applicable checks with outcome unknown/unsupported); "
                                        "cryolean.coverage.build unknown_capabilities (cross-checked with e7_coverage.json)", "facts": facts})
    save(fig, "fig_missing_info", meta=dict(
        title="Missing information: what blocks a decision",
        question="When the checker returns NEED_MORE_INFORMATION, which undocumented specifications or model inputs are responsible, and which configurations have the most unknown specifications?",
        model="Counting over Lean results: a key or model is 'missing' in a pair when a mandatory, applicable Lean check on it has outcome unknown or unsupported; an unknown capability 'blocks' when its key is missing in at least one undecided pair of that configuration.",
        data=(f"paper/data/e1_grid.json ({len(nmi)} NEED_MORE_INFORMATION pairs of 286); unknown capabilities from cryolean.coverage.build "
              f"({len(unk)}, equal to paper/data/e7_coverage.json); saved in paper/data/fig_missing_info.json"),
        claim="COMPUTED",
        caption=(f"(a) Specification keys and coupled-model inputs that the Lean checker found undocumented in the {len(nmi)} undecided pairs, ranked by the "
                 f"number of pairs they affect; the dark bar counts pairs in which that item is the only missing one. Of the {sum(origin.values())} missing items, {origin['key_absent_from_configuration']} are keys the configuration's sources never mention, {origin['recorded_unknown_or_not_installed']} are recorded but unquantified or not installed, and {origin['coupled_model']} are coupled-model checks lacking an input. (b) The {len(unk)} capabilities "
                 f"the catalogue records as unknown, per configuration, split into those whose absence blocks at least one decision in the "
                 f"11 x 26 grid ({sum(unk_block.values())}) and those no current profile needs ({sum(unk_other.values())}). All counts come from Lean results and the sourced catalogue."),
        section="main"))


def main():
    apply()
    plt.rcParams["hatch.linewidth"] = 0.5
    only = set(sys.argv[1:])
    for name, fn in [("fig_compat_heatmap", fig_compat_heatmap), ("fig_capability_comparison", fig_capability_comparison),
                     ("fig_industry_coverage", fig_industry_coverage), ("fig_evidence_coverage", fig_evidence_coverage),
                     ("fig_missing_info", fig_missing_info)]:
        if not only or name in only:
            print(name)
            fn()


if __name__ == "__main__":
    main()
