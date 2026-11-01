import CryoLean.Model
import CryoLean.Num
import CryoLean.Checker
import CryoLean.Json
/-!
# Plain-language explanations (v2)

Generated from the *same* decoded inputs and the *same* evaluations the verdict
used.  Display only: nothing here influences a verdict.
-/

namespace CryoLean

/-- Named SI units for common dimensions. -/
def unitSymbol (d : Dim) : Option String :=
  if d = {} then some ""
  else if d = { K := 1 } then some "K"
  else if d = { m := 1 } then some "m"
  else if d = { kg := 1 } then some "kg"
  else if d = { s := 1 } then some "s"
  else if d = { A := 1 } then some "A"
  else if d = { kg := 1, m := 2, s := -3 } then some "W"
  else if d = { kg := 1, m := 2, s := -2 } then some "J"
  else if d = { kg := 1, s := -2, A := -1 } then some "T"
  else if d = { kg := 1, m := -1, s := -2 } then some "Pa"
  else if d = { s := -1 } then some "Hz"
  else if d = { kg := 1, m := 2, s := -3, A := -1 } then some "V"
  else if d = { kg := 1, m := 2, s := -3, A := -2 } then some "Ω"
  else if d = { K := 1, s := -1 } then some "K/s"
  else if d = { kg := 1, s := -3, A := -1 } then some "T/s"
  else if d = { m := 2 } then some "m²"
  else if d = { m := 3 } then some "m³"
  else if d = { kg := 1, m := 2, s := -3, K := -1 } then some "W/K"
  else if d = { kg := 1, m := 3, s := -3, A := -2 } then some "Ω·m"
  else none

def dimString (d : Dim) : String :=
  let parts := [("K", d.K), ("m", d.m), ("kg", d.kg), ("s", d.s), ("A", d.A), ("mol", d.mol), ("cd", d.cd)]
  " ".intercalate ((parts.filter (·.2 ≠ 0)).map (fun (n, e) => if e = 1 then n else s!"{n}^{e}"))

def pow10 (n : Nat) : Nat := 10 ^ n

/-- Is |num/den| ≥ 10^e ? -/
def geTenPow (num : Nat) (den : Nat) (e : Int) : Bool :=
  if e ≥ 0 then decide (num ≥ den * pow10 e.toNat) else decide (num * pow10 (-e).toNat ≥ den)

def prefixFor : Int → String
  | 9 => "G" | 6 => "M" | 3 => "k" | 0 => "" | -3 => "m" | -6 => "µ" | -9 => "n" | -12 => "p" | _ => "?"

/-- Render |num/den| / 10^e with up to three decimals (rounded half up). -/
def renderScaled (num den : Nat) (e : Int) : String :=
  let a := num * pow10 (3 + (if e < 0 then (-e).toNat else 0))
  let b := den * (if e > 0 then pow10 e.toNat else 1)
  let m := (2 * a + b) / (2 * b)
  let whole := m / 1000
  let frac := m % 1000
  if frac = 0 then toString whole
  else
    let s := toString frac
    let s := "".pushn '0' (3 - s.length) ++ s
    let s := String.ofList (s.toList.reverse.dropWhile (· == '0')).reverse
    toString whole ++ "." ++ s

/-- Human-friendly rendering of a quantity, e.g. 1.8 K, 9 T, 12 µW. -/
def fmtQuantity (q : Quantity) : String :=
  let neg := q.val.num < 0
  let n := q.val.num.natAbs
  let d := q.val.den
  let sign := if neg then "-" else ""
  match unitSymbol q.dim with
  | some u =>
    if u = "" || u = "kg" || u = "K/s" || u = "T/s" || u = "W/K" || u = "Ω·m" then
      s!"{sign}{renderScaled n d 0}{if u = "" then "" else " " ++ u}"
    else if n = 0 then s!"0 {u}"
    else
      let e := ([9, 6, 3, 0, -3, -6, -9, -12] : List Int).find? (fun e => geTenPow n d e) |>.getD (-12)
      s!"{sign}{renderScaled n d e} {prefixFor e}{u}"
  | none => s!"{sign}{renderScaled n d 0} [{dimString q.dim}]"

def describeConstraint : Constraint → String
  | .pointWithin q     => s!"must be able to operate at {fmtQuantity q}"
  | .rangeWithin lo hi => s!"must cover the whole range {fmtQuantity lo} to {fmtQuantity hi}"
  | .atLeast q         => s!"needs at least {fmtQuantity q}"
  | .atMost q          => s!"needs {fmtQuantity q} or lower"
  | .flagIs true       => "must be installed / available"
  | .flagIs false      => "must be absent"
  | .countAtLeast n    => s!"needs at least {n}"
  | .countEquals n     => s!"needs exactly {n}"
  | .enumIn xs         => s!"must be one of {xs}"
  | .setContains xs    => s!"must support all of {xs}"

def describeCapValue : CapValue → String
  | .range lo hi => s!"a documented range of {fmtQuantity lo} to {fmtQuantity hi}"
  | .max q       => s!"a documented maximum of {fmtQuantity q}"
  | .min q       => s!"a documented minimum of {fmtQuantity q}"
  | .flag true   => "documented as present"
  | .flag false  => "documented as absent"
  | .count n     => s!"a documented count of {n}"
  | .enum s      => s!"the documented value '{s}'"
  | .set xs      => s!"the documented set {xs}"
  | .unknown     => "no documented value (UNKNOWN)"

def describeEvidence : EvidenceStatus → String
  | .manufacturerSpecification => "manufacturer specification"
  | .experimentalObservation   => "experimental observation"
  | .referenceData             => "reference data"
  | .certifiedSimulation       => "certified simulation (Lanyon, Gatekeeper-admitted proof)"
  | .userEntered               => "user-entered value"
  | .inferredEstimate          => "inferred estimate"
  | .unknown                   => "no recorded provenance"

