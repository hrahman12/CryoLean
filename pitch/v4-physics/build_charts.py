"""Charts for the v4 Physics deck. Reads the CryoLean repo (read-only) and writes charts/*.svg + *.png.

    pitch/.venv/Scripts/python.exe pitch/v4-physics/build_charts.py
"""
from __future__ import annotations

import json
import pathlib
import sys
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
import chartstyle as cs  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

REPO = HERE.parent.parent  # repository root: this deck lives in <repo>/pitch/<deck>/
OUT = HERE / "charts"
C = cs.C


def load(rel: str):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def uW(s: str) -> float:
    return float(Fraction(s) * 10**6)


# ---------------------------------------------------------------- 1. Demo B heat budget
def heat_budget():
    d = load("paper/data/fig_heat_budget.json")
    states = d["states"]
    limit = uW(states[0]["rhs_W"])  # 12 µW, Bluefors LD400 at 20 mK
    fig, ax = cs.figure(790, 410)
    rows = [("Current\nwiring", states[0]), ("Z3's fix,\nLean re-checks", states[1])]
    parts = [("drive", "drive", C["silver"]), ("flux", "flux", C["blue"]), ("output", "output", C["dim"])]
    y = [1, 0]
    for (label, st), yy in zip(rows, y):
        left = 0.0
        for key, name, col in parts:
            w = uW(st["parts_W"][key])
            ax.barh(yy, w, left=left, height=0.5, color=col, edgecolor=C["panel"], linewidth=1.0)
            if key == "flux":
                ax.text(left + w / 2, yy, f"{st['n_flux_lines']} flux lines  {w:.3f}".rstrip("0"), ha="center",
                        va="center", fontsize=12.5, color="#0a1220", fontweight="bold")
            elif key == "drive":
                ax.text(left + w / 2, yy, "drive", ha="center", va="center", fontsize=12, color="#0a1220",
                        fontweight="bold")
            left += w
        total = uW(st["lhs_W"])
        met = st["verdict"] == "REQUIREMENTS_MET"
        col = C["teal"] if met else C["pink"]
        ax.text(total + 0.25, yy + 0.06, f"{total:.3f} µW", va="bottom", ha="left", fontsize=17,
                fontweight="bold", family="monospace", color=col)
        ax.text(total + 0.25, yy - 0.04, "Requirements met" if met else "Does not meet", va="top", ha="left",
                fontsize=12.5, color=col)
    ax.axvline(limit, color=C["cream"], lw=2, ls=(0, (5, 3)))
    ax.text(limit, 1.6, "12 µW cooling power at 20 mK", ha="center", va="bottom", fontsize=12.5,
            color=C["cream"], bbox=dict(boxstyle="square,pad=0.25", fc=C["panel"], ec="none"))
    ax.text(0.1, 1.6, "+ 8 output lines (dark grey)", ha="left", va="bottom", fontsize=11.5, color=C["muted"])
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=13, color=C["text"])
    ax.set_ylim(-0.55, 1.9)
    ax.set_xlim(0, 19.5)
    ax.set_xticks(range(0, 19, 3))
    ax.tick_params(axis="x", labelsize=12)
    ax.set_xlabel("mixing-chamber heat load with 3× margin (µW)", fontsize=12.5)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    fig.tight_layout(pad=1.0)
    cs.save(fig, OUT / "heat_budget")


