import CryoLean
/-!
# CryoLean vs the regular way, proved

Checked with `lake env lean VsRegular.lean` (run by `bench/vs_regular.py`). This file sits next to `Audit.lean`,
outside the trusted library, so the checker CryoLean ships (and its source hash) is exactly the one benchmarked.

**The regular way** is the spec-sheet checklist: read each datasheet line on its own, believe any number printed
on the sheet, and let a line the sheet is silent on pass. `checklist` below is that procedure written with
CryoLean's own types (a brochure option documented as not fitted counts as absent, so it is not a strawman).

Proved here, all with Lean's standard axioms only:

1. `sound_yes_le_cryolean`, `sound_no_le_cryolean`: **no checker that is never wrong can say YES, or NO, more often
   than CryoLean.** Any YES CryoLean does not give is a YES the specification does not support
   (`extra_yes_unsupported`). CryoLean is the most decisive checker among those that are never wrong.
2. `checklist_yes_to_blank_sheet`: the checklist says YES to a blank datasheet, for every experiment.
   `cryolean_no_yes_to_blank_sheet`: CryoLean never does.
3. `checklist_not_monotone`: hiding one datasheet line turns the checklist's NO into YES (the 10 T magnet on a
   9 T machine). `hiding_lines_never_creates_yes`: no amount of hiding does that to CryoLean.
4. `checklist_believes_a_guess`: an unsourced "about 14 T" turns the checklist's answer into YES; CryoLean
   answers NEED_MORE_INFORMATION.
