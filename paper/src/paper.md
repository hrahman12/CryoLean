---
title: CryoLean: Formally Verified Multiphysics Compatibility Analysis for Cryogenic Scientific Experiments
author: Hanah Rahman
affiliation: University of California, Berkeley
date: November 2026 · Built for the VibeCheck FM + AI Hackathon · Code: https://github.com/hrahman12/CryoLean
keywords: formal verification, Lean 4, SMT, Z3, cryogenics, dilution refrigerators, scientific instruments, proof-carrying results
abstract: |
  Before an experiment is scheduled on a cryostat, someone must decide whether that exact machine can physically perform it: whether it reaches the temperature, the field and the sample size, and whether the experiment's own heat load fits the refrigerator's cooling power at the operating temperature. Today this decision is made by reading datasheets. We present CryoLean, a system in which every such decision is computed by a decision procedure written in Lean 4 and proved sound and complete against an independently written specification. Numbers are exact rationals carrying SI dimension vectors, so no comparison can mix units or round. The checker returns one of three verdicts, and missing or untrusted evidence can only ever produce NEED_MORE_INFORMATION, never acceptance or rejection. An SMT solver (Z3) and large language models are confined to proposing: unsat cores explain failures, alternative cryostats and parameter repairs are suggested, and several experiments are packed into one cooldown, but each proposal is re-decided by Lean. The data layer holds 667 sourced evidence records for 26 configurations of nine instrument families and 11 experiment profiles from published procedures, with 13 coupled multiphysics models such as the mixing-chamber heat budget of superconducting-qubit wiring. Across the full 11 × 26 grid, Lean decides each pair in 0.14 s (median, including process start). In 2,750 fault-injection cases no defective configuration was ever accepted. On the qubit-wiring example, every individual specification passes while the coupled heat budget fails by 2.6 µW, a failure that an independent-property checker cannot detect. The proofs cover our model of the instruments and the sourced data, not a physical certification.
---

# Introduction {#sec:intro}

Cryogenic experiments are expensive to set up and slow to repeat. A dilution refrigerator takes about a day to cool down, and a mistake discovered at base temperature costs that day again. Yet the question that precedes every run is usually answered informally: *can this machine, in this configuration, physically perform this experiment?* The answer depends on many specifications at once (base temperature, temperature range, magnetic field, sample space, electrical lines, optical access) and on physics that couples them. The most important coupling is the heat budget: the power the experiment dissipates at the cold stage must stay below the refrigerator's cooling power *at the operating temperature*, and that cooling power falls steeply as the temperature drops [@krinner2019].

Checking one specification at a time is easy and is what a datasheet comparison does. It is also wrong in a systematic way. A 50-qubit wiring layout can satisfy every individual requirement of a Bluefors LD400 (it reaches 10 mK, below the 20 mK target, and offers 168 lines where 124 are needed) and still fail, because three times the summed per-line heat loads, 14.592 µW, exceeds the 12 µW the refrigerator documents at 20 mK (@sec:results). Conversely, a datasheet that is silent about a quantity is often read as permission. Neither error is acceptable when the decision schedules a week of instrument time.

This paper describes CryoLean, a compatibility checker whose verdicts are machine-checked. Our contributions are:

1. **A verified decision procedure** (@sec:lean). One universal checker, written in Lean 4 [@demoura2021] over exact rationals with seven-component SI dimension vectors, decides REQUIREMENTS_MET, DOES_NOT_MEET_REQUIREMENTS or NEED_MORE_INFORMATION. It is proved sound and complete against an independently written specification. Rejections are proved to rest only on trusted evidence. Dimensions are proved to match in every passing comparison. 44 key theorems use only Lean's standard axioms.
2. **Untrusted search with trusted checking** (@sec:z3). Z3 [@demoura2008] supplies unsat-core explanations, ranked alternative configurations, minimal parameter repairs and minimum-makespan campaign schedules. Lean re-decides every proposal, including a proved schedule validator. This follows the proof-carrying and certifying-algorithm tradition [@necula1997; @mcconnell2011].
3. **Coupled multiphysics as checked relations** (@sec:physics). Thirteen physical relations are expressed as dimensioned inequalities with validity regions, so that the checker evaluates them exactly and refuses to extrapolate.
4. **A sourced, auditable data layer** (@sec:data) of 667 evidence records, in which every value carries its provenance class and only trusted classes can decide a verdict.
5. **An evaluation** (@sec:method, @sec:results) on the full experiment × configuration grid: verdict structure, fault injection, coupled-physics boundaries, robustness to missing data, a baseline comparison and runtime scaling. Every figure is generated by a script from these runs.