# ---------------------------------------------------------------- 2. Demo D schedule
def schedule():
    s = load("docs/examples/demo_d_campaign_schedule.json")
    fits, short = s["fits"], s["too_long"]
    h = lambda t: float(t.split()[0])  # "5 h" -> 5.0
    cool = h(fits["cooldown"]) if isinstance(fits["cooldown"], str) else 5.0
    run = h(fits["run_length"])
    names = {
        "chem_phase_transition_pom": "Polarized microscopy",
        "chem_low_temperature_raman": "Low-T Raman",
        "bio_cryo_fluorescence_vitrified": "Cryo-fluorescence",
    }
    slots = [(names[t["experiment_id"]], h(t["start"]), h(t["stop"])) for t in fits["timeline"]]
    end = max(e for _, _, e in slots)

    import matplotlib.pyplot as plt
    cs.apply()
    fig = plt.figure(figsize=(860 / 96, 440 / 96), dpi=96)
    gs = fig.add_gridspec(2, 1, height_ratios=[5, 1.25], hspace=0.42)
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax)

    labels = ["Cooldown"] + [n for n, _, _ in slots] + ["10 T magnetoresistance"]
    ys = list(range(len(labels)))[::-1]
    ax.barh(ys[0], cool, left=0, height=0.6, color="none", edgecolor=C["silver"], hatch="///", lw=1.2)
    ax.text(cool + 0.5, ys[0], f"{cool:g} h", va="center", fontsize=12.5, color=C["silver"])
    for (n, a, b), yy in zip(slots, ys[1:]):
        ax.barh(yy, b - a, left=a, height=0.6, color=C["teal"])
        ax.text(b + 0.5, yy, f"{b - a:g} h", va="center", fontsize=12.5, color=C["teal"])
    ax.text(1.0, ys[-1], "Does not meet · never scheduled", va="center", fontsize=12.5,
            color=C["pink"])
    ax.axvline(end, color=C["cream"], lw=1.6, ls=(0, (4, 3)))
    ax.text(end + 0.6, ys[1] + 0.55, f"done at {end:g} h", fontsize=14, fontweight="bold", color=C["cream"],
            family="monospace")
    ax.axvline(run, color=C["muted"], lw=1.2)
    ax.text(run - 0.5, ys[0], f"{run:g} h run", ha="right", va="center", fontsize=12, color=C["muted"])
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=13)
    for t in ax.get_yticklabels():
        if t.get_text().startswith("10 T"):
            t.set_color(C["pink"])
    ax.set_ylim(-0.6, len(labels) - 0.4)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", labelbottom=False)
    ax.set_title("Lake Shore CRX-VF, one 48 h cold run", loc="left", fontsize=13, color=C["cream"], pad=8)

    # inset: the 20 h run (Z3 unsat core, not a Lean proof)
    srun = h(short["run_length"])
    ax2.barh(0, cool, height=0.6, color="none", edgecolor=C["silver"], hatch="///", lw=1.2)
    ax2.barh(0, srun - cool, left=cool, height=0.6, color=C["line2"])
    ax2.barh(0, cool + 18 - srun, left=srun, height=0.6, color="none", edgecolor=C["pink"], hatch="xx", lw=1.2)
    ax2.axvline(srun, color=C["pink"], lw=1.6)
    ax2.text(cool + 18 + 0.8, 0, "18 h needed, 15 h left · Z3 unsat core", va="center",
             fontsize=12.5, color=C["pink"])
    ax2.set_yticks([0])
    ax2.set_yticklabels(["20 h run"], fontsize=13)
    ax2.set_ylim(-0.6, 0.6)
    ax2.grid(axis="y", visible=False)
    ax2.spines["left"].set_visible(False)
    ax2.set_xlim(0, 48)
    ax2.set_xticks(range(0, 49, 6))
    ax2.tick_params(axis="x", labelsize=12)
    ax2.set_xlabel("hours from start of run", fontsize=12.5)
    fig.subplots_adjust(left=0.235, right=0.975, top=0.91, bottom=0.14)
    cs.save(fig, OUT / "schedule")


# ---------------------------------------------------------------- 3. Missing data
def missing_data():
    d = load("paper/data/fig_incomplete_info.json")
    s = d["summary_remove_mode"]["all"]
    k = s["k"]
    met = [100 * m[0] for m in s["mean"]]
    info = [100 * m[1] for m in s["mean"]]
    no = [100 * m[2] for m in s["mean"]]
    assert d["non_met_became_met"]["remove"] == 0 and d["non_met_became_met"]["install_unknown"] == 0
    fig, ax = cs.figure(790, 410)
    ax.stackplot(k, met, info, no, colors=[C["teal"], C["amber"], C["pink"]], alpha=0.92,
                 edgecolor=C["bg"], linewidth=0.8)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xticks(range(0, 101, 20))
    ax.set_xticklabels([f"{x}%" for x in range(0, 101, 20)])
    ax.set_yticks(range(0, 101, 25))
    ax.set_yticklabels([f"{x}%" for x in range(0, 101, 25)])
    ax.tick_params(labelsize=12)
    ax.tick_params(axis="x", pad=7)
    ax.tick_params(axis="y", pad=7)
    ax.set_xlabel("share of each machine's documented specs deleted", fontsize=12.5)
    ax.set_ylabel("share of the 286 pairs", fontsize=12.5)
    ax.grid(False)
    ax.text(48, 45, "Need more information", fontsize=15, fontweight="bold", color="#0a1220", ha="center")
    ax.text(14, 84, "Does not meet", fontsize=14, fontweight="bold", color="#0a1220", ha="left")
    ax.annotate("Requirements met", xy=(4, 3.5), xytext=(13, 16), fontsize=13, color=C["cream"],
                fontweight="bold", arrowprops=dict(arrowstyle="-", color=C["cream"], lw=1.2))
    n = d["lean_checks"]
    ax.text(98, 84, f"{n:,} Lean checks\n0 became met", ha="right", va="center", fontsize=14,
            fontweight="bold", color=C["cream"], family="monospace",
            bbox=dict(boxstyle="round,pad=0.45", fc=C["bg"], ec=C["line2"]))
    fig.tight_layout(pad=1.0)
    cs.save(fig, OUT / "missing_data")


if __name__ == "__main__":
    heat_budget()
    schedule()
    missing_data()
    print("charts written to", OUT)
