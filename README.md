# CryoLean

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/e0c64585-dddc-47d8-a132-848fa78e7c3c" />

<img width="2989" height="1815" alt="image" src="https://github.com/user-attachments/assets/178931bc-4b6c-43e0-80ed-d97f642310e1" />

**Cryo, made simple.** CryoLean answers one question: *can this cryogenic machine physically perform my
experiment under its actual operating conditions?* The product proposal is in [docs/PRODUCT.md](docs/PRODUCT.md).
Built for the [VibeCheck FM + AI Hackathon](https://fmxai.org/vibecheck/).

```
your experiment ─► sourced requirements ─► Lean 4 verdict (trusted) ─► Z3 suggestions ─► Lean re-checks each suggestion
                                              │
                         REQUIREMENTS_MET · DOES_NOT_MEET_REQUIREMENTS · NEED_MORE_INFORMATION
```

| Layer | Role | Trusted? |
|---|---|---|
| **Lean 4** (`lean/`) | One universal compatibility checker over exact rationals with dimensional analysis; 33 audited soundness/completeness theorems (no `sorry`, standard axioms only). The compiled binary *is* the proven definitions. | **Yes — the only source of verdicts** |
| **Z3** (`cryolean/smt.py`) | After the verdict: unsat cores (why it fails, with the datasheet facts), ranked alternative configurations across all manufacturers, optimised parameter changes. Every suggestion is re-checked by Lean. | No |
| **SQLite** (`data/cryolean.db`) | Evidence-backed catalog built from version-controlled JSON seeds: 667 sourced records, 9 equipment families, 26 configurations, 11 experiment profiles, 40 physical properties, 13 coupled models. | Data (validated, not proven) |
| **Python** (`cryolean/`) | Local orchestration, exact unit conversion, desktop bridge for the Antigravity frontend. | Never decides a verdict |
| **AI** (`cryolean/ai.py`) | Natural-language matching onto prepared profiles (closed set), research drafting into *untrusted* candidates. | No |

No web server is needed: the Antigravity frontend calls `window.pywebview.api.*` (see [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)).

## Setup on Windows

Requirements: Python ≥ 3.11 and [elan](https://github.com/leanprover/elan) (Lean 4.35.0 is pinned in `lean/lean-toolchain`).

```powershell
pip install -r requirements.txt
```

```powershell
cd lean; lake build; cd ..
```

```powershell
python -m cryolean build-db
```

```powershell
python -m cryolean demo
```

```powershell
python -m pytest
```

Launch with the Antigravity frontend (PyWebView):

```powershell
python -m cryolean.desktop --frontend C:\path\to\antigravity\dist\index.html
```

`python -m pytest` compiles every Lean proof (`lake build`) and runs the axiom audit; use `-m "not slow"` to skip those two.
Verification is fully offline once the database is built. Optional: `CRYOLEAN_AI_PROVIDER=claude` (with Anthropic API credentials) for
Claude-based matching and research drafting; the default matcher is offline.

## The three demonstrations (`python -m cryolean demo`)

* **A — confirmed incompatibility.** A 10 T magnetoresistance measurement on the PPMS DynaCool 9 T: Lean rejects
  (`magnetic_field.max`), Z3's unsat core cites the Quantum Design brochure quote, and the 14 T configuration is proposed.
* **B — coupled multiphysics.** A 50-qubit wiring layout (Krinner et al., *EPJ Quantum Technology* 2019) on a Bluefors LD400
  with high-density wiring: temperature (10 mK ≤ 20 mK) and line count (168 ≥ 124) pass, but Lean computes the mixing-chamber
  heat budget `3 × (58·13 nW + 50·(29 + 50) nW + 8·20 nW) = 14.592 µW > 12 µW` and rejects. Z3 suggests 39 flux lines;
  Lean re-checks it as `REQUIREMENTS_MET` (11.985 µW ≤ 12 µW).
* **C — new industry.** Semiconductors are registered, a sourced candidate (two open-access papers using Lake Shore probe
  stations) passes the validation gate and reviewer approval, Z3 searches every configuration, the same Lean binary verifies
  the Lake Shore CRX-VF (and rejects the 2-probe-arm CRX-4K configuration for the ≥ 3-arm requirement), and the hash of the
  Lean core is unchanged.

## What is in the catalog

| Equipment | Configurations |
|---|---|
| Leica CM1950 | legacy standard; legacy vacuum + motor + object cooling; 2026 DualEcoTec |
| Linkam THMS600 | with LNP96 + T96; heating only; THMSEL600 electrical variant |
| Quantum Design PPMS DynaCool | 9 T ETO + resistivity; 14 T ETO + VSM + heat capacity; 12 T VSM |
| Quantum Design PPMS (classic) | 14 T; 16 T |
| Bluefors LD | LD250 (manual v2.0); LD400 + high-density wiring; LD450 (2026 spec) |
| Oxford Instruments TeslatronPT / OptistatDry | 8, 12, 14 T, 6-1-1 T vector / BLV, TLEX |
| Lake Shore CRX / Janis CCS | CRX-VF, CRX-4K / CCS-100, 300S, 400, 400H |

Experiment profiles (from published procedures): frozen-tissue cryosectioning; temperature-controlled cryo-microscopy;
low-temperature Raman; phase-transition microscopy (203–393 K); low-temperature resistance; VSM magnetometry (5–300 K, 9 T);
plus photoluminescence, 10 T magnetoresistance, transmon characterisation, mK vector-field transport and the qubit wiring heat budget.
Missing facts are UNKNOWN (121 capability entries); `get_research_coverage()` lists every gap.

## Repository

| Path | Contents |
|---|---|
| `lean/CryoLean/` | `Model` (universal types, SI dimensions), `Num` (exact rationals), `Checker`, `Spec` (independent specification), `Soundness` (proofs), `Json`, `Explain`, `Report`; `lean/Main.lean` CLI; `lean/Audit.lean` axiom audit |
| `cryolean/` | `bridge` (desktop API), `verifier` (Lean then Z3), `smt`, `serialize` (the Python→Lean boundary), `units`, `db`, `catalog`, `validation`, `research`, `modifications`, `edits`, `coverage`, `ai`, `demo`, `desktop` |
| `data/` | JSON seeds (`cryostats/`, `experiments/`, `evidence/`, `physics/`, `capability_vocabulary.json`, `industries.json`), `evidence.json`, `coverage.json`, `SCHEMA.md` |
| `research/` | raw research notes and the independently re-verified v2 research (`research/v2/`), new-industry candidate |
| `docs/` | `PRODUCT.md`, `antigravity/cryolean-client.js`, real example outputs in `examples/` |
| `scripts/` | `validate_sources.py`, `build_evidence.py`, `build_coverage.py`, `promote_candidate.py`, `import_research_v2.py` |
| `tests/` | 68 tests: the 20 required scenarios, engine guarantees, review regressions, Lean build + axiom audit, data and bridge |

Read [VERIFICATION_SCOPE.md](VERIFICATION_SCOPE.md) for exactly what is and is not guaranteed, and
[RESEARCH_SOURCES.md](RESEARCH_SOURCES.md) for every source.

## License

MIT — see [LICENSE](LICENSE).
