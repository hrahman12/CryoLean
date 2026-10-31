import CryoLean.Spec
/-!
# Soundness of the generic checker

Every theorem here is about the *fixed* executable checker in `CryoLean.Checker`
and the *independent* specification in `CryoLean.Spec`.  None of them mentions
an industry, a manufacturer, or an experiment: they hold for every data record
that decodes into the model, which is what makes the engine universal.

Guarantee map (see `VERIFICATION_SCOPE.md`):

| Guarantee                                             | Theorem                              |
|-------------------------------------------------------|--------------------------------------|
| ACCEPT ⇒ every mandatory requirement is satisfied     | `verdict_accept_sound`               |
| ACCEPT ⇒ every mandatory requirement was checked=pass | `accept_all_mandatory_pass`          |
| Missing information cannot produce ACCEPT             | `accept_no_unknown`, `missing_capability_unknown` |
| Unsupported requirements cannot produce ACCEPT        | `accept_no_unknown`                  |
| A confirmed incompatibility cannot produce ACCEPT     | `fail_implies_reject`                |
| REJECT ⇒ a documented conflict exists                 | `verdict_reject_sound`               |
| Installed vs optional accessories are distinguished   | `not_installed_never_passes`         |
| Estimates are never treated as specifications         | `estimate_never_passes`              |
| Units are never silently converted                    | `pass_implies_units_match`           |
| Unconfirmed / empty profiles are never accepted       | `unconfirmed_not_accept`, `empty_not_accept` |
| Verdict is bound to the exact inputs                  | `run_binds_inputs`, `verdict_deterministic` |
| The industry label cannot influence the verdict       | `verdict_industry_irrelevant`        |
| Satisfaction and violation are mutually exclusive     | `satisfies_violates_exclusive`       |
| ACCEPT exactly characterises the spec (completeness)  | `verdict_accept_iff`                 |
-/

namespace CryoLean

/-! ## Value-level soundness -/

theorem checkValue_pass_sound {c : Constraint} {v : CapValue}
    (h : checkValue c v = .pass) : ValueMeets c v := by
  cases c <;> cases v <;> simp only [checkValue] at h <;> (try cases h)
  case pointWithin.range q lo hi =>
    split at h
    · split at h
      · rename_i hu hv; exact .pointWithin hu.1 hu.2 hv.1 hv.2
      · cases h
    · cases h
  case rangeWithin.range rlo rhi lo hi =>
    split at h
    · split at h
      · rename_i hu hv; exact .rangeWithin hu.1 hu.2.1 hu.2.2.1 hu.2.2.2 hv.1 hv.2
      · cases h
    · cases h
  case atLeast.range q lo hi =>
    split at h
    · split at h
      · rename_i hu hv; exact .atLeastRange hu hv
      · cases h
    · cases h
  case atLeast.max q m =>
    split at h
    · split at h
      · rename_i hu hv; exact .atLeastMax hu hv
      · cases h
    · cases h
  case atMost.range q lo hi =>
    split at h
    · split at h
      · rename_i hu hv; exact .atMostRange hu hv
      · cases h
    · cases h
  case atMost.min q m =>
    split at h
    · split at h
      · rename_i hu hv; exact .atMostMin hu hv
      · cases h
    · cases h
  case present.flag b =>
    cases b
    · cases h
    · exact .present
  case countAtLeast.count n m =>
    split at h
    · rename_i hv; exact .countAtLeast hv
    · cases h

theorem checkValue_fail_sound {c : Constraint} {v : CapValue}
    (h : checkValue c v = .fail) : ValueFails c v := by
  cases c <;> cases v <;> simp only [checkValue] at h <;> (try cases h)
  case pointWithin.range q lo hi =>
    split at h
    · split at h
      · cases h
      · rename_i hu hv
        refine .pointWithin hu.1 hu.2 ?_
        omega
    · cases h
  case rangeWithin.range rlo rhi lo hi =>
    split at h
    · split at h
      · cases h
      · rename_i hu hv
        refine .rangeWithin hu.1 hu.2.1 hu.2.2.1 hu.2.2.2 ?_
        omega
    · cases h
  case atLeast.range q lo hi =>
    split at h
    · split at h
      · cases h
      · rename_i hu hv; exact .atLeastRange hu (by omega)
    · cases h
  case atLeast.max q m =>
    split at h
    · split at h
      · cases h
      · rename_i hu hv; exact .atLeastMax hu (by omega)
    · cases h
  case atMost.range q lo hi =>
    split at h
    · split at h
      · cases h
      · rename_i hu hv; exact .atMostRange hu (by omega)
    · cases h
  case atMost.min q m =>
    split at h
    · split at h
      · cases h
      · rename_i hu hv; exact .atMostMin hu (by omega)
    · cases h
  case present.flag b =>
    cases b
    · exact .present
    · cases h
  case countAtLeast.count n m =>
    split at h
    · cases h
    · rename_i hv; exact .countAtLeast (by omega)

