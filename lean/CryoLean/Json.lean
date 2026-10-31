import Lean.Data.Json
import CryoLean.Model
import CryoLean.Checker
/-!
# JSON codec for the universal model

Decoding is *fail-closed*: any unrecognised enum string, missing field or wrong
shape is an error, never a default.  The data layer (Python) is responsible for
unit normalisation; here we only transport integer values and unit strings.
-/

namespace CryoLean
open Lean

def quantityFromJson (j : Json) : Except String Quantity := do
  let v ← (← j.getObjVal? "value").getInt?
  let u ← (← j.getObjVal? "unit").getStr?
  pure ⟨v, u⟩

def quantityToJson (q : Quantity) : Json :=
  Json.mkObj [("value", toJson q.value), ("unit", toJson q.unit)]

def evidenceStatusFromJson (j : Json) : Except String EvidenceStatus := do
  match ← j.getStr? with
  | "manufacturer_specification" => pure .manufacturerSpecification
  | "experimental_observation"   => pure .experimentalObservation
  | "user_entered"               => pure .userEntered
  | "inferred_estimate"          => pure .inferredEstimate
  | "unknown"                    => pure .unknown
  | s => throw s!"unknown evidence_status '{s}'"

def evidenceStatusToString : EvidenceStatus → String
  | .manufacturerSpecification => "manufacturer_specification"
  | .experimentalObservation   => "experimental_observation"
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
  | .installed              => "installed"
  | .optionalNotInstalled   => "optional_not_installed"
  | .unknown                => "unknown"

def capValueFromJson (j : Json) : Except String CapValue := do
  match ← (← j.getObjVal? "kind").getStr? with
  | "range"   => pure (.range (← quantityFromJson (← j.getObjVal? "lo")) (← quantityFromJson (← j.getObjVal? "hi")))
  | "max"     => pure (.max (← quantityFromJson (← j.getObjVal? "q")))
  | "min"     => pure (.min (← quantityFromJson (← j.getObjVal? "q")))
  | "flag"    => pure (.flag (← (← j.getObjVal? "b").getBool?))
  | "count"   => pure (.count (← (← j.getObjVal? "n").getNat?))
  | "unknown" => pure .unknown
  | s => throw s!"unknown capability value kind '{s}'"

def capValueToJson : CapValue → Json
  | .range lo hi => Json.mkObj [("kind", "range"), ("lo", quantityToJson lo), ("hi", quantityToJson hi)]
  | .max q       => Json.mkObj [("kind", "max"), ("q", quantityToJson q)]
  | .min q       => Json.mkObj [("kind", "min"), ("q", quantityToJson q)]
  | .flag b      => Json.mkObj [("kind", "flag"), ("b", toJson b)]
  | .count n     => Json.mkObj [("kind", "count"), ("n", toJson n)]
  | .unknown     => Json.mkObj [("kind", "unknown")]

def constraintFromJson (j : Json) : Except String Constraint := do
  match ← (← j.getObjVal? "kind").getStr? with
  | "point_within"   => pure (.pointWithin (← quantityFromJson (← j.getObjVal? "q")))
  | "range_within"   => pure (.rangeWithin (← quantityFromJson (← j.getObjVal? "lo")) (← quantityFromJson (← j.getObjVal? "hi")))
  | "at_least"       => pure (.atLeast (← quantityFromJson (← j.getObjVal? "q")))
  | "at_most"        => pure (.atMost (← quantityFromJson (← j.getObjVal? "q")))
  | "present"        => pure .present
  | "count_at_least" => pure (.countAtLeast (← (← j.getObjVal? "n").getNat?))
  | s => throw s!"unknown constraint kind '{s}'"

def constraintToJson : Constraint → Json
  | .pointWithin q    => Json.mkObj [("kind", "point_within"), ("q", quantityToJson q)]
  | .rangeWithin lo hi => Json.mkObj [("kind", "range_within"), ("lo", quantityToJson lo), ("hi", quantityToJson hi)]
  | .atLeast q        => Json.mkObj [("kind", "at_least"), ("q", quantityToJson q)]
  | .atMost q         => Json.mkObj [("kind", "at_most"), ("q", quantityToJson q)]
  | .present          => Json.mkObj [("kind", "present")]
  | .countAtLeast n   => Json.mkObj [("kind", "count_at_least"), ("n", toJson n)]

def stringListFromJson (j : Json) : Except String (List String) := do
  let arr ← j.getArr?
  arr.toList.mapM Json.getStr?

def optField (j : Json) (k : String) : Option Json :=
  match j.getObjVal? k with
  | .ok v => some v
  | .error _ => none

def capabilityFromJson (j : Json) : Except String Capability := do
  let key ← (← j.getObjVal? "key").getStr?
  let value ← capValueFromJson (← j.getObjVal? "value")
  let install ← installStatusFromJson (← j.getObjVal? "install")
  let evidence ← evidenceStatusFromJson (← j.getObjVal? "evidence_status")
  let ids ← match optField j "evidence_ids" with
    | some a => stringListFromJson a
    | none => pure []
  pure ⟨key, value, install, evidence, ids⟩

def capabilityToJson (c : Capability) : Json :=
  Json.mkObj [
    ("key", toJson c.key),
    ("value", capValueToJson c.value),
    ("install", toJson (installStatusToString c.install)),
    ("evidence_status", toJson (evidenceStatusToString c.evidence)),
    ("evidence_ids", toJson c.evidenceIds)]

def configurationFromJson (j : Json) : Except String Configuration := do
  let id ← (← j.getObjVal? "id").getStr?
  let eq ← (← j.getObjVal? "equipment_id").getStr?
  let name ← (← j.getObjVal? "name").getStr?
  let caps ← (← (← j.getObjVal? "capabilities").getArr?).toList.mapM capabilityFromJson
  pure ⟨id, eq, name, caps⟩

def requirementFromJson (j : Json) : Except String Requirement := do
  let key ← (← j.getObjVal? "key").getStr?
  let c ← constraintFromJson (← j.getObjVal? "constraint")
  let m ← (← j.getObjVal? "mandatory").getBool?
  let o ← evidenceStatusFromJson (← j.getObjVal? "origin")
  let rationale ← match optField j "rationale" with
    | some s => s.getStr?
    | none => pure ""
  let ids ← match optField j "evidence_ids" with
    | some a => stringListFromJson a
    | none => pure []
  pure ⟨key, c, m, o, rationale, ids⟩

def requirementToJson (r : Requirement) : Json :=
  Json.mkObj [
    ("key", toJson r.key),
    ("constraint", constraintToJson r.constraint),
    ("mandatory", toJson r.mandatory),
    ("origin", toJson (evidenceStatusToString r.origin)),
    ("rationale", toJson r.rationale),
    ("evidence_ids", toJson r.evidenceIds)]

def experimentFromJson (j : Json) : Except String Experiment := do
  let id ← (← j.getObjVal? "id").getStr?
  let name ← (← j.getObjVal? "name").getStr?
  let industry ← (← j.getObjVal? "industry").getStr?
  let reqs ← (← (← j.getObjVal? "requirements").getArr?).toList.mapM requirementFromJson
  let confirmed ← (← j.getObjVal? "confirmed").getBool?
  pure ⟨id, name, industry, reqs, confirmed⟩

def outcomeToString : Outcome → String
  | .pass        => "pass"
  | .fail        => "fail"
  | .unknown     => "unknown"
  | .unsupported => "unsupported"

def verdictToString : Verdict → String
  | .accept       => "ACCEPT"
  | .reject       => "REJECT"
  | .needMoreInfo => "NEED_MORE_INFORMATION"

end CryoLean
