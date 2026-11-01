# FRONTEND_INTEGRATION — connecting the Antigravity frontend to the local CryoLean backend

CryoLean runs **locally on Windows with no web server**. The Antigravity frontend is loaded into a native
window by PyWebView, and calls the Python backend directly through `window.pywebview.api.*`.

```
Antigravity UI (HTML/JS) ──window.pywebview.api.method(...)──► cryolean.bridge.CryoLeanAPI (Python)
                                                                 ├─ SQLite evidence/catalog DB   (data/cryolean.db)
                                                                 ├─ Lean 4 checker (subprocess)  (lean/.lake/build/bin/cryolean.exe)
                                                                 └─ Z3 solver (in process)
```

## 1. Copy-paste for Antigravity

1. Copy [`docs/antigravity/cryolean-client.js`](docs/antigravity/cryolean-client.js) into the frontend project.
2. Use it like this:

```js
import * as cryo from "./cryolean-client.js";

// "What would you like to do?"
const { industries } = await cryo.listIndustries();          // category tabs
const { experiments } = await cryo.listExperiments("materials_and_nanotechnology");
const ai = await cryo.matchExperiment("test how a material's resistance changes in a strong magnetic field");
// -> ai.matches[0].experiment_id, ai.matches[0].plain_name ; ALWAYS ask the user to confirm

// Review the prepared profile, let the user edit values, then confirm
const profile = await cryo.getExperimentRequirements("mat_magnetoresistance_10T");

// "Change cryostat"
const { equipment } = await cryo.listEquipment();

// "Check setup"  (show "Checking your setup…" while awaiting)
const r = await cryo.checkCompatibility("mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res", { confirmed: true });
render(cryo.HEADLINE[r.verdict], r.user_message, r.next_step);
showBadge(cryo.isVerified(r));                       // badge ONLY for a Lean REQUIREMENTS_MET
renderChecks(r.checks.concat(r.coupled_checks));    // "See checks": cryo.checkQuestion(c), c.outcome, c.explanation, evidence
renderSuggestions(r.suggestions);                    // Z3: conflicts, parameter_changes, alternatives (each with lean_verdict)

// Switching cryostats without losing the experiment
const s = await cryo.startSession("mat_magnetoresistance_10T");
await cryo.updateSession(s.id, { confirmed: true });
await cryo.selectEquipment(s.id, "qd_dynacool_9T_eto_res");
const r1 = await cryo.checkSession(s.id);
await cryo.selectEquipment(s.id, "qd_dynacool_14T_eto_vsm_hc");   // previous result is invalidated
const r2 = await cryo.checkSession(s.id);
```

3. Short prompt for Antigravity:

> Build the CryoLean screen described in the README using `cryolean-client.js`. Never compute a verdict in
> the UI; show `HEADLINE[result.verdict]`, `result.user_message` and `result.next_step`, and a verified badge
> only when `isVerified(result)` is true. "See checks" lists `result.checks` and `result.coupled_checks`
> with `checkQuestion(check)`, the outcome, the explanation and the evidence (document title, page/section,
> quote, link). Show `result.missing_information` as questions. Show `result.suggestions` under "Other
> options": `parameter_changes` and `alternatives` with their own `lean_verdict` (only `verified: true` may be
> called compatible). When the user changes the cryostat, call `selectEquipment` and clear the old result.
> Handle `CryoLeanError` codes: `stale_result` → clear and re-check; `lean_unavailable` → "Verification is
> unavailable" (no verdict); `edit_refused` → show the message.

## 2. Launching locally (Windows)

```powershell
pip install -r requirements.txt pywebview
cd lean; lake build; cd ..
python -m cryolean build-db
python -m cryolean.desktop --frontend C:\path\to\antigravity\dist\index.html
```

Without `--frontend`, a status page shows the Lean checker status. Every bridge method can also be called
from the command line for testing:

