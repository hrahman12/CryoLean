# VERIFICATION_SCOPE — exact guarantees and limitations (v2)

Every result separates four things, and so does this document:

| Layer | What it means | Where |
|---|---|---|
| **Generic theorem verification** | Properties of the checker for *all* inputs, kernel-checked by Lean when the project is built | `lean/CryoLean/Soundness.lean`, `lean/Audit.lean` |
| **Concrete compatibility evaluation** | The compiled checker (the same definitions) evaluated on *this* configuration and experiment | `lean/.lake/build/bin/cryolean` via `cryolean/lean_runner.py` |
| **Source-data validation** | The data is well formed and traceable (sources, quotes, units, shapes) — not that it is true | `cryolean/validation.py` |
| **Physical-model assumptions** | The equations, assumptions and validity ranges of each coupled model | `data/physics/coupled_models.json` |

## 1. Formally verified (Lean 4, no `sorry`/`admit`/custom axioms/`native_decide`)

The trusted core has no notion of industry, manufacturer or property. Numbers are exact rationals in SI coherent units
with a 7-component dimension vector; every comparison checks dimensions; units are never converted inside Lean.
`Spec.lean` defines satisfaction/violation independently of the checker (shared: `lookup`, `findParam`, exact
rational order `Q.le`, exact arithmetic). `lean/Audit.lean` prints the axioms of the 33 key theorems; the test suite requires
`{propext, Classical.choice, Quot.sound}` only.

| # | Required guarantee | Theorem(s) |
|---|---|---|
| 1 | ACCEPT ⇒ every applicable mandatory requirement passes (or is excluded by a definitely-false condition) | `verdict_accept_sound`, `verdict_accept_iff` |
| 2 | Missing mandatory information cannot produce ACCEPT | `accept_no_unknown`, `missing_capability_unknown`, `unknown_value_never_passes`, `cap_not_usable_missing` |
| 3 | Unsupported mandatory requirements (dimension/shape mismatch, model invalid here) cannot produce ACCEPT | `accept_no_unknown`, `pass_implies_dims_match`, `coupled_pass_dims_match` |
| 4 | A confirmed mandatory failure prevents ACCEPT | `fail_implies_reject`, `violation_prevents_accept`, `verdict_reject_complete` |
| 5 | Every applicable mandatory coupled constraint passes before ACCEPT | `accept_all_coupled`, `verdict_accept_sound` (`CoupledOK`) |
| 6 | Optional requirements do not block acceptance | `verdict_ignores_optional` |
| 7 | Non-applicable requirements do not cause false failures | `verdict_ignores_nonapplicable`, `condition_false_not_applicable` |
| 8 | Installed accessories are distinguished from optional ones | `not_installed_never_passes`, `unknown_install_never_passes`, `cap_not_usable_missing` |
| 9 | A verdict applies only to the exact configuration and experiment | `run_binds_inputs`, `verdict_deterministic`, `run_reports_everything` (+ input hash and fingerprint) |
| 10 | AI cannot bypass the gate | Lean's input has no AI field; injected `"verdict"` fields are ignored (test); AI output is a closed-set match or an untrusted candidate |
| 11 | Z3 cannot override a Lean rejection | `candidates_verdicts_are_lean`, `candidates_accept_sound` (the `check-candidates` entry point) |
| 12 | New industries cannot bypass mandatory checking | `verdict_industry_irrelevant`, `verdict_name_irrelevant` |
| — | ACCEPT and REJECT specifications are exclusive; evaluation of coupled expressions is sound and complete w.r.t. the big-step semantics | `satisfies_spec_exclusive`, `evalExpr_sound`, `evalExpr_complete` |
| — | The rational order does not depend on the representation | `Q.le_scale_left`, `Q.le_scale_right` |

Evidence classes that may support a pass: manufacturer specification, experimental observation, reference data,
user-entered. Inferred estimates and records without provenance never pass (`estimate_never_passes`, `no_provenance_never_passes`).

## 2. Concrete evaluation and the serialization boundary

`cryolean/serialize.py` builds the only documents Lean reads. It converts catalog integers in canonical units to SI
rationals exactly (`fractions.Fraction`; floats are refused), derives `<cooling_power key>.temperature` from the vocabulary
(same evidence ids), resolves each coupled model's cooling-power slot to the **highest documented temperature not above the
operating temperature**, and expands model templates. Lean re-checks every slot through the model's validity bounds
(`T_doc ≤ T_op`), so a wrong slot can only produce a failure or an UNSUPPORTED/UNKNOWN check, never a false pass. The
decoder is fail-closed (unknown enum strings, zero denominators, empty key lists are decode errors). If the Lean binary is
missing or fails, the bridge returns `lean_unavailable` with `verdict: null`.

## 3. Not trusted, by design

| Component | Role | Safeguard |
|---|---|---|
| Z3 (`cryolean/smt.py`) | unsat cores, alternatives, parameter optimisation | every suggestion is re-checked by Lean; only `verified: true` (Lean `REQUIREMENTS_MET` on the exact document) may be shown as compatible; tested with a deliberately wrong Z3 ranking |
| AI (`cryolean/ai.py`) | closed-set matching; research drafting | invented ids discarded; drafts become untrusted candidates; the user confirms the match |
| Research pipeline | candidates | validation gate + named reviewer before anything enters the trusted tables |

## 4. Rules that protect requirements

Profiles start unconfirmed in sessions and Lean answers NEED_MORE_INFORMATION until confirmed. Mandatory requirements
cannot be removed or made optional through the bridge. Edited values become `user_entered` and reset confirmation.
Switching equipment invalidates results; stored results are refused when the fingerprint changes. Modifications are
`installed_documented` (user-entered evidence, new configuration id), `proposed` (never applied to the real check) or
`undocumented` (the capability becomes UNKNOWN).

## 5. The 40 physical properties

All 40 are representable as vocabulary keys and/or coupled models (`data/physics/properties.json`). Their status is
computed from the data (`get_physical_properties()`): at the time of writing 25 are implemented with documented data,
14 are representable but no registered equipment documents them yet, and 1 (thermal conductivity) has no validated model.
Coupled models with status `validated`: Joule heating vs cooling power, mixing-chamber wiring heat budget, magnet ramp time,
cooldown time budget, differential thermal contraction, objective working-distance clearance, NA vs f-number, frost/condensation
(as a conditional any-of requirement). Not validated — always reported UNSUPPORTED: field–temperature envelope, temperature
stability during field sweeps, cryogen consumption, thermal stress, pressure at temperature.

## 6. What a verdict does NOT mean

* Lean proves logical conclusions from the modelled requirements and the supplied facts. It does not prove that a datasheet
  or paper is correct, that values were transcribed correctly (source validation and independent re-checks reduce that risk),
  or that a physical model captures every real effect.
* Experiment profiles record specific published procedures; a reported 2 K or 9 T is that procedure's condition, and each
  requirement's `rationale` says so. Users should enter their own values.
* Configuration install status is a catalog assumption built from documented options; describe a real instrument with modifications.
* Model assumptions matter: e.g. the wiring heat budget uses Krinner et al.'s measured per-line loads (central values, no
  uncertainty propagation) and their factor-three design rule; Joule heating counts only the sample's I²R.
* Angles are dimensionless degrees; oersted is converted with B = µ0·H; logarithmic units and noise densities (V/√Hz) are not representable.

## 7. Coverage

`get_research_coverage()` (and `data/coverage.json`) is computed from the data: 4 of 20 listed industries have researched
profiles (5 once the semiconductor acceptance candidate is approved in a working database). A universal architecture does
not mean every industry or experiment has been researched.