5. `checklist_misses_coupled_physics`: the 50-qubit wiring layout on a Bluefors LD400 passes every datasheet line
   (10 mK ≤ 20 mK, 168 ≥ 124 lines) and the checklist says YES; CryoLean says NO because
   3 × 4.864 µW = 14.592 µW > 12 µW (Krinner et al. 2019, the refrigerator's documented 20 mK cooling power).
-/

namespace CryoLean
namespace Regular

/-! ## The regular way -/

/-- One datasheet line, read the regular way: any number on the sheet counts (provenance is not looked at);
a brochure option documented as not fitted counts as absent; a line the sheet is silent on is `unknown`. -/
def lineKey (cfg : Configuration) (k : Constraint) (key : String) : Outcome :=
  match lookup cfg key with
  | none => .unknown
  | some c =>
    match c.install with
    | .optionalNotInstalled => if k = .flagIs false then .pass else .fail
    | .unknown => .unknown
    | .installed => checkValue k c.value

/-- A requirement read the regular way: any of its keys may satisfy it. -/
def line (cfg : Configuration) (r : Requirement) : Outcome :=
  combineAny (r.keys.map (lineKey cfg r.constraint))

/-- **The spec-sheet checklist.** NO if some line visibly fails, otherwise YES. Coupled physics is not part of a
datasheet comparison, and a silent line never blocks. -/
def checklist (cfg : Configuration) (e : Experiment) : Verdict :=
  if .fail ∈ (relevantReqs e).map (line cfg) then .reject else .accept

/-! ## 1. CryoLean is the most decisive checker that is never wrong -/

/-- Any checker whose every YES satisfies the specification says YES only where CryoLean does. -/
theorem sound_yes_le_cryolean (chk : Configuration → Experiment → Verdict)
    (hsound : ∀ c e, chk c e = .accept → AcceptSpec c e) {c : Configuration} {e : Experiment}
    (h : chk c e = .accept) : verdict c e = .accept :=
  verdict_accept_complete (hsound c e h)

/-- Any checker whose every NO rests on a documented, trusted violation says NO only where CryoLean does. -/
theorem sound_no_le_cryolean (chk : Configuration → Experiment → Verdict)
    (hsound : ∀ c e, chk c e = .reject → RejectSpec c e) {c : Configuration} {e : Experiment}
    (h : chk c e = .reject) : verdict c e = .reject :=
  verdict_reject_complete (hsound c e h)

/-- Every YES that CryoLean does not give is a YES the specification does not support. -/
theorem extra_yes_unsupported (chk : Configuration → Experiment → Verdict) {c : Configuration} {e : Experiment}
    (h : chk c e = .accept) (hn : verdict c e ≠ .accept) : chk c e = .accept ∧ ¬ AcceptSpec c e :=
  ⟨h, fun hs => hn (verdict_accept_complete hs)⟩

/-- Every NO that CryoLean does not give is a NO without a documented, trusted violation behind it. -/
theorem extra_no_unsupported (chk : Configuration → Experiment → Verdict) {c : Configuration} {e : Experiment}
    (h : chk c e = .reject) (hn : verdict c e ≠ .reject) : chk c e = .reject ∧ ¬ RejectSpec c e :=
  ⟨h, fun hs => hn (verdict_reject_complete hs)⟩

/-! ## 2. A blank datasheet -/

/-- A datasheet with nothing on it. -/
def blankSheet : Configuration := ⟨"blank", "blank", "a datasheet with nothing on it", []⟩

theorem lineKey_blank (k : Constraint) (key : String) : lineKey blankSheet k key = .unknown := rfl

theorem line_blank_ne_fail (r : Requirement) : line blankSheet r ≠ .fail := by
  intro h
  obtain ⟨hne, hall⟩ := combineAny_fail h
  obtain ⟨key, hk⟩ : ∃ key, key ∈ r.keys := by
    cases hks : r.keys with
    | nil => simp [hks] at hne
    | cons k _ => exact ⟨k, by simp⟩
  have := hall (lineKey blankSheet r.constraint key) (List.mem_map.2 ⟨key, hk, rfl⟩)
  rw [lineKey_blank] at this
  cases this

/-- **The checklist says YES to a blank datasheet, whatever the experiment.** -/
theorem checklist_yes_to_blank_sheet (e : Experiment) : checklist blankSheet e = .accept := by
  unfold checklist
  split
  · rename_i hf
    obtain ⟨r, _, hr⟩ := List.mem_map.1 hf
    exact absurd hr (line_blank_ne_fail r)
  · rfl

/-- No requirement can pass on a blank datasheet in CryoLean: passing needs a documented record. -/
theorem cryolean_blank_no_pass {e : Experiment} (r : Requirement) : checkRequirement blankSheet e r ≠ .pass := by
  intro h
  obtain ⟨_, key, _, c, hc, _⟩ := checkRequirement_pass_sound h
  simp [lookup, blankSheet] at hc

/-- **CryoLean never says YES to a blank datasheet** (for any experiment whose checks are datasheet lines; a coupled
constraint that reads only the experiment's own parameters could in principle pass without the sheet). -/
theorem cryolean_no_yes_to_blank_sheet (e : Experiment) (hc : e.coupled = []) :
    verdict blankSheet e ≠ .accept := by
  intro h
  have hp := (accept_iff_outcomes.1 h).2.2
  rcases mem_outcomes.1 hp with ⟨r, _, hr⟩ | ⟨c, hcm, _⟩
  · exact cryolean_blank_no_pass r hr
  · simp [relevantCoupled, hc] at hcm

/-- So on a blank sheet the checklist's YES is never supported by the specification. -/
theorem checklist_blank_yes_unsupported (e : Experiment) (hc : e.coupled = []) :
    checklist blankSheet e = .accept ∧ ¬ AcceptSpec blankSheet e :=
  extra_yes_unsupported checklist (checklist_yes_to_blank_sheet e) (cryolean_no_yes_to_blank_sheet e hc)

/-! ## 3. Hiding one datasheet line (the 10 T magnet on a 9 T machine) -/

/-- Dimension of magnetic flux density (tesla = kg s⁻² A⁻¹). -/
def teslaDim : Dim := { kg := 1, s := -2, A := -1 }
def tesla (n : Int) : Quantity := ⟨⟨n, 1⟩, teslaDim⟩

/-- 10 T magnetoresistance: the field must reach at least 10 T. -/
def needs10T : Experiment :=
  { id := "mat_magnetoresistance_10T", name := "10 T magnetoresistance", industry := "materials", params := [],
    requirements := [⟨["magnetic_field.max"], .atLeast (tesla 10), true, true, [], .experimentalObservation,
      "the measurement sweeps to 10 T", []⟩],
    coupled := [], confirmed := true }

/-- The PPMS DynaCool 9 T configuration: its brochure states a 9 T magnet. -/
def dynacool9T : Configuration :=
  ⟨"qd_dynacool_9T_eto_res", "qd_ppms_dynacool", "PPMS DynaCool, 9 T magnet",
   [⟨"magnetic_field.max", .max (tesla 9), .installed, .manufacturerSpecification, ["ev_qd_0002"]⟩]⟩

/-- The same machine, with the magnet line hidden (the sheet is silent on it). -/
def dynacool9T_hidden : Configuration := ⟨"qd_dynacool_9T_eto_res", "qd_ppms_dynacool", "PPMS DynaCool, line hidden", []⟩

/-- Hiding a line is a refinement in reverse: everything the hidden sheet decides is still on the full sheet. -/
theorem hidden_refines_full : Refines dynacool9T_hidden dynacool9T := by
  intro key c h _
  simp [lookup, dynacool9T_hidden] at h

theorem checklist_full : checklist dynacool9T needs10T = .reject := by decide
theorem checklist_hidden : checklist dynacool9T_hidden needs10T = .accept := by decide
theorem cryolean_full : verdict dynacool9T needs10T = .reject := by decide
theorem cryolean_hidden : verdict dynacool9T_hidden needs10T = .needMoreInfo := by decide

/-- **Hiding one line turns the checklist's NO into YES.** -/
theorem checklist_not_monotone :
    ∃ c c' e, Refines c c' ∧ checklist c' e = .reject ∧ checklist c e = .accept :=
  ⟨dynacool9T_hidden, dynacool9T, needs10T, hidden_refines_full, checklist_full, checklist_hidden⟩

/-- **Hiding lines can never turn CryoLean's NO into YES** (from information monotonicity, `verdict_refines`). -/
theorem hiding_lines_never_creates_yes {c c' : Configuration} {e : Experiment}
    (hr : Refines c c') (h : verdict c' e = .reject) : verdict c e ≠ .accept := by
  intro ha
  rw [accept_preserved_by_refinement hr ha] at h
  cases h

/-! ## 4. An unsourced number -/

/-- The same machine with an unsourced "about 14 T" (a number read off the 14 T brochure, a forum, a guess). -/
def dynacoolGuess : Configuration :=
  ⟨"qd_dynacool_9T_eto_res", "qd_ppms_dynacool", "PPMS DynaCool, field guessed",
   [⟨"magnetic_field.max", .max (tesla 14), .installed, .inferredEstimate, []⟩]⟩

/-- **The checklist believes the guess; CryoLean does not decide on it.** -/
theorem checklist_believes_a_guess :
    checklist dynacoolGuess needs10T = .accept ∧ verdict dynacoolGuess needs10T = .needMoreInfo := by
  constructor <;> decide

/-! ## 5. Coupled physics: the 50-qubit wiring heat budget -/

def wattDim : Dim := { m := 2, kg := 1, s := -3 }
def kelvinDim : Dim := { K := 1 }
def num (n : Int) : Quantity := ⟨⟨n, 1⟩, Dim.one⟩
def nanowatt (n : Int) : Quantity := ⟨⟨n, 1000000000⟩, wattDim⟩

/-- Bluefors LD400 with high-density wiring: 10 mK base, 168 RF lines, 12 µW documented at 20 mK. -/
def ld400 : Configuration :=
  ⟨"bluefors_ld400_hdw", "bluefors_ld", "Bluefors LD400 + high-density wiring",
   [⟨"temperature.base", .min ⟨⟨1, 100⟩, kelvinDim⟩, .installed, .manufacturerSpecification, []⟩,
    ⟨"electrical.coax_lines", .count 168, .installed, .manufacturerSpecification, []⟩,
    ⟨"cooling_power.at_20mK", .max (nanowatt 12000), .installed, .manufacturerSpecification, []⟩]⟩

/-- Krinner et al.'s design rule: 3 × (58 drive × 13 nW + 50 flux × (29 + 50) nW + 8 output × 20 nW). -/
def wiringLoad : Expr :=
  .mul (.lit (num 3))
    (.add (.add (.mul (.lit (num 58)) (.lit (nanowatt 13)))
                (.mul (.lit (num 50)) (.add (.lit (nanowatt 29)) (.lit (nanowatt 50)))))
          (.mul (.lit (num 8)) (.lit (nanowatt 20))))

/-- The 50-qubit processor: base ≤ 20 mK, ≥ 124 RF lines, and the heat budget at the mixing chamber. -/
def qubits50 : Experiment :=
  { id := "quantum_mxc_wiring_heat_budget", name := "50-qubit wiring heat budget", industry := "quantum",
    params := [],
    requirements :=
      [⟨["temperature.base"], .atMost ⟨⟨1, 50⟩, kelvinDim⟩, true, true, [], .experimentalObservation, "20 mK", []⟩,
       ⟨["electrical.coax_lines"], .countAtLeast 124, true, true, [], .experimentalObservation, "124 RF lines", []⟩],
    coupled :=
      [⟨"mxc_wiring_heat_budget", "wiring heat load (3x margin) vs cooling power at 20 mK", "mxc_wiring_heat_budget",
        wiringLoad, .cap "cooling_power.at_20mK" .max, [], true, true, [], .experimentalObservation,
        "Krinner et al. 2019", []⟩],
    confirmed := true }

/-- **Every datasheet line passes, so the checklist says YES; the coupled heat budget fails, so CryoLean says NO.** -/
theorem checklist_misses_coupled_physics :
    checklist ld400 qubits50 = .accept ∧ verdict ld400 qubits50 = .reject := by
  constructor <;> decide

/-- The number behind it, evaluated exactly: the wiring load is `n` nanowatts. -/
def wiringLoadIs (n : Int) : Bool :=
  match evalExpr ld400 qubits50 wiringLoad with
  | .ok q => decide (Q.le q.val (nanowatt n).val ∧ Q.le (nanowatt n).val q.val)
  | _ => false

/-- 3 × (58 × 13 + 50 × 79 + 8 × 20) nW = 14 592 nW = 14.592 µW, against 12 000 nW documented at 20 mK. -/
theorem wiring_load_is_14592_nW : wiringLoadIs 14592 = true := by decide

/-- And the checklist's YES there is unsupported. -/
theorem checklist_qubits_yes_unsupported :
    checklist ld400 qubits50 = .accept ∧ ¬ AcceptSpec ld400 qubits50 :=
  extra_yes_unsupported checklist checklist_misses_coupled_physics.1
    (by rw [checklist_misses_coupled_physics.2]; decide)

end Regular
end CryoLean

open CryoLean.Regular

-- axiom audit: every theorem above must list only propext / Classical.choice / Quot.sound
#print axioms sound_yes_le_cryolean
#print axioms sound_no_le_cryolean
#print axioms extra_yes_unsupported
#print axioms extra_no_unsupported
#print axioms checklist_yes_to_blank_sheet
#print axioms cryolean_no_yes_to_blank_sheet
#print axioms checklist_blank_yes_unsupported
#print axioms checklist_not_monotone
#print axioms hiding_lines_never_creates_yes
#print axioms checklist_believes_a_guess
#print axioms checklist_misses_coupled_physics
#print axioms wiring_load_is_14592_nW
#print axioms checklist_qubits_yes_unsupported
