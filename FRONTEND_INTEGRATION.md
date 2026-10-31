# FRONTEND_INTEGRATION — connecting Antigravity to the CryoLean backend

Base URL (local): `http://127.0.0.1:8000`. Interactive docs: `/docs`. OpenAPI 3 schema: `/openapi.json`
(a copy is committed as `openapi.json`; regenerate with `python scripts/export_openapi.py`).
All responses are JSON. No authentication in the MVP.

## 1. The three answers

Render `verdict` with `headline` and `user_message`; never compute a verdict client-side.

| `verdict` | `headline` | UI |
|---|---|---|
| `ACCEPT` | Requirements met | Show the verified badge (only when `verified_by_lean === true`). |
| `REJECT` | Doesn't meet requirements | Show `user_message` (the first failing check, in plain words) and offer "Change cryostat" / "Find alternatives". |
| `NEED_MORE_INFORMATION` | Need more information | Show `user_message`; list `missing_information` as specific questions. |

`next_step` is a one-line suggestion. "See checks" = the `checks` array: each has `key`, `mandatory`,
`outcome` (`pass|fail|unknown|unsupported`), `explanation` (plain sentence from Lean),
`capability` (value + install + evidence status), `capability_evidence` and `requirement_evidence`
(records with `source_url`, `document_title`, `location`, `quote`, `evidence_status`, `accessed`).

Plain-language question per check (suggested mapping by key prefix):
`temperature.*` → "Is it cold enough?", `sample.*` → "Does the sample fit?", `magnetic_field.*` →
"Is the magnetic field strong enough?", `cooling_power.*` → "Is there enough cooling power?",
`optical*` → "Can you see the sample?", `electrical.*` → "Does it have the connections?",
`module.*` → "Is the measurement module installed?", `vacuum.*`/`pressure.*` → "Can it hold a vacuum?".
Fall back to `checks[i].vocabulary.description`.

## 2. Main flow (recommended: sessions)

```
GET  /industries                       → category tabs (filter with ?q=)
GET  /experiments?industry=<id>        → experiment picker (use plain_name)
POST /ai/match {text}                  → "Describe your experiment" box; show matches, ask user to confirm
POST /sessions {experiment_id}         → session (starts UNCONFIRMED)
GET  /sessions/{id}                    → requirements for review (experiment.requirements)
PATCH /sessions/{id}/requirements [...] → user edits a value (resets confirmation)
POST /sessions/{id}/confirm            → user confirms the requirements
GET  /equipment, /configurations       → "Change cryostat" catalog (manufacturer, model, configuration name)
POST /sessions/{id}/select-configuration {configuration_id}
POST /sessions/{id}/verify             → "Check setup" (show "Checking your setup…" while pending)
GET  /sessions/{id}/result             → current result; 409 if stale → clear the result UI
POST /ai/explain {session_id}          → explanation + alternatives (each Lean-checked)
```

Switching cryostat = `select-configuration` again: the experiment stays, the previous result is
invalidated (`has_valid_result: false`, `GET result` → 409). Never keep showing a previous machine's result.

Instrument differences: `PUT /sessions/{id}/instrument-overrides` with
`[{key, documented, value?, install?, note}]`. `documented:false` = undocumented modification (that check
becomes Need more information). Overrides are cleared when the configuration changes.

## 3. Stateless endpoints

| Endpoint | Use |
|---|---|
| `POST /verify` `{experiment_id, configuration_id, confirmed, requirement_edits?, instrument_overrides?}` | One check |
| `POST /compare` `{experiment_id, configuration_ids[], confirmed}` | "Compare cryostats" view (2–3 machines, one verdict each, across manufacturers/industries) |
| `POST /search` `{experiment_id, allow_hypothetical_options?, max_candidates?, equipment_filter?}` | "Find another suitable configuration": Z3 proposals, each with its Lean result. Show `verified_compatible` as compatible; `candidates_not_verified` with their Lean verdict. `candidate.kind`: `catalog`, `hypothetical` (adds documented optional accessories — label "with option X installed"), `pending_information` (`assumed_unknown` lists what is missing). |
| `GET /configurations/{id}` | Specifications with evidence per capability (`include_evidence=true`) |
| `GET /evidence/{id}`, `GET /evidence?ids=a,b` | Evidence records |
| `GET /coverage` | Research coverage (what has and has not been researched) |
| `GET /health` | Lean availability, theorem count, Z3 version |
| `GET /vocabulary` | Capability keys, shapes, canonical units |

## 4. Any industry / custom experiments

* `POST /industries {name, description?, id?}` registers a custom industry (it is just a label).
* No good AI match (`no_good_match: true`) or an industry without profiles → `POST /research/requests
  {industry, description}`. The response has `verdict: "NEED_MORE_INFORMATION"`, the 10 research steps
  and any partially matching profiles. Show it as "We need to research this experiment first".
* `POST /research/candidates` accepts research output; it is validated and stored as **untrusted**
  (`trust: "candidate"`). It is never used for verification until a reviewer promotes it.
* `POST /vocabulary/propose` registers a new capability key (shape + canonical unit).

## 5. Units

Quantities are integers in canonical units: temperature `mK`, field `mT`, length `um`, power `nW`,
pressure `uPa`, frequency `kHz`, time `s` (see `GET /vocabulary`). Convert for display
(e.g. `{"value": 1800, "unit": "mK"}` → 1.8 K). When the user edits a value, convert back to the
canonical unit and send an integer; a different unit string is reported as `unsupported`, never converted.

## 6. Errors

| HTTP | Meaning | UI |
|---|---|---|
| 400 | Invalid edit (e.g. trying to remove/relax a mandatory requirement) | Show `error` |
| 404 | Unknown experiment/configuration/industry/evidence | Show `error` |
| 409 | Stale result (`stale: true`) | Clear the result, prompt to check again |
| 422 | Lean rejected the input document | Show `error`; no verdict |
| 503 | Lean checker unavailable (`verdict: null`) | "Verification is temporarily unavailable" — never show a verdict |

## 7. Saving a report

Persist the whole `VerificationResult`: it includes `lean_input` (the exact document Lean checked),
`lean_input_hash`, `result_token`, `catalog_version`, `checked_at` and all evidence — enough to reproduce
the verdict with `cryolean check`.
