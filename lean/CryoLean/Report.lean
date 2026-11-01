import Lean.Data.Json
import CryoLean.Model
import CryoLean.Checker
import CryoLean.Json
import CryoLean.Explain
/-!
# Result serialisation (v2)

Produced from `CryoLean.run`, whose verdict field is proven equal to
`verdict cfg e` (`run_binds_inputs`).  The output echoes a hash of the exact
input document, every requirement, every coupled constraint with the values
Lean computed, and plain-language explanations.
-/

namespace CryoLean
open Lean

def evalRToJson : EvalR → Json
  | .ok q => Json.mkObj [("status", "ok"), ("value", quantityToJson q), ("display", toJson (fmtQuantity q))]
  | .missing w => Json.mkObj [("status", "missing"), ("what", toJson w)]
  | .bad w => Json.mkObj [("status", "unsupported"), ("why", toJson w)]

def reqResultToJson (rr : ReqResult) : Json :=
  let r := rr.requirement
  Json.mkObj [
    ("kind", "requirement"),
    ("keys", toJson r.keys),
    ("mandatory", toJson r.mandatory),
    ("applicable", toJson r.applicable),
    ("conditions", toJson (r.conditions.map conditionToJson)),
    ("constraint", constraintToJson r.constraint),
    ("required_display", toJson (describeConstraint r.constraint)),
    ("requirement_origin", toJson (evidenceStatusToString r.origin)),
    ("requirement_rationale", toJson r.rationale),
    ("requirement_evidence_ids", toJson r.evidenceIds),
    ("per_key", toJson (rr.perKey.map (fun (k, c, o) => Json.mkObj [
        ("key", toJson k),
        ("capability", match c with | some c => capabilityToJson c | none => Json.null),
        ("available_display", toJson (match c with | some c => describeCapValue c.value | none => "not documented")),
        ("outcome", toJson (outcomeToString o))]))),
    ("outcome", toJson (outcomeToString rr.outcome)),
    ("explanation", toJson (explainReq rr))]

def coupledResultToJson (cr : CoupledResult) : Json :=
  let c := cr.coupled
  Json.mkObj [
    ("kind", "coupled"),
    ("id", toJson c.id),
    ("name", toJson c.name),
    ("model", toJson c.model),
    ("mandatory", toJson c.mandatory),
    ("applicable", toJson c.applicable),
    ("conditions", toJson (c.conditions.map conditionToJson)),
    ("lhs", evalRToJson cr.lhs),
    ("rhs", evalRToJson cr.rhs),
    ("validity", toJson (cr.validity.map (fun (a, b, o) => Json.mkObj [
        ("a", evalRToJson a), ("b", evalRToJson b), ("outcome", toJson (outcomeToString o))]))),
    ("origin", toJson (evidenceStatusToString c.origin)),
    ("rationale", toJson c.rationale),
    ("evidence_ids", toJson c.evidenceIds),
    ("outcome", toJson (outcomeToString cr.outcome)),
    ("explanation", toJson (explainCoupled cr))]

def resultToJson (res : Result) (inputHash : String) (experimentName industry : String) : Json :=
  let mreq := res.reqs.filter (fun r => r.requirement.mandatory && r.requirement.applicable)
  let mcp := res.coupled.filter (fun c => c.coupled.mandatory && c.coupled.applicable)
  Json.mkObj [
    ("checker", "CryoLean Lean 4 compatibility checker v2"),
    ("lean_version", toJson Lean.versionString),
    ("verdict", toJson (verdictToString res.verdict)),
    ("configuration_id", toJson res.configurationId),
    ("equipment_id", toJson res.equipmentId),
    ("experiment_id", toJson res.experimentId),
    ("experiment_name", toJson experimentName),
    ("industry", toJson industry),
    ("input_hash", toJson inputHash),
    ("mandatory_applicable_requirements", toJson mreq.length),
    ("mandatory_applicable_coupled", toJson mcp.length),
    ("summary", toJson (explainVerdict res)),
    ("checks", toJson (res.reqs.map reqResultToJson)),
    ("coupled_checks", toJson (res.coupled.map coupledResultToJson))]

/-- Decode a `{configuration, experiment}` document, run the checker, serialise. -/
def checkDocument (doc : Json) : Except String Json := do
  let cfg ← configurationFromJson (← doc.getObjVal? "configuration")
  let e ← experimentFromJson (← doc.getObjVal? "experiment")
  pure (resultToJson (run cfg e) (toString (hash doc.compress)) e.name e.industry)

/-- Decode `{experiment, candidates: [configuration]}` and check every candidate with `checkCandidates`. -/
def checkCandidatesDocument (doc : Json) : Except String Json := do
  let e ← experimentFromJson (← doc.getObjVal? "experiment")
  let cs ← (← (← doc.getObjVal? "candidates").getArr?).toList.mapM configurationFromJson
  let h := toString (hash doc.compress)
  pure (toJson ((checkCandidates cs e).map (fun r => resultToJson r h e.name e.industry)))

end CryoLean