```powershell
python -m cryolean methods
python -m cryolean call check_compatibility "{\"experiment_id\": \"mat_magnetoresistance_10T\", \"configuration_id\": \"qd_dynacool_9T_eto_res\", \"confirmed\": true}"
```

## 3. Envelope and errors

Every method returns `{"ok": true, "data": ...}` or `{"ok": false, "error": {"code", "message", "verdict": null}}`.

| code | meaning | UI |
|---|---|---|
| `lean_unavailable` | Lean binary missing or failed — **no verdict exists** | "Verification is unavailable" |
| `lean_rejected_input` | Lean refused a malformed document (fail-closed) | show message |
| `not_found` | unknown experiment / configuration / equipment / result / session (also: an unapproved candidate) | show message |
| `invalid_input` | bad unit, float value, bad JSON | show message |
| `edit_refused` | tried to remove or make optional a mandatory requirement, or a bad modification | show message |
| `stale_result` | the catalog, configuration or experiment changed since the result | clear result, re-check |
| `research_refused` | candidate promotion refused (validation errors / no reviewer) | show message |
| `internal_error` | unexpected | show message |

## 4. Method reference (exact signatures)

Arguments may be passed as objects or JSON strings. Quantities are `{"value": "<int or exact decimal string>", "unit": "<symbol>"}`
— floats are refused. Units: `K mK uK m mm um nm cm inch kg g mg ug s ms min h A mA uA nA pA W mW uW nW J T mT uT Oe T_per_s mT_per_s uT_per_s Oe_per_s Pa uPa mbar Torr Hz kHz MHz GHz V mV uV nV Ohm kOhm MOhm mOhm uOhm K_per_s K_per_min mK_per_min count percent ppm deg mdeg NA f_number m3 L L_per_min Pa_m3_per_s mbar_L_per_s W_per_m_K K_per_W`.

| Method | Purpose |
|---|---|
| `list_industries(query=None)` | all industries (standard + registered + used), `status`: known / registered / researched |
| `register_industry(name, description="", industry_id=None)` | add any industry (a label; no special logic) |
| `list_experiments(industry=None)` | prepared profiles (`plain_name` for the menu) |
| `get_experiment_requirements(experiment_id)` | requirements, parameters, coupled constraints, sources, evidence, `missing_information` |
| `match_experiment(text, top_k=3)` | AI closed-set matching; `needs_confirmation` is always true |
| `register_experiment(document, evidence=None, submitted_by="user", request_id=None)` | validated, stored **untrusted** |
| `register_equipment(document, evidence=None, submitted_by="user", request_id=None)` | same for equipment |
| `approve_candidate(candidate_id, reviewed_by)` | reviewer promotion into the trusted catalog |
| `list_candidates()` | research candidates and their validation |
| `list_equipment(manufacturer=None, family=None)` | catalog for "Change cryostat" |
| `get_equipment_details(equipment_or_configuration_id)` | capabilities with evidence, `unknown_capabilities`, `optional_accessories_not_installed`, modifications |
| `register_modification(configuration_id, status, changes, description="")` | `installed_documented` / `proposed` / `undocumented` |
| `check_compatibility(experiment_id, configuration_id, parameters=None, requirement_edits=None, confirmed=False, extra_modifications=None, suggestions=True)` | **the main call** |
| `find_compatible_equipment(experiment_id, parameters=None, requirement_edits=None, confirmed=True, max_results=10, include_hypothetical_options=True)` | Z3 search over all equipment, each candidate Lean-checked |
| `compare_equipment(experiment_id, configuration_ids, parameters=None, requirement_edits=None, confirmed=True)` | one Lean verdict per configuration + comparison table |
| `get_verification_details(result_id)` | stored result; `stale_result` if anything changed |
| `start_session(experiment_id)` / `update_session(session_id, parameters=None, requirement_edits=None, confirmed=None)` / `select_equipment(session_id, configuration_id)` / `check_session(session_id)` / `get_session_result(session_id)` | switching cryostats with automatic invalidation |
| `research_new_experiment(description, industry="unspecified", research_text=None)` | NEED_MORE_INFORMATION + 12-step research plan (+ optional untrusted AI draft) |
| `get_research_coverage()` | coverage registry (industries, profiles, equipment, evidence, 40 properties, coupled models, gaps) |
| `get_lean_status()` / `get_physical_properties()` / `reload_catalog()` | status and registries |
| `get_verification_card()` | theorem names, audited axioms, Lean source hash, forensics summary |
| `schedule_campaign(configuration_id, experiment_ids, run_length, durations, parameters=None, confirmed=False)` | Lean verdict per experiment, Z3 packs the accepted ones into one cooldown (minimum makespan, unsat core if they cannot fit), Lean `validSchedule` checks the slots. Show "Schedule OK" only when `schedule_ok` is true |
| `check_schedule(document)` | Lean `validSchedule` on an edited slot list (the `lean_input` of a schedule result) |
| `submit_lean_rule(name, source, proposer="user")` | Gatekeeper: compile, no sorry/axiom/native_decide, standard axioms only; admitted rules go to the Registry |
| `list_registry()` | admitted rules (sha256, theorems, axioms, proposer) |
| `get_lanyon_status()` / `run_lanyon_model(problem, instructions=None, name=None)` / `import_lanyon_session(run_dir)` | Lanyon certified simulations. A result counts as `certified_simulation` only if Lanyon certified it **and** its exported Lean proof passed the Gatekeeper; otherwise it is an `inferred_estimate`. `run_lanyon_model` sends the prompt to Lanyon's servers, so ask the user first |

