import Lean.Data.Json
import CryoLean.Model
import CryoLean.Checker
/-!
# JSON codec (v2) — the auditable serialization boundary

Decoding is *fail-closed*: an unrecognised enum string, a missing mandatory
field, a wrong shape or a zero denominator is a decoding error, never a
default.  Optional fields with a documented default: `applicable` (true),
`conditions` ([]), `coupled` ([]), `params` ([]), `evidence_ids` ([]),
`rationale` (""), and the dimension exponents (0).  Unknown extra fields
(for example a `"verdict"` someone injected into the document) are ignored:
the verdict is always recomputed.
-/

namespace CryoLean
open Lean

def optField (j : Json) (k : String) : Option Json :=
  match j.getObjVal? k with
  | .ok Json.null => none
  | .ok v => some v
  | .error _ => none

def getStr (j : Json) (k : String) : Except String String := do
  match j.getObjVal? k with
  | .ok v => match v.getStr? with
    | .ok s => pure s
    | .error _ => throw s!"field '{k}' must be a string"
  | .error _ => throw s!"missing field '{k}'"

def getBool (j : Json) (k : String) : Except String Bool := do
  match j.getObjVal? k with
  | .ok v => match v.getBool? with
    | .ok b => pure b
    | .error _ => throw s!"field '{k}' must be a boolean"
  | .error _ => throw s!"missing field '{k}'"

def getBoolD (j : Json) (k : String) (d : Bool) : Except String Bool :=
  match optField j k with
  | some v => match v.getBool? with
    | .ok b => pure b
    | .error _ => throw s!"field '{k}' must be a boolean"
  | none => pure d

def strList (j : Json) : Except String (List String) := do
  (← j.getArr?).toList.mapM Json.getStr?

def strListD (j : Json) (k : String) : Except String (List String) :=
  match optField j k with
  | some a => strList a
  | none => pure []

def dimKeys : List String := ["K", "m", "kg", "s", "A", "mol", "cd"]

def dimFromJson (j : Json) : Except String Dim := do
  let obj ← match j.getObj? with
    | .ok o => pure o
    | .error _ => throw "'dim' must be an object"
  for (k, _) in obj.toList do
    if !(dimKeys.contains k) then throw s!"unknown dimension name '{k}' (allowed: {dimKeys})"
  let g (k : String) : Except String Int :=
    match optField j k with
    | some v => v.getInt?
    | none => pure 0
  pure ⟨← g "K", ← g "m", ← g "kg", ← g "s", ← g "A", ← g "mol", ← g "cd"⟩

def dimToJson (d : Dim) : Json :=
  Json.mkObj [("K", toJson d.K), ("m", toJson d.m), ("kg", toJson d.kg), ("s", toJson d.s),
              ("A", toJson d.A), ("mol", toJson d.mol), ("cd", toJson d.cd)]

def quantityFromJson (j : Json) : Except String Quantity := do
  let num ← (← j.getObjVal? "num").getInt?
  let den ← (← j.getObjVal? "den").getNat?
  if den = 0 then throw "quantity denominator must be positive"
  let dim ← match optField j "dim" with
    | some d => dimFromJson d
    | none => throw "quantity is missing its dimension 'dim'"
  pure ⟨⟨num, den⟩, dim⟩

def quantityToJson (q : Quantity) : Json :=
  Json.mkObj [("num", toJson q.val.num), ("den", toJson q.val.den), ("dim", dimToJson q.dim)]

def evidenceStatusFromJson (j : Json) : Except String EvidenceStatus := do
  match ← j.getStr? with
  | "manufacturer_specification" => pure .manufacturerSpecification
  | "experimental_observation"   => pure .experimentalObservation
  | "reference_data"             => pure .referenceData
  | "certified_simulation"       => pure .certifiedSimulation
  | "user_entered"               => pure .userEntered
  | "inferred_estimate"          => pure .inferredEstimate
  | "unknown"                    => pure .unknown
  | s => throw s!"unknown evidence_status '{s}'"

