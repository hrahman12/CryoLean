import CryoLean.Soundness
/-!
# Campaign schedules (`validSchedule`)

Z3 packs several experiments into one cryostat run (an UNTRUSTED proposal).  This
module is the trusted check of such a proposal: a schedule is valid only if

* every scheduled experiment is ACCEPTED by the proven verdict on this exact
  configuration (so infeasible experiments can never be scheduled),
* every slot starts after the configuration's documented cooldown time and ends
  (start + the experiment's `run_duration` parameter) within the run length,
* slots are pairwise disjoint,
* all times are exact rationals in seconds (dimension checked).
-/

namespace CryoLean

/-- One proposed slot: which experiment starts when (seconds from the start of the run). -/
structure Slot where
  experimentId : String
  start        : Q
deriving Repr, Inhabited

/-- A slot resolved against its experiment: start and duration in seconds. -/
structure Placed where
  experimentId : String
  start        : Q
  dur          : Q
deriving Repr, Inhabited

def secDim : Dim := { s := 1 }

def Placed.stop (p : Placed) : Q := Q.add p.start p.dur

/-- The documented cooldown time of the configuration (a `min`-shaped bound, lower is better). -/
def cooldownOf (cfg : Configuration) : Option Quantity :=
  match lookup cfg "cooldown_time.max" with
  | some c => if usable c then (match c.value with | .min q => some q | _ => none) else none
  | none => none

/-- The experiment's trusted `run_duration` parameter, in seconds. -/
def durationOf (e : Experiment) : Option Q :=
  match paramValue e "run_duration" with
  | some q => if q.dim = secDim ∧ 0 < q.val.den then some q.val else none
  | none => none

/-- Pair slots with experiments in order; ids must match and every duration must be known. -/
def resolve : List Experiment → List Slot → Option (List Placed)
  | [], [] => some []
  | e :: es, s :: ss =>
      if s.experimentId = e.id then
        match durationOf e, resolve es ss with
        | some d, some rest => some (⟨s.experimentId, s.start, d⟩ :: rest)
        | _, _ => none
      else none
  | _, _ => none

/-- Two placed slots do not overlap. -/
def Disjoint (a b : Placed) : Prop := Q.le a.stop b.start ∨ Q.le b.stop a.start

instance (a b : Placed) : Decidable (Disjoint a b) := by unfold Disjoint; infer_instance

/-- **Specification** of a valid schedule. -/
def ScheduleOK (cfg : Configuration) (exps : List Experiment) (slots : List Slot) (runLength : Quantity) : Prop :=
  ∃ ps cd, resolve exps slots = some ps ∧ cooldownOf cfg = some cd ∧
    cd.dim = secDim ∧ runLength.dim = secDim ∧
    (∀ e ∈ exps, verdict cfg e = .accept) ∧
    (∀ p ∈ ps, Q.le cd.val p.start ∧ Q.le p.stop runLength.val) ∧
    ps.Pairwise Disjoint

/-- **Checker** (what the `cryolean check-schedule` command runs). -/
def validSchedule (cfg : Configuration) (exps : List Experiment) (slots : List Slot) (runLength : Quantity) : Bool :=
  match resolve exps slots, cooldownOf cfg with
  | some ps, some cd =>
      decide (cd.dim = secDim) && decide (runLength.dim = secDim) &&
      decide (∀ e ∈ exps, verdict cfg e = .accept) &&
      decide (∀ p ∈ ps, Q.le cd.val p.start ∧ Q.le p.stop runLength.val) &&
      decide (ps.Pairwise Disjoint)
  | _, _ => false

theorem validSchedule_sound {cfg : Configuration} {exps : List Experiment} {slots : List Slot} {L : Quantity}
    (h : validSchedule cfg exps slots L = true) : ScheduleOK cfg exps slots L := by
  unfold validSchedule at h
  split at h
  · rename_i ps cd hps hcd
    simp only [Bool.and_eq_true, decide_eq_true_eq] at h
    obtain ⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩ := h
    exact ⟨ps, cd, hps, hcd, h1, h2, h3, h4, h5⟩
  · cases h

theorem validSchedule_complete {cfg : Configuration} {exps : List Experiment} {slots : List Slot} {L : Quantity}
    (h : ScheduleOK cfg exps slots L) : validSchedule cfg exps slots L = true := by
  obtain ⟨ps, cd, hps, hcd, h1, h2, h3, h4, h5⟩ := h
  unfold validSchedule
  rw [hps, hcd]
  simp only [Bool.and_eq_true, decide_eq_true_eq]
  exact ⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩

/-- Every slot of a valid schedule lies inside [cooldown, run length]. -/
theorem validSchedule_bounds {cfg : Configuration} {exps : List Experiment} {slots : List Slot} {L : Quantity}
    (h : validSchedule cfg exps slots L = true) :
    ∃ ps cd, resolve exps slots = some ps ∧ cooldownOf cfg = some cd ∧
      ∀ p ∈ ps, Q.le cd.val p.start ∧ Q.le p.stop L.val := by
  obtain ⟨ps, cd, hps, hcd, _, _, _, h4, _⟩ := validSchedule_sound h
  exact ⟨ps, cd, hps, hcd, h4⟩

/-- The slots of a valid schedule are pairwise disjoint. -/
theorem validSchedule_disjoint {cfg : Configuration} {exps : List Experiment} {slots : List Slot} {L : Quantity}
    (h : validSchedule cfg exps slots L = true) :
    ∃ ps, resolve exps slots = some ps ∧ ps.Pairwise Disjoint := by
  obtain ⟨ps, _, hps, _, _, _, _, _, h5⟩ := validSchedule_sound h
  exact ⟨ps, hps, h5⟩

/-- Only experiments that the proven checker ACCEPTS on this configuration can be scheduled. -/
theorem validSchedule_only_accepted {cfg : Configuration} {exps : List Experiment} {slots : List Slot} {L : Quantity}
    (h : validSchedule cfg exps slots L = true) : ∀ e ∈ exps, AcceptSpec cfg e := by
  obtain ⟨_, _, _, _, _, _, h3, _, _⟩ := validSchedule_sound h
  exact fun e he => verdict_accept_sound (h3 e he)

/-- A schedule that includes an experiment Lean does not accept is always rejected. -/
theorem validSchedule_rejects_unaccepted {cfg : Configuration} {exps : List Experiment} {slots : List Slot} {L : Quantity}
    {e : Experiment} (he : e ∈ exps) (hv : verdict cfg e ≠ .accept) : validSchedule cfg exps slots L = false := by
  cases h : validSchedule cfg exps slots L
  · rfl
  · obtain ⟨_, _, _, _, _, _, h3, _, _⟩ := validSchedule_sound h
    exact absurd (h3 e he) hv

/-- Resolution respects order and ids: the i-th slot belongs to the i-th experiment. -/
theorem resolve_ids : ∀ {exps : List Experiment} {slots : List Slot} {ps : List Placed},
    resolve exps slots = some ps → ps.map (·.experimentId) = exps.map (·.id)
  | [], [], ps, h => by simp [resolve] at h; subst h; rfl
  | e :: es, s :: ss, ps, h => by
      simp only [resolve] at h
      split at h
      · rename_i hid
        split at h
        · rename_i d rest _ hr
          cases h
          simp [hid, resolve_ids hr]
        · cases h
      · cases h
  | [], _ :: _, _, h => by simp [resolve] at h
  | _ :: _, [], _, h => by simp [resolve] at h

end CryoLean