`requirement_edits`: `[{"key": "magnetic_field.max", "constraint": {"kind": "at_least", "q": {"value": 12000, "unit": "mT"}}}]`.
Edits mark the requirement `user_entered` and reset confirmation; removing a mandatory requirement or changing its
`mandatory` flag is refused.

## 5. The result object (`check_compatibility`, real values from Demo B)

Full real outputs: [`docs/examples/demo_a_incompatibility.json`](docs/examples/demo_a_incompatibility.json),
[`demo_b_coupled.json`](docs/examples/demo_b_coupled.json), [`demo_c_new_industry_check.json`](docs/examples/demo_c_new_industry_check.json),
[`demo_c_new_industry_search.json`](docs/examples/demo_c_new_industry_search.json).

```jsonc
{
  "verdict": "DOES_NOT_MEET_REQUIREMENTS",          // REQUIREMENTS_MET | DOES_NOT_MEET_REQUIREMENTS | NEED_MORE_INFORMATION
  "headline": "Doesn't meet requirements",
  "user_message": "Mixing-chamber wiring heat load (with design margin) vs cooling power: 14.592 µW exceeds 12 µW. Constraint not met.",
  "next_step": "See why it fails and the suggested alternatives below.",
  "equipment": {"id": "bluefors_ld", "manufacturer": "Bluefors", "configuration_id": "bluefors_ld400_hdw", "modifications_applied": []},
  "experiment": {"id": "quantum_mxc_wiring_heat_budget", "industry": "quantum_computing_and_sensing", "confirmed": true, "parameters": [...]},
  "checks": [{"kind": "requirement", "keys": ["temperature.base"], "mandatory": true, "applicable": true, "outcome": "pass",
              "required": "needs 20 mK or lower", "available": "a documented minimum of 10 mK",
              "explanation": "...", "property": 1, "capability_evidence": [{"id": "ev_bf_0003", "quote": "...", "document_title": "...", "location": "...", "source_url": "..."}]}],
  "coupled_checks": [{"kind": "coupled", "model": "mxc_wiring_heat_budget", "outcome": "fail",
                      "lhs": {"display": "14.592 µW", "value": {"num": ..., "den": ..., "dim": {...}}},
                      "rhs": {"display": "12 µW"}, "equation": "margin * (...) <= P_cool(T_doc)", "assumptions": ["..."],
                      "slot_resolution": {"cooling": "cooling_power.at_20mK"}, "evidence": [...]}],
  "missing_information": [],                          // keys/models that blocked acceptance for lack of evidence
  "failed_requirements": ["Mixing-chamber wiring heat load (with design margin) vs cooling power"],
  "verification": {
    "generic_theorems": {"status": "kernel-checked when the Lean project is built", "key_theorems": ["verdict_accept_sound", "..."]},
    "concrete_evaluation": {"engine": "CryoLean Lean 4 compatibility checker v2", "verified_by_lean": true, "lean_input_hash": "...", "verdict": "..."},
    "source_data_validation": {"ok": true, "errors": [], "warnings": []},
    "physical_model_assumptions": [{"model": "mxc_wiring_heat_budget", "equation": "...", "assumptions": ["..."]}]
  },
  "suggestions": {                                     // Z3, AFTER the Lean verdict
    "conflicts": {"status": "unsat", "conflicts": [{"explanation": "... cannot hold together with p_flux_dc = 50 nW; ...", "requirements": [...], "facts": [...]}]},
    "parameter_changes": [{"parameter": "n_flux_lines", "current": "50", "suggested": "39", "lean_verdict": "REQUIREMENTS_MET", "verified": true}],
    "requirement_relaxations": [],                    // only offered: changing a requirement is the user's decision
    "alternatives": [{"configuration_id": "...", "z3_status": "satisfiable|needs_options|pending_information", "added_options": [], "hypothetical": false,
                      "lean_verdict": "REQUIREMENTS_MET", "verified": true}]
  },
  "references": [{"type": "experiment_source", "citation": "...", "doi": "10.1140/epjqt/s40507-019-0072-0"}],
  "fingerprint": "427a71d0...",                        // SHA-256 of catalog version + exact Lean input
  "result_id": "res_9e2722c43fb7",
  "lean_input": {"configuration": {...}, "experiment": {...}}   // the exact documents Lean checked
}
```

