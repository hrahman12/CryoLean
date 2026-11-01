import CryoLean
open Lean CryoLean

/-!
# `cryolean` command-line checker (v2)

```
cryolean check <file|->             # {"configuration": ..., "experiment": ...}
cryolean check-batch <file|->       # [ {configuration, experiment}, ... ]
cryolean check-candidates <file|->  # {"experiment": ..., "candidates": [configuration, ...]}
cryolean selftest
cryolean version
```
Exit code 0: verdict(s) produced.  Exit code 2: input could not be decoded (the
error is printed as JSON with "verdict": null).  Nothing is ever guessed.
-/

partial def readStream (s : IO.FS.Stream) (acc : String) : IO String := do
  let line ← s.getLine
  if line.isEmpty then pure acc else readStream s (acc ++ line)

def readInput (path : String) : IO String := do
  if path == "-" then readStream (← IO.getStdin) "" else IO.FS.readFile path

def emitError (msg : String) : IO UInt32 := do
  IO.println (Json.mkObj [("error", toJson msg), ("verdict", Json.null)]).compress
  pure 2

def withDoc (path : String) (k : Json → IO UInt32) : IO UInt32 := do
  match Json.parse (← readInput path) with
  | .error e => emitError s!"invalid JSON: {e}"
  | .ok doc => k doc

def cmdCheck (path : String) : IO UInt32 := withDoc path fun doc =>
  match checkDocument doc with
  | .error e => emitError s!"decode error: {e}"
  | .ok out => do IO.println out.compress; pure 0

def cmdCheckBatch (path : String) : IO UInt32 := withDoc path fun doc =>
  match doc.getArr? with
  | .error e => emitError s!"expected array: {e}"
  | .ok arr => do
    let outs := arr.toList.map fun d =>
      match checkDocument d with
      | .ok o => o
      | .error e => Json.mkObj [("error", toJson s!"decode error: {e}"), ("verdict", Json.null)]
    IO.println (toJson outs).compress
    pure 0

def cmdCheckSchedule (path : String) : IO UInt32 := withDoc path fun doc =>
  match checkScheduleDocument doc with
  | .error e => emitError s!"decode error: {e}"
  | .ok out => do IO.println out.compress; pure 0

def cmdCheckCandidates (path : String) : IO UInt32 := withDoc path fun doc =>
  match checkCandidatesDocument doc with
  | .error e => emitError s!"decode error: {e}"
  | .ok out => do IO.println out.compress; pure 0

/-! ## Self-test (synthetic fixtures, independent of the data files) -/

def qj (num : Int) (den : Nat) (dim : List (String × Int)) : Json :=
  Json.mkObj [("num", toJson num), ("den", toJson den),
              ("dim", Json.mkObj (dim.map (fun (k, v) => (k, toJson v))))]

def K := [("K", (1 : Int))]
def T := [("kg", (1 : Int)), ("s", -2), ("A", -1)]
def W := [("kg", (1 : Int)), ("m", 2), ("s", -3)]
def Ohm := [("kg", (1 : Int)), ("m", 2), ("s", -3), ("A", -2)]
def Amp := [("A", (1 : Int))]

