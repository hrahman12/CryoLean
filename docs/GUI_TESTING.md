# Testing the CryoLean GUI

The GUI (`frontend/`, React) only displays what the backend returns. Every result comes from the Lean checker,
through `cryolean.bridge.CryoLeanAPI`. These steps test the whole application through the GUI.

## 0. Install and start

macOS / Linux:

```bash
make install        # first run: a few minutes (downloads Lean 4.35.0 and builds the checker)
make run            # opens the CryoLean window
```

Windows (PowerShell, from the repository root):

```powershell
python -m venv .venv; .venv\Scripts\pip install -r requirements.txt
cd lean; lake build; cd ..
.venv\Scripts\python -m cryolean build-db
npm ci --prefix frontend; npm run build --prefix frontend
.venv\Scripts\python -m cryolean.desktop --frontend frontend\dist\index.html
```

Expected: the window opens, the top-right pill says **Lean checker ready**, and the right side asks
**What would you like to do?** with one tab per field (20 fields).

## 1. Automated walkthrough (recommended first)

```bash
make test-e2e       # or: cd frontend && npx playwright test
```

This starts `scripts/dev_bridge.py` (the real CryoLeanAPI on 127.0.0.1:8765) and a static preview of `frontend/dist`. It then
drives a browser through scenarios A–E below plus the boot check (6 tests). `make test` also runs the fast Python suite.

## 2. Manual walkthrough

Use the Change cryostat search box to find the machines named below.

### A. Requirements met (Biology)
1. Tab **Biology & biotechnology** → **Cut a frozen tissue sample**.
2. Read the requirements. They are in plain language, each with its source and why it is needed. Press **These requirements are right**.
3. **Choose cryostat** → search `CM1950` → pick **Leica CM1950 … DualEcoTec**.
4. Expected: the image changes to a cryostat microtome and the check runs by itself (requirements were confirmed). The result shows
   **Requirements met** with a **Verified by Lean** badge.
5. **See checks**: each check is phrased as a question (Is it cold enough? Does the sample fit? …), with Yes/No/Not documented.
   Open a row for the explanation and the source quotes with document, page and link. **How this was verified** lists the theorems,
   axioms, Lean source hash and input hash.
6. **Save report: PDF** and **JSON**. A save dialog appears and both files open correctly.

### B. Does not meet requirements, then switching machines (Materials)
1. **‹ All experiments** → tab **Materials & nanotechnology** → **Measure how a crystal's resistance changes in a 10 T field at 2 K**. Confirm.
2. Change cryostat → search `DynaCool 9 T` → **PPMS DynaCool, 9 T magnet …**.
3. Expected: **Doesn't meet requirements**. The message says the maximum magnetic field needs at least 10 T but the machine documents 9 T.
   No verified badge. **Try another cryostat** is offered.
4. Change cryostat → `DynaCool 14 T` → **14 T ETO + VSM + heat capacity**.
5. Expected: the old red result disappears at once and the experiment stays selected. The new answer is **Need more information**:
   this machine's documentation doesn't give the maximum sample width, length or height. Missing information is never shown as a pass.

### C. Unconfirmed profile (any experiment)
1. Pick **Cut a frozen tissue sample** again, but do not confirm. Choose the Leica CM1950 DualEcoTec.
2. Nothing runs by itself. Press **Check setup**.
3. Expected: **Need more information** with the question "Have you reviewed your experiment's requirements?".
   **Confirm and check again** → **Requirements met**.

### D. A suggested change, reviewed before it is applied (Quantum)
1. Tab **Quantum computing & sensing** → **Check that the wiring for a superconducting qubit chip does not overheat the coldest stage**. Confirm.
2. Change cryostat → `LD400` → **Bluefors LD400 … High-Density Wiring**.
3. Expected: **Doesn't meet requirements** (14.592 µW heat load exceeds 12 µW). Under **Other options**:
   "Change number of flux lines from 50 to 39 · Lean checked this option".
4. **Review** shows Now 50 → Suggested 39, and states that the requirements stay the same. **Accept and check**.
5. Expected: **Requirements met**, verified badge, and the note "Lean re-checked exactly the setup it had verified".

### E. Editing requirements (any experiment)
1. With experiment B selected and checked, press **Review** on the green "Requirements confirmed" bar.
2. **Edit** "Maximum magnetic field" → type `1e4`. Expected: **Save change** stays disabled (only plain numbers).
3. Type `8000` (unit mT), **Save change**. Expected: the requirement shows **Entered by you**, the profile asks you to confirm again,
   and the old result is cleared. Confirm and check again. In **See checks**, the magnetic-field check now passes (8 T ≤ 9 T),
   but the answer is still **Need more information** because this machine does not document its sample-space size.
4. There is no way to delete a required item or make it optional. The backend refuses it (`edit_refused`) and the GUI never offers it.

### F. Questions for missing values
1. **Measure electrical resistance at low temperature**: the profile starts with **A few questions first** (excitation current,
   sample resistance). These are values the papers did not state, so the app asks rather than guesses. Enter e.g. `100` µA and
   `10` Ω and press Save. The questions disappear, and the values are listed as **Entered by you**.
2. Confirm and check on the PPMS DynaCool 9 T. Expected: **Need more information** (sample size not documented). In See checks,
   the optional Joule-heating check shows "Not documented" because the catalog has no cooling-power figure for it. It still never counts as a pass.

### G. Verification unavailable
1. Quit the app. Temporarily rename `lean/.lake/build/bin/cryolean` (`cryolean.exe` on Windows) and run `make run` again.
2. Expected: the pill says **Verification is unavailable**. Check setup gives "Verification is unavailable" and **no** verdict.
3. Rename the binary back.

## 3. What to look for everywhere
* A verified badge appears only on a Lean **Requirements met** for the exact machine and experiment on screen.
* Changing the machine, a value or a requirement always clears the previous result before anything new is shown.
* Saving a report re-checks freshness first (`get_session_result`). If anything changed, it refuses and clears the result.
* Suggestions are listed only when the backend marks them `verified: true`. Z3 explanations are labelled as hints.

## 4. Developing the GUI
`make dev` serves the GUI with hot reload at http://127.0.0.1:5173. The browser has no PyWebView, so the page talks to
`scripts/dev_bridge.py`, a localhost-only forwarder to the same `CryoLeanAPI`. The desktop app never uses it.
