import CryoLean.Model
import CryoLean.Num
/-!
# The generic compatibility checker (v2)

Pure, total, executable.  `CryoLean.Soundness` proves it sound against the
independent specification in `CryoLean.Spec`.  The compiled `cryolean` binary
runs exactly these definitions on the JSON documents produced by the Python
data layer.
-/

namespace CryoLean

/-- Find the capability stored under `key` (first match). -/
def lookup (cfg : Configuration) (key : String) : Option Capability :=
  cfg.capabilities.find? (fun c => c.key == key)

/-- Find an experiment parameter by name (first match). -/
def findParam (e : Experiment) (name : String) : Option Param :=
  e.params.find? (fun p => p.name == name)

/-- Evidence classes a verified result may rest on. -/
def trustedB : EvidenceStatus → Bool
  | .manufacturerSpecification => true
  | .experimentalObservation   => true
  | .referenceData             => true
  | .userEntered               => true
  | .inferredEstimate          => false
  | .unknown                   => false

/-- Installed and backed by trusted evidence. -/
def usable (c : Capability) : Bool :=
  decide (c.install = .installed) && trustedB c.evidence

/-! ## Single-capability constraints -/

/-- Compare a constraint with a documented value.  Dimensions must match exactly. -/
def checkValue : Constraint → CapValue → Outcome
  | _, .unknown => .unknown
  | .pointWithin q, .range lo hi =>
      if lo.dim = q.dim ∧ hi.dim = q.dim then
        if Q.le lo.val q.val ∧ Q.le q.val hi.val then .pass else .fail
      else .unsupported
  | .rangeWithin rlo rhi, .range lo hi =>
      if rlo.dim = rhi.dim ∧ lo.dim = rlo.dim ∧ hi.dim = rlo.dim ∧ Q.le rlo.val rhi.val then
        if Q.le lo.val rlo.val ∧ Q.le rhi.val hi.val then .pass else .fail
      else .unsupported
  | .atLeast q, .max m =>
      if m.dim = q.dim then (if Q.le q.val m.val then .pass else .fail) else .unsupported
  | .atLeast q, .range _ hi =>
      if hi.dim = q.dim then (if Q.le q.val hi.val then .pass else .fail) else .unsupported
  | .atMost q, .min m =>
      if m.dim = q.dim then (if Q.le m.val q.val then .pass else .fail) else .unsupported
  | .atMost q, .range lo _ =>
      if lo.dim = q.dim then (if Q.le lo.val q.val then .pass else .fail) else .unsupported
  | .flagIs b, .flag v => if v = b then .pass else .fail
  | .countAtLeast n, .count m => if n ≤ m then .pass else .fail
  | .countEquals n, .count m => if n = m then .pass else .fail
  | .enumIn allowed, .enum s => if s ∈ allowed then .pass else .fail
  | .setContains needed, .set xs => if ∀ x ∈ needed, x ∈ xs then .pass else .fail
  | _, _ => .unsupported

/-- Check a constraint against one capability, honouring install status and provenance. -/
def checkCapability (k : Constraint) (c : Capability) : Outcome :=
  match c.install with
  | .optionalNotInstalled =>
      -- a documented option that is NOT fitted: absent.  It satisfies only "must be absent".
      if k = .flagIs false then (if trustedB c.evidence then .pass else .unknown) else .fail
  | .unknown => .unknown
  | .installed => if trustedB c.evidence then checkValue k c.value else .unknown

/-- Outcome for one key. A missing capability is `unknown`. -/
def keyOutcome (cfg : Configuration) (k : Constraint) (key : String) : Outcome :=
  match lookup cfg key with
  | none => .unknown
  | some c => checkCapability k c

/-- Disjunction over alternative keys: pass if any passes, fail only if all fail. -/
def combineAny (os : List Outcome) : Outcome :=
  if .pass ∈ os then .pass
  else if os ≠ [] ∧ ∀ o ∈ os, o = .fail then .fail
  else if .unknown ∈ os then .unknown
  else .unsupported

/-! ## Conditions -/

inductive CondR where
  | holds | fails | unknown
