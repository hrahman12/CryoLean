import CryoLean.Model
import CryoLean.Num
import CryoLean.Checker
/-!
# Independent specification (v2)

Propositions written from the *meaning* of each construct, not from the
executable checker.  Shared with the checker are only `lookup`/`findParam`
("the record stored under this name"), the exact rational order `Q.le` and the
exact arithmetic on quantities (`Quantity.add`, `.mul`, ...).
`CryoLean.Soundness` proves the checker against these definitions.
-/

namespace CryoLean

/-- Evidence classes a verified verdict may rest on.  Estimates and unknowns are excluded. -/
def TrustedEvidence : EvidenceStatus → Prop
  | .manufacturerSpecification => True
  | .experimentalObservation   => True
  | .referenceData             => True
  | .userEntered               => True
  | .inferredEstimate          => False
  | .unknown                   => False

/-- "documented value `v` meets constraint `k`" -/
inductive ValueMeets : Constraint → CapValue → Prop
  | pointWithin {q lo hi : Quantity} (d₁ : lo.dim = q.dim) (d₂ : hi.dim = q.dim)
      (h₁ : Q.le lo.val q.val) (h₂ : Q.le q.val hi.val) : ValueMeets (.pointWithin q) (.range lo hi)
  | rangeWithin {rlo rhi lo hi : Quantity} (d₀ : rlo.dim = rhi.dim) (d₁ : lo.dim = rlo.dim)
      (d₂ : hi.dim = rlo.dim) (wf : Q.le rlo.val rhi.val)
      (h₁ : Q.le lo.val rlo.val) (h₂ : Q.le rhi.val hi.val) : ValueMeets (.rangeWithin rlo rhi) (.range lo hi)
  | atLeastMax {q m : Quantity} (d : m.dim = q.dim) (h : Q.le q.val m.val) : ValueMeets (.atLeast q) (.max m)
  | atLeastRange {q lo hi : Quantity} (d : hi.dim = q.dim) (h : Q.le q.val hi.val) : ValueMeets (.atLeast q) (.range lo hi)
  | atMostMin {q m : Quantity} (d : m.dim = q.dim) (h : Q.le m.val q.val) : ValueMeets (.atMost q) (.min m)
  | atMostRange {q lo hi : Quantity} (d : lo.dim = q.dim) (h : Q.le lo.val q.val) : ValueMeets (.atMost q) (.range lo hi)
  | flagIs {b : Bool} : ValueMeets (.flagIs b) (.flag b)
  | countAtLeast {n m : Nat} (h : n ≤ m) : ValueMeets (.countAtLeast n) (.count m)
  | countEquals {n : Nat} : ValueMeets (.countEquals n) (.count n)
  | enumIn {allowed : List String} {s : String} (h : s ∈ allowed) : ValueMeets (.enumIn allowed) (.enum s)
  | setContains {needed xs : List String} (h : ∀ x ∈ needed, x ∈ xs) : ValueMeets (.setContains needed) (.set xs)

/-- "documented value `v` demonstrably conflicts with constraint `k`" (comparable dimensions, limit excludes it) -/
inductive ValueFails : Constraint → CapValue → Prop
  | pointWithin {q lo hi : Quantity} (d₁ : lo.dim = q.dim) (d₂ : hi.dim = q.dim)
      (h : ¬ (Q.le lo.val q.val ∧ Q.le q.val hi.val)) : ValueFails (.pointWithin q) (.range lo hi)
  | rangeWithin {rlo rhi lo hi : Quantity} (d₀ : rlo.dim = rhi.dim) (d₁ : lo.dim = rlo.dim)
      (d₂ : hi.dim = rlo.dim) (wf : Q.le rlo.val rhi.val)
      (h : ¬ (Q.le lo.val rlo.val ∧ Q.le rhi.val hi.val)) : ValueFails (.rangeWithin rlo rhi) (.range lo hi)
  | atLeastMax {q m : Quantity} (d : m.dim = q.dim) (h : ¬ Q.le q.val m.val) : ValueFails (.atLeast q) (.max m)
  | atLeastRange {q lo hi : Quantity} (d : hi.dim = q.dim) (h : ¬ Q.le q.val hi.val) : ValueFails (.atLeast q) (.range lo hi)
  | atMostMin {q m : Quantity} (d : m.dim = q.dim) (h : ¬ Q.le m.val q.val) : ValueFails (.atMost q) (.min m)
  | atMostRange {q lo hi : Quantity} (d : lo.dim = q.dim) (h : ¬ Q.le lo.val q.val) : ValueFails (.atMost q) (.range lo hi)
  | flagIs {b v : Bool} (h : v ≠ b) : ValueFails (.flagIs b) (.flag v)
  | countAtLeast {n m : Nat} (h : m < n) : ValueFails (.countAtLeast n) (.count m)
  | countEquals {n m : Nat} (h : m ≠ n) : ValueFails (.countEquals n) (.count m)
  | enumIn {allowed : List String} {s : String} (h : s ∉ allowed) : ValueFails (.enumIn allowed) (.enum s)
  | setContains {needed xs : List String} (h : ¬ ∀ x ∈ needed, x ∈ xs) : ValueFails (.setContains needed) (.set xs)

