# CryoLean backend

**"Can this cryostat do my experiment?"** — a research-grounded verification backend.

* **AI** maps a plain-language request onto a prepared, research-based experiment profile.
* **Z3 (SMT)** searches every registered configuration, across manufacturers and industries, for candidates.
* **Lean 4** checks the exact configuration against the experiment with a checker whose soundness is
  proven (`lean/CryoLean/Soundness.lean`, no `sorry`). Only Lean produces a verdict.
* **FastAPI** serves it to the Antigravity frontend (no GUI in this repository).

Verdicts: `ACCEPT` (Requirements met) · `REJECT` (Doesn't meet requirements) · `NEED_MORE_INFORMATION`.

## Setup

Requirements: Python ≥ 3.11, [elan](https://github.com/leanprover/elan) (Lean 4.35.0 is pinned in `lean/lean-toolchain`).

```bash
pip install -r requirements.txt
```

```bash
cd lean && lake build && cd ..
```

```bash
uvicorn backend.api:app --reload
```

Open `http://127.0.0.1:8000/docs`. Optional: `CRYOLEAN_AI_PROVIDER=claude` with `ANTHROPIC_API_KEY` set
uses Claude (`claude-opus-5-5`, closed-set ranking only) for matching; the default is an offline lexical matcher.

## Run the checks

```bash
python -m pytest
```

```bash
python scripts/validate_sources.py
```

```bash
python scripts/demo.py
```

`pytest` includes `lake build` (re-checks every proof) and an axiom audit (`lean/Audit.lean`); skip those two
with `-m "not slow"`. The Lean binary can also be used directly:

```bash
lean/.lake/build/bin/cryolean selftest
```

## Repository layout

| Path | Contents |
|---|---|
| `lean/` | Lean 4 project: `Model` (universal vocabulary), `Checker` (executable), `Spec` (independent specification), `Soundness` (proofs), `Json`/`Explain`/`Report` (I/O), `Main` (CLI `cryolean`), `Audit.lean` |
| `solver/z3_search.py` | Z3 configuration search (candidates only) |
| `backend/` | FastAPI app, catalog loader, Lean runner, verifier, sessions, modifications, AI matching, research pipeline, coverage, validation |
| `data/cryostats/` | 9 sourced equipment profiles, 26 exact configurations |
| `data/experiments/` | 8 research-grounded experiment profiles (Biology, Chemistry, Materials, Quantum) |
| `data/evidence/` + `data/evidence.json` | 394 provenance records (URL, title, page/section, verbatim quote, status, access date) |
| `data/capability_vocabulary.json` | Extensible capability keys and canonical integer units |
| `data/coverage.json` | Generated research-coverage registry |
| `research/` | Raw research notes per manufacturer and for experiments, incl. failed fetches; `research/new_industry/` holds the semiconductor candidate |
| `scripts/` | `validate_sources.py`, `build_evidence.py`, `build_coverage.py`, `promote_candidate.py`, `export_openapi.py`, `demo.py` |
| `tests/` | Real-data compatibility, unknown-never-supported, search/AI/session, universal-industry acceptance, Lean proof tests |
| `RESEARCH_SOURCES.md` | Source inventory (generated) |
| `VERIFICATION_SCOPE.md` | Exact guarantees and limitations |
| `FRONTEND_INTEGRATION.md` | API guide for Antigravity |

## Catalog (researched 2026-10-31)

| Equipment | Configurations |
|---|---|
| Leica CM1950 | legacy standard; legacy vacuum + motor + object cooling; 2026 DualEcoTec standard |
| Linkam THMS600 | with LNP96 + T96; heating only; THMSEL600 electrical variant |
| Quantum Design PPMS DynaCool | 9 T ETO + resistivity; 14 T ETO + VSM + heat capacity; 12 T VSM |
| Quantum Design PPMS (classic, discontinued) | 14 T; 16 T |
| Bluefors LD | LD250 (manual v2.0); LD400 + high-density wiring; LD450 (current) |
| Oxford Instruments TeslatronPT | 8 T; 12 T; 14 T; 6-1-1 T vector |
| Oxford Instruments OptistatDry | BLV; TLEX |
| Lake Shore CRX probe stations | CRX-VF; CRX-4K |
| Lake Shore / Janis CCS | CCS-100; CCS-300S; CCS-400; CCS-400H |

Experiments: frozen-tissue cryosectioning; cryo-fluorescence of vitrified samples; low-temperature Raman;
temperature-dependent photoluminescence; low-temperature electrical resistance; 10 T magnetoresistance;
transmon characterisation; millikelvin vector-field transport. Missing facts are recorded as UNKNOWN —
see `GET /coverage` for the full list (113 unknown capability entries at the time of writing).

## Adding an industry, experiment or instrument

1. `POST /industries` (any name) — industries are labels; the checker never reads them.
2. Research → `POST /research/candidates` (validated, stored untrusted in `data/candidates/`).
3. Review → `python scripts/promote_candidate.py <id> --reviewed-by "<name>"`.
4. New capability types → `POST /vocabulary/propose` (shape + canonical unit). No Lean change is needed:
   `tests/test_universal_industries.py` adds the semiconductor industry this way and asserts the Lean core is unchanged.
