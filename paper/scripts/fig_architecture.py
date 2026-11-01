#!/usr/bin/env python
"""Figure: CryoLean system architecture (ILLUSTRATIVE schematic of the implemented components)."""
from __future__ import annotations

from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from style import *  # noqa: F401,F403

apply()
W, H = 14.0, 6.6
fig, ax = plt.subplots(figsize=(COL2, COL2 * H / W))
ax.set_xlim(0, W)
ax.set_ylim(-0.45, H)
ax.axis("off")


def box(x, y, w, h, title, lines, edge=AXIS, face="white", title_color=INK, mono=()):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", linewidth=0.9,
                                edgecolor=edge, facecolor=face))
    ax.text(x + 0.12, y + h - 0.2, title, fontsize=6.3, fontweight="bold", color=title_color, va="top")
    for i, ln in enumerate(lines):
        ax.text(x + 0.12, y + h - 0.48 - i * 0.22, ln, fontsize=4.9, color=INK2, va="top",
                family="DejaVu Sans Mono" if i in mono else "DejaVu Sans")


def zone(x, y, w, h, label, color, dashed):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.2", linewidth=1.2,
                                edgecolor=color, facecolor=color + "10", linestyle=(0, (5, 4)) if dashed else "-"))
    ax.text(x + 0.05, y + h + 0.08, label, fontsize=6.2, fontweight="bold", color=color, va="bottom")


def arrow(x1, y1, x2, y2, color=INK2, dashed=False, label=None, lx=None, ly=None, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8, linewidth=1.0, color=color,
                                 linestyle=(0, (4, 3)) if dashed else "-", connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 + 0.1, label,
                fontsize=5.0, color=color, ha="center", style="italic")


# columns
ax.text(0.2, 6.25, "INPUTS", fontsize=6.2, fontweight="bold", color=MUTED)
zone(3.55, 0.55, 3.6, 5.6, "UNTRUSTED: may propose", ORANGE, True)
zone(7.65, 0.55, 3.75, 5.6, "TRUSTED: Lean 4 decides", "#1a7f37", False)
ax.text(11.7, 6.25, "OUTPUTS", fontsize=6.2, fontweight="bold", color=MUTED)

box(0.2, 4.6, 3.0, 1.5, "Desktop UI", ["Codex-built frontend in a", "PyWebView window; no server", "cryolean/bridge.py"], mono=(2,))
box(0.2, 2.95, 3.0, 1.45, "Cryostat sheet", ["SQLite: 26 configurations, 9 families", "667 sourced evidence records", "121 explicit UNKNOWN entries"])
box(0.2, 1.3, 3.0, 1.45, "Experiment sheet", ["SQLite: 11 profiles from published", "procedures; 13 coupled models", "20 registered industries"])
box(0.2, 0.0, 3.0, 1.05, "Python boundary", ["exact rationals + SI dimensions", "cryolean/serialize.py"], mono=(1,))

box(3.75, 4.55, 3.2, 1.4, "Z3 feasibility search", ["assert_and_track: unsat core =", "reason; ranked alternatives;", "parameter repairs (Optimize)"], edge="#e7b48f")
box(3.75, 3.0, 3.2, 1.35, "Z3 campaign scheduler", ["pack accepted experiments in", "one cooldown; min makespan"], edge="#e7b48f")
box(3.75, 1.75, 3.2, 1.05, "LLM (Claude)", ["proposes Lean rules or new", "sheets; stored untrusted"], edge="#e7b48f")
box(3.75, 0.7, 3.2, 0.85, "Lanyon simulation", ["certificate + exported Lean proof"], edge="#e7b48f")

box(7.85, 3.75, 3.35, 2.2, "verdict cfg e", ["verdict_accept_iff", "verdict_reject_sound", "fail_needs_trusted", "accept_no_unknown",
                                            "pass_dims_all_match"], edge="#7fc79a", mono=(0, 1, 2, 3, 4))
box(7.85, 2.2, 3.35, 1.35, "validSchedule", ["validSchedule_sound, _complete,", "_bounds, _disjoint,", "_only_accepted"],
    edge="#7fc79a", mono=(0, 1, 2))
box(7.85, 0.7, 3.35, 1.3, "Gatekeeper", ["compiles against the project;", "no sorry, axiom, native_decide;", "axioms ⊆ {propext, Choice, Quot}"],
    edge="#7fc79a")

for (y, h, title, lines, col) in [(4.15, 1.8, "Verdict", ["Requirements met", "Does not meet + reason", "Need more information"], None),
                                  (2.2, 1.35, "Schedule", ["valid (checked slot list)", "or rejected + reasons"], None),
                                  (0.7, 1.3, "Rule Registry", ["admitted rules only", "(sha256, theorems, axioms)"], None)]:
    box(11.65, y, 2.3, h, title, lines, mono=())

# arrows: inputs -> proposers / kernel
for y0, y1 in [(5.3, 5.25), (3.7, 3.65), (2.0, 2.3)]:
    arrow(3.2, y0, 3.75, y1)
ax.plot([3.2, 9.5], [0.35, 0.35], color=INK2, linewidth=1.0)
arrow(9.5, 0.35, 9.5, 0.58, color=INK2)
ax.text(6.3, 0.18, "exact Lean JSON for every check", fontsize=5.2, color=INK2, ha="center", style="italic")
# proposers -> kernel (dashed = hint)
arrow(6.95, 5.2, 7.85, 5.0, ORANGE, True, "hint", 7.4, 5.25)
arrow(6.95, 3.65, 7.85, 3.0, ORANGE, True, "slots", 7.4, 3.5)
arrow(6.95, 2.25, 7.85, 1.6, ORANGE, True, "code", 7.38, 2.12)
arrow(6.95, 1.1, 7.85, 1.15, ORANGE, True, "proof", 7.4, 1.25)
# kernel -> outputs
for y in (4.85, 2.85, 1.35):
    arrow(11.2, y, 11.65, y, "#1a7f37")
ax.text(W / 2, -0.4, "Verdict card back to the UI: verdict · reason · theorem names · axioms · source hash    "
        "(Z3 output is a hint, never a verdict)", fontsize=5.8, color=NAVY, ha="center", va="bottom", fontweight="bold")

save(fig, "fig_architecture", meta=dict(
    title="CryoLean system architecture",
    question="How do untrusted proposers (Z3, an LLM, a simulation service) relate to the trusted Lean decision procedure?",
    model="Schematic of the implemented components and data flow (cryolean/bridge.py, verifier.py, smt.py, schedule.py, gatekeeper.py, lanyon.py; lean/CryoLean/*.lean).",
    data="Counts from paper/data/e7_coverage.json and the theorem names in lean/CryoLean/Soundness.lean and Schedule.lean.",
    claim="ILLUSTRATIVE",
    caption="System architecture. Inputs reach the trusted Lean kernel only as serialised exact-rational documents. Z3, an LLM and a simulation service propose; their outputs pass through verdict, validSchedule or the Gatekeeper before they reach the user as a verdict card.",
    section="main"))
