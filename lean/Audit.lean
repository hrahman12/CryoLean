import CryoLean
/-!
Axiom audit (run by `tests/test_lean_proofs.py`):

    lake env lean Audit.lean

Every soundness theorem must depend only on Lean's standard axioms
(`propext`, `Classical.choice`, `Quot.sound`) — never on `sorryAx`.
-/
open CryoLean

#print axioms verdict_accept_sound
#print axioms verdict_accept_complete
#print axioms verdict_accept_iff
#print axioms verdict_reject_sound
#print axioms accept_no_unknown
#print axioms fail_implies_reject
#print axioms missing_capability_unknown
#print axioms not_installed_never_passes
#print axioms unknown_install_never_passes
#print axioms estimate_never_passes
#print axioms no_provenance_never_passes
#print axioms unknown_value_never_passes
#print axioms pass_implies_units_match
#print axioms unconfirmed_not_accept
#print axioms empty_not_accept
#print axioms satisfies_violates_exclusive
#print axioms run_binds_inputs
#print axioms verdict_industry_irrelevant
#print axioms checks_cover_requirements
