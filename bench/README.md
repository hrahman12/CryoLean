# CryoLean vs the regular way

Is CryoLean better than checking a cryostat the regular way? This folder answers with measurements whose right answer
does not come from CryoLean, plus Lean theorems that explain the measurements.

```bash
cd lean && lake build && cd ..          # the checker CryoLean ships, unchanged
python -m cryolean build-db
python bench/vs_regular.py              # ~2 min: all tests + compiles lean/VsRegular.lean
python bench/report.py                  # RESULTS.md, figures/, vs_regular_way.html
```

| File | What it is |
|---|---|
| `regular_way.py` | The regular way, three versions: spec-sheet checklist, careful spreadsheet, physics-aware float script. Same input documents as the Lean checker. Not verified, on purpose. |
| `vs_regular.py` | The tests (T0 catalog head-to-head, T1 hide one line, T2 borrowed number, T3 qubit heat-budget sweep, T4 project history, T5 fault injection). |
| `../lean/VsRegular.lean` | The checklist written in Lean and 13 theorems: no checker that is never wrong can say YES where CryoLean does not; the checklist says YES to a blank sheet, flips NO to YES when a line is hidden, believes a guessed 14 T, and misses the 14.592 µW > 12 µW wiring heat budget. Outside the trusted library, so the shipped checker is untouched. |
| `report.py` | Writes `RESULTS.md`, `figures/` and `vs_regular_way.html` from `results/*.json`. No number is typed by hand. |
| `RESULTS.md` | The numbers. |

Headline (from `results/summary.json`): on T1–T4 the checklist approved 16,966 setups the evidence rules out, the careful spreadsheet 225, the physics-aware script 197, CryoLean 0.
