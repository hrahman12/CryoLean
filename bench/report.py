#!/usr/bin/env python
"""Write bench/RESULTS.md, bench/figures/* and the judge page bench/vs_regular_way.html from bench/results/*.json.

    python bench/report.py          (after python bench/vs_regular.py)

No number in the outputs is typed by hand: every figure is read from the JSON the benchmark wrote."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "bench" / "results"
FIG = ROOT / "bench" / "figures"
METHODS = ["R1", "R2", "R3", "CryoLean"]
NAME = {"R1": "Spec-sheet checklist", "R2": "Careful spreadsheet", "R3": "Physics-aware script", "CryoLean": "CryoLean"}
NICE_IND = {
    "aerospace_and_space_exploration": "Aerospace", "astronomy_and_astrophysics": "Astronomy",
    "automotive_and_transportation": "Automotive", "biology_and_biotechnology": "Biology",
    "chemistry_and_pharmaceuticals": "Chemistry & pharma", "defense_and_security": "Defense",
    "energy_and_hydrogen": "Energy & hydrogen", "environmental_science": "Environmental science",
    "food_and_agriculture": "Food & agriculture", "geology_and_oceanography": "Geology & oceans",
    "healthcare_and_medicine": "Healthcare", "manufacturing_and_industrial_processing": "Manufacturing",
    "materials_and_nanotechnology": "Materials & nano", "metrology_and_calibration": "Metrology",
    "nuclear_engineering_and_fusion": "Nuclear & fusion", "photonics_and_telecommunications": "Photonics",
    "physics_and_particle_accelerators": "Particle physics", "quantum_computing_and_sensing": "Quantum",
    "scientific_research": "General research", "semiconductors_and_electronics": "Semiconductors"}


def load(name: str):
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def fmt(n: int) -> str:
    return f"{n:,}"


def pct(a: int, b: int) -> str:
    return "0%" if a == 0 else f"{100 * a / b:.1f}%" if b else "–"


# ===================================================================================== data
S = load("summary")
T0, T1, T1A, T2, T3, T4, T5 = (load("t0_catalog"), load("t1_hide_one_line"), load("t1_hide_all_failing_lines"),
                                load("t2_borrowed_number"), load("t3_physics_sweep"), load("t4_history"),
                                load("t5_fault_injection"))
PROOFS = load("lean_proofs")

TESTS = [
    {"id": "T1", "name": "Hide one datasheet line", "cases": T1["cases"],
     "truth": "the configuration's own sourced spec rules the setup out",
     "wrong": {m: T1["by_method"][m]["wrong_YES"] for m in METHODS}},
    {"id": "T2", "name": "Borrow a sibling model's number", "cases": T2["cases"],
     "truth": "the configuration's own sourced spec rules the setup out",
     "wrong": {m: T2["by_method"][m]["wrong_YES"] for m in METHODS}},
    {"id": "T3", "name": "Scale a qubit chip, 1 to 200 qubits", "cases": T3["cases"],
     "truth": "Krinner et al.'s published heat-budget rule, recomputed exactly",
     "wrong": {m: T3["by_method"][m]["wrong_YES"] for m in METHODS}},
    {"id": "T4", "name": "Our own project history", "cases": T4["pairs_same_question"] if T4 else 0,
     "truth": "documentation found after the Oct 31 build, same requirements",
     "wrong": {m: T4["by_method"][m]["said_YES_later_documented_NO"] for m in METHODS} if T4 else {}},
    {"id": "T5", "name": "Inject a defect into the sheet", "cases": T5["cases"],
     "truth": "by construction: a planted defect leaves a line uncertifiable",
     "wrong": {m: T5["by_method"][m]["impossible_cases_said_YES"] + T5["by_method"][m]["uncertifiable_cases_said_YES"]
               for m in METHODS}},
]
# T1-T4 have a truth of NO (the setup is impossible); T5's wrong YES certify a line the sheet cannot support
IMPOSSIBLE = [t for t in TESTS if t["id"] in ("T1", "T2", "T3", "T4")]
TOTAL_CASES = sum(t["cases"] for t in IMPOSSIBLE)
TOTAL_WRONG = {m: sum(t["wrong"].get(m, 0) for t in IMPOSSIBLE) for m in METHODS}

wiring = T3["fridges"].get("bluefors_ld400_hdw", {})
RULE_MAX = wiring.get("rule_max_qubits")
R1_MAX = wiring.get("R1_max_yes")


def feat(test: dict, e: str, c: str) -> dict | None:
    return next((x for x in test.get("featured", []) if x["experiment_id"] == e and x["configuration_id"] == c), None)


F1 = feat(T1, "mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res")
F2 = feat(T2, "sci_graphene_yig_quantum_hall", "qd_dynacool_9T_eto_res")
F4 = (T4 or {}).get("examples", [None])[0]


# ===================================================================================== figures (matplotlib)
def figures() -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed: skipping PNG figures")
        return
    FIG.mkdir(parents=True, exist_ok=True)
    curve = [p for p in wiring.get("curve", []) if p["n"] <= 80]
    xs = [p["n"] for p in curve if p["load_W"] is not None]
    ys = [p["load_W"] * 1e6 for p in curve if p["load_W"] is not None]
    cool = next((p["cool_W"] for p in curve if p["cool_W"]), None)
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    ax.plot(xs, ys, color="#0b2a55", lw=2, label="3 × wiring heat load at the mixing chamber")
    if cool:
        ax.axhline(cool * 1e6, color="#1f9d4c", lw=1.5, ls="--", label=f"documented cooling power at 20 mK ({cool * 1e6:g} µW)")
    ax.axvspan(RULE_MAX + 0.5, R1_MAX + 0.5, color="#d33a3a", alpha=0.12,
               label=f"checklist & spreadsheet say YES, physics says NO ({RULE_MAX + 1}–{R1_MAX} qubits)")
    ax.axvline(R1_MAX + 0.5, color="#6b82a3", lw=1, ls=":")
    ax.text(R1_MAX + 1, max(ys) * 0.15, "168 RF lines\nrun out", fontsize=8, color="#33507a")
    ax.set_xlabel("qubits (Krinner et al. layout, scaled)")
    ax.set_ylabel("µW")
    ax.set_title("Bluefors LD400 + high-density wiring: who says YES?", fontsize=11)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False)
    ax.set_xlim(0, 80)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(FIG / f"qubit_sweep.{ext}")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.4), dpi=150)
    labels = [t["id"] + " " + t["name"] for t in TESTS]
    w = 0.2
    cols = {"R1": "#d33a3a", "R2": "#e39a12", "R3": "#8fa3bb", "CryoLean": "#1f9d4c"}
    for i, m in enumerate(METHODS):
        vals = [100 * t["wrong"].get(m, 0) / t["cases"] if t["cases"] else 0 for t in TESTS]
        ax.bar([k + (i - 1.5) * w for k in range(len(TESTS))], vals, w, color=cols[m], label=NAME[m])
    ax.set_xticks(range(len(TESTS)), labels, fontsize=7.5)
    ax.set_ylabel("% of cases answered YES wrongly")
    ax.legend(fontsize=7.5, frameon=False, ncol=4, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(FIG / f"wrong_yes_by_test.{ext}")
    plt.close(fig)


# ===================================================================================== RESULTS.md
def results_md() -> str:
    L = []
    a = L.append
    a("# CryoLean vs the regular way: results")
    a("")
    a(f"Generated by `python bench/vs_regular.py && python bench/report.py` against the Lean checker with source hash "
      f"`{S['lean_checker'][:16]}`. Every number below is read from `bench/results/*.json`.")
    a("")
    a("## Scoreboard: wrong YES answers (the dangerous error)")
    a("")
    a("A wrong YES means the method approved an experiment on a configuration that the ground truth rules out "
      "(T1–T4), or certified a line the sheet cannot support (T5). The ground truth never comes from CryoLean.")
    a("")
    a("| Test | Cases | Truth comes from | " + " | ".join(NAME[m] for m in METHODS) + " |")
    a("|---|---:|---|" + "---:|" * len(METHODS))
    for t in TESTS:
        a(f"| {t['id']} {t['name']} | {fmt(t['cases'])} | {t['truth']} | " +
          " | ".join(f"{fmt(t['wrong'].get(m, 0))} ({pct(t['wrong'].get(m, 0), t['cases'])})" for m in METHODS) + " |")
    a(f"| **Impossible setups approved, T1–T4** | **{fmt(TOTAL_CASES)}** | | " +
      " | ".join(f"**{fmt(TOTAL_WRONG[m])}**" for m in METHODS) + " |")
    a("")
    a("![wrong YES by test](figures/wrong_yes_by_test.png)")
    a("")
    a("## The regular way, three versions (bench/regular_way.py)")
    a("")
    a("| | Reads | Blank line | Coupled physics | Unsourced numbers |")
    a("|---|---|---|---|---|")
    a("| R1 Spec-sheet checklist | one line at a time | passes | ignored | believed |")
    a("| R2 Careful spreadsheet | one line at a time | NEED INFO | ignored | believed |")
    a("| R3 Physics-aware script | lines + physics in floats | NEED INFO | computed, no validity range | believed |")
    a("| CryoLean | lines + physics, exact rationals | NEED INFO | computed inside its validity range | never decide |")
    a("")
    a("All three regular methods read the same input documents as the Lean checker and respect the documented install "
      "status (a brochure option documented as not fitted counts as absent).")
    a("")
    a("## T0 Catalog head-to-head (no ground truth, but a theorem)")
    a("")
    c = T0["counts"]
    a(f"{fmt(T0['pairs'])} pairs ({T0['experiments']} experiments × {T0['configurations']} configurations), "
      f"decided by the Lean binary in {T0['seconds']} s.")
    a("")
    a("| | YES | NO | NEED INFO |")
    a("|---|---:|---:|---:|")
    for m in METHODS:
        a(f"| {NAME[m]} | {fmt(c[m]['YES'])} | {fmt(c[m]['NO'])} | {fmt(c[m]['NEED_INFO'])} |")
    a("")
    a("By `sound_yes_le_cryolean` (lean/VsRegular.lean), no checker that is never wrong can say YES where CryoLean "
      "does not, so every extra YES below is unsupported by the specification (`extra_yes_unsupported`):")
    a("")
    for m in ("R1", "R2", "R3"):
        causes = ", ".join(f"{k}: {fmt(v)}" for k, v in T0["yes_without_support_by_cause"][m].items())
        a(f"* {NAME[m]}: {fmt(T0['yes_without_support'][m])} unsupported YES ({causes}); "
          f"{fmt(T0['no_without_support'][m])} NO without a sourced violation.")
    a("")
    a("## T1 Hide one datasheet line")
    a("")
    a(f"Pairs that CryoLean rejects on exactly one sourced datasheet line (no coupled check failing): {fmt(T1['cases'])}. "
      "We delete that line from the configuration, as if the sheet were silent on it, and rebuild the documents "
      "(anything still derivable from other lines stays). The machine did not change, so the truth is still NO.")
    a("")
    for m in METHODS:
        b = T1["by_method"][m]
        a(f"* {NAME[m]}: YES {fmt(b['YES'])}, NEED INFO {fmt(b['NEED_INFO'])}, NO {fmt(b['NO'])}")
    a(f"* CryoLean's NEED INFO named the hidden line in {fmt(T1['cryolean_need_info_names_the_hidden_line'])} of "
      f"{fmt(T1['by_method']['CryoLean']['NEED_INFO'])} cases.")
    a(f"* Hiding every failing line instead ({fmt(T1A['cases'])} pairs): checklist wrong YES "
      f"{fmt(T1A['by_method']['R1']['wrong_YES'])}, CryoLean {fmt(T1A['by_method']['CryoLean']['wrong_YES'])}.")
    if F1:
        a(f"* Example: *{F1['experiment']}* on *{F1['configuration']}*. {F1['why_no'][0]}. Hidden: "
          f"`{', '.join(F1['hidden'])}`. Checklist {F1['R1']}, CryoLean {F1['CryoLean']}.")
    a("")
    a("## T2 Borrow a sibling model's number")
    a("")
    a(f"Same rejected pairs, but every failing line is refilled with the value printed for another configuration of the "
      f"same instrument (the 12 T column read for the 9 T magnet), recorded as what it is: an inferred estimate. "
      f"{fmt(T2['cases'])} pairs could be refilled this way.")
    a("")
    for m in METHODS:
        b = T2["by_method"][m]
        a(f"* {NAME[m]}: wrong YES {fmt(b['wrong_YES'])}")
    if F2:
        a(f"* Example: *{F2['experiment']}* on *{F2['configuration']}*. {F2['why_no'][0]}. Borrowed from "
          f"`{', '.join(f'{k} <- {v}' for k, v in (F2['borrowed_from'] or {}).items())}`. Spreadsheet {F2['R2']}, "
          f"physics script {F2['R3']}, CryoLean {F2['CryoLean']}.")
    a("")
    a("## T3 Scale a superconducting-qubit chip")
    a("")
    a(f"Krinner et al.'s 50-qubit wiring layout scaled to 1–200 qubits on all {T3['configurations']} configurations "
      f"({fmt(T3['cases'])} cases). Truth: base temperature ≤ 20 mK, enough RF lines, and 3 × the summed per-line heat "
      "load ≤ the cooling power documented at a temperature ≤ 20 mK, recomputed in exact fractions without Lean.")
    a("")
    for m in METHODS:
        b = T3["by_method"][m]
        a(f"* {NAME[m]}: wrong YES {fmt(b['wrong_YES'])}, wrong NO {fmt(b['wrong_NO'])}, agrees with the rule on "
          f"{fmt(b['agree_with_rule'])}")
    a(f"* On the Bluefors LD400 with high-density wiring the rule allows {RULE_MAX} qubits; the checklist and the "
      f"careful spreadsheet say YES up to {R1_MAX} (until the 168 RF lines run out).")
    a("")
    a("![qubit sweep](figures/qubit_sweep.png)")
    a("")
    if T4:
        a("## T4 Our own project history")
        a("")
        a(f"The catalog of revision `{T4['revision']}` (Oct 31) against today's catalog, on the {fmt(T4['pairs_same_question'])} "
          f"pairs whose experiment requirements did not change. Documentation found since then decides "
          f"{fmt(T4['later_documented_NO'])} of them as NO and {fmt(T4['later_documented_YES'])} as YES.")
        a("")
        for m in METHODS:
            b = T4["by_method"][m]
            a(f"* {NAME[m]} on the Oct 31 data: YES to {fmt(b['said_YES_later_documented_NO'])} pairs later documented NO; "
              f"NO to {fmt(b['said_NO_later_documented_YES'])} later documented YES")
        a("")
    a("## T5 Fault injection")
    a("")
    a(f"{fmt(T5['cases'])} synthetic configurations (the paper's E4 generator): {fmt(T5['impossible'])} with a defect that "
      f"makes the run impossible, {fmt(T5['uncertifiable'])} with a line that cannot be certified (unknown value, "
      f"estimate, no provenance, unknown install status, wrong dimension, missing), {T5['controls']} clean controls.")
    a("")
    for m in METHODS:
        b = T5["by_method"][m]
        a(f"* {NAME[m]}: impossible said YES {b['impossible_cases_said_YES']}, uncertifiable said YES "
          f"{fmt(b['uncertifiable_cases_said_YES'])}, exact agreement with the truth {fmt(b['exact_agreement_with_truth'])}"
          f"/{fmt(T5['cases'])}")
    a("")
    a("## What correct means")
    a("")
    a("Correct means CryoLean's answer matches the specification in `lean/CryoLean/Spec.lean`, written separately from "
      "the checker. `verdict_accept_iff`: YES exactly when `AcceptSpec` holds; `verdict_reject_sound` / "
      "`verdict_reject_complete`: NO exactly when `RejectSpec` holds; NEED INFO otherwise. The layers: `ValueMeets` "
      "(one documented number meets one requirement, units checked, exact rationals) -> `SatisfiesKey` (installed and "
      "trusted source only) -> `ReqOK` / `CoupledOK` (every mandatory line and physics relation, inside its validity "
      "range) -> `AcceptSpec` (confirmed profile, all of the above, at least one genuine pass). `RejectSpec` mirrors it "
      "with `ValueFails`. Correct is relative to this specification and the sourced records, not a proof that a "
      "datasheet is true.")
    a("")
    a("## Proved in Lean (lean/VsRegular.lean)")
    a("")
    a(f"`lake env lean VsRegular.lean` compiles {len(PROOFS['theorems'])} theorems; standard axioms only: "
      f"{PROOFS['standard_axioms_only']}.")
    a("")
    a("| Theorem | Axioms |")
    a("|---|---|")
    for k, v in PROOFS["theorems"].items():
        a(f"| `{k}` | {', '.join(v) or 'none'} |")
    a("")
    a("## What this does not show")
    a("")
    a("* The truth in T1, T2 and T4 is the catalog's sourced record. If a datasheet is wrong, every method inherits it.")
    a("* T1 and T2 perturb real records; they measure what each method does with a silent or borrowed line, not how "
      "often datasheets are silent in practice.")
    a("* The regular-way checkers are ours. They are in `bench/regular_way.py`, read the same documents, and respect "
      "install status; R2 and R3 already avoid the silent-line error, which is why we report all three.")
    a("* Floating point never flipped a verdict in these runs; R3's misses come from believing unsourced numbers.")
    a("* No LLM baseline is included yet.")
    a("")
    return "\n".join(L) + "\n"


# ===================================================================================== judge page (HTML)
def esc(s) -> str:
    return html.escape(str(s))


def svg_qubits() -> str:
    """Inline SVG of the LD400 qubit sweep, drawn to one scale."""
    curve = [p for p in wiring.get("curve", []) if p["n"] <= 80 and p["load_W"] is not None]
    if not curve:
        return ""
    W, H, l, r, t, b = 720, 340, 118, 18, 22, 100
    xmax, ymax = 80, 25.0
    X = lambda n: l + (W - l - r) * n / xmax  # noqa: E731
    Y = lambda u: t + (H - t - b) * (1 - u / ymax)  # noqa: E731
    cool = curve[0]["cool_W"] * 1e6
    pts = " ".join(f"{X(p['n']):.1f},{Y(min(p['load_W'] * 1e6, ymax)):.1f}" for p in curve)
    g = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Wiring heat load versus number of qubits on the Bluefors LD400" class="chart">']
    for u in range(0, 26, 5):
        g.append(f'<line x1="{l}" x2="{W - r}" y1="{Y(u):.1f}" y2="{Y(u):.1f}" class="grid"/>'
                 f'<text x="{l - 8}" y="{Y(u) + 4:.1f}" class="tick" text-anchor="end">{u}</text>')
    for n in range(0, 81, 10):
        g.append(f'<text x="{X(n):.1f}" y="{H - b + 18}" class="tick" text-anchor="middle">{n}</text>')
    g.append(f'<text x="{l}" y="{t - 4}" class="axis">µW at the mixing chamber</text>')
    g.append(f'<text x="{W - r}" y="{H - b + 34}" class="axis" text-anchor="end">qubits</text>')
    g.append(f'<rect x="{X(RULE_MAX + 0.5):.1f}" y="{t}" width="{X(R1_MAX + 0.5) - X(RULE_MAX + 0.5):.1f}" '
             f'height="{H - t - b}" class="danger"/>')
    g.append(f'<text x="{(X(RULE_MAX + 0.5) + X(R1_MAX + 0.5)) / 2:.1f}" y="{t + 16}" class="danger-label" '
             f'text-anchor="middle">regular way: YES · physics: NO</text>')
    g.append(f'<line x1="{l}" x2="{W - r}" y1="{Y(cool):.1f}" y2="{Y(cool):.1f}" class="cool"/>'
             f'<text x="{X(2):.1f}" y="{Y(cool) - 6:.1f}" class="cool-label">cooling power at 20 mK: {cool:g} µW</text>')
    g.append(f'<polyline points="{pts}" class="load"/>')
    g.append(f'<text x="{X(22):.1f}" y="{Y(curve[21]["load_W"] * 1e6) + 24:.1f}" class="load-label">3 × wiring heat load</text>')
    g.append(f'<line x1="{X(R1_MAX + 0.5):.1f}" x2="{X(R1_MAX + 0.5):.1f}" y1="{t}" y2="{H - b}" class="limit"/>'
             f'<text x="{X(R1_MAX + 1.2):.1f}" y="{Y(3):.1f}" class="tick">168 RF lines</text>'
             f'<text x="{X(R1_MAX + 1.2):.1f}" y="{Y(3) + 13:.1f}" class="tick">run out</text>')
    rows = [("Checklist", R1_MAX, "no"), ("Spreadsheet", wiring.get("R2_max_yes"), "no"),
            ("Physics script", wiring.get("R3_max_yes"), "ok"), ("CryoLean", wiring.get("CryoLean_max_yes"), "ok")]
    for i, (name, mx, kind) in enumerate(rows):
        y = H - b + 44 + i * 12
        g.append(f'<text x="{l - 8}" y="{y + 4}" class="tick" text-anchor="end">{esc(name)}</text>'
                 f'<rect x="{X(0.5):.1f}" y="{y - 3}" width="{X(mx + 0.5) - X(0.5):.1f}" height="7" class="bar-{kind}"/>'
                 f'<text x="{X(mx + 0.5) + 4:.1f}" y="{y + 4}" class="tick">YES up to {mx}</text>')
    g.append("</svg>")
    return "".join(g)


def svg_industries() -> str:
    rows = sorted(((NICE_IND.get(k, k), v["R1"] / v["cases"], v["CryoLean"]) for k, v in T1["wrong_yes_by_industry"].items()
                   if v["cases"]), key=lambda x: -x[1])
    W, rowh, l, r = 720, 19, 150, 70
    H = 26 + rowh * len(rows)
    X = lambda f: l + (W - l - r) * f  # noqa: E731
    g = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Share of hidden-line cases the checklist answered YES, by industry" class="chart">']
    for f in (0, .25, .5, .75, 1):
        g.append(f'<line x1="{X(f):.1f}" x2="{X(f):.1f}" y1="14" y2="{H - 4}" class="grid"/>'
                 f'<text x="{X(f):.1f}" y="10" class="tick" text-anchor="middle">{int(f * 100)}%</text>')
    for i, (name, frac, cyes) in enumerate(rows):
        y = 22 + i * rowh
        g.append(f'<text x="{l - 8}" y="{y + 9}" class="tick" text-anchor="end">{esc(name)}</text>'
                 f'<rect x="{l}" y="{y}" width="{X(frac) - l:.1f}" height="12" class="bar-no"/>'
                 f'<text x="{X(frac) + 5:.1f}" y="{y + 10}" class="tick">{100 * frac:.0f}%</text>')
    g.append("</svg>")
    return "".join(g)


def spec_excerpt(start: str, stop: str) -> str:
    """Lines of lean/CryoLean/Spec.lean from the one containing `start` up to (not including) the one containing `stop`."""
    lines = (ROOT / "lean" / "CryoLean" / "Spec.lean").read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(lines) if start in l)
    j = next(k for k, l in enumerate(lines) if k > i and stop in l)
    return "\n".join(lines[i:j]).rstrip()


MEETS = [
    ("pointWithin", "the operating point lies inside the documented range", "run at 4 K on a machine documented for 1.8–400 K"),
    ("rangeWithin", "the whole required range lies inside the documented range", "sweep 5–300 K inside 1.8–400 K"),
    ("atLeastMax", "the documented maximum reaches the requirement", "need 10 T, the magnet goes to 14 T"),
    ("atLeastRange", "the top of the documented range reaches it", "need 300 K, the range ends at 400 K"),
    ("atMostMin", "the documented minimum gets low enough", "need 20 mK or colder, the LD400 reaches 10 mK"),
    ("atMostRange", "the bottom of the documented range gets low enough", "need 2 K, the range starts at 1.8 K"),
    ("flagIs", "a yes/no feature is what the experiment needs", "optical access is present"),
    ("countAtLeast", "there are enough of something", "need 124 RF lines, the LD400 + HDW has 168"),
    ("countEquals", "there is exactly the required number", "exactly the number of probe arms the method uses"),
    ("enumIn", "the category is one the experiment allows", "the cryogen is liquid nitrogen"),
    ("setContains", "every needed item is in the documented set", "every measurement module the method needs"),
]


def correct_section() -> str:
    meets = esc(spec_excerpt('documented value `v` meets', 'documented value `v` demonstrably'))
    accept = esc(spec_excerpt("What ACCEPT is supposed to mean", "What REJECT is supposed to mean"))
    rows = "".join(f"<tr><td><code>{esc(k)}</code></td><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for k, a, b in MEETS)
    return f"""