Outcomes per check: `pass`, `fail`, `unknown` (missing information), `unsupported` (unrepresentable or model not
valid here), `not_applicable` (a condition is false, e.g. the frost rule above 0 °C).

## 6. The verdict card

Every `check_compatibility` result has `verdict_card`:

```json
{ "verdict": "DOES_NOT_MEET_REQUIREMENTS",
  "reason": "'magnetic_field.max' needs at least 10 T, but this configuration has a documented maximum of 9 T (manufacturer specification). Requirement not met.",
  "theorems": ["verdict_reject_sound", "fail_implies_reject", "fail_needs_trusted", "violation_prevents_accept", "run_binds_inputs"],
  "axioms": { "verdict_reject_sound": ["propext", "Quot.sound"], "...": [] },
  "axioms_standard_only": true, "axiom_audit": "current",
  "source_hash": "5262e4e8c30d…", "lean_input_hash": "4122767249582765024",
  "z3_role": "Z3 output is a hint, never a verdict" }
```

`cryo.verdictCard(result)` returns it ready to render: verdict · reason · theorem names · axioms · source hash.
`axiom_audit` is `stale` if the Lean sources changed since `python scripts/audit_axioms.py` last ran.

## 7. How results update when equipment changes

* Each result is bound to its exact inputs by `fingerprint`; `get_verification_details(result_id)` recomputes it and
  returns `stale_result` if the catalog version, configuration (including modifications) or experiment changed.
* In a session, `select_equipment` keeps the experiment and parameters, clears `result_id`, and
  `get_session_result` returns `stale_result` until `check_session` runs again.
* Editing requirements or parameters resets `confirmed`; the next check is `NEED_MORE_INFORMATION` until the user confirms.
* A modified instrument is checked under a new id `<configuration>~mod:<hash>` so its verdict is never shown for the catalog configuration.