deriving Repr, DecidableEq, Inhabited

/-- The trusted value of a parameter, if any. -/
def paramValue (e : Experiment) (name : String) : Option Quantity :=
  match findParam e name with
  | some p => if trustedB p.origin then p.value else none
  | none => none

def evalCond (cfg : Configuration) (e : Experiment) : Condition → CondR
  | .capFlag key b =>
      match lookup cfg key with
      | none => .unknown
      | some c =>
          if c.install = .optionalNotInstalled then
            (if trustedB c.evidence then (if b = false then .holds else .fails) else .unknown)
          else if usable c then
            match c.value with
            | .flag v => if v = b then .holds else .fails
            | _ => .unknown
          else .unknown
  | .paramAtMost name q =>
      match paramValue e name with
      | some v => if v.dim = q.dim then (if Q.le v.val q.val then .holds else .fails) else .unknown
      | none => .unknown
  | .paramAtLeast name q =>
      match paramValue e name with
      | some v => if v.dim = q.dim then (if Q.le q.val v.val then .holds else .fails) else .unknown
      | none => .unknown

/-- A conjunction of conditions: any definite failure makes the item not applicable. -/
def condsResult (cfg : Configuration) (e : Experiment) (cs : List Condition) : CondR :=
  if ∃ c ∈ cs, evalCond cfg e c = .fails then .fails
  else if ∀ c ∈ cs, evalCond cfg e c = .holds then .holds
  else .unknown

/-! ## Requirements -/

def checkRequirement (cfg : Configuration) (e : Experiment) (r : Requirement) : Outcome :=
  match condsResult cfg e r.conditions with
  | .fails => .notApplicable
  | .unknown => .unknown
  | .holds => combineAny (r.keys.map (keyOutcome cfg r.constraint))

/-! ## Coupled constraints -/

inductive EvalR where
  | ok (q : Quantity)
  | missing (what : String)
  | bad (why : String)
deriving Repr, Inhabited

def selValue (v : CapValue) (s : Sel) : EvalR :=
  match s, v with
  | _, .unknown => .missing "value UNKNOWN"
  | .lo, .range lo _ => .ok lo
  | .hi, .range _ hi => .ok hi
  | .max, .max q => .ok q
  | .min, .min q => .ok q
  | .count, .count n => .ok ⟨Q.ofNat n, Dim.one⟩
  | _, _ => .bad "selector does not match the capability shape"

def evalExpr (cfg : Configuration) (e : Experiment) : Expr → EvalR
  | .lit q => if q.val.den = 0 then .bad "zero denominator" else .ok q
  | .cap key s =>
      match lookup cfg key with
      | none => .missing key
      | some c => if usable c then selValue c.value s else .missing key
  | .param name =>
      match paramValue e name with
      | some q => if q.val.den = 0 then .bad "zero denominator" else .ok q
      | none => .missing name
  | .add a b =>
      match evalExpr cfg e a, evalExpr cfg e b with
      | .ok x, .ok y => if x.dim = y.dim then .ok (x.add y) else .bad "dimension mismatch in +"
      | .missing w, _ => .missing w
      | _, .missing w => .missing w
      | .bad w, _ => .bad w
      | _, .bad w => .bad w
  | .sub a b =>
      match evalExpr cfg e a, evalExpr cfg e b with
      | .ok x, .ok y => if x.dim = y.dim then .ok (x.sub y) else .bad "dimension mismatch in -"
      | .missing w, _ => .missing w
      | _, .missing w => .missing w
      | .bad w, _ => .bad w
      | _, .bad w => .bad w
  | .mul a b =>
      match evalExpr cfg e a, evalExpr cfg e b with
      | .ok x, .ok y => .ok (x.mul y)
      | .missing w, _ => .missing w
      | _, .missing w => .missing w
      | .bad w, _ => .bad w
      | _, .bad w => .bad w
  | .neg a =>
      match evalExpr cfg e a with
      | .ok x => .ok x.neg
      | r => r