We are careful about what is and is not claimed. The Lean theorems are about the decision procedure and the specification. They do not certify that a datasheet is correct, that a physical model is complete, or that a machine will behave as documented. @sec:limits separates these layers, and `paper/CLAIM_AUDIT.md` maps every claim to its evidence.

# Related work {#sec:related}

**Certified results from untrusted search.** Proof-carrying code [@necula1997] ships an untrusted artefact with a proof that a small trusted checker validates. Certifying algorithms [@mcconnell2011] return an easily checkable witness with each output. CryoLean applies this division of labour to engineering feasibility: Z3 and LLMs produce candidates, and a Lean function with machine-checked soundness and completeness theorems decides.

**SMT solvers and proof assistants.** Several systems connect SMT solvers to proof assistants by replaying solver proofs in a trusted kernel: LCF-style reconstruction for Z3 in Isabelle/HOL and HOL4 [@bohme2010], SMTCoq [@ekici2017], hammers [@blanchette2016], and in Lean 4, lean-smt [@mohamed2025] and Lean-auto [@qian2025]. These tools discharge proof goals. CryoLean instead keeps the solver entirely outside Lean, as an optimiser and explainer, and re-decides the concrete artefact it returns. No solver proof is reconstructed, because the verdict is recomputed by a verified procedure.

**Language models with formal checkers.** Autoformalization [@wu2022] and verifier-grounded reasoning [@zhou2024] use proof assistants to check what a model proposes, and recent work documents how formal statements can be vacuous or wrong [@ammanamanchi2026; @kupferman2003]. CryoLean's Gatekeeper admits LLM- or simulation-proposed Lean code only if it compiles and its axioms are standard. We also audited our own statements with an external forensics tool, which found a real specification gap (@sec:lean).

**Units of measure.** Units have been encoded in type systems since Kennedy's work [@kennedy1997], and dimensional analysis has been formalized in Lean [@bobbin2025]. Physics libraries in Lean exist for high-energy physics [@toobysmith2025]. CryoLean uses a minimal dimension-vector representation, but within an application-level decision procedure whose correctness is proved.

**Configuration and diagnosis.** Knowledge-based product configuration [@felfernig2004] and preferred explanations of over-constrained problems such as QuickXplain [@junker2004] are close in spirit to our unsat-core explanations. They treat the solver and its explanation as authoritative. In CryoLean the explanation is advisory and the verdict is re-decided.

**Laboratory planning.** Self-driving laboratories [@abolhasani2023] and laboratory orchestrators [@mcdannald2026] schedule instruments with constraint solvers. Recent work represents laboratories computably in order to check workflows before execution [@li2026]. At a neutron facility, EXEQ checks whether planned experiments fit an instrument's envelope [@bartkowiak2020]. None of the systems we found validates its decisions in a proof assistant.

**Novelty claim.** To our knowledge, CryoLean is the first system that decides whether a specific cryogenic configuration can perform a specified experiment using only verdicts from a decision procedure checked in a proof assistant, with solvers and language models confined to proposing. Our search covered Lune, alphaXiv and web search, and was limited: one database was unavailable and another rate-limited. We found no peer-reviewed tool for matching cryostats to experiments at all, only vendor buying guides.

# Problem formulation {#sec:formulation}