/-- Completeness at the value level: whenever the spec holds the checker says pass. -/
theorem checkValue_pass_complete {c : Constraint} {v : CapValue}
    (h : ValueMeets c v) : checkValue c v = .pass := by
  cases h <;> simp [checkValue, *]

/-- A passing comparison always happened in identical units (no silent conversion). -/
theorem pass_implies_units_match {q m : Quantity}
    (h : checkValue (.atLeast q) (.max m) = .pass) : m.unit = q.unit := by
  cases checkValue_pass_sound h; assumption

theorem pass_implies_units_match_point {q lo hi : Quantity}
    (h : checkValue (.pointWithin q) (.range lo hi) = .pass) :
    lo.unit = q.unit ∧ hi.unit = q.unit := by
  cases checkValue_pass_sound h; exact ⟨‹_›, ‹_›⟩

/-- An explicitly unknown value never passes. -/
theorem unknown_value_never_passes (c : Constraint) : checkValue c .unknown ≠ .pass := by
  cases c <;> simp [checkValue]

/-! ## Capability-level soundness -/

theorem checkCapability_pass_sound {r : Requirement} {c : Capability}
    (h : checkCapability r c = .pass) :
    c.install = .installed ∧ TrustedEvidence c.evidence ∧ ValueMeets r.constraint c.value := by
  revert h
  cases hi : c.install <;> cases he : c.evidence <;>
    simp [checkCapability, hi, he, TrustedEvidence] <;>
    exact checkValue_pass_sound

theorem checkCapability_fail_sound {r : Requirement} {c : Capability}
    (h : checkCapability r c = .fail) :
    c.install = .optionalNotInstalled ∨
      (c.install = .installed ∧ TrustedEvidence c.evidence ∧ ValueFails r.constraint c.value) := by
  revert h
  cases hi : c.install <;> cases he : c.evidence <;>
    simp [checkCapability, hi, he, TrustedEvidence] <;>
    exact checkValue_fail_sound

/-- An optional accessory that is not fitted to this configuration never passes. -/
theorem not_installed_never_passes {r : Requirement} {c : Capability}
    (h : c.install = .optionalNotInstalled) : checkCapability r c ≠ .pass := by
  simp [checkCapability, h]

/-- Unknown installation status never passes. -/
theorem unknown_install_never_passes {r : Requirement} {c : Capability}
    (h : c.install = .unknown) : checkCapability r c ≠ .pass := by
  simp [checkCapability, h]

/-- An inferred estimate is never treated as a verified specification. -/
theorem estimate_never_passes {r : Requirement} {c : Capability}
    (h : c.evidence = .inferredEstimate) : checkCapability r c ≠ .pass := by
  cases hi : c.install <;> simp [checkCapability, hi, h]

/-- A fact with no recorded provenance never passes. -/
theorem no_provenance_never_passes {r : Requirement} {c : Capability}
    (h : c.evidence = .unknown) : checkCapability r c ≠ .pass := by
  cases hi : c.install <;> simp [checkCapability, hi, h]

/-! ## Requirement-level soundness -/

theorem checkRequirement_pass_sound {cfg : Configuration} {r : Requirement}
    (h : checkRequirement cfg r = .pass) : Satisfies cfg r := by
  unfold checkRequirement at h
  split at h
  · cases h
  · rename_i c hc
    obtain ⟨h₁, h₂, h₃⟩ := checkCapability_pass_sound h
    exact ⟨c, hc, h₁, h₂, h₃⟩

theorem checkRequirement_fail_sound {cfg : Configuration} {r : Requirement}
    (h : checkRequirement cfg r = .fail) : Violates cfg r := by
  unfold checkRequirement at h
  split at h
  · cases h
  · rename_i c hc
    exact ⟨c, hc, checkCapability_fail_sound h⟩

