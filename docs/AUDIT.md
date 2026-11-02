# CryoLean repository audit (2026-11-01)

Read-only audit; no source changes. All commands from repo root with
`CRYOLEAN_LEAN_BIN=<scratchpad>/leanbuild/.lake/build/bin/cryolean.exe`.

## Commands run

| Command | Result |
|---|---|
| `python -m pytest -q -p no:cacheprovider` | 105 tests collected, **104 passed, 1 failed** (pytest.ini adds a second `-q`, so pytest prints no final summary line; counts read from the progress dots). |
| failure | `tests/test_frontend_contract.py::test_frontend_readonly_catalog_matches_real_ids`: `frontend/src/data/catalog.json` is a stale snapshot; the live catalog has profiles it lacks (e.g. `quantum_heralded_qubit_amplifier`, `geo_noble_gas_he_ne_cryotrap`). Fix: `python scripts/export_frontend_catalog.py` (frontend is Codex-owned). |
| `python scripts/audit_axioms.py` | `audited 48 theorems; all standard axioms: True`. Note: the script rewrites `lean/audit-axioms.json`. |
| `python -m cryolean demo` | Lean checker available, `cryolean v2 (Lean 4.35.0)`, selftest True, theorems=128, unsafe=[]. Verdicts below. |

### Demo verdicts (all from the Lean binary)
- A: 10 T magnetoresistance on DynaCool 9 T rejected; Z3 alternatives (DynaCool 14 T, Proteox MX450 14 T, LD250) re-checked by Lean as NEED_MORE_INFORMATION, not REQUIREMENTS_MET.
- B: LD400 wiring budget 14.592 uW > 12 uW, rejected; Z3 fix n_flux 50 -> 39, Lean re-check REQUIREMENTS_MET.
- C: semiconductors pipeline; Lean REQUIREMENTS_MET for CRX-VF, EMPX-H2, FWPX-6arm; NEED_MORE_INFORMATION for attoDRY800, CPX; core hash unchanged (3cf2d6e8e5a8784d). `verify before approval -> not_found`.
- D: 10 T run excluded (DOES_NOT_MEET_REQUIREMENTS); Z3 makespan 23 h, Lean `validSchedule` True; 20 h variant Z3 unsat (18 h needed, 15 h available).

### Lean scan
- `grep sorry|admit|axiom` over `lean/CryoLean`: no `sorry`, `admit`, `axiom` declarations or `native_decide`; the only hit is a docstring in `Model.lean:59`.
- Theorem keyword counts: Soundness 100, Monotone 18, Schedule 7, Num 5, Report 1. Audit JSON lists 48 theorems, standard axioms only (`propext`, `Quot.sound`, `Classical.choice`).

### Full grid DB (scratchpad `full_v4.db`)
`grid.summary` runs: 204 experiments x 220 configurations, per-experiment met/not_met/need_info counts present.

## README claims

| Claim | Status | Evidence |
|---|---|---|
| Lean is the only verdict source; Z3 outputs re-checked by Lean | VERIFIED | demo output (every Z3 suggestion shows a Lean re-check) |
| "44 audited theorems, standard axioms only" | PARTIAL | audit now reports 48 theorems, all standard; number stale |
| Gatekeeper admits only kernel-accepted, std-axiom code | PARTIAL | `cryolean/gatekeeper.py` present; tests pass; not run live in this audit |
| Forall forensics: 839 declarations, 0 smells | PARTIAL | `docs/forensics/summary.json` exists; `run_forensics.py` not re-run |
| Z3 unsat cores, alternatives, fixes, campaign packing | VERIFIED | demos A-D |
| Claude matching/drafting (optional) | PARTIAL | `cryolean/ai.py`; offline default used; Claude path not exercised |
| Lanyon certified simulations via Gatekeeper | PARTIAL | `cryolean/lanyon.py`, `docs/lanyon/`; external service not called |
| SQLite: 667 records, 26 configurations, 11 profiles | NOT FOUND (stale) | `data/cryolean.db` has 220 configurations, 204 experiments, 3335 evidence rows |
| PyWebView desktop + bridge, no web server | PARTIAL | `desktop.py`, `bridge.py`; bridge tested by pytest; window not launched |
| Codex frontend in `frontend/` | PARTIAL | `frontend/dist` built; its catalog snapshot is stale (failing test) |
| `verdict_accept_iff`, `verdict_reject_sound`, `fail_needs_trusted`, `validSchedule_*` | VERIFIED | `lean/audit-axioms.json`, demo D theorem list |
| Three verdicts incl. NEED_MORE_INFORMATION | VERIFIED | demos A, C |
| Demo A "the 14 T configuration is proposed" | PARTIAL | proposed by Z3 but Lean says NEED_MORE_INFORMATION (missing sample-limit data) |
| Demo B numbers 14.592 / 11.985 uW, 39 flux lines | VERIFIED | demo B |
| Demo C "rejects the 2-arm CRX-4K" | NOT FOUND in demo output | demo printed other candidates; CRX-4K line not shown |
| Demo D 5 h cooldown, 23 h, 20 h unsat | VERIFIED | demo D |
| "121 capability entries UNKNOWN" | NOT FOUND (not checked; likely stale given catalog growth) | `data/coverage.json` |
| `tests/`: "68 tests" | NOT FOUND (stale) | 105 collected |
| `pytest` runs `lake build` + axiom audit (slow marker) | PARTIAL | `test_lean_proofs.py`, `pytest.ini` marker; passed |
| Scripts listed exist | VERIFIED | `scripts/` (plus many unlisted: build_grid, import_research_v3/v4, v5_*) |

## Executes end to end
Lean binary selftest; `python -m cryolean demo` (A-D); pytest (104/105); axiom audit; full Lean grid summary from the stored DB.

## Incomplete / gaps for a hackathon demo
1. Stale frontend catalog snapshot (only failing test); regenerate before demo.
2. README numbers stale (44 theorems, 26 configs, 11 profiles, 68 tests, 667 records).
3. Demo A's "14 T alternative" ends in NEED_MORE_INFORMATION (honest, but narrate it that way).
4. Claude, Lanyon and desktop window paths not exercised offline; need credentials / GUI.
5. `audit_axioms.py` writes into `lean/`; running it dirties the tree.
6. pytest's doubled `-q` hides the summary line.
