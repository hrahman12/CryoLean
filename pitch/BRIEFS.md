# CryoLean pitch decks: five briefs

All five use the LeanKeel format (`pitch/shared/FORMAT.md`). Every slide has an eyebrow, a headline that states a claim,
one main visual, and a grey footer naming its sources. Every number below comes from the latest GitHub `main` (b2b80ff)
and is listed in `pitch/facts/FACTS_quick.md`.

**Title slide, same in every deck.** Eyebrow `VIBECHECK · THE USABLE FORMAL METHODS / HACKATHON · SAN FRANCISCO · NOV 2026`.
Author line: Hanah Rahman · Nicholas Brandenburg. Links: hrahman12.github.io/CryoLean · github.com/hrahman12/CryoLean.
Illustration: a generic cryostat drawn in code.

**Colours.** teal = Requirements met · amber = Need more information · pink = Does not meet requirements · purple = Lean.

| | Version | Slides | Audience | Story in one line |
|---|---|---|---|---|
| v1 | Classic | 4 | general judges, 2 min | Cryostat time is costly and specs are scattered; CryoLean answers with a reason; here is the evidence. |
| v2 | Demo-first | 3 | right before a live demo | One question, three honest answers, now you try it. |
| v3 | Formal methods | 4 | formal-methods judges | Every verdict is a theorem; we audited our own verifier and fixed a real bug; AI can only propose. |
| v4 | Physics | 4 | cryogenics and quantum-lab experts | The costly failures are coupled; CryoLean catches them before cooldown, schedules cold time, and never guesses. |
| v5 | Vision and ask | 3 | sponsors, partners, cryostat makers | Every lab asks the same question; one proof covers 20 industries; help us fill the gaps. |

---

## v1 · Classic (4 slides)

**1 · Title.** Subtitle: "Can this cryostat do my experiment?" Pills: `Claude · Lanyon · suggest` (amber) ·
`Lean 4 · decides` (purple) · `Z3 · explains` (teal).

**2 · The problem.** Eyebrow `/ THE PROBLEM · WHY CRYOSTATS`.
- Headline: **A cryostat's limits are fixed. Every experiment asks for something different.**
- Visual: all 220 catalogued configurations plotted as coldest temperature (log K) against strongest magnetic field (T),
  coloured by machine type. Computed from `data/cryostats/`.
- Cards:
  - **24 h**: time for a Bluefors LD to reach base temperature. A mismatch found there costs that day again.
  - **23.5 %**: share of capability entries with no confirmed value (665 of 2,832).
  - **220**: machine configurations in the catalog.
  - **204**: experiment profiles taken from published procedures.
- Line: "Today the match is read off brochures by hand. A datasheet-style checker says yes to **149** of 286 pairs that
  Lean won't sign off on."
- Footer: `data/evidence/bluefors.json`, `data/coverage`, `paper/data/fig_baseline_comparison.json` (paper evaluation).
  Of the 149, 148 have no trusted evidence and 1 genuinely overheats.

**3 · What it does.** Eyebrow `/ WHAT IT DOES`.
- Headline: **Ask if an experiment fits a machine. Get the answer and the reason.**
- Visual: LeanKeel's ask → answer layout.
  - **The ask**: "Can a Bluefors LD400 run our 50-qubit wiring?" Underneath: 10 mK ≤ 20 mK ✓ · 168 ≥ 124 lines ✓.
  - **Lean's answer**: **DOES NOT MEET** (pink). "Each spec passes, but together the lines put 14.592 µW into a
    mixing chamber that removes 12 µW."
  - Second, smaller teal answer: "Z3 suggests 39 flux lines. Lean re-checks: 11.985 µW ≤ 12 µW, Requirements met."
- Timing label: median 138 ms per check, including process start.
- Footer: `docs/examples/demo_b_coupled.json`, `paper/data/e5_heat.json`, `e2_latency.json`; wiring from Krinner et al.,
  *EPJ Quantum Technology* 2019.

**4 · Proof it works.** Eyebrow `/ PROOF IT WORKS`.
- Headline: **Every verdict comes from a theorem.**
- Visual: code panel showing `theorem verdict_accept_iff … : verdict cfg e = .accept ↔ AcceptSpec cfg e`, with the line
  "In words: Lean says *requirements met* exactly when a separately written specification holds."
- Numbers:
  - **128** theorems, 0 `sorry`.
  - **48** axiom-audited theorems, standard axioms only.
  - **2,750** fault-injected configurations, 0 defective ones accepted.
  - **15,795 / 15,795** heat-budget designs on which Z3 and Lean agree.
- Footer: `lean/CryoLean/Soundness.lean:861`, `lean/audit-axioms.json`, `paper/data/e4_faults.json`,
  `fig_z3_lean_agreement.json`. Proofs cover the modelled requirements and sourced facts, not the physical machine.

---

## v2 · Demo-first (3 slides)

**1 · Title.** Subtitle: "One experiment. One machine. One honest answer." Pills: `Requirements met` (teal) ·
`Need more information` (amber) · `Does not meet` (pink).

