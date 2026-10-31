import CryoLean.Model
/-!
# The generic compatibility checker

Pure, total, executable functions.  `CryoLean.Soundness` proves them sound
against the independent specification in `CryoLean.Spec`.
-/

namespace CryoLean

/-- Find the capability stored under `key` (first match). -/
def lookup (cfg : Configuration) (key : String) : Option Capability :=
  cfg.capabilities.find? (fun c => c.key == key)

/-- Compare a constraint against a capability value.  Units must match exactly;
mismatched units or incompatible shapes are `unsupported`, an unknown value is
`unknown`. -/
def checkValue : Constraint → CapValue → Outcome
  | _, .unknown => .unknown
  | .pointWithin q, .range lo hi =>
      if lo.unit = q.unit ∧ hi.unit = q.unit then
        if lo.value ≤ q.value ∧ q.value ≤ hi.value then .pass else .fail
      else .unsupported
  | .rangeWithin rlo rhi, .range lo hi =>
      if rlo.unit = rhi.unit ∧ lo.unit = rlo.unit ∧ hi.unit = rlo.unit ∧ rlo.value ≤ rhi.value then
        if lo.value ≤ rlo.value ∧ rhi.value ≤ hi.value then .pass else .fail
      else .unsupported
  | .atLeast q, .max m =>
      if m.unit = q.unit then (if q.value ≤ m.value then .pass else .fail) else .unsupported
  | .atLeast q, .range _ hi =>
      if hi.unit = q.unit then (if q.value ≤ hi.value then .pass else .fail) else .unsupported
  | .atMost q, .min m =>
      if m.unit = q.unit then (if m.value ≤ q.value then .pass else .fail) else .unsupported
  | .atMost q, .range lo _ =>
      if lo.unit = q.unit then (if lo.value ≤ q.value then .pass else .fail) else .unsupported
  | .present, .flag b => if b then .pass else .fail
  | .countAtLeast n, .count m => if n ≤ m then .pass else .fail
  | _, _ => .unsupported

/-- Check a requirement against the capability found under its key, taking
installation status and evidence class into account. -/
def checkCapability (r : Requirement) (c : Capability) : Outcome :=
  match c.install with
  | .optionalNotInstalled => .fail
  | .unknown => .unknown
  | .installed =>
    match c.evidence with
    | .inferredEstimate => .unknown
    | .unknown => .unknown
    | _ => checkValue r.constraint c.value

/-- Check one requirement against a configuration. A missing capability is `unknown`. -/
def checkRequirement (cfg : Configuration) (r : Requirement) : Outcome :=
  match lookup cfg r.key with
  | none => .unknown
  | some c => checkCapability r c

/-- The mandatory requirements of an experiment. -/
def mandatoryReqs (e : Experiment) : List Requirement :=
  e.requirements.filter (·.mandatory)

/-- The overall verdict.  Order matters and is part of the specification:
unconfirmed or empty profiles can never be accepted; any mandatory failure
rejects; acceptance needs every mandatory requirement to pass. -/
def verdict (cfg : Configuration) (e : Experiment) : Verdict :=
  if e.confirmed = false then .needMoreInfo
  else if (mandatoryReqs e).isEmpty then .needMoreInfo
  else if (mandatoryReqs e).any (fun r => checkRequirement cfg r == .fail) then .reject
  else if (mandatoryReqs e).all (fun r => checkRequirement cfg r == .pass) then .accept
  else .needMoreInfo

/-- Per-requirement result record. -/
structure CheckResult where
  requirement : Requirement
  capability  : Option Capability
  outcome     : Outcome
deriving Repr, BEq, Inhabited

/-- The full result, bound to the exact inputs by id. -/
structure Result where
  configurationId : String
  equipmentId     : String
  experimentId    : String
  verdict         : Verdict
  checks          : List CheckResult
deriving Repr, BEq, Inhabited

def checkAll (cfg : Configuration) (e : Experiment) : List CheckResult :=
  e.requirements.map (fun r => ⟨r, lookup cfg r.key, checkRequirement cfg r⟩)

def run (cfg : Configuration) (e : Experiment) : Result :=
  ⟨cfg.id, cfg.equipmentId, e.id, verdict cfg e, checkAll cfg e⟩

end CryoLean