/-- `a ≤ b` evaluated exactly with a dimension check. -/
def checkLe (cfg : Configuration) (e : Experiment) (a b : Expr) : Outcome :=
  match evalExpr cfg e a, evalExpr cfg e b with
  | .ok x, .ok y =>
      if x.dim = y.dim then (if Q.le x.val y.val then .pass else .fail) else .unsupported
  | .missing _, _ => .unknown
  | _, .missing _ => .unknown
  | _, _ => .unsupported

/-- All validity bounds of a model must hold; otherwise the model is unsupported (or unknown). -/
def validityOutcome (cfg : Configuration) (e : Experiment) (vs : List (Expr × Expr)) : Outcome :=
  if ∀ p ∈ vs, checkLe cfg e p.1 p.2 = .pass then .pass
  else if ∃ p ∈ vs, checkLe cfg e p.1 p.2 = .unknown then .unknown
  else .unsupported

def checkCoupled (cfg : Configuration) (e : Experiment) (c : Coupled) : Outcome :=
  match condsResult cfg e c.conditions with
  | .fails => .notApplicable
  | .unknown => .unknown
  | .holds =>
      match validityOutcome cfg e c.validity with
      | .pass => checkLe cfg e c.lhs c.rhs
      | o => o

/-! ## Verdict -/

/-- Mandatory, applicable requirements. -/
def relevantReqs (e : Experiment) : List Requirement :=
  e.requirements.filter (fun r => r.mandatory && r.applicable)

/-- Mandatory, applicable coupled constraints. -/
def relevantCoupled (e : Experiment) : List Coupled :=
  e.coupled.filter (fun c => c.mandatory && c.applicable)

/-- Every outcome that can influence the verdict. -/
def outcomes (cfg : Configuration) (e : Experiment) : List Outcome :=
  (relevantReqs e).map (checkRequirement cfg e) ++ (relevantCoupled e).map (checkCoupled cfg e)

/-- The verdict.  Unconfirmed profiles are never accepted; any mandatory failure
rejects; acceptance needs every relevant outcome to pass (or be not applicable by
a definitely-false condition) and at least one to pass. -/
def verdict (cfg : Configuration) (e : Experiment) : Verdict :=
  if e.confirmed = false then .needMoreInfo
  else if .fail ∈ outcomes cfg e then .reject
  else if (∀ o ∈ outcomes cfg e, o = .pass ∨ o = .notApplicable) ∧ .pass ∈ outcomes cfg e then .accept
  else .needMoreInfo

/-! ## Results -/

structure ReqResult where
  requirement : Requirement
  perKey      : List (String × Option Capability × Outcome)
  outcome     : Outcome
deriving Repr, Inhabited

structure CoupledResult where
  coupled  : Coupled
  lhs      : EvalR
  rhs      : EvalR
  validity : List (EvalR × EvalR × Outcome)
  outcome  : Outcome
deriving Repr, Inhabited

structure Result where
  configurationId : String
  equipmentId     : String
  experimentId    : String
  verdict         : Verdict
  reqs            : List ReqResult
  coupled         : List CoupledResult
deriving Repr, Inhabited

def reqResult (cfg : Configuration) (e : Experiment) (r : Requirement) : ReqResult :=
  ⟨r, r.keys.map (fun k => (k, lookup cfg k, keyOutcome cfg r.constraint k)), checkRequirement cfg e r⟩

def coupledResult (cfg : Configuration) (e : Experiment) (c : Coupled) : CoupledResult :=
  ⟨c, evalExpr cfg e c.lhs, evalExpr cfg e c.rhs,
   c.validity.map (fun p => (evalExpr cfg e p.1, evalExpr cfg e p.2, checkLe cfg e p.1 p.2)),
   checkCoupled cfg e c⟩

def run (cfg : Configuration) (e : Experiment) : Result :=
  ⟨cfg.id, cfg.equipmentId, e.id, verdict cfg e,
   e.requirements.map (reqResult cfg e), e.coupled.map (coupledResult cfg e)⟩

/-- Check every candidate proposed by an untrusted search (Z3). -/
def checkCandidates (cs : List Configuration) (e : Experiment) : List Result :=
  cs.map (fun c => run c e)

end CryoLean