def selftestDocs : List (String × Json) :=
  let cap (k : String) (v : Json) (inst ev : String) :=
    Json.mkObj [("key", k), ("value", v), ("install", inst), ("evidence_status", ev)]
  let req (k : String) (c : Json) :=
    Json.mkObj [("key", k), ("constraint", c), ("mandatory", true), ("origin", "user_entered")]
  let cfg (id : String) (caps : List Json) :=
    Json.mkObj [("id", id), ("equipment_id", "fixture"), ("name", id), ("capabilities", toJson caps)]
  let exp (reqs : List Json) (coupled : List Json) (params : List Json) (confirmed : Bool) :=
    Json.mkObj [("id", "fixture_exp"), ("name", "fixture"), ("industry", "any"), ("params", toJson params),
                ("requirements", toJson reqs), ("coupled", toJson coupled), ("confirmed", toJson confirmed)]
  let field10 := req "magnetic_field.max" (Json.mkObj [("kind", "at_least"), ("q", qj 10 1 T)])
  let temp2 := req "temperature.range" (Json.mkObj [("kind", "point_within"), ("q", qj 2 1 K)])
  let tRange := cap "temperature.range" (Json.mkObj [("kind", "range"), ("lo", qj 18 10 K), ("hi", qj 400 1 K)]) "installed" "manufacturer_specification"
  let f9 := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", qj 9 1 T)]) "installed" "manufacturer_specification"
  let f14 := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", qj 14 1 T)]) "installed" "manufacturer_specification"
  let f14est := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", qj 14 1 T)]) "installed" "inferred_estimate"
  let f14K := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", qj 14 1 K)]) "installed" "manufacturer_specification"
  let fOpt := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", qj 14 1 T)]) "optional_not_installed" "manufacturer_specification"
  let cp := cap "cooling_power.at_2K" (Json.mkObj [("kind", "max"), ("q", qj 1 1000 W)]) "installed" "manufacturer_specification"
  -- Joule heating I^2 R must not exceed the documented cooling power
  let joule := Json.mkObj [("id", "joule"), ("name", "Joule heating vs cooling power"), ("model", "joule_vs_cooling"),
    ("lhs", Json.mkObj [("op", "mul"), ("a", Json.mkObj [("op", "mul"), ("a", Json.mkObj [("op", "param"), ("name", "I")]), ("b", Json.mkObj [("op", "param"), ("name", "I")])]), ("b", Json.mkObj [("op", "param"), ("name", "R")])]),
    ("rhs", Json.mkObj [("op", "cap"), ("key", "cooling_power.at_2K"), ("sel", "max")]),
    ("mandatory", true), ("origin", "user_entered")]
  let pI (num : Int) (den : Nat) := Json.mkObj [("name", "I"), ("value", qj num den Amp), ("origin", "user_entered")]
  let pR := Json.mkObj [("name", "R"), ("value", qj 1000 1 Ohm), ("origin", "user_entered")]
  let mk (name : String) (c e : Json) := (name, Json.mkObj [("configuration", c), ("experiment", e)])
  [ mk "REQUIREMENTS_MET: 14 T, 2 K" (cfg "c14" [tRange, f14]) (exp [field10, temp2] [] [] true),
    mk "DOES_NOT_MEET_REQUIREMENTS: 9 T magnet for 10 T requirement" (cfg "c9" [tRange, f9]) (exp [field10, temp2] [] [] true),
    mk "NEED_MORE_INFORMATION: no field capability recorded" (cfg "cNoField" [tRange]) (exp [field10, temp2] [] [] true),
    mk "NEED_MORE_INFORMATION: 14 T is only an inferred estimate" (cfg "c14est" [tRange, f14est]) (exp [field10, temp2] [] [] true),
    mk "NEED_MORE_INFORMATION: dimension mismatch (K vs T) is unsupported" (cfg "c14K" [tRange, f14K]) (exp [field10, temp2] [] [] true),
    mk "DOES_NOT_MEET_REQUIREMENTS: 14 T magnet is an option not installed" (cfg "cOpt" [tRange, fOpt]) (exp [field10, temp2] [] [] true),
    mk "NEED_MORE_INFORMATION: requirements not confirmed by user" (cfg "c14" [tRange, f14]) (exp [field10, temp2] [] [] false),
    mk "NEED_MORE_INFORMATION: no mandatory requirements" (cfg "c14" [tRange, f14]) (exp [] [] [] true),
    mk "REQUIREMENTS_MET: 0.5 mA through 1 kΩ dissipates 0.25 mW <= 1 mW" (cfg "cCool" [tRange, cp]) (exp [temp2] [joule] [pI 5 10000, pR] true),
    mk "DOES_NOT_MEET_REQUIREMENTS: 2 mA through 1 kΩ dissipates 4 mW > 1 mW (coupled)" (cfg "cCool" [tRange, cp]) (exp [temp2] [joule] [pI 2 1000, pR] true),
    mk "NEED_MORE_INFORMATION: measurement current not supplied" (cfg "cCool" [tRange, cp]) (exp [temp2] [joule] [pR] true),
    mk "REQUIREMENTS_MET: 'must be absent' is met by an option that is not installed"
      (cfg "cOpt" [tRange, fOpt]) (exp [temp2, req "magnetic_field.max" (Json.mkObj [("kind", "absent")])] [] [] true) ]