def evidenceStatusToString : EvidenceStatus → String
  | .manufacturerSpecification => "manufacturer_specification"
  | .experimentalObservation   => "experimental_observation"
  | .referenceData             => "reference_data"
  | .certifiedSimulation       => "certified_simulation"
  | .userEntered               => "user_entered"
  | .inferredEstimate          => "inferred_estimate"
  | .unknown                   => "unknown"

def installStatusFromJson (j : Json) : Except String InstallStatus := do
  match ← j.getStr? with
  | "installed"              => pure .installed
  | "optional_not_installed" => pure .optionalNotInstalled
  | "unknown"                => pure .unknown
  | s => throw s!"unknown install status '{s}'"

def installStatusToString : InstallStatus → String
  | .installed            => "installed"
  | .optionalNotInstalled => "optional_not_installed"
  | .unknown              => "unknown"

def capValueFromJson (j : Json) : Except String CapValue := do
  match ← getStr j "kind" with
  | "range"   => pure (.range (← quantityFromJson (← j.getObjVal? "lo")) (← quantityFromJson (← j.getObjVal? "hi")))
  | "max"     => pure (.max (← quantityFromJson (← j.getObjVal? "q")))
  | "min"     => pure (.min (← quantityFromJson (← j.getObjVal? "q")))
  | "flag"    => pure (.flag (← getBool j "b"))
  | "count"   => pure (.count (← (← j.getObjVal? "n").getNat?))
  | "enum"    => pure (.enum (← getStr j "s"))
  | "set"     => pure (.set (← strList (← j.getObjVal? "xs")))
  | "unknown" => pure .unknown
  | s => throw s!"unknown capability value kind '{s}'"

def capValueToJson : CapValue → Json
  | .range lo hi => Json.mkObj [("kind", "range"), ("lo", quantityToJson lo), ("hi", quantityToJson hi)]
  | .max q       => Json.mkObj [("kind", "max"), ("q", quantityToJson q)]
  | .min q       => Json.mkObj [("kind", "min"), ("q", quantityToJson q)]
  | .flag b      => Json.mkObj [("kind", "flag"), ("b", toJson b)]
  | .count n     => Json.mkObj [("kind", "count"), ("n", toJson n)]
  | .enum s      => Json.mkObj [("kind", "enum"), ("s", toJson s)]
  | .set xs      => Json.mkObj [("kind", "set"), ("xs", toJson xs)]
  | .unknown     => Json.mkObj [("kind", "unknown")]

def constraintFromJson (j : Json) : Except String Constraint := do
  match ← getStr j "kind" with
  | "point_within"   => pure (.pointWithin (← quantityFromJson (← j.getObjVal? "q")))
  | "range_within"   => pure (.rangeWithin (← quantityFromJson (← j.getObjVal? "lo")) (← quantityFromJson (← j.getObjVal? "hi")))
  | "at_least"       => pure (.atLeast (← quantityFromJson (← j.getObjVal? "q")))
  | "at_most"        => pure (.atMost (← quantityFromJson (← j.getObjVal? "q")))
  | "present"        => pure (.flagIs true)
  | "absent"         => pure (.flagIs false)
  | "flag_is"        => pure (.flagIs (← getBool j "b"))
  | "count_at_least" => pure (.countAtLeast (← (← j.getObjVal? "n").getNat?))
  | "count_equals"   => pure (.countEquals (← (← j.getObjVal? "n").getNat?))
  | "enum_in"        => do
      let xs ← strList (← j.getObjVal? "allowed")
      if xs.isEmpty then throw "enum_in needs a non-empty 'allowed' list"
      pure (.enumIn xs)
  | "set_contains"   => do
      let xs ← strList (← j.getObjVal? "needed")
      if xs.isEmpty then throw "set_contains needs a non-empty 'needed' list (an empty list would pass vacuously)"
      pure (.setContains xs)
  | s => throw s!"unknown constraint kind '{s}'"

