# CryoLean v4 · Physics: 60-second talk track

**1 · Title (10 s).** CryoLean checks whether a cryostat can run your experiment, before the cooldown rather than at 10 millikelvin. It covers heat budgets, cooldown schedules and Lean 4 proofs.

**2 · Coupled heat (17 s).** Take 50-qubit wiring on a Bluefors LD400. Base temperature passes and the line count passes. Together, those lines put 14.592 microwatts into a mixing chamber that removes 12. Z3 suggests 39 flux lines, and Lean re-checks the fix at 11.985.

**3 · One cooldown (17 s).** Cold time is expensive, so we pack one run. Lean rejects the 10-tesla experiment. Z3 fits the other three after a 5-hour cooldown, finishing at 23 hours, and Lean proves the schedule valid. Lean and an independent checker agreed on 400 of 400 tampered schedules.

**4 · Missing data (16 s).** We store unknowns as unknowns: 665 entries. In 188,760 checks with specs deleted, nothing became a pass. Missing data only ever means "need more information".