/-- Documents the decoder must refuse (fail closed). -/
def selftestRejects : List (String × Json) :=
  let cap (k : String) (v : Json) :=
    Json.mkObj [("key", k), ("value", v), ("install", "installed"), ("evidence_status", "manufacturer_specification")]
  let tR := Json.mkObj [("kind", "range"), ("lo", qj 18 10 K), ("hi", qj 400 1 K)]
  let cfg (caps : List Json) := Json.mkObj [("id", "c"), ("equipment_id", "x"), ("name", "c"), ("capabilities", toJson caps)]
  let exp (reqs : List Json) (params : List Json) := Json.mkObj [("id", "e"), ("name", "e"), ("industry", "x"),
    ("params", toJson params), ("requirements", toJson reqs), ("confirmed", true)]
  let req (k : String) (c : Json) := Json.mkObj [("key", k), ("constraint", c), ("mandatory", true), ("origin", "user_entered")]
  let pt := req "temperature.range" (Json.mkObj [("kind", "point_within"), ("q", qj 2 1 K)])
  let p := Json.mkObj [("name", "T"), ("value", qj 2 1 K), ("origin", "user_entered")]
  [ ("duplicate capability key", Json.mkObj [("configuration", cfg [cap "temperature.range" tR, cap "temperature.range" tR]), ("experiment", exp [pt] [])]),
    ("duplicate parameter", Json.mkObj [("configuration", cfg [cap "temperature.range" tR]), ("experiment", exp [pt] [p, p])]),
    ("empty set_contains", Json.mkObj [("configuration", cfg [cap "temperature.range" tR]),
       ("experiment", exp [req "gas.compatible" (Json.mkObj [("kind", "set_contains"), ("needed", toJson ([] : List String))])] [])]),
    ("unknown dimension name", Json.mkObj [("configuration", cfg [cap "temperature.range" (Json.mkObj [("kind", "range"),
       ("lo", Json.mkObj [("num", toJson (1 : Int)), ("den", toJson (1 : Nat)), ("dim", Json.mkObj [("kelvin", toJson (1 : Int))])]),
       ("hi", qj 400 1 K)])]), ("experiment", exp [pt] [])]),
    ("zero denominator", Json.mkObj [("configuration", cfg [cap "temperature.range" (Json.mkObj [("kind", "range"), ("lo", qj 1 0 K), ("hi", qj 400 1 K)])]),
       ("experiment", exp [pt] [])]) ]

def cmdSelftest : IO UInt32 := do
  let mut failures := 0
  for (name, doc) in selftestDocs do
    match checkDocument doc with
    | .error e => IO.println s!"[ERROR] {name}: {e}"; failures := failures + 1
    | .ok out =>
      let v := (out.getObjVal? "verdict" >>= Json.getStr?).toOption.getD "?"
      let expected := (name.splitOn ":").headD ""
      let ok := v == expected
      IO.println s!"[{if ok then "ok" else "FAIL"}] {name} → {v}"
      if !ok then failures := failures + 1
  for (name, doc) in selftestRejects do
    match checkDocument doc with
    | .error e => IO.println s!"[ok] refused ({name}): {e}"
    | .ok _ => IO.println s!"[FAIL] accepted a malformed document ({name})"; failures := failures + 1
  if failures == 0 then
    IO.println "selftest: all examples produced the expected verdict"; pure 0
  else
    IO.println s!"selftest: {failures} failure(s)"; pure 1

def usage : String :=
  "usage: cryolean check <file|->  |  check-batch <file|->  |  check-candidates <file|->  |  check-schedule <file|->  |  selftest  |  version"

def main (args : List String) : IO UInt32 := do
  match args with
  | ["check", p] => cmdCheck p
  | ["check-batch", p] => cmdCheckBatch p
  | ["check-candidates", p] => cmdCheckCandidates p
  | ["check-schedule", p] => cmdCheckSchedule p
  | ["selftest"] => cmdSelftest
  | ["version"] => IO.println s!"cryolean v2 (Lean {Lean.versionString})"; pure 0
  | _ => IO.println usage; pure 1
