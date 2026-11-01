# CryoLean data schema (v2)

The JSON files here are the reviewable seeds; `python -m cryolean build-db` compiles them into `data/cryolean.db`
(SQLite), which is what the application reads. Runtime registrations go to the database.

Quantities in seeds: `{"value": <int or exact decimal string>, "unit": "<symbol from cryolean/units.py>"}`.
The serializer converts them exactly to SI rationals with dimensions for Lean (`{"num", "den", "dim"}`).
Vocabulary keys declare their canonical unit, shape and which direction is better (`capability_vocabulary.json`).

## Evidence (`evidence/*.json`)
`{id, claim, value_as_printed, si|normalized, quote, source_url, document_title, location, doi, applies_to,
evidence_status, accessed, verification}` — status ∈ manufacturer_specification, experimental_observation,
reference_data, textbook_model, user_entered, inferred_estimate, unknown. Sourced records need a verbatim quote.

## Equipment (`cryostats/*.json`)
`{id, manufacturer, model, family, description, documents, configurations: [{id, name, configuration_basis,
capabilities: [{key, value, install, evidence_status, evidence_ids}]}]}`
* `value.kind`: `range{lo,hi}` · `max{q}` · `min{q}` (bounds where lower is better) · `flag{b}` · `count{n}` · `enum{s}` · `set{xs}` · `unknown`
* `install`: `installed` · `optional_not_installed` (an option the family offers, NOT fitted) · `unknown`
* Unknown values: `{"kind": "unknown"}` with `evidence_status: "unknown"` — never omitted, never zero.

## Experiments (`experiments/*.json`)
```jsonc
{
  "id", "name", "plain_name", "industry", "description", "keywords", "sources": [{citation, doi, url, accessed}],
  "reported_conditions": [...],          // what the paper actually did (observations, not universal requirements)
  "reported_equipment": ["PPMS"],        // equipment named in the sources (used only to rank Z3 alternatives)
  "requirements": [{
    "key": "magnetic_field.max" | "keys": ["vacuum.available", "purge.gas"],   // keys = any-of alternatives
    "constraint": {"kind": "point_within|range_within|at_least|at_most|present|absent|flag_is|count_at_least|count_equals|enum_in|set_contains", ...},
    "mandatory": true, "applicable": true,
    "conditions": [{"kind": "param_at_most|param_at_least", "name": "operating_temperature", "q": {...}} | {"kind": "cap_flag", "key", "b"}],
    "origin": "experimental_observation|user_entered|...", "rationale": "...", "evidence_ids": [...]
  }],
  "params": [{"name", "value": {...} | "material:<id>@<mK>" | null, "origin", "description", "evidence_ids"}],
  "coupled": [{"model": "<id in physics/coupled_models.json>", "mandatory": true, "rationale": "..."}],
  "missing_information": [...], "confirmed": true, "confirmation_note": "..."
}
```

## Physics (`physics/`)
* `properties.json` — the 40 physical properties → vocabulary keys and coupled models.
* `coupled_models.json` — models: `relations` (lhs ≤ rhs expression templates), `validity`, `parameters` (with
  `adjustable` direction for Z3 suggestions), `slots`, `assumptions`, `valid_range`, `justification_evidence_ids`, `status`.
  Only `validated` models are evaluated; others are emitted as UNSUPPORTED checks.
* `materials.json` — integrated thermal contraction reference data with evidence ids.
