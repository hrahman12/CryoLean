import CryoLean
/-!
Axiom audit (run by `tests/test_lean_proofs.py`):

    lake env lean Audit.lean

Every listed theorem must depend only on Lean's standard axioms
(`propext`, `Classical.choice`, `Quot.sound`) — never on `sorryAx`.
-/
open CryoLean

-- guarantees 1, 5: ACCEPT ⇒ every applicable mandatory requirement and coupled constraint holds
#print axioms verdict_accept_sound
#print axioms accept_all_coupled
-- completeness of ACCEPT and REJECT
#print axioms verdict_accept_complete
#print axioms verdict_accept_iff
#print axioms verdict_reject_sound
#print axioms verdict_reject_complete
-- guarantees 2, 3: missing / unsupported information cannot produce ACCEPT
#print axioms accept_no_unknown
#print axioms missing_capability_unknown
#print axioms unknown_value_never_passes
#print axioms estimate_never_passes
#print axioms no_provenance_never_passes
#print axioms cap_not_usable_missing
-- guarantee 4: a confirmed mandatory failure prevents ACCEPT
#print axioms fail_implies_reject
#print axioms violation_prevents_accept
-- guarantees 6, 7: optional and non-applicable requirements
#print axioms verdict_ignores_optional
#print axioms verdict_ignores_nonapplicable
#print axioms condition_false_not_applicable
-- guarantee 8: installed vs optional accessories
#print axioms not_installed_never_passes
#print axioms unknown_install_never_passes
-- guarantee 9: verdict bound to exact inputs
#print axioms run_binds_inputs
#print axioms verdict_deterministic
#print axioms run_reports_everything
-- guarantees 10, 11: untrusted proposers (AI / Z3) cannot override Lean
#print axioms candidates_accept_sound
#print axioms candidates_verdicts_are_lean
-- guarantee 12: industries are opaque labels
#print axioms verdict_industry_irrelevant
#print axioms verdict_name_irrelevant
-- units, dimensions and exact arithmetic
#print axioms pass_implies_dims_match
#print axioms coupled_pass_dims_match
#print axioms Q.le_scale_left
#print axioms Q.le_scale_right
#print axioms evalExpr_sound
#print axioms evalExpr_complete
#print axioms satisfies_spec_exclusive
