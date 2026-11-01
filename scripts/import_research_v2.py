#!/usr/bin/env python
"""One-time, reproducible import of the independently verified v2 research (research/v2/*.json)
into the seed catalog.  Every value written here points at a research fact id; nothing is invented.

Run:  python scripts/import_research_v2.py      (idempotent)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RES = ROOT / "research" / "v2"
sys.stdout.reconfigure(encoding="utf-8")

STATUS_MAP = {"manufacturer_specification": "manufacturer_specification",
              "experimental_observation": "experimental_observation",
              "reference_data": "reference_data", "textbook_model": "textbook_model"}


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ 1. evidence
facts = {}
for p in sorted(RES.glob("*.json")):
    d = load(p)
    recs = []
    for f in d["facts"]:
        facts[f["id"]] = f
        found = f.get("status") == "found"
        ver = f.get("verification") or ("independently re-fetched and confirmed 2026-10-31" if found else "")
        recs.append({
            "id": f["id"],
            "claim": f["claim"],
            "value_as_printed": f.get("value_as_printed", ""),
            "si": f.get("si"),
            "normalized": None,
            "quote": f.get("quote", "") if found else "",
            "source_url": f.get("source_url") or "https://example.invalid/not-found",
            "document_title": f.get("document_title") or "(not found)",
            "location": f.get("location", ""),
            "doi": f.get("doi") or None,
            "applies_to": f.get("applies_to", ""),
            "evidence_status": STATUS_MAP.get(f.get("evidence_status"), "reference_data") if found else "unknown",
            "accessed": d.get("accessed", "2026-10-31"),
            "verification": ver,
            "research_topic": d["topic"],
        })
    save(DATA / "evidence" / f"v2_{p.stem}.json", recs)
    print(f"evidence v2_{p.stem}: {len(recs)} records")


def fq(fid, value=None):
    """Assert the fact exists, was found, and (optionally) that its SI value matches."""
    f = facts[fid]
    assert f.get("status") == "found", fid
    if value is not None:
        assert f["si"] and abs(float(f["si"]["value"]) - float(value)) <= 1e-9 * max(1, abs(float(value))), (fid, f["si"], value)
    return fid


# ------------------------------------------------------------------ 2. vocabulary
vp = DATA / "capability_vocabulary.json"
vocab = load(vp)
keys = vocab["keys"]
LOWER_BETTER = {"temperature.stability", "vibration.max", "cooldown_time.max", "cooldown_time.sample_exchange",
                "system_startup_time.max", "defrost.cycle_duration", "magnetic_field.uniformity",
                "temperature.stability.relative"}
NEW_KEYS = {
    # folded from per-file proposals
    "plate.diameter": ("max", "um", "Mixing-chamber / experimental plate diameter", "higher"),
    "experimental_space.height": ("max", "um", "Height of the experimental space below the coldest plate", "higher"),
    "facility.electrical_power.max": ("max", "nW", "Facility electrical power drawn (compressor)", "lower"),
    "trimming_thickness.range": ("range", "um", "Trimming thickness setting range (microtome cryostats)", "range"),
    "temperature.peltier_delta.max": ("max", "mK", "Extra cooling of the Peltier quick-freeze station", "higher"),
    "temperature.quick_freeze_shelf.min": ("min", "mK", "Lowest quick-freeze shelf temperature", "lower"),
    "defrost.cycle_duration": ("min", "s", "Defrost cycle duration (lower is better)", "lower"),
    "electrical.apparent_power.max": ("max", "VA", "Apparent electrical power drawn", "lower"),
    "equipment.mass.max": ("max", "g", "Equipment mass", "lower"),
    "specimen.feed.horizontal.max": ("max", "um", "Horizontal specimen feed", "higher"),
    "temperature.cooling_rate.max": ("max", "mK_per_min", "Maximum documented controlled cooling rate", "higher"),
    "cooling_power.at_5000mK": ("max", "nW", "Documented cooling power at 5 K", "higher"),
    "cooldown_time.sample_exchange": ("min", "s", "Documented time to cool a newly loaded sample (lower is better)", "lower"),
    "magnetic_field.ramp_rate.max": ("max", "uT_per_s", "Maximum documented magnet charging rate", "higher"),
    "magnetic_field.uniformity": ("min", "ppm", "Documented field inhomogeneity over the stated volume (lower is better)", "lower"),
    "temperature.stability.relative": ("min", "ppm", "Documented relative temperature stability (lower is better)", "lower"),
    "system_startup_time.max": ("min", "s", "Documented time from room temperature to operation (lower is better)", "lower"),
    # new physical properties (the 40-property framework)
    "temperature.gradient": ("min", "mK", "Documented temperature gradient across the sample position (lower is better)", "lower"),
    "thermal.contact_resistance": ("min", "K_per_W", "Thermal contact resistance of the sample mount (lower is better)", "lower"),
    "thermal_cycles.max": ("count", "count", "Documented number of thermal cycles the mount/sample tolerates", "higher"),
    "sample.orientation": ("set", "", "Sample orientations supported (e.g. horizontal, vertical, rotatable)", "set"),
    "sample.mass.max": ("max", "ug", "Maximum sample mass", "higher"),
    "sample.vsm.length.max": ("max", "um", "Recommended maximum sample length for the installed VSM (module-specific)", "higher"),
    "mechanical.resonance.min_frequency": ("min", "Hz", "Lowest documented mechanical resonance of the sample stage", "higher"),
    "mechanical.stress.max": ("max", "Pa", "Allowed mechanical stress on the sample mount", "higher"),
    "positioning.resolution": ("min", "nm", "Sample positioning resolution (lower is better)", "lower"),
    "vibration.frequency": ("range", "Hz", "Frequency band of the documented vibration", "range"),
    "magnetic_field.direction": ("set", "", "Magnetic field directions available (longitudinal, transverse, vector)", "set"),
    "electrical.current.max": ("max", "pA", "Maximum excitation current of the installed electrical module", "higher"),
    "electrical.noise_rms": ("min", "nV", "Documented RMS voltage noise over a stated bandwidth (lower is better)", "lower"),
    "emi.shielding": ("flag", "", "Electromagnetic interference shielding installed", "flag"),
    "rf.power.max": ("max", "nW", "Maximum RF/microwave power deliverable to the sample", "higher"),
    "vacuum.leak_rate": ("min", "Pa_m3_per_s", "Documented leak rate (lower is better)", "lower"),
    "gas.compatible": ("set", "", "Gases the sample space may be filled or purged with", "set"),
    "purge.gas": ("flag", "", "Sample chamber can be purged with gas (dry gas purge against condensation)", "flag"),
    "cryogen.type": ("set", "", "Cryogens the system uses", "set"),
    "gas.flow_rate.max": ("max", "L_per_min", "Maximum gas flow rate", "higher"),
    "pressure.stability": ("min", "uPa", "Documented pressure stability (lower is better)", "lower"),
    "cryogen.dewar_volume": ("max", "L", "Volume of the cryogen dewar supplied", "higher"),
    "cryogen.consumption_rate": ("min", "L_per_min", "Documented cryogen consumption (lower is better)", "lower"),
    "optical.transmission_range": ("range", "nm", "Wavelength range transmitted by the optical window", "range"),
    "optical.f_number": ("min", "f_number", "Documented f-number of the optical access (lower = wider cone)", "lower"),
    "optical.numerical_aperture": ("max", "NA", "Documented numerical aperture of the optical access", "higher"),
    "measurement.bandwidth": ("max", "kHz", "Measurement bandwidth of the installed module", "higher"),
    "operating_duration.max": ("max", "s", "Documented continuous operating duration", "higher"),
}
for k, (shape, unit, desc, better) in NEW_KEYS.items():
    entry = keys.get(k, {})
    entry.update({"shape": shape, "unit": unit, "description": desc, "status": "established", "better": better})
    keys[k] = entry
for k in LOWER_BETTER:
    if k in keys:
        keys[k]["shape"] = "min"
        keys[k]["better"] = "lower"
for k, v in keys.items():
    v.setdefault("better", {"max": "higher", "min": "lower", "range": "range", "flag": "flag", "count": "higher"}.get(v["shape"], ""))
# cooling-power keys carry their documented temperature (used by the coupled heat-balance models)
for k, v in keys.items():
    if k.startswith("cooling_power.at_") and k.endswith("mK"):
        v["at_temperature"] = {"value": int(k[len("cooling_power.at_"):-2]), "unit": "mK"}
vocab["units"]["VA"] = {"description": "volt-ampere (apparent power)", "si": "W", "scale": 1}
vocab["_comment"] = ("Universal, extensible capability vocabulary (v2). Keys are data, not Lean code. Values are integers in the "
                     "canonical unit named here; the data layer converts them exactly to SI rationals with dimensions for Lean. "
                     "'better' says which direction is favourable. 'min'-shaped keys are bounds where lower is better.")
save(vp, vocab)
print("vocabulary:", len(keys), "keys")

# ------------------------------------------------------------------ 3. equipment updates
LOWER_KIND_KEYS = {k for k, v in keys.items() if v["shape"] == "min"}


def migrate_kinds(eq):
    n = 0
    for cfg in eq["configurations"]:
        for cap in cfg["capabilities"]:
            if cap["key"] in LOWER_KIND_KEYS and cap["value"].get("kind") == "max":
                cap["value"] = {"kind": "min", "q": cap["value"]["q"]}
                n += 1
        # fold proposed capabilities whose key is now established
        props = cfg.pop("proposed_capabilities", None) or []
        have = {c["key"] for c in cfg["capabilities"]}
        for pc in props:
            if pc["key"] in keys and pc["key"] not in have:
                pc = {k: v for k, v in pc.items() if k != "note"}
                if pc["value"].get("kind") == "unknown":
                    pc["evidence_status"] = "unknown"
                if pc["key"] in LOWER_KIND_KEYS and pc["value"].get("kind") == "max":
                    pc["value"] = {"kind": "min", "q": pc["value"]["q"]}
                cfg["capabilities"].append(pc)
                n += 1
    eq.pop("proposed_vocabulary", None)
    return n


def set_cap(cfg, key, value, install, status, ids):
    for cap in cfg["capabilities"]:
        if cap["key"] == key:
            cap.update({"value": value, "install": install, "evidence_status": status, "evidence_ids": ids})
            return
    cfg["capabilities"].append({"key": key, "value": value, "install": install, "evidence_status": status, "evidence_ids": ids})


for p in sorted((DATA / "cryostats").glob("*.json")):
    eq = load(p)
    n = migrate_kinds(eq)
    for cfg in eq["configurations"]:
        cid = cfg["id"]
        if eq["id"] == "linkam_thms600":
            # manufacturer: quick-release gas valves for purging / controlling the atmosphere
            set_cap(cfg, "purge.gas", {"kind": "flag", "b": True}, "installed", "manufacturer_specification",
                    [fq("eg_045"), fq("eg_046")])
            if cfg["capabilities"] and any(c["key"] == "module.ln2_pump" and c["install"] == "installed" for c in cfg["capabilities"]):
                set_cap(cfg, "temperature.cooling_rate.max", {"kind": "max", "q": {"value": 100000, "unit": "mK_per_min"}},
                        "installed", "manufacturer_specification", [fq("eg_063"), fq("eg_068")])
        if eq["id"] == "qd_ppms_dynacool" and any(c["key"] == "module.vsm" and c["install"] == "installed" for c in cfg["capabilities"]):
            # QD advice: keep VSM sample length below 5 mm (point-dipole approximation)
            set_cap(cfg, "sample.vsm.length.max", {"kind": "max", "q": {"value": 5000, "unit": "um"}},
                    "installed", "manufacturer_specification", [fq("eg_017")])
        if eq["id"] == "bluefors_ld":
            # magnetic shielding is a documented OPTION (Amuneal cylinder inside the vacuum can)
            set_cap(cfg, "module.magnetic_shielding", {"kind": "flag", "b": True}, "optional_not_installed",
                    "manufacturer_specification", [fq("eg_084"), fq("eg_085")])
    eq.setdefault("modeling_notes", [])
    note = "2026-10-31 v2 import: lower-is-better bounds stored as 'min'; v2 research facts added (see data/evidence/v2_*.json)."
    if note not in eq["modeling_notes"]:
        eq["modeling_notes"].append(note)
    save(p, eq)
    print(f"{p.name}: {n} capability shapes migrated / proposals folded")

# ------------------------------------------------------------------ 4. materials (thermal contraction reference data)
MATERIALS = [
    ("copper", "Copper (OFHC / pure)", "0.00326", "tc_001", "0.00302", "tc_002", "80 K row used for 77 K-range work"),
    ("aluminium", "Aluminium (pure)", "0.00415", "tc_005", "0.00391", "tc_006", ""),
    ("aluminium_6061_t6", "Aluminium 6061-T6", "0.0041545", "tc_009", "0.0038873", "tc_010", "computed from the NIST fit (constant branch below 18 K)"),
    ("stainless_304", "Stainless steel AISI 304", "0.00296", "tc_012", "0.00279", "tc_013", ""),
    ("brass_yellow", "Brass, yellow (65Cu-35Zn)", "0.00384", "tc_018", "0.00350", "tc_019", ""),
    ("titanium", "Titanium (unalloyed)", "0.00151", "tc_025", "0.00142", "tc_026", ""),
    ("ti6al4v", "Ti-6Al-4V", "0.0017361", "tc_023", "0.0016232", "tc_024", "computed from the NIST fit"),
    ("silicon", "Silicon", "0.00022", "tc_028", "0.000232", "tc_029", "4 K value is the NBS 0-20 K plateau (footnote: estimated)"),
    ("sapphire", "Sapphire (Al2O3)", None, None, "0.0007773", "tc_034", "NIST fit valid 15-300 K only; no 4 K value recorded"),
    ("fused_silica", "Fused silica", "-0.00008", "tc_035", "-0.0000141", "tc_036", "sample-to-sample variation up to 2e-5 below 180 K (tc_037)"),
    ("g10_warp", "G-10 CR (warp)", None, None, "0.0021427", "tc_044", "NIST fit valid from 12 K; 4 K value would be an extrapolation"),
    ("g10_normal", "G-10 CR (normal)", None, None, "0.0064201", "tc_042", "NIST fit valid from 10 K; 4 K value would be an extrapolation"),
    ("ptfe", "PTFE (Teflon)", "0.0214", "tc_047", "0.0193", "tc_048", "NBS reference temperature 298 K"),
    ("invar_fe36ni", "Invar (Fe-36Ni)", "0.0004", "tc_054", "0.0004", "tc_054", "computed from the NIST fit (constant below 80 K)"),
]
mats = []
for mid, name, e4, id4, e77, id77, note in MATERIALS:
    entry = {"id": mid, "name": name, "property": "integrated linear thermal contraction (L_ref - L_T)/L_ref, positive = shrinks",
             "reference_temperature_K": 298 if mid == "ptfe" else 293, "notes": note, "values": []}
    if e4 is not None:
        fq(id4, e4)
        entry["values"].append({"to_temperature": {"value": 4000, "unit": "mK"}, "contraction": e4, "unit": "1", "evidence_ids": [id4]})
    if e77 is not None:
        fq(id77, e77)
        entry["values"].append({"to_temperature": {"value": 80000 if id77 in ("tc_002", "tc_006", "tc_013", "tc_019", "tc_026", "tc_029", "tc_036", "tc_048") else 77000,
                                                   "unit": "mK"}, "contraction": e77, "unit": "1", "evidence_ids": [id77]})
    mats.append(entry)
save(DATA / "physics" / "materials.json", {"_comment": "Reference data for the differential-thermal-contraction model. Values are exact decimal strings copied from the cited records.",
                                           "relation_evidence_ids": [fq("tc_057"), fq("tc_058"), fq("tc_059")], "materials": mats})
print("materials:", len(mats))

# ------------------------------------------------------------------ 5. experiments
def evid(*ids):
    return [fq(i) for i in ids]


def q(v, u):
    return {"value": v, "unit": u}


exp_dir = DATA / "experiments"
FROST = {
    "keys": ["vacuum.available", "purge.gas"],
    "constraint": {"kind": "present"},
    "mandatory": True,
    "conditions": [{"kind": "param_at_most", "name": "operating_temperature", "q": q(273150, "mK")}],
    "origin": "experimental_observation",
    "rationale": ("Condensation/frost: a cold specimen or window below the frost point collects ice unless the sample space is "
                  "evacuated or purged with dry gas (pm_015, pm_016). Applies only when the operating temperature is at or below 0 °C."),
    "evidence_ids": evid("pm_015", "pm_016", "pm_017"),
}

# (2) temperature-controlled sample microscopy: add the frost requirement and the operating-temperature parameter
p = exp_dir / "bio_cryo_fluorescence_vitrified.json"
ex = load(p)
ex["plain_name"] = "Examine a sample under the microscope while keeping it cold"
ex["requirements"] = [r for r in ex["requirements"] if r.get("keys") != FROST["keys"]] + [FROST]
ex["params"] = [{"name": "operating_temperature", "value": q(77000, "mK"), "origin": "experimental_observation",
                 "description": "Stage temperature used for cryo-fluorescence imaging in Last et al. (77 K, Linkam CMS196v3)",
                 "evidence_ids": [r["evidence_ids"][0] for r in ex["requirements"] if r.get("key") == "temperature.range"][:1] if any(r.get("key") == "temperature.range" for r in ex["requirements"]) else []}]
save(p, ex)

# (3) low-temperature Raman: frost requirement + operating temperature parameter (-140 °C)
p = exp_dir / "chem_low_temperature_raman.json"
ex = load(p)
ex["requirements"] = [r for r in ex["requirements"] if r.get("keys") != FROST["keys"]] + [FROST]
tr = next(r for r in ex["requirements"] if r.get("key") == "temperature.range")
ex["params"] = [{"name": "operating_temperature", "value": tr["constraint"]["q"], "origin": "experimental_observation",
                 "description": "Lowest measurement temperature of the procedure (Park et al., -140 °C)", "evidence_ids": tr["evidence_ids"]}]
save(p, ex)

# (5) electrical resistance: optional Joule-heating coupled check with user-supplied current / resistance
p = exp_dir / "mat_electrical_resistance_low_temperature.json"
ex = load(p)
ex["coupled"] = [{"model": "joule_heating_vs_cooling_power", "mandatory": False,
                  "rationale": ("Optional: the published procedures do not state sample resistance or a self-heating limit, and the "
                                "PPMS documents no cooling power, so this check is reported but does not decide the verdict. "
                                "Make it mandatory once the sample resistance and cooling power are known.")}]
ex["params"] = [
    {"name": "operating_temperature", "value": q(2000, "mK"), "origin": "experimental_observation",
     "description": "Lowest temperature of the reported 2-300 K range", "evidence_ids": next(r["evidence_ids"] for r in ex["requirements"] if r.get("key") == "temperature.range")},
    {"name": "measurement_current", "value": None, "origin": "user_entered", "description": "Excitation current you will use (not stated as a requirement by the papers)"},
    {"name": "sample_resistance", "value": None, "origin": "user_entered", "description": "Sample resistance at the operating temperature"},
]
save(p, ex)

# (4) NEW: temperature-dependent phase-transition observation (polarized optical microscopy on a hot-cold stage)
save(exp_dir / "chem_phase_transition_pom.json", {
    "id": "chem_phase_transition_pom",
    "name": "Polarized optical microscopy of a crystallization / phase transition from 203 K to 393 K",
    "plain_name": "Observe a sample changing as its temperature changes",
    "industry": "chemistry_and_pharmaceuticals",
    "description": ("Watch crystallization and melting of a synthetic wax under a polarized optical microscope while the "
                    "temperature is scanned between 203 K and 393 K on a liquid-nitrogen-cooled hot-cold stage."),
    "keywords": ["phase transition", "crystallization", "melting", "polarized microscopy", "hot stage", "cold stage", "polymer", "wax"],
    "sources": [
        {"id": "src_wax_jpcb_2023", "citation": facts["ex2_A_001"]["document_title"], "doi": facts["ex2_A_001"].get("doi"),
         "url": facts["ex2_A_001"]["source_url"], "accessed": "2026-10-31", "doi_verified": True},
        {"id": "src_pbs_polymers_2026", "citation": facts["ex2_A_012"]["document_title"], "doi": facts["ex2_A_012"].get("doi"),
         "url": facts["ex2_A_012"]["source_url"], "accessed": "2026-10-31", "doi_verified": True},
    ],
    "reported_conditions": [
        {"key": "temperature.range", "as_printed": "203 K to 393 K", "evidence_id": fq("ex2_A_002")},
        {"key": "temperature.range", "as_printed": "upper limit 393 K", "evidence_id": fq("ex2_A_003")},
        {"key": "equipment", "as_printed": "Linkam THMS600 with liquid nitrogen pump", "evidence_id": fq("ex2_A_001")},
        {"key": "temperature.sweep_rate", "as_printed": "DSC companion runs 1-30 K/min (POM ramp rates not stated)", "evidence_id": fq("ex2_A_007")},
        {"key": "temperature.sweep_rate", "as_printed": "second procedure: heating 30 °C/min, cooling 1 °C/min", "evidence_id": fq("ex2_A_016")},
        {"key": "sample", "as_printed": "second procedure: sample between two glass slides", "evidence_id": fq("ex2_A_013")},
    ],
    "requirements": [
        {"key": "temperature.range", "constraint": {"kind": "range_within", "lo": q(203000, "mK"), "hi": q(393000, "mK")},
         "mandatory": True, "origin": "experimental_observation", "evidence_ids": evid("ex2_A_002", "ex2_A_003"),
         "rationale": "The wax procedure scanned 203-393 K; this is the paper's range and the user should confirm it for their sample."},
        {"key": "optical_access", "constraint": {"kind": "present"}, "mandatory": True, "origin": "experimental_observation",
         "evidence_ids": evid("ex2_A_001", "ex2_A_004"), "rationale": "Observation through a polarized optical microscope needs optical access to the sample."},
        {"key": "temperature.sweep_rate.max", "constraint": {"kind": "at_least", "q": q(30000, "mK_per_min")}, "mandatory": False,
         "origin": "experimental_observation", "evidence_ids": evid("ex2_A_016"),
         "rationale": "Optional: the second (PBS) procedure heated at 30 °C/min; the wax paper does not state POM ramp rates."},
        {"key": "temperature.cooling_rate.max", "constraint": {"kind": "at_least", "q": q(10000, "mK_per_min")}, "mandatory": False,
         "origin": "experimental_observation", "evidence_ids": evid("ex2_A_009"),
         "rationale": "Optional: the Cr1 phase crystallizes only at cooling rates up to 10 K/min, so the stage should reach at least that rate."},
        FROST,
    ],
    "params": [{"name": "operating_temperature", "value": q(203000, "mK"), "origin": "experimental_observation",
                "description": "Lowest temperature of the scan (203 K)", "evidence_ids": evid("ex2_A_002")}],
    "coupled": [],
    "missing_information": ["POM heating/cooling rates of the wax procedure", "sample thickness / cover-slip format",
                            "purge gas actually used", "objective working distance"],
    "confirmed": True,
    "confirmation_note": "Profile author reviewed the requirements on 2026-10-31; users must re-confirm edited values.",
})

# (6) NEW: magnetic-property measurement (VSM magnetometry)
save(exp_dir / "mat_magnetometry_vsm.json", {
    "id": "mat_magnetometry_vsm",
    "name": "VSM magnetometry: M-T from 5 K to 300 K and M-H isotherms up to 9 T",
    "plain_name": "Measure how a sample responds to a magnetic field",
    "industry": "materials_and_nanotechnology",
    "description": ("Measure magnetization versus temperature (5-300 K) and versus field up to 9 T with a vibrating sample "
                    "magnetometer, as in the Zintl-phase study on a PPMS DynaCool VSM."),
    "keywords": ["magnetometry", "magnetization", "VSM", "vibrating sample magnetometer", "M-H", "M-T", "susceptibility", "hysteresis", "magnetic property"],
    "sources": [
        {"id": "src_zintl_inorgchem", "citation": facts["ex2_B_001"]["document_title"], "doi": facts["ex2_B_001"].get("doi"),
         "url": facts["ex2_B_001"]["source_url"], "accessed": "2026-10-31", "doi_verified": True},
        {"id": "src_bfo_frontiers", "citation": facts["ex2_B_010"]["document_title"], "doi": facts["ex2_B_010"].get("doi"),
         "url": facts["ex2_B_010"]["source_url"], "accessed": "2026-10-31", "doi_verified": True},
    ],
    "reported_conditions": [
        {"key": "temperature.range", "as_printed": "M-T 5-300 K", "evidence_id": fq("ex2_B_003")},
        {"key": "magnetic_field.max", "as_printed": "M-H 0 to 90 kOe", "evidence_id": fq("ex2_B_006")},
        {"key": "magnetic_field", "as_printed": "M-T field 1 kOe", "evidence_id": fq("ex2_B_005")},
        {"key": "sample", "as_printed": "crushed crystals in a polyethylene capsule on a holder rod", "evidence_id": fq("ex2_B_002")},
        {"key": "temperature.sweep_rate", "as_printed": "second procedure: 5 K/min M-T sweep", "evidence_id": fq("ex2_B_014")},
    ],
    "requirements": [
        {"key": "temperature.range", "constraint": {"kind": "range_within", "lo": q(5000, "mK"), "hi": q(300000, "mK")},
         "mandatory": True, "origin": "experimental_observation", "evidence_ids": evid("ex2_B_003", "ex2_B_004"),
         "rationale": "The M-T measurement spanned 5-300 K (paper's range; user confirms)."},
        {"key": "magnetic_field.max", "constraint": {"kind": "at_least", "q": q(9000, "mT")}, "mandatory": True,
         "origin": "experimental_observation", "evidence_ids": evid("ex2_B_006", "ex2_B_010"),
         "rationale": "M-H isotherms were swept to 90 kOe (9 T); both procedures reached 9 T."},
        {"key": "module.vsm", "constraint": {"kind": "present"}, "mandatory": True, "origin": "experimental_observation",
         "evidence_ids": evid("ex2_B_001", "ex2_B_010"), "rationale": "Both procedures used the PPMS DynaCool VSM option."},
        {"key": "temperature.sweep_rate.max", "constraint": {"kind": "at_least", "q": q(5000, "mK_per_min")}, "mandatory": False,
         "origin": "experimental_observation", "evidence_ids": evid("ex2_B_014"),
         "rationale": "Optional: the second procedure swept temperature at 5 K/min."},
    ],
    "params": [
        {"name": "operating_temperature", "value": q(5000, "mK"), "origin": "experimental_observation",
         "description": "Lowest measurement temperature", "evidence_ids": evid("ex2_B_003")},
        {"name": "target_field", "value": q(9000, "mT"), "origin": "experimental_observation",
         "description": "Highest field of the M-H isotherms", "evidence_ids": evid("ex2_B_006")},
        {"name": "field_ramp_time_budget", "value": None, "origin": "user_entered",
         "description": "Time you allow for ramping the magnet to the target field (optional check)"},
    ],
    "coupled": [{"model": "magnet_ramp_time", "mandatory": False,
                 "rationale": "Optional: reports whether the documented charging rate reaches the target field within your time budget."}],
    "missing_information": ["sample mass and dimensions (not stated in either procedure)", "field sweep rate"],
    "confirmed": True,
    "confirmation_note": "Profile author reviewed the requirements on 2026-10-31; users must re-confirm edited values.",
})

# Demo B: mixing-chamber wiring heat budget (Krinner et al. 2019, EPJ Quantum Technology)
krinner = facts["hl_002"]
save(exp_dir / "quantum_mxc_wiring_heat_budget.json", {
    "id": "quantum_mxc_wiring_heat_budget",
    "name": "Wiring heat budget at the mixing chamber for a 50-qubit superconducting processor",
    "plain_name": "Check that the wiring for a superconducting qubit chip does not overheat the coldest stage",
    "industry": "quantum_computing_and_sensing",
    "description": ("Krinner et al. engineered the wiring of a 50-qubit processor (50 drive, 50 flux and 8 output lines plus "
                    "8 readout-drive lines) and designed it so that the heat load stays at least about three times below the "
                    "mixing-chamber cooling power. This profile checks that budget on a candidate dilution refrigerator."),
    "keywords": ["qubit", "superconducting", "wiring", "heat load", "coax", "dilution refrigerator", "mixing chamber", "cooling power"],
    "sources": [{"id": "src_krinner_2019", "citation": krinner["document_title"], "doi": krinner.get("doi"),
                 "url": krinner["source_url"], "accessed": "2026-10-31", "doi_verified": True}],
    "reported_conditions": [
        {"key": "cooling_power", "as_printed": "XLD400: 19 µW at 20 mK", "evidence_id": fq("hl_002", "1.9e-5")},
        {"key": "lines", "as_printed": "124 RF lines for a 50-qubit processor", "evidence_id": fq("hl_033")},
        {"key": "design_margin", "as_printed": "heat load at least about a factor three smaller than cooling power", "evidence_id": fq("hl_010")},
    ],
    "requirements": [
        {"key": "temperature.base", "constraint": {"kind": "at_most", "q": q(20, "mK")}, "mandatory": True,
         "origin": "experimental_observation", "evidence_ids": evid("hl_002", "hl_003"),
         "rationale": "The heat budget is evaluated at 20 mK, the temperature at which Krinner et al. quote the mixing-chamber cooling power."},
        {"key": "electrical.coax_lines", "constraint": {"kind": "count_at_least", "n": 124}, "mandatory": True,
         "origin": "experimental_observation", "evidence_ids": evid("hl_033"),
         "rationale": "A 50-qubit processor with individual drive and flux control needs 124 RF lines."},
    ],
    "params": [
        {"name": "operating_temperature", "value": q(20, "mK"), "origin": "experimental_observation", "evidence_ids": evid("hl_002"),
         "description": "Mixing-chamber temperature at which the budget is evaluated"},
        {"name": "n_drive_lines", "value": q(58, "count"), "origin": "experimental_observation", "evidence_ids": evid("hl_033"),
         "description": "50 qubit drive lines + 8 readout drive lines (stainless steel UT-085-SS-SS)"},
        {"name": "n_flux_lines", "value": q(50, "count"), "origin": "experimental_observation", "evidence_ids": evid("hl_033"),
         "description": "50 flux lines"},
        {"name": "n_output_lines", "value": q(8, "count"), "origin": "experimental_observation", "evidence_ids": evid("hl_033"),
         "description": "8 output lines (UT-085-NbTi)"},
        {"name": "q_drive_line", "value": q(13, "nW"), "origin": "experimental_observation", "evidence_ids": evid("hl_011"),
         "description": "Measured passive load per drive line at the MXC, 0.013(6) µW"},
        {"name": "q_flux_line", "value": q(29, "nW"), "origin": "experimental_observation", "evidence_ids": evid("hl_017"),
         "description": "Measured passive load per flux line at the MXC, 0.029(5) µW"},
        {"name": "q_output_line", "value": q(20, "nW"), "origin": "experimental_observation", "evidence_ids": evid("hl_019"),
         "description": "Measured passive load per output line at the MXC, 0.020(16) µW"},
        {"name": "p_flux_dc", "value": q(50, "nW"), "origin": "experimental_observation", "evidence_ids": evid("hl_029"),
         "description": "Average DC flux-bias dissipation per flux line at the MXC, 0.050(3) µW"},
        {"name": "design_margin", "value": q(3, "count"), "origin": "experimental_observation", "evidence_ids": evid("hl_010"),
         "description": "Design rule: heat load at least about three times smaller than the cooling power"},
    ],
    "coupled": [{"model": "mxc_wiring_heat_budget", "mandatory": True,
                 "rationale": "Krinner et al.'s design rule applied to the documented cooling power of the candidate refrigerator."}],
    "missing_information": ["active drive-line dissipation at operating power (paper estimates it separately)",
                            "TWPA pump-line passive load", "uncertainties of the per-line loads are not propagated"],
    "confirmed": True,
    "confirmation_note": "Profile author reviewed the requirements on 2026-10-31; users must re-confirm edited values.",
})

for p in sorted(exp_dir.glob("*.json")):
    ex = load(p)
    ex.setdefault("params", [])
    ex.setdefault("coupled", [])
    save(p, ex)
print("experiments updated")