**2 · Three answers.** Eyebrow `/ WHAT IT DOES · THREE REAL CHECKS`.
- Headline: **Three experiments. Three honest answers.**
- Visual: three tall verdict cards.

| | Experiment | Machine | Verdict | Why |
|---|---|---|---|---|
| AEROSPACE | Mars-rover temperature sensors: −135 to +70 °C cycles plus a +125 °C bake | Tinius Olsen environmental chamber, documented −150 to +600 °C | **Requirements met** | every need sits inside the documented range |
| QUANTUM | whole 300 mm silicon wafers at ≤ 1.6 K | Bluefors XLDHe (`bluefors_xldhehp_3section`) | **Need more information** | 1 of 3 needs (wafer size) is unconfirmed; Lean won't answer until it is |
| BIOLOGY | protein crystal flash-cooled in liquid nitrogen | Lake Shore CCS-800 | **Does not meet** | the machine documents no cryogen; switch to the Thermo Scientific CryoMed TSCM48XV and it turns green |

- Footer: `site/data.json` verdicts, `data/experiments/v4_aero_mars_prt_thermal_cycling.json`. Values are the ones the
  website uses.

**3 · Live demo.** Teal eyebrow `● LIVE · REAL LEAN VERDICTS`.
- Headline: **Live: you pick the experiment.**
- Visual: five numbered steps (LeanKeel slide 14) beside a framed screenshot of the Demos tab.
  1. Choose an industry: 20 industries, 3 experiments each.
  2. Choose a cryostat: 220 configurations.
  3. Check the setup: Lean answers and shows the first stage where the run fails (load → pump → cool down → magnet →
     measure → hold).
  4. Ask Lanyon AI for a fix: Lean re-checks every idea, so you only see proven ones.
  5. Break it: untick a need and watch the answer become *need more information*.
- Footer: hrahman12.github.io/CryoLean. Every answer on the page is one of 138,564 precomputed Lean outcomes
  (13,200 featured pairs).

---

## v3 · Formal methods (4 slides)

**1 · Title.** Subtitle: "A cryostat checker where every verdict is a theorem." Pills: `Lean 4 · decides` (purple) ·
`Z3 · Claude · Lanyon · propose` (amber) · `Forall · audits` (teal).

**2 · The theorems.** Purple eyebrow `/ THE THEOREMS · LEAN 4`.
- Headline: **If Lean says met, every requirement holds. Provably.**
- Visual: code panel with verbatim signature lines, each followed by its meaning in words.

| Theorem | In words |
|---|---|
| `verdict_accept_iff` | *met* exactly when the specification holds |
| `verdict_reject_sound` | every *does not meet* rests on a documented violation |
| `fail_needs_trusted` | every failure rests on trusted evidence |
| `verdict_refines` (Monotone.lean) | new data can only resolve *need more information*, never flip a decided verdict |

- Numbers:
  - **128** theorems; 0 `sorry` / `admit` / `native_decide`.
  - **48** axiom-audited theorems, standard axioms only.
  - **0** dependencies and no floating point: exact rationals with 7 SI dimensions.
- Footer: `lean/CryoLean/Soundness.lean`, `Monotone.lean`, `lean/audit-axioms.json`, Lean 4.35.0.

**3 · The self-audit.** Eyebrow `/ FORENSICS · AUDITING THE CHECKER`.
- Headline: **We audited our own verifier. It found a real bug.**
- Visual: before and after of the one changed line in `checkCapability`:
  - before: `if k = .flagIs false then (if trustedB c.evidence then .pass else .unknown) else .fail`
  - after: `if trustedB c.evidence then (if k = .flagIs false then .pass else .fail) else .unknown`
  - "The build was green, because the spec had the same hole."
  - New theorems: `fail_needs_trusted`, `untrusted_never_passes`, `untrusted_never_fails`. They are now cited on every
    *does not meet* verdict card.
- Numbers:
  - **839** declarations scanned; 0 non-standard axioms, 0 statement smells, 0 unsafe flags.
  - **7** judges raised **27** flags, each re-checked by the Lean kernel.
  - **1** real soundness gap, fixed.
- Footer: `docs/forensics/README.md`, `Checker.lean:65-73`. The scan predates `Monotone.lean`.

**4 · One judge.** Eyebrow `/ UNTRUSTED HELPERS, ONE JUDGE`.
- Headline: **AI proposes. Lean decides.**
- Visual: diagram. Claude, Lanyon AI and Z3 (amber, untrusted) feed the Lean 4 checker (purple), which produces the
  verdict card (verdict · reason · theorem names · axioms · source hash).
- Facts:
  - `candidates_verdicts_are_lean`: Z3 and AI candidates get Lean's own verdict.
  - The Gatekeeper admitted 2 of 7 proofs. It rejected a `sorry`, a `native_decide`, a custom axiom, a false statement,
    and an AI proof with 54 compile errors.
  - Z3 and Lean agree on 15,795 / 15,795 designs.
