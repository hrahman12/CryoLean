import Lean.Data.Json
import CryoLean.Model
import CryoLean.Checker
import CryoLean.Json
import CryoLean.Explain
import CryoLean.Schedule
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

/-- Decode `{configuration, experiments, slots, run_length}` and run the proven `validSchedule`. -/
def checkScheduleDocument (doc : Json) : Except String Json := do
  let cfg ← configurationFromJson (← doc.getObjVal? "configuration")
  let exps ← (← (← doc.getObjVal? "experiments").getArr?).toList.mapM experimentFromJson
  let slots ← (← (← doc.getObjVal? "slots").getArr?).toList.mapM (fun j => do
    let q ← quantityFromJson (← j.getObjVal? "start")
    if q.dim ≠ secDim then throw "slot start must be in seconds"
    pure (⟨← getStr j "experiment_id", q.val⟩ : Slot))
  let L ← quantityFromJson (← doc.getObjVal? "run_length")
  let ok := validSchedule cfg exps slots L
  -- diagnostics (display only; the decision is `ok`)
  let reasons : List String :=
    (if slots.length ≠ exps.length then ["the number of slots differs from the number of experiments"] else []) ++
    (match cooldownOf cfg with
     | none => ["the configuration has no documented, trusted cooldown time (cooldown_time.max)"]
     | some cd => if cd.dim ≠ secDim then ["cooldown time is not in seconds"] else []) ++
    (if L.dim ≠ secDim then ["run length is not in seconds"] else []) ++
    ((exps.filter (fun e => verdict cfg e != .accept)).map (fun e => s!"experiment '{e.id}' is not accepted on this configuration ({verdictToString (verdict cfg e)})")) ++
    (match resolve exps slots with
     | none => ["slots do not match the experiments in order, or an experiment has no trusted run_duration in seconds"]
     | some ps =>
        (match cooldownOf cfg with
         | some cd => (ps.filter (fun p => !(decide (Q.le cd.val p.start)))).map (fun p => s!"slot '{p.experimentId}' starts before the cooldown is complete")
         | none => []) ++
        ((ps.filter (fun p => !(decide (Q.le p.stop L.val)))).map (fun p => s!"slot '{p.experimentId}' ends after the run")) ++
        (if decide (ps.Pairwise Disjoint) then [] else ["two slots overlap"]))
  let placed : List Json := match resolve exps slots with
    | some ps => ps.map (fun p => Json.mkObj [("experiment_id", toJson p.experimentId),
        ("start", quantityToJson ⟨p.start, secDim⟩), ("stop", quantityToJson ⟨p.stop, secDim⟩),
        ("start_display", toJson (fmtQuantity ⟨p.start, secDim⟩)), ("stop_display", toJson (fmtQuantity ⟨p.stop, secDim⟩))])
    | none => []
  pure (Json.mkObj [
    ("checker", "CryoLean Lean 4 validSchedule"),
    ("valid", toJson ok),
    ("configuration_id", toJson cfg.id),
    ("experiment_verdicts", toJson (exps.map (fun e => Json.mkObj [("experiment_id", toJson e.id), ("verdict", toJson (verdictToString (verdict cfg e)))]))),
    ("slots", toJson placed),
    ("run_length_display", toJson (fmtQuantity L)),
    ("reasons", toJson (if ok then ([] : List String) else reasons)),
    ("theorems", toJson ["validSchedule_sound", "validSchedule_bounds", "validSchedule_disjoint", "validSchedule_only_accepted"]),
    ("input_hash", toJson (toString (hash doc.compress)))])

end CryoLean