def constraintToJson : Constraint → Json
  | .pointWithin q     => Json.mkObj [("kind", "point_within"), ("q", quantityToJson q)]
  | .rangeWithin lo hi => Json.mkObj [("kind", "range_within"), ("lo", quantityToJson lo), ("hi", quantityToJson hi)]
  | .atLeast q         => Json.mkObj [("kind", "at_least"), ("q", quantityToJson q)]
  | .atMost q          => Json.mkObj [("kind", "at_most"), ("q", quantityToJson q)]
  | .flagIs b          => Json.mkObj [("kind", "flag_is"), ("b", toJson b)]
  | .countAtLeast n    => Json.mkObj [("kind", "count_at_least"), ("n", toJson n)]
  | .countEquals n     => Json.mkObj [("kind", "count_equals"), ("n", toJson n)]
  | .enumIn xs         => Json.mkObj [("kind", "enum_in"), ("allowed", toJson xs)]
  | .setContains xs    => Json.mkObj [("kind", "set_contains"), ("needed", toJson xs)]

def conditionFromJson (j : Json) : Except String Condition := do
  match ← getStr j "kind" with
  | "cap_flag"       => pure (.capFlag (← getStr j "key") (← getBool j "b"))
  | "param_at_most"  => pure (.paramAtMost (← getStr j "name") (← quantityFromJson (← j.getObjVal? "q")))
  | "param_at_least" => pure (.paramAtLeast (← getStr j "name") (← quantityFromJson (← j.getObjVal? "q")))
  | s => throw s!"unknown condition kind '{s}'"

def conditionToJson : Condition → Json
  | .capFlag k b        => Json.mkObj [("kind", "cap_flag"), ("key", toJson k), ("b", toJson b)]
  | .paramAtMost n q    => Json.mkObj [("kind", "param_at_most"), ("name", toJson n), ("q", quantityToJson q)]
  | .paramAtLeast n q   => Json.mkObj [("kind", "param_at_least"), ("name", toJson n), ("q", quantityToJson q)]

def conditionsD (j : Json) : Except String (List Condition) :=
  match optField j "conditions" with
  | some a => do (← a.getArr?).toList.mapM conditionFromJson
  | none => pure []

def capabilityFromJson (j : Json) : Except String Capability := do
  pure ⟨← getStr j "key", ← capValueFromJson (← j.getObjVal? "value"),
        ← installStatusFromJson (← j.getObjVal? "install"),
        ← evidenceStatusFromJson (← j.getObjVal? "evidence_status"), ← strListD j "evidence_ids"⟩

def capabilityToJson (c : Capability) : Json :=
  Json.mkObj [("key", toJson c.key), ("value", capValueToJson c.value),
    ("install", toJson (installStatusToString c.install)),
    ("evidence_status", toJson (evidenceStatusToString c.evidence)), ("evidence_ids", toJson c.evidenceIds)]

/-- The first repeated string, if any. -/
def firstDuplicate : List String → Option String
  | [] => none
  | x :: xs => if xs.contains x then some x else firstDuplicate xs

def configurationFromJson (j : Json) : Except String Configuration := do
  let caps ← (← (← j.getObjVal? "capabilities").getArr?).toList.mapM capabilityFromJson
  match firstDuplicate (caps.map (·.key)) with
  | some k => throw s!"duplicate capability key '{k}' (the verdict must not depend on record order)"
  | none => pure ()
  pure ⟨← getStr j "id", ← getStr j "equipment_id", ← getStr j "name", caps⟩

def paramFromJson (j : Json) : Except String Param := do
  let v ← match optField j "value" with
    | some q => some <$> quantityFromJson q
    | none => pure none
  pure ⟨← getStr j "name", v, ← evidenceStatusFromJson (← j.getObjVal? "origin")⟩

def requirementFromJson (j : Json) : Except String Requirement := do
  let keys ← match optField j "keys" with
    | some a => strList a
    | none => do pure [← getStr j "key"]
  if keys.isEmpty then throw "a requirement needs at least one key"
  let rationale ← match optField j "rationale" with
    | some s => s.getStr?
    | none => pure ""
  pure ⟨keys, ← constraintFromJson (← j.getObjVal? "constraint"), ← getBool j "mandatory",
        ← getBoolD j "applicable" true, ← conditionsD j, ← evidenceStatusFromJson (← j.getObjVal? "origin"),
        rationale, ← strListD j "evidence_ids"⟩

