# CryoLean data schema

All files are UTF-8 JSON. Every number that reaches the Lean checker is an
**integer in the canonical unit** listed in `capability_vocabulary.json`
(mK, mT, um, nW, uPa, kHz, s, ...). Conversion from the unit printed in the
source happens once, in the evidence record, and is recorded there.

## `data/evidence.json` — one record per sourced fact

```json
{
  "id": "ev_qd_0001",
  "claim": "DynaCool 9 T magnet option: maximum field 9 T",
  "value_as_printed": "9 T",
  "normalized": {"value": 9000, "unit": "mT"},
  "source_url": "https://qdusa.com/siteDocs/productBrochures/1307-010.pdf",
  "document_title": "Product Description / Cryogen-Free Physical Property Measurement System / PPMS DynaCool (1307-010 Rev. G0)",
  "location": "PDF page 2, Magnet options table",
  "quote": "either a 9 T, 12 T or 14 T ...",
  "applies_to": "PPMS DynaCool with 9 T magnet option",
  "evidence_status": "manufacturer_specification",
  "accessed": "2026-10-31",
  "collected_by": "research agent",
  "review_status": "unreviewed"
}
```

`evidence_status` ∈ `manufacturer_specification | experimental_observation | user_entered | inferred_estimate | unknown`.
`normalized` may be `null` for non-numeric facts (flags, lists) or UNKNOWN facts.

## `data/cryostats/<equipment_id>.json`

```json
{
  "id": "qd_ppms_dynacool",
  "manufacturer": "Quantum Design",
  "model": "PPMS DynaCool",
  "family": "cryogen-free physical property measurement platform",
  "description": "...",
  "documents": [{"id": "doc_qd_B", "url": "...", "title": "...", "accessed": "2026-10-31"}],
  "configurations": [
    {
      "id": "qd_dynacool_9T_eto",
      "name": "PPMS DynaCool, 9 T magnet, Electrical Transport Option",
      "configuration_basis": "catalog combination of documented options; install status is a catalog assumption, capability values are manufacturer specifications",
      "capabilities": [
        {"key": "temperature.range",
         "value": {"kind": "range", "lo": {"value": 1800, "unit": "mK"}, "hi": {"value": 400000, "unit": "mK"}},
         "install": "installed", "evidence_status": "manufacturer_specification", "evidence_ids": ["ev_qd_0003"]},
        {"key": "magnetic_field.max",
         "value": {"kind": "max", "q": {"value": 9000, "unit": "mT"}},
         "install": "installed", "evidence_status": "manufacturer_specification", "evidence_ids": ["ev_qd_0001"]},
        {"key": "module.vsm", "value": {"kind": "flag", "b": true},
         "install": "optional_not_installed", "evidence_status": "manufacturer_specification", "evidence_ids": ["ev_qd_0010"]},
        {"key": "cooling_power.at_4200mK", "value": {"kind": "unknown"},
         "install": "installed", "evidence_status": "unknown", "evidence_ids": ["ev_qd_0099"]}
      ]
    }
  ],
  "unknowns": [{"key": "optical_access", "note": "base system optical access not documented in sources fetched"}]
}
```

Rules:
* `install`: `installed` | `optional_not_installed` | `unknown`. An option that the
  product family offers but this configuration does not include MUST appear as
  `optional_not_installed` (so Z3 can propose the configuration that has it).
* A capability whose value could not be found is recorded with
  `{"kind": "unknown"}` and `evidence_status: "unknown"` (never omitted silently
  if the vocabulary key is relevant to the equipment class).
* `value.kind`: `range{lo,hi}` | `max{q}` | `min{q}` | `flag{b}` | `count{n}` | `unknown`.

## `data/experiments/<experiment_id>.json`

```json
{
  "id": "magnetoresistance_10T_2K",
  "name": "Magnetoresistance of a thin film up to 10 T at 2 K",
  "plain_name": "Test how a material's resistance changes in a strong magnetic field",
  "industry": "materials_and_nanotechnology",
  "sources": [{"id": "src_...", "citation": "...", "doi": "10....", "url": "...", "accessed": "2026-10-31"}],
  "reported_conditions": [
    {"key": "temperature.range", "as_printed": "2–300 K", "normalized": {...}, "evidence_id": "ev_exp_0001"}
  ],
  "requirements": [
    {"key": "magnetic_field.max",
     "constraint": {"kind": "at_least", "q": {"value": 10000, "unit": "mT"}},
     "mandatory": true, "origin": "user_entered",
     "rationale": "User-specified target field for this measurement.",
     "evidence_ids": []},
    {"key": "temperature.range",
     "constraint": {"kind": "point_within", "q": {"value": 2000, "unit": "mK"}},
     "mandatory": true, "origin": "experimental_observation",
     "rationale": "Paper measured at 2 K; user confirmed this operating point.",
     "evidence_ids": ["ev_exp_0001"]}
  ],
  "confirmed": true,
  "confirmation_note": "Requirements reviewed and confirmed by the profile author on 2026-10-31."
}
```

`constraint.kind`: `point_within{q}` | `range_within{lo,hi}` | `at_least{q}` | `at_most{q}` | `present` | `count_at_least{n}`.
`origin` uses the same vocabulary as `evidence_status`. A requirement derived from a
single paper's reported conditions is `experimental_observation` and must say in
`rationale` that it is this paper's choice unless a source states it is a
physical necessity. `confirmed: false` profiles are never accepted by Lean.

## `data/industries.json`

```json
[{"id": "materials_and_nanotechnology", "name": "Materials and nanotechnology",
  "status": "researched", "experiment_ids": ["..."], "notes": "..."}]
```
Industries are plain entries: the checker never reads this file.