/-- The capability under `key` is installed, trusted and meets the constraint — or the constraint
asks for the item to be ABSENT and it is documented (trusted) as an option that is not fitted. -/
def SatisfiesKey (cfg : Configuration) (k : Constraint) (key : String) : Prop :=
  ∃ c, lookup cfg key = some c ∧
    ((c.install = .installed ∧ TrustedEvidence c.evidence ∧ ValueMeets k c.value) ∨
     (c.install = .optionalNotInstalled ∧ TrustedEvidence c.evidence ∧ k = .flagIs false))

/-- The capability under `key` is an option that is not fitted (and the constraint needs it), or is
fitted and demonstrably conflicts. -/
def ViolatesKey (cfg : Configuration) (k : Constraint) (key : String) : Prop :=
  ∃ c, lookup cfg key = some c ∧
    ((c.install = .optionalNotInstalled ∧ k ≠ .flagIs false) ∨
     (c.install = .installed ∧ TrustedEvidence c.evidence ∧ ValueFails k c.value))

/-- A parameter has a trusted value `q`. -/
def ParamIs (e : Experiment) (name : String) (q : Quantity) : Prop :=
  ∃ p, findParam e name = some p ∧ TrustedEvidence p.origin ∧ p.value = some q

def CondHolds (cfg : Configuration) (e : Experiment) : Condition → Prop
  | .capFlag key b => ∃ c, lookup cfg key = some c ∧
      ((c.install = .optionalNotInstalled ∧ TrustedEvidence c.evidence ∧ b = false) ∨
       (c.install = .installed ∧ TrustedEvidence c.evidence ∧ c.value = .flag b))
  | .paramAtMost name q => ∃ v, ParamIs e name v ∧ v.dim = q.dim ∧ Q.le v.val q.val
  | .paramAtLeast name q => ∃ v, ParamIs e name v ∧ v.dim = q.dim ∧ Q.le q.val v.val

def CondFails (cfg : Configuration) (e : Experiment) : Condition → Prop
  | .capFlag key b => ∃ c, lookup cfg key = some c ∧
      ((c.install = .optionalNotInstalled ∧ TrustedEvidence c.evidence ∧ b = true) ∨
       (c.install = .installed ∧ TrustedEvidence c.evidence ∧ ∃ v, c.value = .flag v ∧ v ≠ b))
  | .paramAtMost name q => ∃ v, ParamIs e name v ∧ v.dim = q.dim ∧ ¬ Q.le v.val q.val
  | .paramAtLeast name q => ∃ v, ParamIs e name v ∧ v.dim = q.dim ∧ ¬ Q.le q.val v.val

/-- Big-step semantics of coupled-constraint expressions: `Denotes cfg e x q`
means `x` denotes the quantity `q` using only installed, trusted capabilities,
trusted parameters, and dimensionally consistent additions. -/
inductive Denotes (cfg : Configuration) (e : Experiment) : Expr → Quantity → Prop
  | lit {q : Quantity} (h : q.val.den ≠ 0) : Denotes cfg e (.lit q) q
  | capLo {key c lo hi} (hl : lookup cfg key = some c) (hi_ : c.install = .installed)
      (ht : TrustedEvidence c.evidence) (hv : c.value = .range lo hi) : Denotes cfg e (.cap key .lo) lo
  | capHi {key c lo hi} (hl : lookup cfg key = some c) (hi_ : c.install = .installed)
      (ht : TrustedEvidence c.evidence) (hv : c.value = .range lo hi) : Denotes cfg e (.cap key .hi) hi
  | capMax {key c q} (hl : lookup cfg key = some c) (hi_ : c.install = .installed)
      (ht : TrustedEvidence c.evidence) (hv : c.value = .max q) : Denotes cfg e (.cap key .max) q
  | capMin {key c q} (hl : lookup cfg key = some c) (hi_ : c.install = .installed)
      (ht : TrustedEvidence c.evidence) (hv : c.value = .min q) : Denotes cfg e (.cap key .min) q
  | capCount {key c n} (hl : lookup cfg key = some c) (hi_ : c.install = .installed)
      (ht : TrustedEvidence c.evidence) (hv : c.value = .count n) :
      Denotes cfg e (.cap key .count) ⟨Q.ofNat n, Dim.one⟩
  | param {name q} (hp : ParamIs e name q) (h : q.val.den ≠ 0) : Denotes cfg e (.param name) q
  | add {a b x y} (ha : Denotes cfg e a x) (hb : Denotes cfg e b y) (hd : x.dim = y.dim) :
      Denotes cfg e (.add a b) (x.add y)
  | sub {a b x y} (ha : Denotes cfg e a x) (hb : Denotes cfg e b y) (hd : x.dim = y.dim) :
      Denotes cfg e (.sub a b) (x.sub y)
  | mul {a b x y} (ha : Denotes cfg e a x) (hb : Denotes cfg e b y) : Denotes cfg e (.mul a b) (x.mul y)
  | neg {a x} (ha : Denotes cfg e a x) : Denotes cfg e (.neg a) x.neg