def keyPhrase (keys : List String) : String :=
  match keys with
  | [k] => s!"'{k}'"
  | ks => s!"one of {ks}"

def explainKey (k : Constraint) (key : String) (cap : Option Capability) (o : Outcome) : String :=
  let what := s!"'{key}' {describeConstraint k}"
  match cap, o with
  | none, _ => s!"{what}, but this configuration has no documented value for '{key}'."
  | some c, .pass => s!"{what}; this configuration has {describeCapValue c.value} ({describeEvidence c.evidence})."
  | some c, .fail =>
      match c.install with
      | .optionalNotInstalled => s!"{what}, but '{key}' is documented as not fitted or not available in this configuration ({describeEvidence c.evidence})."
      | _ => s!"{what}, but this configuration has {describeCapValue c.value} ({describeEvidence c.evidence})."
  | some c, .unknown =>
      if c.value == .unknown && c.install != .unknown then
        s!"{what}, but the documented value for '{key}' is UNKNOWN for this configuration."
      else match c.install, c.evidence with
        | .unknown, _ => s!"{what}, but the documentation does not say whether '{key}' is fitted to this configuration."
        | _, .inferredEstimate => s!"{what}; the only value for '{key}' is an inferred estimate, which cannot support a verified result."
        | _, .unknown => s!"{what}; the value recorded for '{key}' has no provenance."
        | _, _ => s!"{what}, but the documented value for '{key}' is UNKNOWN."
  | some c, .unsupported =>
      s!"{what}, but it cannot be compared with {describeCapValue c.value}: the dimensions or value shapes differ."
  | some _, .notApplicable => s!"{what}: not applicable."

def explainReq (rr : ReqResult) : String :=
  let r := rr.requirement
  match rr.outcome with
  | .notApplicable => s!"{keyPhrase r.keys} {describeConstraint r.constraint}: not applicable here (a condition of this requirement is false)."
  | .unknown =>
      match rr.perKey with
      | [] => s!"{keyPhrase r.keys}: whether this requirement applies cannot be decided (a condition depends on missing information)."
      | _ =>
        if rr.perKey.all (fun (_, _, o) => o == .unknown || o == .unsupported || o == .fail) &&
           rr.perKey.any (fun (_, _, o) => o == .unknown) then
          " ".intercalate (rr.perKey.map (fun (k, c, o) => explainKey r.constraint k c o)) ++ " We need more information."
        else s!"{keyPhrase r.keys}: whether this requirement applies cannot be decided (a condition depends on missing information)."
  | .pass =>
      match rr.perKey.find? (fun (_, _, o) => o == .pass) with
      | some (k, c, o) => explainKey r.constraint k c o ++ " Requirement met."
      | none => "Requirement met."
  | .fail => " ".intercalate (rr.perKey.map (fun (k, c, o) => explainKey r.constraint k c o)) ++ " Requirement not met."
  | .unsupported => " ".intercalate (rr.perKey.map (fun (k, c, o) => explainKey r.constraint k c o)) ++ " The requirement is unsupported as stated."

def evalRString : EvalR → String
  | .ok q => fmtQuantity q
  | .missing w => s!"missing ({w})"
  | .bad w => s!"not computable ({w})"

def explainCoupled (cr : CoupledResult) : String :=
  let c := cr.coupled
  let l := evalRString cr.lhs
  let r := evalRString cr.rhs
  match cr.outcome with
  | .pass => s!"{c.name}: {l} ≤ {r}. Constraint met."
  | .fail => s!"{c.name}: {l} exceeds {r}. Constraint not met."
  | .unknown => s!"{c.name}: cannot be evaluated because information is missing (left side: {l}; right side: {r}). We need more information."
  | .unsupported =>
      if cr.validity.any (fun (_, _, o) => o == .fail || o == .unsupported) then
        s!"{c.name}: the physical model '{c.model}' is not valid for these conditions, so the check is unsupported."
      else s!"{c.name}: cannot be computed ({l} vs {r}); the check is unsupported."
  | .notApplicable => s!"{c.name}: not applicable here (a condition of this constraint is false)."

def explainVerdict (res : Result) : String :=
  let mreq := res.reqs.filter (fun r => r.requirement.mandatory && r.requirement.applicable)
  let mcp := res.coupled.filter (fun c => c.coupled.mandatory && c.coupled.applicable)
  let failedR := (mreq.filter (·.outcome == .fail)).map (fun r => keyPhrase r.requirement.keys)
  let failedC := (mcp.filter (·.outcome == .fail)).map (fun c => c.coupled.name)
  let openR := (mreq.filter (fun r => r.outcome == .unknown || r.outcome == .unsupported)).map (fun r => keyPhrase r.requirement.keys)
  let openC := (mcp.filter (fun c => c.outcome == .unknown || c.outcome == .unsupported)).map (fun c => c.coupled.name)
  match res.verdict with
  | .accept => s!"Requirements met. All {mreq.length} applicable mandatory requirements and {mcp.length} coupled constraints are satisfied by the documented capabilities of this configuration."
  | .reject => s!"Does not meet requirements. A documented limitation conflicts with: {", ".intercalate (failedR ++ failedC)}."
  | .needMoreInfo =>
      if mreq.isEmpty && mcp.isEmpty then "Need more information. This experiment profile has no applicable mandatory requirements yet."
      else if (openR ++ openC).isEmpty then "Need more information. The requirements have not been confirmed by the user."
      else s!"Need more information. The available evidence does not establish: {", ".intercalate (openR ++ openC)}."

end CryoLean