**Quantities.** Let $\mathbb{D} = \mathbb{Z}^7$ be the group of dimension vectors over (K, m, kg, s, A, mol, cd). A quantity is a pair $q = (v, d) \in \mathbb{Q} \times \mathbb{D}$. Rationals are stored as $v = n/m$ with $n \in \mathbb{Z}$, $m \in \mathbb{N}$, $m > 0$, and compared exactly by cross-multiplication:

$$ \frac{n_1}{m_1} \le_{\mathbb{Q}} \frac{n_2}{m_2} \iff n_1 m_2 \le n_2 m_1 . $$
{#eq:qle}

A comparison of two quantities is defined only when their dimensions are equal. Otherwise it is *unsupported*.

**Configurations.** A configuration $c$ is a finite map from capability keys $\kappa$ to records $x = (\mathrm{val}(x), \mathrm{inst}(x), \mathrm{ev}(x))$: a value (a range $[\ell, h]$, a maximum, a minimum, a flag, a count, an enumeration or a set, or *unknown*), an install status in $\{\text{installed}, \text{not fitted}, \text{unknown}\}$, and an evidence class. Five classes are trusted, written $T(x)$: manufacturer specification, experimental observation, reference data, certified simulation and user-entered. *Inferred estimate* and *unknown* are not.

**Experiments.** An experiment $e$ has parameters with values and evidence classes, a set of requirements and a set of coupled constraints, each mandatory or optional and each guarded by conditions. A requirement $r$ lists alternative keys $K(r)$ and a constraint $k$ (for example $\text{atLeast}(9\,\mathrm{T})$). A coupled constraint $g$ relates expressions over capabilities and parameters,

$$ g:\quad \mathrm{lhs}(g) \le \mathrm{rhs}(g) \quad \text{subject to} \quad a_i \le b_i \;\; (i = 1..n), $$
{#eq:coupled}

where the $a_i \le b_i$ describe the region in which the physical model is valid.

**The decision problem.** Given $(c, e)$, return

$$ V(c, e) \in \{\mathrm{MET}, \mathrm{NOT\ MET}, \mathrm{NEED\ INFO}\} $$
{#eq:verdict}

such that MET holds exactly when every applicable mandatory item is established from trusted evidence and at least one item positively passes, and NOT MET holds exactly when some applicable mandatory item is *violated by trusted evidence*. Everything else, including missing keys, untrusted values, dimension mismatches and invalid model regions, is NEED INFO. The asymmetry is deliberate: absence of information must never look like either permission or prohibition.

**Proposal problems.** Three optimisation problems sit beside the decision problem, and their answers are always re-decided by $V$:
(i) *explain*: find a minimal set of trusted facts and requirements that is jointly unsatisfiable;
(ii) *repair*: find the smallest change of one adjustable parameter $p$ that makes every coupled constraint hold;
(iii) *schedule*: given accepted experiments with durations $d_i$, cooldown $t_c$ and run length $L$, find starts $s_i$ with

$$ t_c \le s_i,\quad s_i + d_i \le L,\quad [s_i, s_i + d_i) \cap [s_j, s_j + d_j) = \emptyset \;(i \ne j), \quad \min \max_i (s_i + d_i). $$
{#eq:schedule}

# Lean 4 formal verification {#sec:lean}

The trusted core is a Lean 4 (v4.35.0) project of 2,578 lines in nine files: `Model` (types), `Num` (exact arithmetic), `Checker` (the executable procedure), `Spec` (the specification), `Soundness` (proofs), `Schedule` (campaign schedules), and `Json`, `Explain` and `Report` (input and output). The compiled binary *is* these definitions: Python serialises the inputs, runs the binary, and never computes a verdict itself.

## The checker

`checkValue` compares a constraint with a documented value, returning *unsupported* whenever dimensions differ. `checkCapability` adds install status and provenance: an installed, trusted capability is compared; a trusted "not fitted" record passes only a requirement that the item be absent and fails any other; everything untrusted is *unknown*. Alternative keys combine disjunctively, and conditions are three-valued. Coupled constraints are evaluated by `evalExpr`, which uses only installed, trusted capabilities and trusted parameters and refuses to add quantities of different dimensions. A violated validity bound yields *unsupported*, never *fail*: CryoLean does not reject on the strength of a model used outside its range. The verdict is:

```lean
def verdict (cfg : Configuration) (e : Experiment) : Verdict :=
  if e.confirmed = false then .needMoreInfo
  else if .fail ∈ outcomes cfg e then .reject
  else if (∀ o ∈ outcomes cfg e, o = .pass ∨ o = .notApplicable)
          ∧ .pass ∈ outcomes cfg e then .accept
  else .needMoreInfo
```

where `outcomes` collects the outcomes of the mandatory, applicable requirements and coupled constraints.

## The specification

`Spec.lean` states what the verdicts should mean using inductive relations, not the checker's functions. For a key $\kappa$ with record $x$,

$$ \mathrm{Sat}(c,k,\kappa) \iff \mathrm{inst}(x)=\text{installed} \wedge T(x) \wedge \mathrm{Meets}(k,\mathrm{val}(x)) \;\vee\; \mathrm{inst}(x)=\text{not fitted} \wedge T(x) \wedge k = \text{absent}, $$
{#eq:sat}

$$ \mathrm{Viol}(c,k,\kappa) \iff \mathrm{inst}(x)=\text{not fitted} \wedge T(x) \wedge k \ne \text{absent} \;\vee\; \mathrm{inst}(x)=\text{installed} \wedge T(x) \wedge \mathrm{Fails}(k,\mathrm{val}(x)), $$
{#eq:viol}

where `ValueMeets` and `ValueFails` carry their dimension equalities as premises. Coupled constraints get a big-step semantics `Denotes` for expressions. `AcceptSpec` requires a confirmed profile, every mandatory applicable item satisfied (or excluded by a definitely false condition), and at least one positive pass. `RejectSpec` requires a confirmed profile and one item violated on every alternative key. The two share only `lookup`, the rational order and quantity arithmetic with the checker.

## Main theorems

::: theorem verdict_accept_iff (Soundness.lean)
For every configuration and experiment, `verdict cfg e = .accept ↔ AcceptSpec cfg e`. {PROVEN}
:::

::: theorem verdict_reject_sound, verdict_reject_complete
`verdict cfg e = .reject → RejectSpec cfg e`, and conversely. Hence NEED_MORE_INFORMATION holds exactly when neither specification does. {PROVEN}
:::

::: theorem fail_needs_trusted, untrusted_never_passes, untrusted_never_fails
A capability check returns *fail* only on trusted evidence. An untrusted record never passes and never fails, whatever its install status. {PROVEN}
:::

::: theorem accept_no_unknown, pass_dims_all_match
An accepted pair has no *unknown* or *unsupported* outcome. Every passing comparison of every numeric constraint shape compares quantities of a single dimension. {PROVEN}
:::

::: theorem candidates_accept_sound, validSchedule_only_accepted
Any Z3 candidate the checker accepts satisfies `AcceptSpec` for its own configuration. A schedule accepted by `validSchedule` contains only experiments satisfying `AcceptSpec`, with every slot after cooldown, before the end of the run and pairwise disjoint. {PROVEN}
:::

**Information monotonicity.** A record is *informative* if it is trusted and either documents the item as absent or documents an installed value. Write $c \sqsubseteq c'$ (`Refines c c'`) if every informative record of $c$ is found unchanged in $c'$. Records that cannot decide anything (missing keys, untrusted evidence, unknown install status, unknown values) may be replaced or added.

$$ c \sqsubseteq c' \;\wedge\; V(c,e) \neq \mathrm{NEED\ INFO} \;\Longrightarrow\; V(c',e) = V(c,e). $$
{#eq:monotone}

::: theorem verdict_refines, needMoreInfo_of_refined (Monotone.lean)
Refining a configuration never changes a decided verdict: MET stays MET and NOT MET stays NOT MET. Conversely, if the better-documented configuration still needs information, so did the less documented one. Removing information can never create a decision. {PROVEN}
:::

This property justifies treating NEED INFO as the safe default. It also means that the data research of @sec:data can only *resolve* undecided pairs, never overturn a decided one. The proof is a layer-by-layer argument: a decided capability check rests on an informative record, a decided disjunction rests on decided alternatives, a decided condition rests on informative flags, and an evaluated expression rests on usable capabilities.

Further theorems show that optional and non-applicable requirements never change a verdict (`verdict_ignores_optional`, `verdict_ignores_nonapplicable`), that the industry label is irrelevant (`verdict_industry_irrelevant`), and that every result names exactly the inputs it was computed from (`run_binds_inputs`). Some names promise more than the theorems prove. `verdict_deterministic` is congruence of a pure function, and `validSchedule_sound`/`_complete` mostly restate the Boolean conjunction. We report them as such.

## Axiom audit and specification forensics

`lean/Audit.lean` prints the axioms of 44 theorems. All depend only on `propext`, `Classical.choice` and `Quot.sound`, none on `sorryAx`, and no `native_decide` is used. We then audited the *statements* with the for-all-dev forensics tool, which extracts all 839 declarations with their transitive axioms, flags and statement smells (0 non-standard axioms, 0 smells, 0 unsafe flags after one fix). We also applied its seven LLM-judge protocols. The vacuity judge found a genuine gap: in an earlier version, a "not fitted" record with *no provenance* could cause a rejection. The judge confirmed it in Lean (`verdict` returned reject on a configuration whose only evidence was *unknown*). The checker and `ViolatesKey` were corrected, and `fail_needs_trusted` now rules the case out. A green build does not imply a correct specification, and specification auditing should be part of the workflow.

# Z3 constraint solving {#sec:z3}

Z3 is used through its Python API with exact rationals (`z3.Q`) and never decides a verdict.

**Explanations.** For a rejected pair, each requirement and each trusted documented fact is asserted with `assert_and_track` under a unique label. The unsat core names the conflicting facts together with their evidence ids, and is reported as the human-readable reason. Because the core is computed from the same documents Lean reads, it can be checked against the Lean result, but it is not itself evidence.

**Alternatives and repairs.** For each catalog configuration, Z3 classifies the requirement set as *satisfiable*, *needs options* (satisfiable only with a documented but uninstalled accessory) or *pending information*. Candidates are ranked by documented criteria, and every candidate is passed to the proved `check-candidates` entry point. For a failing coupled constraint, `Optimize` finds the boundary value of each adjustable parameter (nonlinear relations use Z3's nlsat). The suggested value is substituted and re-checked by Lean. Only a Lean REQUIREMENTS_MET is shown as *verified*.

**Campaign packing.** The schedule problem (@eq:schedule) is encoded with one real start variable per experiment, disjunctive non-overlap constraints and `minimize(makespan)`. Infeasibility is first diagnosed with a tracked solver, whose unsat core names the experiments that cannot fit together. Only experiments Lean has accepted enter the problem. The returned slot list is checked by the Lean function `validSchedule`, whose soundness and completeness against `ScheduleOK` are proved. Lean does not prove that the makespan is minimal, only that the schedule is valid.

# Cryogenic multiphysics models {#sec:physics}

Each model is a template in `data/physics/coupled_models.json` that the serialiser instantiates with sourced capabilities and experiment parameters. It has an equation, a validity region and its assumptions. Nine are executable in Lean, three are representable but lack data, and one is unsupported.

**Joule heating against cooling power.** For a transport measurement with current $I$ through resistance $R$,

$$ I^2 R \le P_{\mathrm{cool}}(T_{\mathrm{doc}}), \qquad T_{\mathrm{doc}} = \max\{T \in \mathcal{T}_c : T \le T_{\mathrm{op}}\}, $$
{#eq:joule}

where $\mathcal{T}_c$ is the set of temperatures at which configuration $c$ documents its cooling power. Using the highest documented temperature *not above* the operating temperature is conservative, because cooling power increases with temperature. The validity condition $T_{\mathrm{doc}} \le T_{\mathrm{op}}$ makes the checker answer NEED INFO, rather than extrapolate, below the lowest documented point.

**Mixing-chamber wiring heat budget.** Following Krinner et al. [@krinner2019], the heat arriving at the mixing chamber of a dilution refrigerator from $n_d$ drive lines, $n_f$ flux lines and $n_o$ output lines, with design margin $\mu$, must satisfy

$$ \mu \left( n_d\, q_d + n_f\,(q_f + p_{\mathrm{dc}}) + n_o\, q_o \right) \le P_{\mathrm{cool}}(T_{\mathrm{doc}}), $$
{#eq:mxc}

with per-line loads $q_d = 13$ nW, $q_f = 29$ nW, $p_{\mathrm{dc}} = 50$ nW and $q_o = 20$ nW from that paper, and $\mu = 3$. Every term is an exact rational with dimension W.

**Other relations.** Magnet ramp time ($B \le \dot B_{\max}\, t$), cooldown plus run time within the available time, differential thermal contraction between sample and holder ($|L(\varepsilon_s - \varepsilon_h)| \le \delta$, at the tabulated 4 K or 80 K), objective working distance, numerical aperture against an optical port's f-number ($\mathrm{NA}^2 (4N^2 + 1) \le 1$, the division-free form of $\mathrm{NA} \le \sin\arctan(1/2N)$), and frost prevention below 273.15 K. Because `Expr` has no division, every relation is written multiplied out, which keeps evaluation exact.

# Scientific data and evidence {#sec:data}

The catalog is built from version-controlled JSON seeds into SQLite. It contains nine instrument families (Leica CM1950 cryostat microtomes; Linkam THMS600 stages; Quantum Design PPMS and DynaCool; Bluefors LD dilution refrigerators; Oxford Instruments TeslatronPT and OptistatDry; Lake Shore CRX probe stations and Janis CCS cryocoolers) in 26 configurations, and 11 experiment profiles taken from published procedures, spanning biology, chemistry, materials science and quantum technology. 20 industries are registered. Industries are labels with no special logic: `verdict_industry_irrelevant` proves that the label cannot change a verdict.

The 667 evidence records carry a source, a quotation or table location, and one of six classes. A capability's evidence class is what the checker's `TrustedEvidence` predicate reads. 121 capability entries are explicitly *unknown*: we did not find a source, and the checker treats them as missing. The validator rejects any record without a source for a trusted class, and the source validator reports 0 errors and 0 warnings on the current catalog. *Certified simulation* is reserved for results from the Lanyon simulation service whose exported Lean proof passes the Gatekeeper (@sec:arch). The one session we ran produced a proof that did not compile (54 Lean errors), so no evidence in the catalog currently has that class.

# System architecture {#sec:arch}

![System architecture. Inputs (the desktop UI and the sourced cryostat and experiment sheets) reach the trusted Lean kernel only as serialised exact-rational documents. Z3, Claude and the Lanyon simulation service propose, and their outputs pass through `verdict`, `validSchedule` or the Gatekeeper before they reach the user as a verdict card listing the verdict, its reason, the theorems behind it, their axioms and the hash of the Lean sources. {ILLUSTRATIVE}](fig_architecture){#fig:arch width=1.0 wide}

@fig:arch shows the components. A local Python process hosts a PyWebView bridge for the desktop frontend, with no web server. It builds the Lean documents from SQLite, runs the checker as a subprocess, then calls Z3 for suggestions and re-checks each one. The **Gatekeeper** admits proposed Lean code (from an LLM, a person, or a simulation service's exported proof) into a rule Registry only if the code compiles against the project, contains no `sorry`, `admit`, `axiom`, `native_decide`, `opaque`, `unsafe`, `implemented_by` or `extern`, and every declared theorem's `#print axioms` is standard. Every result carries a **verdict card**: the verdict, its reason, the theorem names that justify it, their audited axioms, and SHA-256 hashes of the Lean sources and of the exact input.

RESULTS_PLACEHOLDER
