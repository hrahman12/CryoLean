#!/usr/bin/env python
"""End-to-end demonstration (runs the real FastAPI app in-process, real Z3, real Lean binary).

1. AI matches a plain-language request to a prepared experiment.
2. Z3 searches every registered configuration for candidates.
3. Lean checks the 9 T and 14 T PPMS DynaCool configurations for a user-specified 10 T measurement.
4. The backend returns verdicts with evidence; the frontend gets a plain explanation.
5. The user switches cryostats in a session and re-verifies (previous result invalidated).
6. The same Lean engine checks experiments from other industries, unchanged.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from backend.api import app  # noqa: E402

c = TestClient(app)
EXP = "mat_magnetoresistance_10T"
C9, C14 = "qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc"


def hr(t):
    print("\n" + "=" * 100 + f"\n{t}\n" + "=" * 100)


def show(res):
    print(f"  verdict: {res['verdict']}  ({res['headline']})")
    print(f"  message: {res['user_message']}")
    print(f"  configuration checked by Lean: {res['configuration_id']}   lean input hash {res['lean_input_hash']}")
    for ch in res["checks"]:
        print(f"    [{ch['outcome']:11}] {'M' if ch['mandatory'] else ' '} {ch['key']:28} {ch['explanation'][:150]}")


hr("0. Health: Lean binary, theorem count, Z3")
h = c.get("/health").json()
print(json.dumps({k: h[k] for k in ("status", "lean_checker_available", "lean_version", "lean_theorems", "unproved_markers", "z3_version")}, indent=2))

hr("1. AI matching: 'I want to see how a material's resistance changes in a strong magnetic field when it is cold'")
m = c.post("/ai/match", json={"text": "I want to see how a material's resistance changes in a strong magnetic field when it is cold"}).json()
for x in m["matches"]:
    print(f"  {x['confidence']:.2f}  {x['experiment_id']}  — {x['plain_name']}")
print("  needs_confirmation:", m["needs_confirmation"])

hr("2. Manufacturer evidence for the magnet options")
for cid in (C9, C14):
    cfg = c.get(f"/configurations/{cid}").json()
    cap = next(x for x in cfg["capabilities"] if x["key"] == "magnetic_field.max")
    for ev in cap["evidence"]:
        print(f"  {cid}: {cap['value']}  <- {ev['id']}: \"{ev.get('quote','')[:110]}\"")
        print(f"      {ev['document_title'][:90]} | {ev.get('location','')} | {ev['source_url']}")

hr("3. Z3 search across ALL registered equipment (candidates only, then each is Lean-checked)")
s = c.post("/search", json={"experiment_id": EXP, "confirmed": True, "allow_hypothetical_options": True}).json()
print("  smt stats:", s["smt_stats"])
for e in s["verified_compatible"]:
    print(f"  LEAN ACCEPT  {e['candidate']['configuration_id']}")
for e in s["candidates_not_verified"]:
    print(f"  Z3 candidate, Lean says {e['lean']['verdict']:22} {e['candidate']['configuration_id']}  missing={e['lean']['missing_information']}")
print(f"  rejected by Z3 encoding: {len(s['rejected'])} configurations")

hr(f"4a. Lean check: {C9} for a 10 T measurement")
show(c.post("/verify", json={"experiment_id": EXP, "configuration_id": C9, "confirmed": True}).json())
hr(f"4b. Lean check: {C14} for a 10 T measurement")
r14 = c.post("/verify", json={"experiment_id": EXP, "configuration_id": C14, "confirmed": True}).json()
show(r14)
hr("4c. Same, with the user's own documented transport-puck sample limit (user-entered evidence)")
ov = [{"key": k, "documented": True, "value": {"kind": "max", "q": {"value": 5000, "unit": "um"}},
       "note": "Lab measurement of our transport puck sample area (user-entered)"} for k in ("sample.width.max", "sample.length.max", "sample.height.max")]
show(c.post("/verify", json={"experiment_id": EXP, "configuration_id": C14, "confirmed": True, "instrument_overrides": ov}).json())
hr("4d. Same, but the magnet has an UNDOCUMENTED modification")
show(c.post("/verify", json={"experiment_id": EXP, "configuration_id": C14, "confirmed": True,
                             "instrument_overrides": ov + [{"key": "magnetic_field.max", "documented": False, "note": "magnet re-wound by third party"}]}).json())

hr("5. Session: switch cryostats without changing the experiment")
sid = c.post("/sessions", json={"experiment_id": EXP}).json()["id"]
c.post(f"/sessions/{sid}/confirm")
c.post(f"/sessions/{sid}/select-configuration", json={"configuration_id": C9})
r = c.post(f"/sessions/{sid}/verify").json()
print(f"  {C9}: {r['verdict']}  token {r['state_token']}")
c.post(f"/sessions/{sid}/select-configuration", json={"configuration_id": C14})
stale = c.get(f"/sessions/{sid}/result")
print(f"  after switching: GET result -> HTTP {stale.status_code} {stale.json().get('error')}")
r = c.post(f"/sessions/{sid}/verify").json()
print(f"  {C14}: {r['verdict']}  token {r['state_token']}")
ex = c.post("/ai/explain", json={"session_id": sid}).json()
print("  explanation:", *ex["explanation"], sep="\n    ")
for a in ex["alternatives"]:
    print(f"  alternative: {a['configuration_id']:55} Lean={a['lean_verdict']}")

hr("6. The same Lean engine across industries (no change to the trusted core)")
pairs = [("bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool"),
         ("bio_cryosection_frozen_tissue", "leica_cm1950_genA_standard"),
         ("chem_low_temperature_raman", "linkam_thms600_lnp96_t96"),
         ("chem_low_temperature_raman", "linkam_thms600_heating_only"),
         ("quantum_transmon_characterization", "bluefors_ld400_hdw"),
         ("mat_electrical_resistance_low_temperature", "qd_dynacool_12T_vsm")]
for e, cfg in pairs:
    r = c.post("/verify", json={"experiment_id": e, "configuration_id": cfg, "confirmed": True}).json()
    print(f"  {r['industry']:32} {e:45} on {cfg:42} -> {r['verdict']}")
    print(f"      {r['user_message'][:170]}")