/-- `a ≤ b` holds for the denoted quantities, in equal dimensions. -/
def LeHolds (cfg : Configuration) (e : Experiment) (a b : Expr) : Prop :=
  ∃ x y, Denotes cfg e a x ∧ Denotes cfg e b y ∧ x.dim = y.dim ∧ Q.le x.val y.val

/-- `a ≤ b` demonstrably fails for the denoted quantities, in equal dimensions. -/
def LeFails (cfg : Configuration) (e : Experiment) (a b : Expr) : Prop :=
  ∃ x y, Denotes cfg e a x ∧ Denotes cfg e b y ∧ x.dim = y.dim ∧ ¬ Q.le x.val y.val

/-- A requirement genuinely passes: all its conditions hold and some alternative key satisfies it. -/
def ReqPasses (cfg : Configuration) (e : Experiment) (r : Requirement) : Prop :=
  (∀ c ∈ r.conditions, CondHolds cfg e c) ∧ ∃ key ∈ r.keys, SatisfiesKey cfg r.constraint key

/-- A requirement is fine: a condition definitely fails (so it does not apply) or it passes. -/
def ReqOK (cfg : Configuration) (e : Experiment) (r : Requirement) : Prop :=
  (∃ c ∈ r.conditions, CondFails cfg e c) ∨ ReqPasses cfg e r

/-- A requirement is violated: it applies and every alternative key demonstrably violates it. -/
def ReqViolated (cfg : Configuration) (e : Experiment) (r : Requirement) : Prop :=
  (∀ c ∈ r.conditions, CondHolds cfg e c) ∧ r.keys ≠ [] ∧ ∀ key ∈ r.keys, ViolatesKey cfg r.constraint key

/-- A coupled constraint genuinely passes: it applies, its model is valid here, and `lhs ≤ rhs`. -/
def CoupledPasses (cfg : Configuration) (e : Experiment) (c : Coupled) : Prop :=
  (∀ d ∈ c.conditions, CondHolds cfg e d) ∧ (∀ p ∈ c.validity, LeHolds cfg e p.1 p.2) ∧ LeHolds cfg e c.lhs c.rhs

def CoupledOK (cfg : Configuration) (e : Experiment) (c : Coupled) : Prop :=
  (∃ d ∈ c.conditions, CondFails cfg e d) ∨ CoupledPasses cfg e c

/-- A coupled constraint is violated: it applies, its model is valid here, and `lhs > rhs`. -/
def CoupledViolated (cfg : Configuration) (e : Experiment) (c : Coupled) : Prop :=
  (∀ d ∈ c.conditions, CondHolds cfg e d) ∧ (∀ p ∈ c.validity, LeHolds cfg e p.1 p.2) ∧ LeFails cfg e c.lhs c.rhs

/-- What ACCEPT is supposed to mean. -/
def AcceptSpec (cfg : Configuration) (e : Experiment) : Prop :=
  e.confirmed = true ∧
  (∀ r ∈ e.requirements, r.mandatory = true → r.applicable = true → ReqOK cfg e r) ∧
  (∀ c ∈ e.coupled, c.mandatory = true → c.applicable = true → CoupledOK cfg e c) ∧
  ((∃ r ∈ e.requirements, r.mandatory = true ∧ r.applicable = true ∧ ReqPasses cfg e r) ∨
   (∃ c ∈ e.coupled, c.mandatory = true ∧ c.applicable = true ∧ CoupledPasses cfg e c))

/-- What REJECT is supposed to mean. -/
def RejectSpec (cfg : Configuration) (e : Experiment) : Prop :=
  e.confirmed = true ∧
  ((∃ r ∈ e.requirements, r.mandatory = true ∧ r.applicable = true ∧ ReqViolated cfg e r) ∨
   (∃ c ∈ e.coupled, c.mandatory = true ∧ c.applicable = true ∧ CoupledViolated cfg e c))

end CryoLean