- Footer: `Soundness.lean:1056`, `cryolean/gatekeeper.py`, `paper/data/e9_gatekeeper.json`, plus the scope line.

---

## v4 · Physics (4 slides)

**1 · Title.** Subtitle: "Find the failure before the cooldown, not at 10 mK." Pills: `heat budgets` (teal) ·
`cooldown schedules` (amber) · `Lean 4 proofs` (purple). The illustration's ring is stopped in red at the mixing chamber.

**2 · Coupled heat (Demo B).** Teal eyebrow `/ COUPLED PHYSICS · 50-QUBIT WIRING`.
- Headline: **Each check passes. Together they fail.**
- Visual: stacked bar of the mixing-chamber heat load against a 12 µW limit line.
  - Current wiring: 3 × (58·13 nW + 50·(29 + 50) nW + 8·20 nW) = 14.592 µW.
  - Second bar, Z3's 39 flux lines: 11.985 µW, leaving 15 nW of slack.
- Cards: 10 mK ≤ 20 mK ✓ · 168 ≥ 124 lines ✓ · 14.592 > 12 µW ✗.
- Footer: `docs/examples/demo_b_coupled.json`, `e5_heat.json`, Krinner et al. 2019. Honest note: with ±20 % per-line
  uncertainty, the 39-line design passes about 51 % of the time, and 95 % needs at most 33 lines
  (`paper/data/fig_uncertainty.json`).

**3 · One cooldown (Demo D).** Teal eyebrow `/ SCHEDULING · ONE COLD RUN`.
- Headline: **One cooldown, three experiments, a proved schedule.**
- Visual: Gantt chart for the Lake Shore CRX-VF over a 48 h run.
  - 5 h cooldown, then three Lean-accepted experiments ending at 23 h.
  - The 10 T magnetoresistance run is rejected and never scheduled.
  - Inset: with a 20 h run, 18 h of work can't fit in the 15 h left (Z3 unsat core).
- Numbers: **23 h** makespan. On **400 / 400** tampered schedules, Lean agrees with an independent checker.
- Footer: `docs/examples/demo_d_campaign_schedule.json`, `paper/data/e6_schedule.json`. Lean proves the schedule valid,
  not minimal.

**4 · Missing data.** Eyebrow `/ WHAT WE DON'T KNOW`.
- Headline: **Missing data never becomes a pass.**
- Visual: as 0–100 % of each machine's documented specs are deleted, verdicts only move toward *need more information*.
  188,760 Lean checks; 0 became *met*.
- Numbers:
  - **665** of 2,832 capability entries are stored as UNKNOWN, not guessed.
  - `verdict_refines`: new data only resolves *need more information*.
- Footer: `paper/data/fig_incomplete_info.json`, `lean/CryoLean/Monotone.lean`.

---

## v5 · Vision and ask (3 slides)

**1 · Title.** Subtitle: "Cryo, made simple." Pills: `20 industries` (amber) · `220 machine setups` (teal) ·
`1 Lean checker` (purple).

**2 · Scale.** Eyebrow `/ SCALE · ONE CHECKER, EVERY LAB`.
- Headline: **Twenty industries. One unchanged proof.**
- Visual: the 180 featured pairings redrawn in the dark style: 20 industries × 9 squares. 134 met · 26 need info ·
  20 do not meet (`site/matrix_data.json`).
- Numbers:
  - **44,880** experiment-machine pairs decided (204 × 220).
  - **3,335** sourced evidence records, each with a URL, a location and a date.
  - A new industry is just new data: the Lean core hash was unchanged (Demo C), and `verdict_industry_irrelevant`
    proves the label can't change a verdict.
- Footer: `site/matrix_data.json`, `site/data.json`, `docs/examples/demo_c_new_industry_check.json`, `Soundness.lean:1024`.

**3 · Ask / next / try.** Eyebrow `/ WHAT WE ASK`.
- Headline: **Help us turn unknowns into answers.**
- Visual: framed screenshot of the live checker (LeanKeel slide 13 layout) with three cards:
  - **We ask.** Cryostat makers: machine-readable, sourced specs (665 of 2,832 capability entries are still UNKNOWN).
    Labs: their real experiment needs.
  - **Next we prove.** The 5 coupled physics models still reported UNSUPPORTED (13 defined, 8 validated today).
  - **Try it now.** hrahman12.github.io/CryoLean · github.com/hrahman12/CryoLean · `python -m cryolean demo`
- Footer: the scope line. Lean checks plans against sourced specs; it does not certify machines.

---

## Open points

- **Credits**: "Hanah Rahman · Nicholas Brandenburg" is from git history. Add affiliations if you want them.
- **Live site**: hrahman12.github.io/CryoLean is published from `gh-pages`, which is behind `main`. Its Demos tab label differs slightly.
- **Demo B line count**: the profile quotes "124 lines needed" but the heat formula counts 116. The slides show 124 (as
  printed) and do not mention 116.
- **Still running**: the full fact re-check (2 areas plus their verifiers). Any correction it finds will be applied
  before the build.
