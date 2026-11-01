/-!
# CryoLean trusted data model (v2)

The *universal* vocabulary of the checker.  Nothing here mentions an industry,
a manufacturer, an experiment type or a particular physical property: all of
those are data (JSON records produced by the Python data layer from the SQLite
evidence database) decoded into these types by `CryoLean.Json`.

Design rules the proofs in `CryoLean.Soundness` rely on:

* **Exact arithmetic.** Every physical number is an exact rational `num/den`
  (`den > 0`, enforced by the decoder) in SI *coherent* units.  There is no
  floating point anywhere in the trusted core.
* **Dimensional analysis.** Every quantity carries a `Dim` vector of SI base
  exponents (K, m, kg, s, A, mol, cd).  Comparisons, additions and
  subtractions require equal dimensions; a mismatch is `unsupported`, never a
  pass, and units are never silently converted.
* **Provenance.** A capability that is UNKNOWN, an inferred estimate, without
  provenance, or an optional accessory that is not installed can never
  satisfy a requirement or feed a coupled calculation.
-/

namespace CryoLean

/-- Exponents of the seven SI base dimensions. -/
structure Dim where
  K   : Int := 0
  m   : Int := 0
  kg  : Int := 0
  s   : Int := 0
  A   : Int := 0
  mol : Int := 0
  cd  : Int := 0
deriving Repr, DecidableEq, BEq, Inhabited

def Dim.one : Dim := {}

def Dim.mul (a b : Dim) : Dim :=
  ⟨a.K + b.K, a.m + b.m, a.kg + b.kg, a.s + b.s, a.A + b.A, a.mol + b.mol, a.cd + b.cd⟩

/-- An exact rational `num / den`.  `den = 0` is rejected by the decoder. -/
structure Q where
  num : Int
  den : Nat
deriving Repr, DecidableEq, BEq, Inhabited

/-- A physical quantity: an exact rational value in SI coherent units with its dimension. -/
structure Quantity where
  val : Q
  dim : Dim
deriving Repr, DecidableEq, BEq, Inhabited

/-- Provenance class of a fact. -/
inductive EvidenceStatus where
  | manufacturerSpecification
  | experimentalObservation
  | referenceData
  | userEntered
  | inferredEstimate
  | unknown
deriving Repr, DecidableEq, BEq, Inhabited

/-- Whether a capability is physically present in *this* configuration. -/
inductive InstallStatus where
  | installed
  | optionalNotInstalled
  | unknown
deriving Repr, DecidableEq, BEq, Inhabited

/-- The shape of a documented capability value. -/
inductive CapValue where
  | range (lo hi : Quantity)
  | max (q : Quantity)
  | min (q : Quantity)
  | flag (b : Bool)
  | count (n : Nat)
  | enum (s : String)
  | set (xs : List String)
  | unknown
deriving Repr, DecidableEq, BEq, Inhabited

/-- One documented capability of a configuration (`key` is a vocabulary string). -/
structure Capability where
  key         : String
  value       : CapValue
  install     : InstallStatus
  evidence    : EvidenceStatus
  evidenceIds : List String
deriving Repr, DecidableEq, BEq, Inhabited

/-- An exact configuration of a piece of equipment. -/
structure Configuration where
  id           : String
  equipmentId  : String
  name         : String
  capabilities : List Capability
deriving Repr, DecidableEq, BEq, Inhabited

/-- How a requirement constrains the capability value(s) stored under its key(s). -/
inductive Constraint where
  /-- the operating point `q` lies inside the documented `range` -/
  | pointWithin (q : Quantity)
  /-- the whole interval `[lo, hi]` lies inside the documented `range` -/
  | rangeWithin (lo hi : Quantity)
  /-- the documented `max` (or upper end of a `range`) is at least `q` -/
  | atLeast (q : Quantity)
  /-- the documented `min` (or lower end of a `range`) is at most `q` -/
  | atMost (q : Quantity)
  /-- the documented flag equals `b` (`present` is `flagIs true`) -/
  | flagIs (b : Bool)
  /-- the documented count is at least `n` -/
  | countAtLeast (n : Nat)
  /-- the documented count equals `n` (numeric equality) -/
  | countEquals (n : Nat)
  /-- the documented categorical value is one of `allowed` -/
  | enumIn (allowed : List String)
  /-- the documented set contains every element of `needed` -/
  | setContains (needed : List String)
deriving Repr, DecidableEq, BEq, Inhabited

/-- Experiment parameters (operating conditions supplied by a profile or the user). -/
structure Param where
  name   : String
  value  : Option Quantity
  origin : EvidenceStatus
deriving Repr, DecidableEq, BEq, Inhabited

/-- A condition that decides whether a conditional requirement applies. -/
inductive Condition where
  /-- the capability `key` is installed, trusted and its flag equals `b` -/
  | capFlag (key : String) (b : Bool)
  /-- the experiment parameter `name` is at most `q` -/
  | paramAtMost (name : String) (q : Quantity)
  /-- the experiment parameter `name` is at least `q` -/
  | paramAtLeast (name : String) (q : Quantity)
deriving Repr, DecidableEq, BEq, Inhabited

/-- One requirement.  `keys` is a disjunction: the requirement is met if the
constraint holds for ANY listed capability (usually a single key). -/
structure Requirement where
  keys        : List String
  constraint  : Constraint
  mandatory   : Bool
  applicable  : Bool
  conditions  : List Condition
  origin      : EvidenceStatus
  rationale   : String
  evidenceIds : List String
deriving Repr, DecidableEq, BEq, Inhabited

/-- Which number of a capability an expression reads. -/
inductive Sel where
  | lo | hi | max | min | count
deriving Repr, DecidableEq, BEq, Inhabited

/-- Typed arithmetic expressions for coupled multiphysics constraints.
No division: relations are written in multiplied-out form so evaluation is exact. -/
inductive Expr where
  | lit (q : Quantity)
  | cap (key : String) (sel : Sel)
  | param (name : String)
  | add (a b : Expr)
  | sub (a b : Expr)
  | mul (a b : Expr)
  | neg (a : Expr)
deriving Repr, DecidableEq, BEq, Inhabited

/-- A coupled constraint `lhs ≤ rhs`, valid only where every `validity` pair
`(a, b)` satisfies `a ≤ b` (outside that region the model is `unsupported`). -/
structure Coupled where
  id          : String
  name        : String
  model       : String
  lhs         : Expr
  rhs         : Expr
  validity    : List (Expr × Expr)
  mandatory   : Bool
  applicable  : Bool
  conditions  : List Condition
  origin      : EvidenceStatus
  rationale   : String
  evidenceIds : List String
deriving Repr, Inhabited

/-- An experiment profile.  `industry` is an opaque label the checker never reads. -/
structure Experiment where
  id           : String
  name         : String
  industry     : String
  params       : List Param
  requirements : List Requirement
  coupled      : List Coupled
  confirmed    : Bool
deriving Repr, Inhabited

/-- Outcome of one check. -/
inductive Outcome where
  | pass
  | fail
  | unknown
  | unsupported
  | notApplicable
deriving Repr, DecidableEq, Inhabited

/-- Overall verdict. -/
inductive Verdict where
  | accept
  | reject
  | needMoreInfo
deriving Repr, DecidableEq, Inhabited

end CryoLean