/-- A requirement whose key has no recorded capability is `unknown`, never `pass`. -/
theorem missing_capability_unknown {cfg : Configuration} {r : Requirement}
    (h : lookup cfg r.key = none) : checkRequirement cfg r = .unknown := by
  simp [checkRequirement, h]

theorem checkRequirement_pass_complete {cfg : Configuration} {r : Requirement}
    (h : Satisfies cfg r) : checkRequirement cfg r = .pass := by
  obtain ⟨c, hc, hi, he, hv⟩ := h
  have hcv := checkValue_pass_complete hv
  cases hev : c.evidence <;> simp [hev, TrustedEvidence] at he <;>
    simp [checkRequirement, hc, checkCapability, hi, hev, hcv]

/-! ## Mutual exclusion of the spec -/

theorem valueMeets_valueFails_exclusive {c : Constraint} {v : CapValue}
    (hm : ValueMeets c v) (hf : ValueFails c v) : False := by
  cases hm <;> cases hf <;> omega

theorem satisfies_violates_exclusive {cfg : Configuration} {r : Requirement}
    (hs : Satisfies cfg r) (hv : Violates cfg r) : False := by
  obtain ⟨c, hc, hi, _, hm⟩ := hs
  obtain ⟨c', hc', hbad⟩ := hv
  rw [hc] at hc'
  cases hc'
  rcases hbad with hopt | ⟨_, _, hf⟩
  · rw [hi] at hopt; cases hopt
  · exact valueMeets_valueFails_exclusive hm hf

/-! ## Verdict-level soundness -/

/-- Unpacking lemma: what `verdict = accept` tells us about the executable checks. -/
theorem accept_all_mandatory_pass {cfg : Configuration} {e : Experiment}
    (h : verdict cfg e = .accept) :
    e.confirmed = true ∧ mandatoryReqs e ≠ [] ∧
      ∀ r ∈ mandatoryReqs e, checkRequirement cfg r = .pass := by
  unfold verdict at h
  split at h
  · cases h
  · split at h
    · cases h
    · split at h
      · cases h
      · split at h
        · rename_i hconf hne _ hall
          refine ⟨?_, ?_, ?_⟩
          · cases hc : e.confirmed
            · exact absurd hc hconf
            · rfl
          · intro hnil; simp [hnil] at hne
          · intro r hr
            have := List.all_eq_true.mp hall r hr
            simpa using this
        · cases h

/-- **Main soundness theorem.** ACCEPT implies the independent specification. -/
theorem verdict_accept_sound {cfg : Configuration} {e : Experiment}
    (h : verdict cfg e = .accept) : AcceptSpec cfg e := by
  obtain ⟨hc, hne, hall⟩ := accept_all_mandatory_pass h
  exact ⟨hc, hne, fun r hr => checkRequirement_pass_sound (hall r hr)⟩

/-- Missing or unsupported information on any mandatory requirement blocks ACCEPT. -/
theorem accept_no_unknown {cfg : Configuration} {e : Experiment}
    (h : verdict cfg e = .accept) :
    ∀ r ∈ mandatoryReqs e,
      checkRequirement cfg r ≠ .unknown ∧ checkRequirement cfg r ≠ .unsupported := by
  intro r hr
  have := (accept_all_mandatory_pass h).2.2 r hr
  rw [this]
  exact ⟨by decide, by decide⟩

/-- A single mandatory requirement with a documented conflict forces REJECT. -/
theorem fail_implies_reject {cfg : Configuration} {e : Experiment}
    (hconf : e.confirmed = true)
    (h : ∃ r ∈ mandatoryReqs e, checkRequirement cfg r = .fail) :
    verdict cfg e = .reject := by
  obtain ⟨r, hr, hf⟩ := h
  unfold verdict
  have hne : (mandatoryReqs e).isEmpty = false := by
    cases hm : mandatoryReqs e
    · rw [hm] at hr; cases hr
    · rfl
  have hany : (mandatoryReqs e).any (fun r => checkRequirement cfg r == .fail) = true :=
    List.any_eq_true.mpr ⟨r, hr, by rw [hf]; decide⟩
  simp [hconf, hne, hany]