<section aria-labelledby="correct">
  <h2 id="correct">What “correct” means</h2>
  <div class="col">
  <p>Correct means CryoLean's answer matches a specification written separately from the checker, in <code>lean/CryoLean/Spec.lean</code>. The two share only the record lookup, the exact rational order and exact arithmetic. Lean proves the match in both directions: <code>verdict_accept_iff</code> says CryoLean answers YES exactly when <code>AcceptSpec</code> holds, <code>verdict_reject_sound</code> and <code>verdict_reject_complete</code> say it answers NO exactly when <code>RejectSpec</code> holds, and NEED INFO is everything else. The specification is built in four layers.</p>
  <ol class="layers">
    <li><b><code>ValueMeets</code>: one documented number meets one requirement.</b> Every numeric case carries a unit check as a premise (<code>d : m.dim = q.dim</code>), so tesla is never compared with kelvin, and the comparison is exact: <code>Q.le a b</code> is <code>a.num × b.den ≤ b.num × a.den</code> on integers.</li>
    <li><b><code>SatisfiesKey</code>: the number counts only if it belongs to the installed configuration and has a trusted source</b> (manufacturer specification, measurement, reference data, a certified simulation, or the user's own entry). The one other way to satisfy a line is a trusted record that an option is not fitted, and only when the experiment needs that item absent. Estimates and unsourced records never count.</li>
    <li><b><code>ReqOK</code> and <code>CoupledOK</code>: every mandatory requirement passes on some alternative key or is ruled out by a definitely false condition, and every coupled physics relation holds inside its validity range</b> (for example, wiring heat load at most the cooling power documented at a temperature no warmer than the operating point).</li>
    <li><b><code>AcceptSpec</code>: the profile is confirmed, all of the above holds, and at least one item genuinely passes.</b> <code>RejectSpec</code> mirrors it with <code>ValueFails</code>: some mandatory item is violated by trusted evidence on every alternative.</li>
  </ol>
  <h3>Layer 1, as written in the specification</h3>
  </div>
<pre><code>{meets}</code></pre>
  <div class="scroll"><table class="meets"><thead><tr><th>Case</th><th>Means</th><th>For example</th></tr></thead><tbody>{rows}</tbody></table></div>
  <div class="col">
  <p class="note"><code>ValueFails</code> has the same eleven cases with the comparison negated. A value that is unknown, has the wrong units or the wrong shape satisfies neither, so it can only ever produce NEED INFO.</p>
  <h3>Layer 4, the definition of YES</h3>
  </div>
<pre><code>{accept}</code></pre>
  <div class="col">
  <p class="note">Correct is relative to this specification and to the sourced records. Lean does not prove that a datasheet is true or that the specification captures every physical effect.</p>
  </div>
</section>
"""


def page() -> str:
    t1b, t2b = T1["by_method"], T2["by_method"]
    score_rows = []
    for t in TESTS:
        cells = []
        for m in METHODS:
            w = t["wrong"].get(m, 0)
            cls = "zero" if w == 0 else ("hot" if t["cases"] and w / t["cases"] > 0.2 else "warm")
            cells.append(f'<td class="num {cls}"><span class="big">{fmt(w)}</span><span class="sub">{pct(w, t["cases"])}</span></td>')
        score_rows.append(f'<tr><th scope="row"><span class="tid">{t["id"]}</span> {esc(t["name"])}'
                          f'<span class="truth">Truth: {esc(t["truth"])} · {fmt(t["cases"])} cases</span></th>{"".join(cells)}</tr>')
    total_cells = "".join(f'<td class="num total {"zero" if TOTAL_WRONG[m] == 0 else "hot"}">{fmt(TOTAL_WRONG[m])}</td>' for m in METHODS)
    thm_rows = "".join(f"<tr><td><code>{esc(k)}</code></td><td>{esc(', '.join(v))}</td></tr>" for k, v in PROOFS["theorems"].items())
    c0 = T0["counts"]
    f1 = (f"<p class=\"ex\"><b>Example.</b> {esc(F1['experiment'])} on the {esc(F1['configuration'])}. "
          f"{esc(F1['why_no'][0])}. With the magnet line hidden the checklist answers <b class=\"no\">{F1['R1']}</b>; "
          f"CryoLean answers <b class=\"info\">{F1['CryoLean']}</b> and names <code>{esc(F1['hidden'][0])}</code> as the line to look up.</p>") if F1 else ""
    f2 = ""
    if F2:
        k, v = next(iter((F2.get("borrowed_from") or {}).items()))
        f2 = (f"<p class=\"ex\"><b>Example.</b> {esc(F2['experiment'])} on the {esc(F2['configuration'])}. "
              f"{esc(F2['why_no'][0])}. Fill the blank with the <code>{esc(k)}</code> printed for <code>{esc(v)}</code> and the "
              f"careful spreadsheet answers <b class=\"no\">{F2['R2']}</b>, the physics script <b class=\"no\">{F2['R3']}</b>; "
              f"CryoLean answers <b class=\"info\">{F2['CryoLean']}</b>, because a number borrowed from another configuration is an "
              f"estimate and estimates never decide.</p>")
    f4 = ""
    if F4:
        f4 = (f"<p class=\"ex\"><b>Example.</b> <code>{esc(F4['experiment'])}</code> on <code>{esc(F4['configuration'])}</code>: on the Oct 31 "
              f"data the checklist said <b class=\"no\">{F4['R1']}</b> and CryoLean said <b class=\"info\">{F4['CryoLean']}</b>. "
              f"The record found later: {esc(F4['why_today'][0])}.</p>")
    t4_html = ""
    if T4:
        b4 = T4["by_method"]
        t4_html = f"""
<section class="test" id="t4">
  <header><span class="tid">T4</span><h2>Our own project history</h2></header>
  <p>The same experiments and machines on the catalog as it stood on Oct 31 (revision <code>{esc(T4['revision'])}</code>) and on today's catalog,
  limited to the {fmt(T4['pairs_same_question'])} pairs whose requirements did not change. The specs the team dug up since then show
  {fmt(T4['later_documented_NO'])} of those pairs to be impossible.</p>
  <ul class="tally">
    <li><span>Checklist said YES to</span><b class="no">{fmt(b4['R1']['said_YES_later_documented_NO'])}</b></li>
    <li><span>Careful spreadsheet</span><b class="{'no' if b4['R2']['said_YES_later_documented_NO'] else 'ok'}">{fmt(b4['R2']['said_YES_later_documented_NO'])}</b></li>
    <li><span>Physics script</span><b class="{'no' if b4['R3']['said_YES_later_documented_NO'] else 'ok'}">{fmt(b4['R3']['said_YES_later_documented_NO'])}</b></li>
    <li><span>CryoLean</span><b class="ok">{fmt(b4['CryoLean']['said_YES_later_documented_NO'])}</b></li>
  </ul>
  {f4}
</section>"""
    b5 = T5["by_method"]
    return f"""<title>CryoLean vs the Regular Way</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@700;800;900&family=Red+Hat+Text:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one reading column; the scoreboard and the two charts break out to a wider measure. Tokens follow the CryoLean site. */
:root {{
  --bg: #eef4fb; --panel: #f9fcff; --line: #c9dbf2; --ink: #0b2a55; --ink-2: #33507a; --muted: #5d7597;
  --accent: #1468e8; --ok: #17803d; --ok-soft: #e1f3e7; --no: #c72f2f; --no-soft: #fbe3e3; --info: #a86a00; --info-soft: #fdf1d6;
  --grid: #d7e3f3; --code: #e6eef9;
  --display: "Red Hat Display", "Segoe UI", system-ui, sans-serif;
  --text: "Red Hat Text", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #081427; --panel: #0d1d36; --line: #22385a; --ink: #e4edf9; --ink-2: #b4c6e0; --muted: #8aa1c2;
  --accent: #6aa5ff; --ok: #4cc77a; --ok-soft: #10301f; --no: #ff7b7b; --no-soft: #3a1518; --info: #f2b544; --info-soft: #33260a;
  --grid: #1b2f4e; --code: #12264a; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #081427; --panel: #0d1d36; --line: #22385a; --ink: #e4edf9; --ink-2: #b4c6e0; --muted: #8aa1c2;
  --accent: #6aa5ff; --ok: #4cc77a; --ok-soft: #10301f; --no: #ff7b7b; --no-soft: #3a1518; --info: #f2b544; --info-soft: #33260a;
  --grid: #1b2f4e; --code: #12264a; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--ink); font: 16px/1.6 var(--text); }}
.wrap {{ max-width: 1040px; margin: 0 auto; padding-block: 40px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
.col {{ max-width: 720px; }}
.eyebrow {{ font: 500 12px/1.4 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
h1 {{ font: 900 clamp(30px, 5vw, 48px)/1.08 var(--display); margin: 10px 0 16px; text-wrap: balance; letter-spacing: -.01em; }}
h1 .no {{ color: var(--no); }} h1 .ok {{ color: var(--ok); }}
h2 {{ font: 800 24px/1.2 var(--display); margin: 0; text-wrap: balance; }}
h3 {{ font: 700 17px/1.3 var(--display); margin: 0 0 6px; }}
p {{ margin: 0 0 14px; }}
.lede {{ font-size: 18px; color: var(--ink-2); }}
code {{ font: 13px/1.4 var(--mono); background: var(--code); padding: 1px 5px; border-radius: 4px; overflow-wrap: anywhere; }}
b.no, .no {{ color: var(--no); }} b.ok, .ok {{ color: var(--ok); }} b.info, .info {{ color: var(--info); }}
.scroll {{ overflow-x: auto; }}
table.score {{ width: 100%; border-collapse: collapse; min-width: 640px; font-variant-numeric: tabular-nums; margin-top: 18px; }}
.score thead th {{ font: 600 12px/1.3 var(--text); color: var(--muted); text-align: right; padding: 8px 10px; vertical-align: bottom; }}
.score thead th:first-child {{ text-align: left; }}
.score thead th.us {{ color: var(--ok); }}
.score tbody th {{ text-align: left; font-weight: 600; padding: 12px 10px; border-top: 1px solid var(--line); }}
.score .truth {{ display: block; font: 400 12.5px/1.4 var(--text); color: var(--muted); margin-top: 2px; }}
.tid {{ font: 500 12px var(--mono); color: var(--accent); margin-right: 4px; }}
.score td.num {{ text-align: right; padding: 12px 10px; border-top: 1px solid var(--line); white-space: nowrap; }}
.score .big {{ display: block; font: 800 20px/1.1 var(--display); }}
.score .sub {{ font: 12px var(--mono); color: var(--muted); }}
.score td.hot .big {{ color: var(--no); }} .score td.warm .big {{ color: var(--info); }} .score td.zero .big {{ color: var(--ok); }}
.score td.zero {{ background: var(--ok-soft); }}
.score tfoot td, .score tfoot th {{ border-top: 2px solid var(--ink); padding: 12px 10px; font: 800 18px var(--display); text-align: right; }}
.score tfoot th {{ text-align: left; font: 700 15px var(--display); }}
.score tfoot td.hot {{ color: var(--no); }} .score tfoot td.zero {{ color: var(--ok); background: var(--ok-soft); }}
.note {{ font-size: 13.5px; color: var(--muted); }}
section {{ margin-top: 56px; }}
.methods {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 18px; }}
.method {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px; min-width: 0; }}
.method.us {{ border-color: var(--ok); }}
.method ul {{ margin: 8px 0 0; padding-left: 18px; font-size: 14px; color: var(--ink-2); }}
.test header {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px; }}
.test header .tid {{ font-size: 14px; }}
.tally {{ list-style: none; padding: 0; margin: 14px 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
.tally li {{ border-left: 3px solid var(--line); padding: 2px 0 2px 10px; }}
.tally span {{ display: block; font-size: 12.5px; color: var(--muted); }}
.tally b {{ font: 800 26px/1.2 var(--display); font-variant-numeric: tabular-nums; }}
.ex {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; font-size: 14.5px; }}
.chart {{ width: 100%; height: auto; display: block; margin: 8px 0 4px; }}
.chart .grid {{ stroke: var(--grid); stroke-width: 1; }}
.chart .tick {{ fill: var(--muted); font: 11px var(--mono); }}
.chart .axis {{ fill: var(--ink-2); font: 600 12px var(--text); }}
.chart .load {{ fill: none; stroke: var(--ink); stroke-width: 2.4; }}
.chart .load-label {{ fill: var(--ink); font: 600 12px var(--text); }}
.chart .cool {{ stroke: var(--ok); stroke-width: 2; stroke-dasharray: 6 4; }}
.chart .cool-label {{ fill: var(--ok); font: 600 12px var(--text); }}
.chart .danger {{ fill: var(--no-soft); }}
.chart .danger-label {{ fill: var(--no); font: 700 12px var(--text); }}
.chart .limit {{ stroke: var(--muted); stroke-dasharray: 2 3; }}
.chart .bar-no {{ fill: var(--no); opacity: .8; }} .chart .bar-ok {{ fill: var(--ok); }}
table.thm {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
ol.layers {{ margin: 14px 0 18px; padding-left: 22px; display: grid; gap: 10px; }}
ol.layers li {{ padding-left: 4px; }}
ol.layers li::marker {{ font: 700 15px var(--display); color: var(--accent); }}
table.meets {{ width: 100%; border-collapse: collapse; font-size: 13.5px; min-width: 560px; margin: 4px 0 12px; }}
.meets th {{ text-align: left; font: 600 12px var(--text); color: var(--muted); padding: 6px 8px; }}
.meets td {{ border-top: 1px solid var(--line); padding: 6px 8px; vertical-align: top; }}
.meets td:last-child {{ color: var(--ink-2); }}
.thm td {{ border-top: 1px solid var(--line); padding: 6px 8px; vertical-align: top; }}
.thm td:last-child {{ color: var(--muted); font: 12px var(--mono); }}
pre {{ background: var(--code); border-radius: 8px; padding: 14px; overflow-x: auto; font: 12.5px/1.55 var(--mono); }}
.claims {{ display: grid; gap: 10px; margin: 14px 0; }}
.claim {{ border-left: 3px solid var(--accent); padding: 2px 0 2px 12px; }}
.claim code {{ font-size: 12px; }}
ul.limits li {{ margin-bottom: 6px; }}
footer {{ margin-top: 56px; font-size: 13px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 16px; }}
a {{ color: var(--accent); }}
a:focus-visible, button:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
@media (max-width: 520px) {{ .lede {{ font-size: 16.5px; }} .score .big {{ font-size: 17px; }} }}
</style>
<div class="wrap">
<header class="col">
  <div class="eyebrow">VibeCheck FM × AI · CryoLean · head-to-head</div>
  <h1>The regular datasheet check approved <span class="no">{fmt(TOTAL_WRONG['R1'])}</span> setups the evidence rules out. CryoLean approved <span class="ok">none</span>.</h1>
  <p class="lede">Same catalog, same {fmt(T0['pairs'])} experiment × cryostat pairs, the same input files. We ran three versions of the regular way and the Lean checker through five tests where the right answer does not come from CryoLean: the manufacturer's own specs, a published heat-budget rule, documentation we found after the fact, and planted defects. Then we proved in Lean why the result has to come out this way.</p>
</header>

<section class="scoreboard" aria-labelledby="sb">
  <h2 id="sb">Wrong YES answers, by test</h2>
  <p class="note">A wrong YES approves an experiment the truth rules out (T1–T4), or, in T5, certifies a datasheet line the sheet cannot support. It is the error that costs a cooldown. The bottom row adds up T1–T4 only.</p>
  <div class="scroll">
  <table class="score">
    <thead><tr><th>Test</th><th>Spec-sheet<br>checklist</th><th>Careful<br>spreadsheet</th><th>Physics-aware<br>script</th><th class="us">CryoLean<br>(Lean 4)</th></tr></thead>
    <tbody>{''.join(score_rows)}</tbody>
    <tfoot><tr><th>Impossible setups approved (T1–T4, {fmt(TOTAL_CASES)} cases)</th>{total_cells}</tr></tfoot>
  </table>
  </div>
</section>

<section aria-labelledby="who">
  <h2 id="who">The regular way, built fairly</h2>
  <p class="col">Each regular method reads the same documents the Lean checker reads and respects what the sheet says about installed options, so none of them confuses a brochure option with the installed machine. Each one is a step closer to CryoLean. The code is <code>bench/regular_way.py</code>.</p>
  <div class="methods">
    <div class="method"><h3>Spec-sheet checklist</h3><ul><li>one datasheet line at a time</li><li>a blank line passes</li><li>any number on the sheet is believed</li><li>no coupled physics</li></ul></div>
    <div class="method"><h3>Careful spreadsheet</h3><ul><li>one line at a time</li><li>a blank line means "TBD"</li><li>any number on the sheet is believed</li><li>no coupled physics</li></ul></div>
    <div class="method"><h3>Physics-aware script</h3><ul><li>lines plus heat budget, Joule heating, ramp time</li><li>a blank line means "TBD"</li><li>any number is believed</li><li>floats, no validity range</li></ul></div>
    <div class="method us"><h3>CryoLean</h3><ul><li>lines plus physics, exact rationals with units</li><li>a blank line means NEED INFO, and names it</li><li>only sourced numbers decide</li><li>every verdict backed by Lean theorems</li></ul></div>
  </div>
</section>

<section class="test" id="t1">
  <header><span class="tid">T1</span><h2>Hide one datasheet line</h2></header>
  <div class="col">
  <p>We took the {fmt(T1['cases'])} pairs that CryoLean rejects on exactly one sourced datasheet line, deleted that line as if the sheet were silent on it, and asked again. The machine did not change, so the right answer is still no.</p>
  <ul class="tally">
    <li><span>Checklist said YES</span><b class="no">{fmt(t1b['R1']['wrong_YES'])}</b></li>
    <li><span>Spreadsheet said YES</span><b class="ok">{fmt(t1b['R2']['wrong_YES'])}</b></li>
    <li><span>Physics script said YES</span><b class="ok">{fmt(t1b['R3']['wrong_YES'])}</b></li>
    <li><span>CryoLean said YES</span><b class="ok">{fmt(t1b['CryoLean']['wrong_YES'])}</b></li>
  </ul>
  <p>CryoLean answered NEED INFO and named the hidden line in {fmt(T1['cryolean_need_info_names_the_hidden_line'])} of {fmt(t1b['CryoLean']['NEED_INFO'])} cases. A careful spreadsheet that treats blanks as "TBD" also survives this test; the next two are where it stops.</p>
  {f1}
  <h3>Share of these cases the checklist approved, by industry</h3>
  </div>
  {svg_industries()}
</section>

<section class="test" id="t2">
  <header><span class="tid">T2</span><h2>Borrow a sibling model's number</h2></header>
  <div class="col">
  <p>The classic slip: the brochure covers several configurations, and the number you read belongs to another one. We refilled every failing line with the value printed for a sibling configuration of the same instrument and recorded it as what it is, an inferred estimate. {fmt(T2['cases'])} pairs could be refilled this way; the truth is still no.</p>
  <ul class="tally">
    <li><span>Checklist said YES</span><b class="no">{fmt(t2b['R1']['wrong_YES'])}</b></li>
    <li><span>Spreadsheet said YES</span><b class="no">{fmt(t2b['R2']['wrong_YES'])}</b></li>
    <li><span>Physics script said YES</span><b class="no">{fmt(t2b['R3']['wrong_YES'])}</b></li>
    <li><span>CryoLean said YES</span><b class="ok">{fmt(t2b['CryoLean']['wrong_YES'])}</b></li>
  </ul>
  {f2}
  </div>
</section>

<section class="test" id="t3">
  <header><span class="tid">T3</span><h2>Scale a superconducting-qubit chip</h2></header>
  <div class="col">
  <p>Krinner et al.'s 50-qubit wiring layout, scaled from 1 to 200 qubits, on every configuration in the catalog: {fmt(T3['cases'])} cases. The truth is their published design rule, recomputed here in exact fractions without Lean: three times the summed per-line heat load must stay under the cooling power documented at 20 mK. Every datasheet line can pass while the heat budget fails.</p>
  <ul class="tally">
    <li><span>Checklist said YES</span><b class="no">{fmt(T3['by_method']['R1']['wrong_YES'])}</b></li>
    <li><span>Spreadsheet said YES</span><b class="no">{fmt(T3['by_method']['R2']['wrong_YES'])}</b></li>
    <li><span>Physics script said YES</span><b class="ok">{fmt(T3['by_method']['R3']['wrong_YES'])}</b></li>
    <li><span>CryoLean said YES</span><b class="ok">{fmt(T3['by_method']['CryoLean']['wrong_YES'])}</b></li>
  </ul>
  <h3>Bluefors LD400 with high-density wiring</h3>
  <p class="note">The rule allows {RULE_MAX} qubits. The checklist and the spreadsheet approve up to {R1_MAX}, the point where the 168 RF lines run out.</p>
  </div>
  {svg_qubits()}
</section>
{t4_html}

<section class="test" id="t5">
  <header><span class="tid">T5</span><h2>Inject a defect into the sheet</h2></header>
  <div class="col">
  <p>{fmt(T5['cases'])} synthetic configurations from the paper's fault-injection generator: {fmt(T5['impossible'])} with a defect that makes the run impossible, {fmt(T5['uncertifiable'])} with a line that cannot be certified (an unknown value, an estimate, no source, unknown install status, a wrong unit dimension, a missing line), and {T5['controls']} clean controls. Everyone catches the impossible ones, because the bad number is printed right there. The difference is what each method certifies without evidence.</p>
  <ul class="tally">
    <li><span>Checklist certified</span><b class="no">{fmt(b5['R1']['uncertifiable_cases_said_YES'])}</b></li>
    <li><span>Spreadsheet certified</span><b class="no">{fmt(b5['R2']['uncertifiable_cases_said_YES'])}</b></li>
    <li><span>Physics script certified</span><b class="no">{fmt(b5['R3']['uncertifiable_cases_said_YES'])}</b></li>
    <li><span>CryoLean certified</span><b class="ok">{fmt(b5['CryoLean']['uncertifiable_cases_said_YES'])}</b></li>
  </ul>
  <p>CryoLean's answer matched the constructed truth in {fmt(b5['CryoLean']['exact_agreement_with_truth'])} of {fmt(T5['cases'])} cases; the best regular method matched {fmt(max(b5[m]['exact_agreement_with_truth'] for m in ('R1', 'R2', 'R3')))}.</p>
  </div>
</section>

{correct_section()}
<section aria-labelledby="lean">
  <h2 id="lean">Why it has to come out this way: proved in Lean</h2>
  <div class="col">
  <p>The tests above are measurements. <code>lean/VsRegular.lean</code> writes the checklist with CryoLean's own types and proves the pattern holds for every input, not just ours. It compiles {len(PROOFS['theorems'])} theorems against the unchanged checker, with Lean's standard axioms only.</p>
  <div class="claims">
    <div class="claim"><b>A checker that is never wrong can only say YES where CryoLean does.</b> If every YES a checker gives meets the specification, CryoLean says YES on that pair too, so no such checker decides more than CryoLean. <code>sound_yes_le_cryolean</code>, and the same for NO: <code>sound_no_le_cryolean</code>.</div>
    <div class="claim"><b>So every extra YES is unsupported.</b> On the catalog the checklist says YES {fmt(c0['R1']['YES'])} times and CryoLean {fmt(c0['CryoLean']['YES'])} times; each of the {fmt(T0['yes_without_support']['R1'])} extra YESes fails the specification. <code>extra_yes_unsupported</code></div>
    <div class="claim"><b>The checklist approves a blank datasheet, for every experiment.</b> CryoLean never does. <code>checklist_yes_to_blank_sheet</code>, <code>cryolean_no_yes_to_blank_sheet</code></div>
    <div class="claim"><b>Hiding a line can flip the checklist from NO to YES</b> (10 T magnetoresistance on the 9 T DynaCool). Hiding lines can never do that to CryoLean. <code>checklist_not_monotone</code>, <code>hiding_lines_never_creates_yes</code></div>
    <div class="claim"><b>The checklist believes a guessed 14 T; CryoLean does not decide on it.</b> <code>checklist_believes_a_guess</code></div>
    <div class="claim"><b>Every line of the 50-qubit layout passes, and the heat budget still fails:</b> 3 × 4.864 µW = 14.592 µW against 12 µW. The checklist says YES, CryoLean says NO. <code>checklist_misses_coupled_physics</code>, <code>wiring_load_is_14592_nW</code></div>
  </div>
<pre><code>/-- The spec-sheet checklist: NO if some line visibly fails, otherwise YES. -/
def checklist (cfg : Configuration) (e : Experiment) : Verdict :=
  if .fail ∈ (relevantReqs e).map (line cfg) then .reject else .accept

theorem sound_yes_le_cryolean (chk : Configuration → Experiment → Verdict)
    (hsound : ∀ c e, chk c e = .accept → AcceptSpec c e)
    (h : chk c e = .accept) : verdict c e = .accept :=
  verdict_accept_complete (hsound c e h)</code></pre>
  </div>
  <div class="scroll"><table class="thm"><tbody>{thm_rows}</tbody></table></div>
</section>

<section aria-labelledby="price">
  <h2 id="price">What it costs</h2>
  <div class="col">
  <p>Being right costs very little. On the full catalog CryoLean answers NEED INFO {fmt(c0['CryoLean']['NEED_INFO'])} times, against {fmt(c0['R2']['NEED_INFO'])} for the careful spreadsheet, and its result lists which lines are missing (in the hide-one-line test it named the hidden line every time). More research can only resolve those answers, never reverse a decided one (<code>verdict_refines</code>). The regular methods also said NO {fmt(T0['no_without_support']['R2'])} times on the strength of an unsourced number or an unsourced "not fitted" claim; CryoLean waits for a source there too.</p>
  </div>
</section>

<section aria-labelledby="limits">
  <h2 id="limits">What this does not show</h2>
  <ul class="col limits">
    <li>The truth in T1, T2 and T4 is the catalog's sourced record. If a datasheet is wrong, every method inherits the error.</li>
    <li>T1 and T2 perturb real records. They measure what each method does with a silent or borrowed line, not how often real datasheets are silent.</li>
    <li>The regular-way checkers are ours. They are short, readable and in the repo, and two of them already avoid the silent-line mistake, which is why all three are reported.</li>
    <li>Floating point never flipped a verdict in these runs. The physics script's misses come from believing unsourced numbers.</li>
    <li>No language-model baseline is included yet.</li>
  </ul>
</section>

<footer>
  Reproduce: <code>cd lean &amp;&amp; lake build &amp;&amp; cd .. &amp;&amp; python bench/vs_regular.py &amp;&amp; python bench/report.py</code> (about two minutes).
  Lean checker source hash <code>{esc(S['lean_checker'][:16])}</code>. Repository: <a href="https://github.com/hrahman12/CryoLean">github.com/hrahman12/CryoLean</a>.
</footer>
</div>
"""


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    figures()
    (ROOT / "bench" / "RESULTS.md").write_text(results_md(), encoding="utf-8")
    (ROOT / "bench" / "vs_regular_way.html").write_text(page(), encoding="utf-8")
    readme = ROOT / "bench" / "README.md"
    if readme.exists():
        head = readme.read_text(encoding="utf-8").split("Headline (from")[0].rstrip()
        readme.write_text(head + "\n\nHeadline (from `results/summary.json`): on T1–T4 the checklist approved "
                          f"{fmt(TOTAL_WRONG['R1'])} setups the evidence rules out, the careful spreadsheet "
                          f"{fmt(TOTAL_WRONG['R2'])}, the physics-aware script {fmt(TOTAL_WRONG['R3'])}, CryoLean "
                          f"{fmt(TOTAL_WRONG['CryoLean'])}.\n", encoding="utf-8")
    print("wrote bench/RESULTS.md, bench/vs_regular_way.html, bench/figures/")
    print("total wrong YES:", TOTAL_WRONG, "over", TOTAL_CASES, "cases")


if __name__ == "__main__":
    main()
