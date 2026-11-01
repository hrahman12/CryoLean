# Forensics audit of the trusted Lean core

CryoLean's trusted kernel (`lean/CryoLean/*.lean`) is audited with
[for-all-dev/forensics](https://github.com/for-all-dev/forensics) at commit `e5b80ca2`.
A green `lake build` only says the kernel accepted the proofs. Forensics checks whether the
statements mean what they claim and whether anything rests on an escape hatch.

## 1. Static extractor

Run it again with:

```bash
python scripts/run_forensics.py
```

It builds the forensics extractor (core-only Lean, toolchain v4.35.0), runs it over `CryoLean`, and
writes [cryolean-forensics.json](cryolean-forensics.json) and [summary.json](summary.json).

| Check | Result |
| --- | --- |
| Declarations extracted | 839 |
| Depending on `sorryAx`, a `native_decide` axiom or any non-standard axiom | 0 |
| Statement smells (trivial conclusion, vacuous or contradictory hypotheses, ...) | 0 |
| Flags (`partial`, `opaque`, `implemented_by`, `extern`, `unsafe`) | 0 |

The first run flagged one declaration: the JSON expression decoder `exprFromJson` was `partial`, so
nothing could be proved about it. It is now total, with a nesting bound of 64.

## 2. The seven judge indicators

Each indicator was run with the forensics protocol (`app/judges/indicators/<id>/prompt.md` and
`schema.json`). Every flagged item was re-elaborated with `lake env lean` in a scratch file before it
was accepted. Theorem-level indicators used forensics' own sampling rule: sha256 order, seed 0, 40 targets.

| Indicator | Judged | Flagged | Outcome |
| --- | --- | --- | --- |
| unnecessary-hypotheses | 40 theorems | 0 | Every hypothesis is needed. |
| duplicates-dependency | 40 theorems | 2 | `Q.add_den_pos` and `Q.mul_den_pos` now use `Nat.mul_pos` directly. `mem_relevantReqs` kept as a named lemma. |
| definition-fidelity | 49 definitions | 16 | All 16 were missing docstrings. Docstrings added. |
| vacuity-and-misstatement | 4 files | 3 | **Real soundness gap, fixed.** See below. |
| statement-generality | 4 files | 2 | Added `untrusted_never_passes` and `pass_dims_all_match`, the general forms. |
| repeated-proof-machinery | 4 files | 2 | Noted. The scale lemmas and the two filter-invariance proofs are short, so they were left as they are. |
| readable-proof-simplification | 2 files | 2 | `den_pos` proofs simplified. The rest were judged a matter of taste. |

### The soundness gap the vacuity judge found

An optional accessory recorded as "not installed" made a requirement **fail** whatever the record's
provenance. So a record with no source, or only an inferred estimate, could produce
DOES_NOT_MEET_REQUIREMENTS. The judge confirmed it in Lean: `verdict` returned `reject` on a
configuration whose only evidence was `unknown`.

The fix:

- `checkCapability` (Checker.lean) now requires trusted evidence for the "not fitted" claim on both
  the pass and the fail path. Untrusted records give `unknown`.
- `ViolatesKey` (Spec.lean) now requires `TrustedEvidence` on its not-installed branch.
- New theorems `fail_needs_trusted`, `untrusted_never_passes` and `untrusted_never_fails`.
  Together they say every rejection rests on trusted evidence, and untrusted records only ever give
  NEED_MORE_INFORMATION.
- The Python Z3 mirror (`smt.key_status`) was changed the same way.

### Statement fixes

- `pass_implies_dims_match` only covered `atLeast` against a maximum. `pass_dims_all_match` now covers
  every numeric constraint shape.
- `verdict_deterministic` is plain congruence. Its docstring now says so, and the verification scope no
  longer presents it as a deep guarantee.

All 44 audited theorems still depend only on `propext`, `Classical.choice` and `Quot.sound`
(`python scripts/audit_axioms.py`, cached in `lean/audit-axioms.json`).