def selFromJson (s : String) : Except String Sel :=
  match s with
  | "lo" => pure .lo | "hi" => pure .hi | "max" => pure .max | "min" => pure .min | "count" => pure .count
  | s => throw s!"unknown selector '{s}'"

/-- Maximum nesting depth of a coupled-constraint expression.  Bounding the depth makes the decoder
total (no `partial`; flagged by the for-all-dev/forensics extractor) and refuses absurdly deep input. -/
def exprMaxDepth : Nat := 64

/-- Decode an expression, with `fuel` bounding the nesting depth (total, fail-closed). -/
def exprFromJsonFuel : Nat → Json → Except String Expr
  | 0, _ => throw s!"expression nested deeper than {exprMaxDepth} levels"
  | fuel + 1, j => do
    match ← getStr j "op" with
    | "lit"   => pure (.lit (← quantityFromJson (← j.getObjVal? "q")))
    | "cap"   => pure (.cap (← getStr j "key") (← selFromJson (← getStr j "sel")))
    | "param" => pure (.param (← getStr j "name"))
    | "add"   => pure (.add (← exprFromJsonFuel fuel (← j.getObjVal? "a")) (← exprFromJsonFuel fuel (← j.getObjVal? "b")))
    | "sub"   => pure (.sub (← exprFromJsonFuel fuel (← j.getObjVal? "a")) (← exprFromJsonFuel fuel (← j.getObjVal? "b")))
    | "mul"   => pure (.mul (← exprFromJsonFuel fuel (← j.getObjVal? "a")) (← exprFromJsonFuel fuel (← j.getObjVal? "b")))
    | "neg"   => pure (.neg (← exprFromJsonFuel fuel (← j.getObjVal? "a")))
    | s => throw s!"unknown expression op '{s}'"

def exprFromJson (j : Json) : Except String Expr := exprFromJsonFuel exprMaxDepth j

def coupledFromJson (j : Json) : Except String Coupled := do
  let validity ← match optField j "validity" with
    | some a => do (← a.getArr?).toList.mapM (fun p => do
        pure (← exprFromJson (← p.getObjVal? "a"), ← exprFromJson (← p.getObjVal? "b")))
    | none => pure []
  let rationale ← match optField j "rationale" with
    | some s => s.getStr?
    | none => pure ""
  pure ⟨← getStr j "id", ← getStr j "name", ← getStr j "model",
        ← exprFromJson (← j.getObjVal? "lhs"), ← exprFromJson (← j.getObjVal? "rhs"), validity,
        ← getBool j "mandatory", ← getBoolD j "applicable" true, ← conditionsD j,
        ← evidenceStatusFromJson (← j.getObjVal? "origin"), rationale, ← strListD j "evidence_ids"⟩

def experimentFromJson (j : Json) : Except String Experiment := do
  let params ← match optField j "params" with
    | some a => do (← a.getArr?).toList.mapM paramFromJson
    | none => pure []
  match firstDuplicate (params.map (·.name)) with
  | some n => throw s!"duplicate parameter '{n}' (the verdict must not depend on record order)"
  | none => pure ()
  let reqs ← (← (← j.getObjVal? "requirements").getArr?).toList.mapM requirementFromJson
  let coupled ← match optField j "coupled" with
    | some a => do (← a.getArr?).toList.mapM coupledFromJson
    | none => pure []
  pure ⟨← getStr j "id", ← getStr j "name", ← getStr j "industry", params, reqs, coupled, ← getBool j "confirmed"⟩

def outcomeToString : Outcome → String
  | .pass          => "pass"
  | .fail          => "fail"
  | .unknown       => "unknown"
  | .unsupported   => "unsupported"
  | .notApplicable => "not_applicable"

def verdictToString : Verdict → String
  | .accept       => "REQUIREMENTS_MET"
  | .reject       => "DOES_NOT_MEET_REQUIREMENTS"
  | .needMoreInfo => "NEED_MORE_INFORMATION"

end CryoLean
