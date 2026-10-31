import Lean.Data.Json
import CryoLean.Model
import CryoLean.Checker
import CryoLean.Json
import CryoLean.Explain
/-!
# Result serialisation

The output is produced from `CryoLean.run`, whose verdict field is proven equal
to `verdict cfg e` (`run_binds_inputs`).  We additionally echo a hash of the
exact input document so the API layer can bind the result to what it sent.
-/

namespace CryoLean
open Lean

def checkResultToJson (cr : CheckResult) : Json :=
  Json.mkObj [
    ("key", toJson cr.requirement.key),
    ("mandatory", toJson cr.requirement.mandatory),
    ("constraint", constraintToJson cr.requirement.constraint),
    ("requirement_origin", toJson (evidenceStatusToString cr.requirement.origin)),
    ("requirement_rationale", toJson cr.requirement.rationale),
    ("requirement_evidence_ids", toJson cr.requirement.evidenceIds),
    ("capability", match cr.capability with | some c => capabilityToJson c | none => Json.null),
    ("outcome", toJson (outcomeToString cr.outcome)),
    ("explanation", toJson (explainCheck cr))]

def resultToJson (res : Result) (inputHash : String) (experimentName industry : String) : Json :=
  Json.mkObj [
    ("checker", "CryoLean Lean 4 compatibility checker"),
    ("lean_version", toJson Lean.versionString),
    ("verdict", toJson (verdictToString res.verdict)),
    ("configuration_id", toJson res.configurationId),
    ("equipment_id", toJson res.equipmentId),
    ("experiment_id", toJson res.experimentId),
    ("experiment_name", toJson experimentName),
    ("industry", toJson industry),
    ("input_hash", toJson inputHash),
    ("mandatory_requirements", toJson (res.checks.filter (·.requirement.mandatory)).length),
    ("summary", toJson (explainVerdict res)),
    ("checks", toJson (res.checks.map checkResultToJson))]

/-- Decode a `{configuration, experiment}` document, run the checker, serialise. -/
def checkDocument (doc : Json) : Except String Json := do
  let cfg ← configurationFromJson (← doc.getObjVal? "configuration")
  let e ← experimentFromJson (← doc.getObjVal? "experiment")
  let res := run cfg e
  let h := toString (hash doc.compress)
  pure (resultToJson res h e.name e.industry)

end CryoLean
