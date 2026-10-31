/-!
# CryoLean trusted data model

This file defines the *universal* capability/requirement vocabulary that the
Lean checker understands.  Nothing in this file mentions an industry, a
manufacturer, or an experiment type: industries, equipment and experiments are
*data* (JSON records) that are decoded into these types by `CryoLean.Json`.

Design rules that the proofs in `CryoLean.Soundness` depend on:

* Every physical quantity is an integer in an explicitly named unit.  The data
  layer normalises to canonical integer units (mK, mT, um, nW, uPa, kHz, s, ...).
  The checker **never converts units**; it only compares two quantities whose
  unit strings are identical.  A unit mismatch is reported as `unsupported`,
  never as a pass.
* A capability that is documented as unknown, is only an inferred estimate, or is
  an optional accessory that is *not installed* in the configuration being
  checked can never satisfy a requirement.
-/

namespace CryoLean

/-- An integer value in an explicitly named unit (e.g. `⟨1800, "mK"⟩` = 1.8 K). -/
structure Quantity where
  value : Int
  unit  : String
deriving Repr, DecidableEq, BEq, Inhabited

/-- Provenance class of a fact.  Mirrors `evidence_status` in `data/evidence.json`. -/
inductive EvidenceStatus where
  /-- Stated in manufacturer documentation (datasheet, manual, brochure). -/
  | manufacturerSpecification
  /-- Measured/observed and reported in a publication or lab record. -/
  | experimentalObservation
  /-- Entered by the user for their own instrument or experiment. -/
  | userEntered
  /-- Estimated or inferred (by a person or an AI); never trusted by the checker. -/
  | inferredEstimate
  /-- No provenance recorded. -/
  | unknown
deriving Repr, DecidableEq, BEq, Inhabited

/-- Whether a capability is physically present in *this* configuration. -/
inductive InstallStatus where
  /-- Documented as fitted to this configuration. -/
  | installed
  /-- Exists as an option for the product family but is NOT fitted here. -/
  | optionalNotInstalled
  /-- Documentation does not say whether it is fitted. -/
  | unknown
deriving Repr, DecidableEq, BEq, Inhabited

/-- The shape of a documented capability value. -/
inductive CapValue where
  /-- A documented operating interval `[lo, hi]` (e.g. a temperature range). -/
  | range (lo hi : Quantity)
  /-- A documented maximum (e.g. maximum magnetic field). -/
  | max (q : Quantity)
  /-- A documented minimum (e.g. base temperature, base pressure). -/
  | min (q : Quantity)
  /-- A yes/no capability (e.g. optical access, a measurement module). -/
  | flag (b : Bool)
  /-- A documented count (e.g. 24 DC wiring lines). -/
  | count (n : Nat)
  /-- Explicitly recorded as UNKNOWN in the evidence database. -/
  | unknown
deriving Repr, DecidableEq, BEq, Inhabited

/-- One documented capability of a configuration.  `key` is a vocabulary string
such as `"temperature.range"`, `"magnetic_field.max"`, `"module.vsm"`;
the vocabulary is data (`data/capability_vocabulary.json`), not Lean code. -/
structure Capability where
  key         : String
  value       : CapValue
  install     : InstallStatus
  evidence    : EvidenceStatus
  evidenceIds : List String
deriving Repr, DecidableEq, BEq, Inhabited

/-- An exact installed configuration of a piece of equipment. -/
structure Configuration where
  id           : String
  equipmentId  : String
  name         : String
  capabilities : List Capability
deriving Repr, DecidableEq, BEq, Inhabited

/-- How a requirement constrains the capability stored under the same key. -/
inductive Constraint where
  /-- The operating point `q` must lie inside the capability's `range`. -/
  | pointWithin (q : Quantity)
  /-- The whole interval `[lo, hi]` must lie inside the capability's `range`. -/
  | rangeWithin (lo hi : Quantity)
  /-- The capability (`max`, or the upper end of a `range`) must be `≥ q`. -/
  | atLeast (q : Quantity)
  /-- The capability (`min`, or the lower end of a `range`) must be `≤ q`. -/
  | atMost (q : Quantity)
  /-- The flag capability must be installed and true. -/
  | present
  /-- The `count` capability must be `≥ n`. -/
  | countAtLeast (n : Nat)
deriving Repr, DecidableEq, BEq, Inhabited

/-- One requirement of an experiment profile. -/
structure Requirement where
  key         : String
  constraint  : Constraint
  mandatory   : Bool
  origin      : EvidenceStatus
  rationale   : String
  evidenceIds : List String
deriving Repr, DecidableEq, BEq, Inhabited

/-- An experiment profile.  `industry` is an opaque label: the checker never
branches on it. `confirmed` records that the user reviewed the requirements. -/
structure Experiment where
  id           : String
  name         : String
  industry     : String
  requirements : List Requirement
  confirmed    : Bool
deriving Repr, DecidableEq, BEq, Inhabited

/-- Outcome of checking a single requirement. -/
inductive Outcome where
  | pass
  | fail
  | unknown
  | unsupported
deriving Repr, DecidableEq, Inhabited

/-- Overall verdict. -/
inductive Verdict where
  | accept
  | reject
  | needMoreInfo
deriving Repr, DecidableEq, Inhabited

end CryoLean
