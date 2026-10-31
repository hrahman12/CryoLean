import CryoLean
open Lean CryoLean

/-!
# `cryolean` command-line checker

```
cryolean check <file.json>        # {"configuration": ..., "experiment": ...}
cryolean check -                  # same, read from stdin
cryolean check-batch <file.json>  # [ {configuration, experiment}, ... ]
cryolean selftest                 # run the built-in examples
cryolean version
```
Exit code 0: a verdict (any of the three) was produced.  Exit code 2: the input
could not be decoded; the error is printed as JSON on stdout.  The CLI never
guesses: an unrecognised field value is a decoding error, not a default.
-/

partial def readStream (s : IO.FS.Stream) (acc : String) : IO String := do
  let line ← s.getLine
  if line.isEmpty then pure acc else readStream s (acc ++ line)

def readInput (path : String) : IO String := do
  if path == "-" then readStream (← IO.getStdin) "" else IO.FS.readFile path

def emitError (msg : String) : IO UInt32 := do
  IO.println (Json.mkObj [("error", toJson msg), ("verdict", Json.null)]).compress
  pure 2

def cmdCheck (path : String) : IO UInt32 := do
  let txt ← readInput path
  match Json.parse txt with
  | .error e => emitError s!"invalid JSON: {e}"
  | .ok doc =>
    match checkDocument doc with
    | .error e => emitError s!"decode error: {e}"
    | .ok out => IO.println out.compress; pure 0

def cmdCheckBatch (path : String) : IO UInt32 := do
  let txt ← readInput path
  match Json.parse txt with
  | .error e => emitError s!"invalid JSON: {e}"
  | .ok doc =>
    match doc.getArr? with
    | .error e => emitError s!"expected array: {e}"
    | .ok arr =>
      let outs := arr.toList.map fun d =>
        match checkDocument d with
        | .ok o => o
        | .error e => Json.mkObj [("error", toJson e), ("verdict", Json.null)]
      IO.println (toJson outs).compress
      pure 0

/-- Built-in examples exercising the three verdicts; independent of the data files. -/
def selftestDocs : List (String × Json) :=
  let q (v : Int) (u : String) := Json.mkObj [("value", toJson v), ("unit", toJson u)]
  let cap (k : String) (v : Json) (inst ev : String) :=
    Json.mkObj [("key", k), ("value", v), ("install", inst), ("evidence_status", ev), ("evidence_ids", toJson ([] : List String))]
  let req (k : String) (c : Json) (m : Bool) :=
    Json.mkObj [("key", k), ("constraint", c), ("mandatory", toJson m), ("origin", "user_entered")]
  let cfg (id : String) (caps : List Json) :=
    Json.mkObj [("id", id), ("equipment_id", "demo"), ("name", id), ("capabilities", toJson caps)]
  let exp (reqs : List Json) (confirmed : Bool) :=
    Json.mkObj [("id", "demo_exp"), ("name", "demo"), ("industry", "any"), ("requirements", toJson reqs), ("confirmed", toJson confirmed)]
  let field10 := req "magnetic_field.max" (Json.mkObj [("kind", "at_least"), ("q", q 10000 "mT")]) true
  let temp2 := req "temperature.range" (Json.mkObj [("kind", "point_within"), ("q", q 2000 "mK")]) true
  let tRange := cap "temperature.range" (Json.mkObj [("kind", "range"), ("lo", q 1800 "mK"), ("hi", q 400000 "mK")]) "installed" "manufacturer_specification"
  let f9 := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", q 9000 "mT")]) "installed" "manufacturer_specification"
  let f14 := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", q 14000 "mT")]) "installed" "manufacturer_specification"
  let f14est := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", q 14000 "mT")]) "installed" "inferred_estimate"
  let f14gauss := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", q 140000 "G")]) "installed" "manufacturer_specification"
  let fOpt := cap "magnetic_field.max" (Json.mkObj [("kind", "max"), ("q", q 14000 "mT")]) "optional_not_installed" "manufacturer_specification"
  let mk (name : String) (c e : Json) := (name, Json.mkObj [("configuration", c), ("experiment", e)])
  [ mk "ACCEPT: 14 T, 2 K" (cfg "c14" [tRange, f14]) (exp [field10, temp2] true),
    mk "REJECT: 9 T magnet for 10 T requirement" (cfg "c9" [tRange, f9]) (exp [field10, temp2] true),
    mk "NEED_MORE_INFORMATION: no field capability recorded" (cfg "cNoField" [tRange]) (exp [field10, temp2] true),
    mk "NEED_MORE_INFORMATION: 14 T is only an inferred estimate" (cfg "c14est" [tRange, f14est]) (exp [field10, temp2] true),
    mk "NEED_MORE_INFORMATION: unit mismatch (gauss vs mT) is unsupported, not converted" (cfg "c14G" [tRange, f14gauss]) (exp [field10, temp2] true),
    mk "REJECT: 14 T magnet is an option not installed" (cfg "cOpt" [tRange, fOpt]) (exp [field10, temp2] true),
    mk "NEED_MORE_INFORMATION: requirements not confirmed by user" (cfg "c14" [tRange, f14]) (exp [field10, temp2] false),
    mk "NEED_MORE_INFORMATION: no mandatory requirements" (cfg "c14" [tRange, f14]) (exp [] true) ]

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
  if failures == 0 then IO.println "selftest: all examples produced the expected verdict"; pure 0
  else IO.println s!"selftest: {failures} failure(s)"; pure 1

def usage : String :=
  "usage: cryolean check <file|->  |  cryolean check-batch <file|->  |  cryolean selftest  |  cryolean version"

def main (args : List String) : IO UInt32 := do
  match args with
  | ["check", p] => cmdCheck p
  | ["check-batch", p] => cmdCheckBatch p
  | ["selftest"] => cmdSelftest
  | ["version"] => IO.println s!"cryolean (Lean {Lean.versionString})"; pure 0
  | _ => IO.println usage; pure 1
