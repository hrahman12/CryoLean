import CryoLean.Checker
import CryoLean.Soundness
/-!
# Information monotonicity

Learning more about a configuration can only resolve NEED_MORE_INFORMATION. It never turns
REQUIREMENTS_MET into DOES_NOT_MEET_REQUIREMENTS, or the other way round, and it never undoes a
decided verdict. "Learning more" means: every record that can decide something is kept; records that
cannot (missing keys, untrusted evidence, unknown install status, unknown values) may be replaced or added.
-/
namespace CryoLean

/-- A capability record that can decide a check: trusted, and either documented as absent
(not fitted / not available) or installed with a documented value. -/
def Informative (c : Capability) : Prop :=
  trustedB c.evidence = true ∧
    (c.install = .optionalNotInstalled ∨ (c.install = .installed ∧ c.value ≠ .unknown))

/-- `cfg'` refines `cfg`: every informative record of `cfg` is found unchanged in `cfg'`. -/
def Refines (cfg cfg' : Configuration) : Prop :=
  ∀ key c, lookup cfg key = some c → Informative c → lookup cfg' key = some c

/-- An outcome that decides something. -/
def Decided (o : Outcome) : Prop := o = .pass ∨ o = .fail ∨ o = .notApplicable

theorem Refines.refl (cfg : Configuration) : Refines cfg cfg := fun _ _ h _ => h

theorem Refines.trans {a b c : Configuration} (h₁ : Refines a b) (h₂ : Refines b c) : Refines a c :=
  fun key x hx hi => h₂ key x (h₁ key x hx hi) hi

section
variable {cfg cfg' : Configuration} {e : Experiment}

theorem checkValue_unknown (k : Constraint) : checkValue k .unknown = .unknown := by
  cases k <;> rfl

/-- A capability check that passes or fails rests on an informative record. -/
theorem checkCapability_decided_informative {k : Constraint} {c : Capability} {o : Outcome}
    (h : checkCapability k c = o) (ho : o = .pass ∨ o = .fail) : Informative c := by
  unfold checkCapability at h
  split at h
  · rename_i hi
    split at h
    · rename_i ht
      exact ⟨ht, .inl hi⟩
    · subst h; simp at ho
  · subst h; simp at ho
  · rename_i hi
    split at h
    · rename_i ht
      refine ⟨ht, .inr ⟨hi, fun hv => ?_⟩⟩
      rw [hv, checkValue_unknown] at h
      subst h; simp at ho
    · subst h; simp at ho

theorem keyOutcome_refines (hr : Refines cfg cfg') {k : Constraint} {key : String}
    (ho : keyOutcome cfg k key = .pass ∨ keyOutcome cfg k key = .fail) :
    keyOutcome cfg' k key = keyOutcome cfg k key := by
  unfold keyOutcome at ho ⊢
  rcases hl : lookup cfg key with _ | c
  · rw [hl] at ho; simp at ho
  · rw [hl] at ho
    rw [hr key c hl (checkCapability_decided_informative rfl ho)]

theorem combineAny_congr_decided {keys : List String} {f g : String → Outcome}
    (hfg : ∀ key ∈ keys, (f key = .pass ∨ f key = .fail) → g key = f key)
    (hd : combineAny (keys.map f) = .pass ∨ combineAny (keys.map f) = .fail) :
    combineAny (keys.map g) = combineAny (keys.map f) := by
  by_cases hp : Outcome.pass ∈ keys.map f
  · obtain ⟨key, hk, hfk⟩ := List.mem_map.1 hp
    have hgk : g key = .pass := by rw [hfg key hk (.inl hfk)]; exact hfk
    have hp' : Outcome.pass ∈ keys.map g := List.mem_map.2 ⟨key, hk, hgk⟩
    rw [(combineAny_pass_iff _).2 hp, (combineAny_pass_iff _).2 hp']
  · have hf : keys.map f ≠ [] ∧ ∀ o ∈ keys.map f, o = .fail := by
      rcases hd with h | h
      · exact absurd ((combineAny_pass_iff _).1 h) hp
      · exact combineAny_fail h
    have hall : ∀ key ∈ keys, g key = .fail := by
      intro key hk
      have hfk : f key = .fail := hf.2 _ (List.mem_map.2 ⟨key, hk, rfl⟩)
      rw [hfg key hk (.inr hfk)]; exact hfk
    have hg : keys.map g ≠ [] ∧ ∀ o ∈ keys.map g, o = .fail := by
      refine ⟨by simpa using hf.1, ?_⟩
      intro o ho
      obtain ⟨key, hk, rfl⟩ := List.mem_map.1 ho
      exact hall key hk
    have hp' : Outcome.pass ∉ keys.map g := by
      intro h
      have := hg.2 _ h
      cases this
    have h1 : combineAny (keys.map f) = .fail := by
      rcases hd with h | h
      · exact absurd ((combineAny_pass_iff _).1 h) hp
      · exact h
    have h2 : combineAny (keys.map g) = .fail := by
      unfold combineAny
      rw [if_neg hp', if_pos hg]
    rw [h1, h2]

theorem evalCond_refines (hr : Refines cfg cfg') {c : Condition}
    (hd : evalCond cfg e c = .holds ∨ evalCond cfg e c = .fails) :
    evalCond cfg' e c = evalCond cfg e c := by
  cases c with
  | capFlag key b =>
    simp only [evalCond] at hd ⊢
    rcases hl : lookup cfg key with _ | x
    · rw [hl] at hd; simp at hd
    · rw [hl] at hd
      dsimp only at hd
      have hi : Informative x := by
        by_cases hn : x.install = .optionalNotInstalled
        · simp only [hn, if_true] at hd
          by_cases ht : trustedB x.evidence = true
          · exact ⟨ht, .inl hn⟩
          · rw [if_neg ht] at hd; simp at hd
        · rw [if_neg hn] at hd
          by_cases hu : usable x = true
          · rw [if_pos hu] at hd
            have hu' : x.install = .installed ∧ trustedB x.evidence = true := by
              simpa [usable] using hu
            refine ⟨hu'.2, .inr ⟨hu'.1, fun hv => ?_⟩⟩
            rw [hv] at hd; simp at hd
          · rw [if_neg hu] at hd; simp at hd
      rw [hr key x hl hi]
  | paramAtMost name q => rfl
  | paramAtLeast name q => rfl

theorem condsResult_refines (hr : Refines cfg cfg') {cs : List Condition}
    (hd : condsResult cfg e cs = .holds ∨ condsResult cfg e cs = .fails) :
    condsResult cfg' e cs = condsResult cfg e cs := by
  by_cases hf : ∃ c ∈ cs, evalCond cfg e c = .fails
  · obtain ⟨c, hc, hcf⟩ := hf
    have hcf' : evalCond cfg' e c = .fails := by rw [evalCond_refines hr (.inr hcf)]; exact hcf
    have h1 : ∃ c ∈ cs, evalCond cfg' e c = .fails := ⟨c, hc, hcf'⟩
    have h2 : ∃ c ∈ cs, evalCond cfg e c = .fails := ⟨c, hc, hcf⟩
    simp only [condsResult, if_pos h1, if_pos h2]
  · have hh : ∀ c ∈ cs, evalCond cfg e c = .holds := by
      by_cases hc : ∀ c ∈ cs, evalCond cfg e c = .holds
      · exact hc
      · exfalso
        unfold condsResult at hd
        rw [if_neg hf, if_neg hc] at hd
        simp at hd
    have hh' : ∀ c ∈ cs, evalCond cfg' e c = .holds := fun c hc => by
      rw [evalCond_refines hr (.inl (hh c hc))]; exact hh c hc
    have hf' : ¬ ∃ c ∈ cs, evalCond cfg' e c = .fails := by
      rintro ⟨c, hc, h⟩
      rw [hh' c hc] at h
      cases h
    simp only [condsResult, if_neg hf, if_neg hf', if_pos hh, if_pos hh']

theorem checkRequirement_refines (hr : Refines cfg cfg') {r : Requirement}
    (hd : Decided (checkRequirement cfg e r)) :
    checkRequirement cfg' e r = checkRequirement cfg e r := by
  unfold checkRequirement at hd ⊢
  cases hc : condsResult cfg e r.conditions with
  | holds =>
    rw [hc] at hd
    rw [condsResult_refines hr (.inl hc), hc]
    have hd' : combineAny (r.keys.map (keyOutcome cfg r.constraint)) = .pass ∨
        combineAny (r.keys.map (keyOutcome cfg r.constraint)) = .fail := by
      rcases hd with h | h | h
      · exact .inl h
      · exact .inr h
      · exact absurd h (combineAny_ne_notApplicable _)
    exact combineAny_congr_decided (fun key _ h => keyOutcome_refines hr h) hd'
  | fails => rw [condsResult_refines hr (.inr hc), hc]
  | unknown => rw [hc] at hd; simp [Decided] at hd

theorem evalExpr_refines (hr : Refines cfg cfg') (x : Expr) :
    ∀ {q : Quantity}, evalExpr cfg e x = .ok q → evalExpr cfg' e x = .ok q := by
  induction x with
  | lit q' => intro q h; exact h
  | param name => intro q h; exact h
  | cap key s =>
    intro q h
    simp only [evalExpr] at h ⊢
    rcases hl : lookup cfg key with _ | c
    · rw [hl] at h; simp at h
    · rw [hl] at h
      dsimp only at h
      by_cases hu : usable c = true
      · rw [if_pos hu] at h
        have hu' : c.install = .installed ∧ trustedB c.evidence = true := by simpa [usable] using hu
        have hv : c.value ≠ .unknown := by
          intro hv; rw [hv] at h; cases s <;> simp [selValue] at h
        rw [hr key c hl ⟨hu'.2, .inr ⟨hu'.1, hv⟩⟩]
        simp only [if_pos hu]
        exact h
      · rw [if_neg hu] at h; simp at h
  | add a b iha ihb =>
    intro q h
    simp only [evalExpr] at h ⊢
    cases ha : evalExpr cfg e a <;> cases hb : evalExpr cfg e b <;> rw [ha, hb] at h <;>
      first | (simp at h; done) | skip
    rename_i x y
    rw [iha ha, ihb hb]
    exact h
  | sub a b iha ihb =>
    intro q h
    simp only [evalExpr] at h ⊢
    cases ha : evalExpr cfg e a <;> cases hb : evalExpr cfg e b <;> rw [ha, hb] at h <;>
      first | (simp at h; done) | skip
    rename_i x y
    rw [iha ha, ihb hb]
    exact h
  | mul a b iha ihb =>
    intro q h
    simp only [evalExpr] at h ⊢
    cases ha : evalExpr cfg e a <;> cases hb : evalExpr cfg e b <;> rw [ha, hb] at h <;>
      first | (simp at h; done) | skip
    rename_i x y
    rw [iha ha, ihb hb]
    exact h
  | neg a iha =>
    intro q h
    simp only [evalExpr] at h ⊢
    cases ha : evalExpr cfg e a <;> rw [ha] at h <;> first | (simp at h; done) | skip
    rename_i x
    rw [iha ha]
    exact h

theorem checkLe_refines (hr : Refines cfg cfg') {a b : Expr}
    (hd : checkLe cfg e a b = .pass ∨ checkLe cfg e a b = .fail) :
    checkLe cfg' e a b = checkLe cfg e a b := by
  unfold checkLe at hd ⊢
  cases ha : evalExpr cfg e a <;> cases hb : evalExpr cfg e b <;> rw [ha, hb] at hd <;>
    first | (simp at hd; done) | skip
  rename_i x y
  rw [evalExpr_refines hr a ha, evalExpr_refines hr b hb]

theorem validityOutcome_cases (vs : List (Expr × Expr)) :
    validityOutcome cfg e vs = .pass ∨ validityOutcome cfg e vs = .unknown ∨
      validityOutcome cfg e vs = .unsupported := by
  unfold validityOutcome
  split
  · exact .inl rfl
  · split
    · exact .inr (.inl rfl)
    · exact .inr (.inr rfl)

theorem validityOutcome_refines_pass (hr : Refines cfg cfg') {vs : List (Expr × Expr)}
    (h : validityOutcome cfg e vs = .pass) : validityOutcome cfg' e vs = .pass := by
  unfold validityOutcome at h ⊢
  by_cases hall : ∀ p ∈ vs, checkLe cfg e p.1 p.2 = .pass
  · have hall' : ∀ p ∈ vs, checkLe cfg' e p.1 p.2 = .pass := fun p hp => by
      rw [checkLe_refines hr (.inl (hall p hp))]; exact hall p hp
    rw [if_pos hall']
  · rw [if_neg hall] at h
    split at h <;> simp at h

theorem checkCoupled_refines (hr : Refines cfg cfg') {c : Coupled}
    (hd : Decided (checkCoupled cfg e c)) :
    checkCoupled cfg' e c = checkCoupled cfg e c := by
  unfold checkCoupled at hd ⊢
  cases hc : condsResult cfg e c.conditions with
  | holds =>
    rw [hc] at hd
    rw [condsResult_refines hr (.inl hc), hc]
    rcases validityOutcome_cases (cfg := cfg) (e := e) c.validity with hv | hv | hv
    · rw [validityOutcome_refines_pass hr hv, hv]
      rw [hv] at hd
      have hd' : checkLe cfg e c.lhs c.rhs = .pass ∨ checkLe cfg e c.lhs c.rhs = .fail := by
        rcases hd with h | h | h
        · exact .inl h
        · exact .inr h
        · exact absurd h (checkLe_ne_notApplicable _ _ _ _)
      exact checkLe_refines hr hd'
    · rw [hv] at hd; simp [Decided] at hd
    · rw [hv] at hd; simp [Decided] at hd
  | fails => rw [condsResult_refines hr (.inr hc), hc]
  | unknown => rw [hc] at hd; simp [Decided] at hd

/-- **Information monotonicity.** If `cfg'` refines `cfg` (every record of `cfg` that can decide a check
is kept), then a decided verdict on `cfg` is the verdict on `cfg'`: learning more can only resolve
NEED_MORE_INFORMATION. -/
theorem verdict_refines (hr : Refines cfg cfg') (hd : verdict cfg e ≠ .needMoreInfo) :
    verdict cfg' e = verdict cfg e := by
  by_cases hconf : e.confirmed = false
  · exact absurd (by unfold verdict; rw [if_pos hconf]) hd
  · have hv : ∀ c, verdict c e = (if Outcome.fail ∈ outcomes c e then .reject
        else if (∀ o ∈ outcomes c e, o = .pass ∨ o = .notApplicable) ∧ .pass ∈ outcomes c e then .accept
        else .needMoreInfo) := fun c => by unfold verdict; rw [if_neg hconf]
    rw [hv cfg] at hd
    rw [hv cfg', hv cfg]
    by_cases hf : Outcome.fail ∈ outcomes cfg e
    · have hf' : Outcome.fail ∈ outcomes cfg' e := by
        unfold outcomes at hf ⊢
        rcases List.mem_append.1 hf with h | h
        · obtain ⟨r, hr', hro⟩ := List.mem_map.1 h
          refine List.mem_append.2 (.inl (List.mem_map.2 ⟨r, hr', ?_⟩))
          rw [checkRequirement_refines hr (.inr (.inl hro))]; exact hro
        · obtain ⟨c, hc', hco⟩ := List.mem_map.1 h
          refine List.mem_append.2 (.inr (List.mem_map.2 ⟨c, hc', ?_⟩))
          rw [checkCoupled_refines hr (.inr (.inl hco))]; exact hco
      rw [if_pos hf, if_pos hf']
    · rw [if_neg hf] at hd
      by_cases ha : (∀ o ∈ outcomes cfg e, o = .pass ∨ o = .notApplicable) ∧ .pass ∈ outcomes cfg e
      · have hdec : ∀ o ∈ outcomes cfg e, Decided o := fun o ho => by
          rcases ha.1 o ho with h | h
          · exact .inl h
          · exact .inr (.inr h)
        have heq : outcomes cfg' e = outcomes cfg e := by
          unfold outcomes
          have h1 : (relevantReqs e).map (checkRequirement cfg' e) = (relevantReqs e).map (checkRequirement cfg e) := by
            apply List.map_congr_left
            intro r hr'
            exact checkRequirement_refines hr
              (hdec _ (List.mem_append.2 (.inl (List.mem_map.2 ⟨r, hr', rfl⟩))))
          have h2 : (relevantCoupled e).map (checkCoupled cfg' e) = (relevantCoupled e).map (checkCoupled cfg e) := by
            apply List.map_congr_left
            intro c hc
            exact checkCoupled_refines hr
              (hdec _ (List.mem_append.2 (.inr (List.mem_map.2 ⟨c, hc, rfl⟩))))
          rw [h1, h2]
        rw [heq]
      · rw [if_neg ha] at hd; exact absurd rfl hd

/-- An accepted pair stays accepted when more is learned. -/
theorem accept_preserved_by_refinement (hr : Refines cfg cfg') (h : verdict cfg e = .accept) :
    verdict cfg' e = .accept := by
  rw [verdict_refines hr (by rw [h]; decide), h]

/-- A rejected pair stays rejected when more is learned. -/
theorem reject_preserved_by_refinement (hr : Refines cfg cfg') (h : verdict cfg e = .reject) :
    verdict cfg' e = .reject := by
  rw [verdict_refines hr (by rw [h]; decide), h]

/-- If the better-documented configuration still needs more information, so did the less documented one:
removing information can never create a decided verdict. -/
theorem needMoreInfo_of_refined (hr : Refines cfg cfg') (h : verdict cfg' e = .needMoreInfo) :
    verdict cfg e = .needMoreInfo := by
  by_cases hne : verdict cfg e = .needMoreInfo
  · exact hne
  · rw [verdict_refines hr hne] at h
    exact absurd h hne

end
end CryoLean