/-- REJECT implies a documented violation of a mandatory requirement. -/
theorem verdict_reject_sound {cfg : Configuration} {e : Experiment}
    (h : verdict cfg e = .reject) : RejectSpec cfg e := by
  unfold verdict at h
  split at h
  · cases h
  · split at h
    · cases h
    · split at h
      · rename_i hconf _ hany
        obtain ⟨r, hr, hf⟩ := List.any_eq_true.mp hany
        refine ⟨?_, r, hr, checkRequirement_fail_sound (by simpa using hf)⟩
        cases hc : e.confirmed
        · exact absurd hc hconf
        · rfl
      · split at h <;> cases h

/-- An experiment whose requirements the user has not confirmed is never accepted. -/
theorem unconfirmed_not_accept {cfg : Configuration} {e : Experiment}
    (h : e.confirmed = false) : verdict cfg e ≠ .accept := by
  simp [verdict, h]

/-- An experiment with no mandatory requirements is never accepted (no vacuous passes). -/
theorem empty_not_accept {cfg : Configuration} {e : Experiment}
    (h : mandatoryReqs e = []) : verdict cfg e ≠ .accept := by
  intro hacc
  exact (accept_all_mandatory_pass hacc).2.1 h

/-- Completeness: if the specification holds, the checker accepts. -/
theorem verdict_accept_complete {cfg : Configuration} {e : Experiment}
    (h : AcceptSpec cfg e) : verdict cfg e = .accept := by
  obtain ⟨hconf, hne, hall⟩ := h
  have hpass : ∀ r ∈ mandatoryReqs e, checkRequirement cfg r = .pass :=
    fun r hr => checkRequirement_pass_complete (hall r hr)
  have hnotempty : (mandatoryReqs e).isEmpty = false := by
    cases hm : mandatoryReqs e
    · exact absurd hm hne
    · rfl
  have hnoFail : (mandatoryReqs e).any (fun r => checkRequirement cfg r == .fail) = false := by
    rw [Bool.eq_false_iff]
    intro hany
    obtain ⟨r, hr, hf⟩ := List.any_eq_true.mp hany
    rw [hpass r hr] at hf
    exact absurd hf (by decide)
  have hallPass : (mandatoryReqs e).all (fun r => checkRequirement cfg r == .pass) = true :=
    List.all_eq_true.mpr (fun r hr => by rw [hpass r hr]; decide)
  simp [verdict, hconf, hnotempty, hnoFail, hallPass]

/-- ACCEPT holds exactly when the independent specification holds. -/
theorem verdict_accept_iff (cfg : Configuration) (e : Experiment) :
    verdict cfg e = .accept ↔ AcceptSpec cfg e :=
  ⟨verdict_accept_sound, verdict_accept_complete⟩

/-! ## Binding and universality -/

/-- The verdict is a pure function of the exact configuration and experiment. -/
theorem verdict_deterministic {cfg cfg' : Configuration} {e e' : Experiment}
    (h₁ : cfg = cfg') (h₂ : e = e') : verdict cfg e = verdict cfg' e' := by
  subst h₁; subst h₂; rfl

/-- The emitted result carries the ids of exactly the inputs it was computed from. -/
theorem run_binds_inputs (cfg : Configuration) (e : Experiment) :
    (run cfg e).configurationId = cfg.id ∧
    (run cfg e).equipmentId = cfg.equipmentId ∧
    (run cfg e).experimentId = e.id ∧
    (run cfg e).verdict = verdict cfg e :=
  ⟨rfl, rfl, rfl, rfl⟩

/-- The industry label is opaque to the checker: relabelling an experiment with
any industry (including one never seen before) cannot change the verdict.
This is what "new industries cannot bypass the verification gate" means formally. -/
theorem verdict_industry_irrelevant (cfg : Configuration) (e : Experiment) (s : String) :
    verdict cfg { e with industry := s } = verdict cfg e := rfl

/-- Likewise the experiment's display name is irrelevant. -/
theorem verdict_name_irrelevant (cfg : Configuration) (e : Experiment) (s : String) :
    verdict cfg { e with name := s } = verdict cfg e := rfl

/-- Every check reported in a result is the check of a requirement of the
experiment, computed by the same `checkRequirement` the verdict used. -/
theorem checks_cover_requirements (cfg : Configuration) (e : Experiment) :
    (run cfg e).checks.map (·.requirement) = e.requirements := by
  simp [run, checkAll, Function.comp_def]

end CryoLean
