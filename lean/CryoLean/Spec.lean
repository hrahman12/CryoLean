import CryoLean.Model
import CryoLean.Checker
/-!
# Independent specification

`ValueMeets`, `ValueFails`, `Satisfies` and `Violates` are *propositions*
written directly from the meaning of each constraint, without reference to the
executable checker (only `lookup` is shared, as the meaning of "the capability
stored under this key").  `CryoLean.Soundness` connects the two.
-/

namespace CryoLean

/-- Evidence classes a verified verdict may rest on.  Estimates and unknowns are excluded. -/
def TrustedEvidence : EvidenceStatus → Prop
  | .manufacturerSpecification => True
  | .experimentalObservation   => True
  | .userEntered               => True
  | .inferredEstimate          => False
  | .unknown                   => False

/-- Semantic meaning of "capability value `v` meets constraint `c`". -/
inductive ValueMeets : Constraint → CapValue → Prop
  | pointWithin {q lo hi : Quantity}
      (hu₁ : lo.unit = q.unit) (hu₂ : hi.unit = q.unit)
      (h₁ : lo.value ≤ q.value) (h₂ : q.value ≤ hi.value) :
      ValueMeets (.pointWithin q) (.range lo hi)
  | rangeWithin {rlo rhi lo hi : Quantity}
      (hu₀ : rlo.unit = rhi.unit) (hu₁ : lo.unit = rlo.unit) (hu₂ : hi.unit = rlo.unit)
      (hwf : rlo.value ≤ rhi.value)
      (h₁ : lo.value ≤ rlo.value) (h₂ : rhi.value ≤ hi.value) :
      ValueMeets (.rangeWithin rlo rhi) (.range lo hi)
  | atLeastMax {q m : Quantity} (hu : m.unit = q.unit) (h : q.value ≤ m.value) :
      ValueMeets (.atLeast q) (.max m)
  | atLeastRange {q lo hi : Quantity} (hu : hi.unit = q.unit) (h : q.value ≤ hi.value) :
      ValueMeets (.atLeast q) (.range lo hi)
  | atMostMin {q m : Quantity} (hu : m.unit = q.unit) (h : m.value ≤ q.value) :
      ValueMeets (.atMost q) (.min m)
  | atMostRange {q lo hi : Quantity} (hu : lo.unit = q.unit) (h : lo.value ≤ q.value) :
      ValueMeets (.atMost q) (.range lo hi)
  | present : ValueMeets .present (.flag true)
  | countAtLeast {n m : Nat} (h : n ≤ m) : ValueMeets (.countAtLeast n) (.count m)

/-- Semantic meaning of "capability value `v` is documented to conflict with `c`":
the units are comparable and the documented limit excludes the requirement. -/
inductive ValueFails : Constraint → CapValue → Prop
  | pointWithin {q lo hi : Quantity}
      (hu₁ : lo.unit = q.unit) (hu₂ : hi.unit = q.unit)
      (h : q.value < lo.value ∨ hi.value < q.value) :
      ValueFails (.pointWithin q) (.range lo hi)
  | rangeWithin {rlo rhi lo hi : Quantity}
      (hu₀ : rlo.unit = rhi.unit) (hu₁ : lo.unit = rlo.unit) (hu₂ : hi.unit = rlo.unit)
      (hwf : rlo.value ≤ rhi.value)
      (h : rlo.value < lo.value ∨ hi.value < rhi.value) :
      ValueFails (.rangeWithin rlo rhi) (.range lo hi)
  | atLeastMax {q m : Quantity} (hu : m.unit = q.unit) (h : m.value < q.value) :
      ValueFails (.atLeast q) (.max m)
  | atLeastRange {q lo hi : Quantity} (hu : hi.unit = q.unit) (h : hi.value < q.value) :
      ValueFails (.atLeast q) (.range lo hi)
  | atMostMin {q m : Quantity} (hu : m.unit = q.unit) (h : q.value < m.value) :
      ValueFails (.atMost q) (.min m)
  | atMostRange {q lo hi : Quantity} (hu : lo.unit = q.unit) (h : q.value < lo.value) :
      ValueFails (.atMost q) (.range lo hi)
  | present : ValueFails .present (.flag false)
  | countAtLeast {n m : Nat} (h : m < n) : ValueFails (.countAtLeast n) (.count m)

/-- A configuration *satisfies* a requirement: a capability is recorded under the
requirement's key, it is installed, its evidence is trusted, and its documented
value meets the constraint. -/
def Satisfies (cfg : Configuration) (r : Requirement) : Prop :=
  ∃ c, lookup cfg r.key = some c ∧
       c.install = .installed ∧
       TrustedEvidence c.evidence ∧
       ValueMeets r.constraint c.value

/-- A configuration *violates* a requirement: either the capability is documented
as an option that is not fitted, or it is installed with trusted evidence whose
value is documented to exclude the requirement. -/
def Violates (cfg : Configuration) (r : Requirement) : Prop :=
  ∃ c, lookup cfg r.key = some c ∧
       (c.install = .optionalNotInstalled ∨
        (c.install = .installed ∧ TrustedEvidence c.evidence ∧ ValueFails r.constraint c.value))

/-- What ACCEPT is supposed to mean. -/
def AcceptSpec (cfg : Configuration) (e : Experiment) : Prop :=
  e.confirmed = true ∧ mandatoryReqs e ≠ [] ∧ ∀ r ∈ mandatoryReqs e, Satisfies cfg r

/-- What REJECT is supposed to mean. -/
def RejectSpec (cfg : Configuration) (e : Experiment) : Prop :=
  e.confirmed = true ∧ ∃ r ∈ mandatoryReqs e, Violates cfg r

end CryoLean
