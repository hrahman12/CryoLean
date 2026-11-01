"""Acceptance demonstrations (real data, real Lean binary, real Z3).

A — confirmed incompatibility: 10 T measurement on the documented 9 T PPMS DynaCool.
B — coupled multiphysics: Bluefors LD400 + high-density wiring passes temperature and line-count
    checks but fails the mixing-chamber heat budget (Krinner et al. 2019 per-line loads and design rule).
C — new industry: semiconductors, registered through the research pipeline (scratch database),
    searched with Z3 and checked by the same, unmodified Lean core.

Outputs are written to docs/examples/*.json (used in FRONTEND_INTEGRATION.md).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from . import config, db
from .bridge import CryoLeanAPI

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs" / "examples"


def _hr(t):
    print("\n" + "=" * 100 + f"\n{t}\n" + "=" * 100)


def _save(name, obj):
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    (EXAMPLES / f"{name}.json").write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _checks(r):
    for c in r["checks"]:
        print(f"   [{c['outcome']:14}] {'M' if c['mandatory'] else ' '} {'/'.join(c['keys']):36} {c['explanation'][:130]}")
    for c in r["coupled_checks"]:
        print(f"   [{c['outcome']:14}] C {c['name'][:60]}")
        print(f"        lhs = {c['lhs'].get('display', c['lhs'])}   rhs = {c['rhs'].get('display', c['rhs'])}")
        print(f"        {c['explanation'][:160]}")


def lean_core_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((ROOT / "lean" / "CryoLean").glob("*.lean")) + [ROOT / "lean" / "Main.lean"]:
        h.update(p.read_bytes())
    b = config.lean_binary_path()
    if b.exists():
        h.update(b.read_bytes())
    return h.hexdigest()[:16]


def run() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    api = CryoLeanAPI()
    st = api.get_lean_status()["data"]
    _hr("Lean checker")
    print(f"   available={st['lean_available']} version={st['version']} selftest={st['selftest_passed']} theorems={st['theorem_count']} unsafe={st['unsafe_markers']}")

    # ------------------------------------------------------------------ A
    _hr("Demo A — confirmed incompatibility: 10 T magnetoresistance on the PPMS DynaCool 9 T")
    r = api.check_compatibility("mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res", confirmed=True)["data"]
    print(f"   VERDICT: {r['verdict']} — {r['user_message']}")
    _checks(r)
    for c in r["suggestions"]["conflicts"]["conflicts"]:
        print("   Z3 unsat core:", c["explanation"])
        for f in c["facts"]:
            print("      evidence:", f.get("evidence_ids"))
    ev = next(c for c in r["checks"] if c["keys"] == ["magnetic_field.max"])["capability_evidence"]
    for e in ev:
        print(f"   manufacturer evidence {e['id']}: \"{e.get('quote', '')[:100]}\" — {e['document_title'][:70]} ({e['location'][:50]})")
    for a in r["suggestions"]["alternatives"][:3]:
        print(f"   Z3 alternative {a['configuration_id']:40} z3={a['z3_status']:20} Lean={a['lean_verdict']}")
    _save("demo_a_incompatibility", r)

    # ------------------------------------------------------------------ B
    _hr("Demo B — coupled multiphysics: qubit wiring heat budget on a Bluefors LD400 with high-density wiring")
    r = api.check_compatibility("quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw", confirmed=True)["data"]
    print(f"   VERDICT: {r['verdict']} — {r['user_message']}")
    _checks(r)
    c = r["coupled_checks"][0]
    print("   equation:", c["equation"])
    for a in c["assumptions"]:
        print("   assumption:", a)
    print("   cooling-power slot:", c["slot_resolution"])
    for p in r["suggestions"]["parameter_changes"]:
        if p["status"] == "found":
            print(f"   Z3 parameter change: {p['parameter']} {p['current']} -> {p['suggested']}  | Lean re-check: {p['lean_verdict']} (verified={p['verified']})")
    _save("demo_b_coupled", r)

    # ------------------------------------------------------------------ C
    _hr("Demo C — new industry (semiconductors) through the research pipeline, same Lean core")
    before = lean_core_hash()
    tmp = Path(tempfile.mkdtemp(prefix="cryolean_demo_"))
    shutil.copy(config.db_path(), tmp / "demo.db")
    api2 = CryoLeanAPI(str(tmp / "demo.db"))
    ind = api2.register_industry("Semiconductors and electronics", "cryogenic device characterisation", "semiconductors_and_electronics")["data"]
    print("   registered industry:", ind["id"], "status:", ind["status"])
    rr = api2.research_new_experiment("Measure I-V of a MoS2 transistor on a cold probe station from 10 K to room temperature",
                                      "semiconductors_and_electronics")["data"]
    print("   research request:", rr["request"]["id"], "->", rr["verdict"], "| closest prepared profiles:",
          [m["experiment_id"] for m in rr["closest_profiles"]])
    nd = ROOT / "research" / "new_industry"
    doc = json.loads((nd / "semiconductor_candidate_experiment.json").read_text(encoding="utf-8"))
    evid = json.loads((nd / "semiconductor_candidate_evidence.json").read_text(encoding="utf-8"))
    cand = api2.register_experiment(doc, evid, "research agent", rr["request"]["id"])["data"]
    print("   candidate:", cand["id"], "validation ok:", cand["validation"]["ok"], "| warnings:", len(cand["validation"]["warnings"]))
    before_approve = api2.check_compatibility(doc["id"], "lakeshore_crx_vf", confirmed=True)
    print("   verify before approval ->", before_approve.get("error", {}).get("code"))
    api2.approve_candidate(cand["id"], "demo reviewer")
    found = api2.find_compatible_equipment(doc["id"], confirmed=True)["data"]
    for c in found["candidates"][:5]:
        print(f"   Z3 candidate {c['configuration_id']:30} z3={c['z3_status']:20} Lean={c['lean_verdict']}")
    r = api2.check_compatibility(doc["id"], found["candidates"][0]["configuration_id"], confirmed=True, suggestions=False)["data"]
    print(f"   Lean check of the top candidate: {r['verdict']} (industry={r['experiment']['industry']})")
    _checks(r)
    after = lean_core_hash()
    print(f"   Lean core hash before={before} after={after} unchanged={before == after}")
    _save("demo_c_new_industry_search", found)
    _save("demo_c_new_industry_check", r)
    shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ D
    _hr("Demo D — campaign: three experiments in one cooldown of the Lake Shore CRX-VF (Z3 packs, Lean validSchedule decides)")
    exps = ["bio_cryo_fluorescence_vitrified", "chem_low_temperature_raman", "chem_phase_transition_pom",
            "mat_magnetoresistance_10T"]
    durs = {exps[0]: {"value": 6, "unit": "h"}, exps[1]: {"value": 8, "unit": "h"}, exps[2]: {"value": 4, "unit": "h"},
            exps[3]: {"value": 2, "unit": "h"}}
    d = api.schedule_campaign("lakeshore_crx_vf", exps, {"value": 48, "unit": "h"}, durs, None, True)["data"]
    for e in d["excluded_experiments"]:
        print(f"   excluded by Lean: {e['experiment_id']} ({e['lean_verdict']})")
    print(f"   cooldown {d['cooldown']}, Z3 makespan {d['z3']['makespan']}")
    for t in d["timeline"]:
        print(f"   {t['start']:>6} - {t['stop']:>6}  {t['experiment_id']}")
    print(f"   Lean validSchedule: {d['lean']['valid']}  theorems: {', '.join(d['lean']['theorems'])}")
    tight = api.schedule_campaign("lakeshore_crx_vf", exps[:3], {"value": 20, "unit": "h"}, durs, None, True)["data"]
    print(f"   20 h run instead: Z3 {tight['z3']['status']}: {tight['z3']['explanation']}")
    d.pop("lean_input", None)
    _save("demo_d_campaign_schedule", {"fits": d, "too_long": tight})
    return 0
