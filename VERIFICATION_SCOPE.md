# VERIFICATION_SCOPE — exact guarantees and limitations

CryoLean answers *"Can this cryostat do my experiment?"* with one of three verdicts:
`ACCEPT` (Requirements met), `REJECT` (Doesn't meet requirements), `NEED_MORE_INFORMATION`.
This document states precisely what a verdict does and does not mean.

## 1. What is formally verified (Lean 4)

The trusted core is `lean/CryoLean/{Model,Checker,Spec,Soundness}.lean`. It is industry-agnostic: industries,
equipment, experiments and the capability vocabulary are data. The checker never branches on an industry
or manufacturer.

`Spec.lean` defines, *independently of the executable checker*, what it means for a configuration to
**satisfy** (`Satisfies`) or **violate** (`Violates`) a requirement, and what ACCEPT/REJECT should mean
(`AcceptSpec`, `RejectSpec`). `Soundness.lean` proves the checker against that specification.

| Guarantee | Theorem |
|---|---|
| ACCEPT ⇒ the profile is user-confirmed, has ≥ 1 mandatory requirement, and **every** mandatory requirement is satisfied | `verdict_accept_sound` |
| ACCEPT ⇔ the specification holds (no false rejections of a fully documented match either) | `verdict_accept_iff` (+ `verdict_accept_complete`) |
| Every mandatory requirement was checked and returned `pass` | `accept_all_mandatory_pass` |
| Missing or unsupported information on any mandatory requirement blocks ACCEPT | `accept_no_unknown`, `missing_capability_unknown` |
| An explicitly UNKNOWN value never passes | `unknown_value_never_passes` |
| A documented incompatibility on a mandatory requirement forces REJECT | `fail_implies_reject` |
| REJECT ⇒ a documented violation of a mandatory requirement exists | `verdict_reject_sound` |
| Optional accessories that are not installed never pass; unknown install status never passes | `not_installed_never_passes`, `unknown_install_never_passes` |
| Inferred estimates and facts without provenance never pass | `estimate_never_passes`, `no_provenance_never_passes` |
| Units are never converted: a pass implies identical unit strings | `pass_implies_units_match`, `pass_implies_units_match_point` |
| Unconfirmed or empty profiles are never accepted | `unconfirmed_not_accept`, `empty_not_accept` |
| Satisfaction and violation are mutually exclusive | `satisfies_violates_exclusive` |
| The result carries the ids of exactly the inputs it was computed from; the verdict is a pure function of them | `run_binds_inputs`, `verdict_deterministic` |
| The industry label (and display name) cannot change a verdict — new industries cannot bypass the gate | `verdict_industry_irrelevant`, `verdict_name_irrelevant` |
| The reported checks are exactly the experiment's requirements | `checks_cover_requirements` |

Proof hygiene (enforced by `tests/test_lean_proofs.py`): no `sorry`, `admit`, custom `axiom` or
`native_decide`; `lean/Audit.lean` prints the axioms of every theorem above and the test requires them to
be a subset of `{propext, Classical.choice, Quot.sound}`. Tactics used: `omega`, `simp`, `split`, `cases`, `decide`.

## 2. How a verdict is produced (trust chain)

1. **Data layer** (`backend/catalog.py`) builds the exact Lean input document from the catalog JSON:
   configuration capabilities (value, install status, evidence status, evidence ids) and experiment
   requirements (constraint, mandatory flag, origin, evidence ids, `confirmed`).
2. **Lean binary** (`lean/.lake/build/bin/cryolean`) decodes it *fail-closed* (an unknown enum string is an
   error, never a default), runs the proven `verdict`/`run`, and returns per-requirement outcomes,
   plain-language explanations and a hash of the input it read.
3. **API** adds evidence records and a `result_token` (SHA-256 of catalog version + the exact Lean input).
   It never computes or alters a verdict. If Lean is unavailable the API returns **HTTP 503 with
   `verdict: null`** — there is no fallback.
4. Every result includes `lean_input`, so anyone can re-run `cryolean check` on it and get the same verdict.

## 3. Roles that are *not* trusted

| Component | Role | Why it is not trusted |
|---|---|---|
| Z3 (`solver/`) | Proposes candidate configurations (including hypothetical ones with documented optional accessories added, and "pending information" candidates with no documented conflict) | SAT is not a proof. Every candidate is re-checked by Lean on its exact document; only Lean `ACCEPT` appears under `verified_compatible`. A test injects an invalid SMT proposal and shows Lean rejects it. |
| AI matching (`backend/ai_matching.py`) | Maps natural language onto the *closed* set of prepared profiles; explains results | Cannot create profiles, requirements, specifications or verdicts. Invented ids are discarded; users must confirm the match. |
| Research pipeline | Produces *candidate* profiles | Candidates are validated and stored under `data/candidates/` as untrusted; they enter the catalog only via `scripts/promote_candidate.py --reviewed-by`. |

## 4. Rules that protect the requirements

* A session starts **unconfirmed**; Lean returns NEED_MORE_INFORMATION until the user confirms.
* Editing a requirement value marks it `user_entered`, clears its evidence ids and resets confirmation.
* The `mandatory` flag of a prepared requirement cannot be changed and a mandatory requirement cannot be
  removed through the API (HTTP 400).
* Switching configuration keeps the experiment and invalidates the result; `GET /sessions/{id}/result`
  returns 409 whenever the experiment, configuration, instrument overrides or catalog version changed.
* User-described instrument changes produce a new configuration id `<id>~mod:<hash>`: documented values
  are `user_entered` (visible in every check); undocumented modifications make the capability UNKNOWN.

## 5. What a verdict does NOT mean

* Lean verifies **logical consistency** between the recorded requirements and the recorded capabilities.
  It does **not** prove that a manufacturer datasheet or a paper is factually correct, that the values were
  transcribed correctly, or that a physical instrument in a given lab matches its catalog configuration.
* ACCEPT does not guarantee that an experiment will succeed. Only the *modelled* requirements are checked.
  Things not modelled (e.g. sample chemistry, operator skill, thermal contact quality, vibration
  coupling to a specific microscope, safety approvals) are outside scope.
* Optional (non-mandatory) requirements are reported but never decide the verdict.
* Experiment profiles record one or two published procedures. A paper reporting 2 K does not establish
  that every experiment of that type needs 2 K; the profile's `rationale` says which conditions are the
  paper's choice and which a source states as a physical necessity. Users should edit values to match their
  own plan (which then become `user_entered`).
* Configuration install status is a **catalog assumption** (e.g. "DynaCool, 14 T, ETO + VSM + HC") built
  from documented options; real installed units may differ — describe them with instrument overrides.
* Values whose evidence is an `inferred_estimate` (e.g. a distributor listing, a value derived from a
  percentage spec, a pdftotext column mapping not checked against the rendered PDF) never support ACCEPT.

## 6. Known modelling decisions (read before relying on a result)

* `range` capabilities: `at_least` compares against the upper end, `at_most` against the lower end (e.g.
  "reach 136 K or colder" uses the documented lower temperature limit).
* "< −195 °C" (Linkam) is recorded as −195 °C; "<3 K" (Optistat) as 3 K. Using the stated bound is
  conservative for `at_most` checks.
* DynaCool VSM bore and heat-capacity platform limits are module-specific keys (`sample.vsm.*`,
  `sample.heat_capacity.*`). No documented sample-size limit was found for the transport puck, so transport
  experiments on DynaCool return NEED_MORE_INFORMATION unless the user enters their own puck's limit.
* The semiconductor candidate's "≥ 3 probe arms" requirement is an inference from a three-terminal device;
  it is marked `inferred_estimate` and flagged by the validator for reviewer confirmation.

## 7. Coverage

`GET /coverage` (and `data/coverage.json`) is computed from the data: known vs researched industries,
verified profiles, equipment families, evidence counts by status and host, every UNKNOWN capability, and
requirement keys that no equipment documents. A universal architecture does **not** mean every industry
or experiment has been researched: at the time of writing 4 of 20 listed industries have researched
profiles (5 including the semiconductor acceptance-test candidate once promoted).
