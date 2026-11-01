#!/usr/bin/env python
"""Data corrections from the 2026-10-31 adversarial review (findings DP-1, DP-2, DP-3, DP-5, DP-7, DP-9).
Each change is justified by an existing evidence record; nothing new is invented. Idempotent."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def save(p, o):
    p.write_text(json.dumps(o, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cap(cfg, key):
    return next(c for c in cfg["capabilities"] if c["key"] == key)


def note(eq, text):
    eq.setdefault("modeling_notes", [])
    if text not in eq["modeling_notes"]:
        eq["modeling_notes"].append(text)


# DP-1: OptistatDry with windows fitted -> lower bound is the 6.5 K "4 windows" figure (ev_ox_0024), not "<3 K / <4 K (blanks fitted)"
p = ROOT / "data/cryostats/oxford_optistatdry.json"
eq = load(p)
for cfg in eq["configurations"]:
    c = cap(cfg, "temperature.range")
    if c["value"].get("kind") == "range" and "ev_ox_0024" not in c["evidence_ids"]:
        c["value"]["lo"] = {"value": 6500, "unit": "mK"}
        c["evidence_ids"] = ["ev_ox_0024"] + [i for i in c["evidence_ids"] if i not in ("ev_ox_0020", "ev_ox_0022")]
note(eq, "Review fix DP-1: configurations with windows fitted use the documented 6.5 K (4 windows) lower bound; "
         "the <3 K / <4 K figures apply only with window blanks fitted (no optical access).")
save(p, eq)

# DP-2: CRX-4K configuration is the 2-probe-arm variant (its 4.5 K / 5 K figures are documented for 2 arms)
p = ROOT / "data/cryostats/lakeshore_crx.json"
eq = load(p)
for cfg in eq["configurations"]:
    if cfg["id"] == "lakeshore_crx_4k":
        c = cap(cfg, "electrical.probe_arms")
        c["value"] = {"kind": "count", "n": 2}
        c["evidence_ids"] = ["ev_ls_0030", "ev_ls_0032"]
note(eq, "Review fix DP-2: lakeshore_crx_4k records the 2 probe arms its documented base/range figures apply to "
         "(up to 6 arms are possible but change the base temperature; model them as a separate configuration).")
save(p, eq)

# DP-3: Leica set-range tolerance is not a stability specification -> UNKNOWN
p = ROOT / "data/cryostats/leica_cm1950.json"
eq = load(p)
for cfg in eq["configurations"]:
    c = cap(cfg, "temperature.stability")
    if c["value"].get("kind") != "unknown":
        c["value"] = {"kind": "unknown"}
        c["evidence_status"] = "unknown"
note(eq, "Review fix DP-3: the printed set-range tolerances (±5 K Gen A, ±3 K Gen B) are not temperature-stability "
         "specifications; temperature.stability is UNKNOWN (the tolerance records remain in the evidence database).")
save(p, eq)

# DP-9: Bluefors vector magnet compatibility with standard LD frames is not stated -> UNKNOWN
p = ROOT / "data/cryostats/bluefors_ld.json"
eq = load(p)
for cfg in eq["configurations"]:
    c = cap(cfg, "magnetic_field.vector")
    c.update(value={"kind": "unknown"}, install="unknown", evidence_status="unknown")
note(eq, "Review fix DP-9: vector-magnet compatibility with standard LD frames is not stated in the sources "
         "(ev_bf_0039 says so; ev_bf_0040 is the Ultra-Compact LD350 kit), so magnetic_field.vector is UNKNOWN.")
save(p, eq)

# DP-5: the phase-transition cooling-rate requirement reversed its DSC source -> removed
p = ROOT / "data/experiments/chem_phase_transition_pom.json"
ex = load(p)
ex["requirements"] = [r for r in ex["requirements"] if r.get("key") != "temperature.cooling_rate.max"]
mi = "controlled slow cooling (<= 10 K/min) is needed to observe the Cr1 phase (DSC observation, ex2_A_009); a stage's ability to hold a slow controlled rate is not modelled"
if mi not in ex["missing_information"]:
    ex["missing_information"].append(mi)
save(p, ex)

# DP-7: the 77 K stage-temperature parameter cites the record that states 77 K
p = ROOT / "data/experiments/bio_cryo_fluorescence_vitrified.json"
ex = load(p)
for prm in ex["params"]:
    if prm["name"] == "operating_temperature":
        prm["evidence_ids"] = ["ev_exp_0011"]
save(p, ex)
print("data fixes applied")
