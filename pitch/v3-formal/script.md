# CryoLean v3 · Formal methods: 60-second talk track

**1 · Title (10 s).** CryoLean answers one question: can this cryostat run my experiment? Every answer it gives is a theorem, checked by Lean 4.

**2 · The theorems (17 s).** If Lean says met, every requirement holds, provably. Met exactly when the spec holds. Every rejection rests on a documented violation and on trusted evidence. And new data never flips a decided verdict. That is 128 theorems, zero sorry, 48 axiom-audited, no dependencies, no floating point.

**3 · The self-audit (17 s).** Then we audited our own verifier: 839 declarations, seven judges, 27 flags, each re-checked by the kernel. One was real. An untrusted "not installed" record could force a rejection, and the build was green because the spec had the same hole. We fixed the line and proved three new theorems.

**4 · One judge (16 s).** Claude, Lanyon and Z3 only propose. Lean decides. The Gatekeeper admitted two of seven proofs, and Z3 and Lean agree on 15,795 of 15,795 designs.
