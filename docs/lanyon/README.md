# Lanyon AI in CryoLean

[Lanyon](https://lanyon.ai) turns a physics prompt into a specification, certifies it with an exported Lean and Rocq proof,
compiles it to C, and runs the simulation. CryoLean calls it through `cryolean/lanyon.py`, using the pinned client
`.tools/lanyon/lanyon-cli.pyz` (SHA-256 `34d8c73f…886d`).

A Lanyon result becomes CryoLean evidence with status `certified_simulation` only when all three hold:

1. the session log has a `proof.certified` event and no `proof.discrepancy_detected` event;
2. the exported `proof-*.lean` passes the Gatekeeper: it compiles, has no `sorry`/`axiom`/`native_decide`, and
   `#print axioms` lists only `propext`, `Classical.choice` and `Quot.sound`;
3. the proof is admitted to the rule Registry, and the evidence record cites it.

Otherwise the result is an `inferred_estimate`, which the Lean checker never counts as a pass or a fail.

Running Lanyon sends the prompt to Lanyon's servers on Modal. CryoLean only runs it when asked:

```bash
python -c "from cryolean import lanyon; print(lanyon.run(open('research/lanyon/problem.txt').read(), open('research/lanyon/instructions.txt').read(), name='heat_rod'))"
```

From the frontend, call `run_lanyon_model(problem, instructions)`, then read `import`.

## First session: heat flow along a sample rod

Session `81d0a139-dc26-4d67-9a00-360945d23987`, files in [session-81d0a139/](session-81d0a139/).

The prompt was 1D transient heat diffusion `u_t = α u_xx` on a rod with the cold end on the cryostat stage and a heater
at the warm end, discretised with conservative finite volumes. The property asked for was a maximum principle, which bounds
the temperature difference across the sample.

| Stage | Result |
| --- | --- |
| specify | Succeeded. Specification `specification-67d6f88ec23a.rkt`. |
| verify | Succeeded. Certificate `43962e75-ee93-5650-a4ca-6b2912e36809`, status `certified`, kind `lanyon_symbolic`. Lean proof `proof-819d111ce6f9.lean` (Mathlib, 25 theorems and lemmas, no `sorry`) and Rocq proof `proof_9b839e7436a2.v`. |
| compile | Failed on Lanyon's side: gcc rejected the generated C (`domain_rejection`). |
| simulate | Not run, because compile failed. |

### Gatekeeper result: refused

The proof was compiled in the Mathlib workspace (`.tools/mathlib-gate`, Mathlib `v4.35.0`, same Lean toolchain as CryoLean).
It does not compile: Lean reports 54 errors.

| Error | Count | Example |
| --- | --- | --- |
| Unknown identifier | 38 | `f`, `f_L`, `f_R` in the minmod reconstruction (line 453) and `f_Rx`, `f_Lx` in the interface gradient, which no `let` defines |
| Unsolved goals | 12 | tactic proofs that stop short |
| `ring_nf` made no progress, and others | 4 | lines 483 and 487 |

The unknown identifiers are errors in the exported text itself, not a Mathlib version difference. So Lanyon's
`certified` status rests on its own symbolic checker, and the exported Lean file is not a proof Lean accepts.

This is the case the Gatekeeper exists for. The session stays `inferred_estimate`, and nothing entered the Registry.
To reproduce:

```bash
python -c "from cryolean.catalog import Catalog; from cryolean import lanyon; print(lanyon.import_session(Catalog(), 'research/lanyon/runs/20261101T021635Z_heat_rod_max_principle')['why_not_certified'])"
```

## What this means for verdicts

No CryoLean verdict uses this session. There was no simulation output, and the proof was refused, so no capability
record was created. The run shows the whole path working: CryoLean ran Lanyon, read the certificate, downloaded the
proof, compiled it, and refused it with Lean's reasons.
