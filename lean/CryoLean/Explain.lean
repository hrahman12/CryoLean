import CryoLean.Model
import CryoLean.Checker
import CryoLean.Json
/-!
# Plain-language explanations

Generated from the *same* decoded inputs the verdict used, so the explanation
can never describe a different configuration than the one checked.
-/

namespace CryoLean

/-- Render an integer scaled by `d` with up to three decimals, e.g. 1800/1000 → "1.8". -/
def fmtScaled (v : Int) (d : Nat) : String :=
  let neg := v < 0
  let a := v.natAbs
  let whole := a / d
  let rem := a % d
  let frac :=
    if rem = 0 then ""
    else
      let s := toString (rem * 1000 / d)
      let s := "".pushn '0' (3 - s.length) ++ s
      let s := String.ofList (s.toList.reverse.dropWhile (· == '0')).reverse
      "." ++ s
  (if neg then "-" else "") ++ toString whole ++ frac

/-- Human-friendly rendering of a canonical-unit quantity (raw value kept alongside). -/
def fmtQuantity (q : Quantity) : String :=
  match q.unit with
  | "mK"  => s!"{fmtScaled q.value 1000} K"
  | "mT"  => s!"{fmtScaled q.value 1000} T"
  | "um"  => s!"{fmtScaled q.value 1000} mm"
  | "nW"  => s!"{fmtScaled q.value 1000} µW"
  | "uPa" => s!"{fmtScaled q.value 1000000} Pa"
  | "kHz" => s!"{fmtScaled q.value 1000000} GHz"
  | "mK_per_min" => s!"{fmtScaled q.value 1000} K/min"
  | "s"   => s!"{q.value} s"
  | "count" => s!"{q.value}"
  | u => s!"{q.value} {u}"

def describeConstraint : Constraint → String
  | .pointWithin q    => s!"must be able to operate at {fmtQuantity q}"
  | .rangeWithin lo hi => s!"must cover the whole range {fmtQuantity lo} to {fmtQuantity hi}"
  | .atLeast q        => s!"needs at least {fmtQuantity q}"
  | .atMost q         => s!"needs to reach {fmtQuantity q} or lower"
  | .present          => "must be installed"
  | .countAtLeast n   => s!"needs at least {n}"

def describeCapValue : CapValue → String
  | .range lo hi => s!"a documented range of {fmtQuantity lo} to {fmtQuantity hi}"
  | .max q       => s!"a documented maximum of {fmtQuantity q}"
  | .min q       => s!"a documented minimum of {fmtQuantity q}"
  | .flag true   => "documented as present"
  | .flag false  => "documented as absent"
  | .count n     => s!"a documented count of {n}"
  | .unknown     => "no documented value (UNKNOWN)"

def describeEvidence : EvidenceStatus → String
  | .manufacturerSpecification => "manufacturer specification"
  | .experimentalObservation   => "experimental observation"
  | .userEntered               => "user-entered value"
  | .inferredEstimate          => "inferred estimate"
  | .unknown                   => "no recorded provenance"

/-- One sentence per check, phrased for a non-specialist. -/
def explainCheck (cr : CheckResult) : String :=
  let r := cr.requirement
  let what := s!"'{r.key}' {describeConstraint r.constraint}"
  match cr.capability, cr.outcome with
  | none, _ =>
      s!"{what}, but this configuration has no documented value for '{r.key}'. We need more information."
  | some c, .pass =>
      s!"{what}; this configuration has {describeCapValue c.value} ({describeEvidence c.evidence}). Requirement met."
  | some c, .fail =>
      match c.install with
      | .optionalNotInstalled =>
          s!"{what}, but '{r.key}' is an option that is not installed in this configuration. Requirement not met."
      | _ =>
          s!"{what}, but this configuration has {describeCapValue c.value} ({describeEvidence c.evidence}). Requirement not met."
  | some c, .unknown =>
      if c.value == .unknown && c.install != .unknown then
        s!"{what}, but the documented value for '{r.key}' is UNKNOWN for this configuration. We need more information."
      else
        match c.install, c.evidence with
        | .unknown, _ => s!"{what}, but the documentation does not say whether '{r.key}' is fitted to this configuration. We need more information."
        | _, .inferredEstimate => s!"{what}; the only available value for '{r.key}' is an inferred estimate, which cannot be used for a verified result. We need a documented value."
        | _, .unknown => s!"{what}; the value recorded for '{r.key}' has no provenance and cannot be used. We need a sourced value."
        | _, _ => s!"{what}, but the documented value for '{r.key}' is UNKNOWN. We need more information."
  | some c, .unsupported =>
      s!"{what}, but it cannot be compared with {describeCapValue c.value}: the units or value shapes differ. The requirement is unsupported as stated."

def explainVerdict (res : Result) : String :=
  let mand := res.checks.filter (·.requirement.mandatory)
  let fails := mand.filter (·.outcome == .fail)
  let open_ := mand.filter (fun c => c.outcome == .unknown || c.outcome == .unsupported)
  match res.verdict with
  | .accept => s!"Requirements met. All {mand.length} mandatory requirements of this experiment are satisfied by the documented capabilities of this configuration."
  | .reject =>
      let keys := ", ".intercalate (fails.map (·.requirement.key))
      s!"Does not meet requirements. A documented limitation of this configuration conflicts with: {keys}. Choose another configuration or cryostat."
  | .needMoreInfo =>
      if mand.isEmpty then
        "Need more information. This experiment profile has no confirmed mandatory requirements yet."
      else
        let keys := ", ".intercalate (open_.map (·.requirement.key))
        s!"Need more information. The available evidence does not establish: {keys}."

end CryoLean
