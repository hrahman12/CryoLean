"""Source-guided presentation metadata; never an input to compatibility logic.

The research descriptors describe published apparatus, not newly installed
capabilities. Unknown dimensions stay unknown. WebGL uses representative sizes.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from . import config


@lru_cache(maxsize=1)
def _research():
    experiments, machines, selection = {}, {}, {}
    for p in sorted((config.ROOT / "research/expansion").glob("*_manifest.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        experiments.update(m.get("experiment_scenes", {}))
        machines.update(m.get("equipment_scenes", {}))
        selection.update({i["id"]: i for i in m.get("industries", [])})
    v4 = config.ROOT / "research/v4/site_selection.json"
    if v4.exists():
        selection.update(json.loads(v4.read_text(encoding="utf-8")))
    geometry = {}
    for p in sorted((config.ROOT / "research/v4/scene").glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        if doc.get("configuration_id"):
            geometry[doc["configuration_id"]] = doc
    return experiments, machines, geometry, selection


def _choose(text, rules, fallback):
    text = text.lower()
    for keys, value in rules:
        if any(key in text for key in keys.split("|")):
            return value
    return fallback


MACHINE_RULES = [
    ("mri|drycool|magnetom", "mri"),
    ("cryo-room|cryotherapy chamber", "cryo_room"),
    ("microtome|ultramicrotomy", "microtome"),
    ("wafer prober|wafer probe|probe station|probe_station|hall_station", "probe_station"),
    ("dilution", "dilution"),
    ("thermal-vacuum|thermal_vacuum|telescope_vacuum|tvac", "thermal_vacuum"),
    ("wind_tunnel|wind tunnel", "wind_tunnel"),
    ("tensile|mechanical (tensile|conductor_test|magnet_test|brittleness|charpy|impact-test", "tensile"),
    ("cryogenic_mill|cryogenic mill|cryogenic grinder|cryogenic ball|mixer mill|impact mill|freezer mill", "mill"),
    ("freeze dryer|freeze_dryer|lyophilizer", "freeze_dryer"),
    ("vitrification|plunge freezer", "plunge_freezer"),
    ("nerve_cryoablation", "nerve_probe"),
    ("freeze-substitution", "freeze_substitution"),
    ("gas_adsorption|gas-sorption|cryogenic_sorption", "sorption"),
    ("gas_preconcentrator|gas preconcentrator|cold trap|permeation", "gas_manifold"),
    ("propellant_loop|reliquefier|liquefier|helium refrigerator", "propellant"),
    ("srf_test", "srf"),
    ("noble_liquid|bolometer_array", "particle_detector"),
    ("neutron", "neutron"),
    ("radiometer|superconducting_standard|cryogenic_calibration", "metrology"),
    ("optical_resonator|optical_emitter|optical_detector", "optical_bench"),
    ("cryopump", "cryopump"),
    ("microscope|optical_cold_stage|microthermometry|heating/freezing stage", "optical_stage"),
    ("optical cryostat|optical_cryostat|magneto-optical|optical test dewar", "optical_cryostat"),
    ("dnp|nmr spectrometer", "nmr"),
    ("magnet|ppms|physical property", "magnet"),
    ("gas-stream|cryostream", "gas_stream"),
    ("etch tool|cryo-drie", "etch"),
    ("cryocooler|micro_jt", "cryocooler"),
    ("dewar|vapour-phase|vapor-phase", "storage_dewar"),
    ("freezer|freeze_thaw|climatic|test chamber|thermal shock|thermal cycling|cryogenic_cabinet|cryogenic treatment", "freezer"),
    ("bath|circulator|calorimeter|insulation_test", "calorimeter"),
    ("detector|gamma|germanium|hpge|radionuclide", "detector"),
    ("quantum hall resistance", "magnet"),
    ("cryogenic_rf_fixture", "rf_fixture"),
    ("heated-block|fixed-point", "metrology"),
    ("dilatometer", "dilatometer"),
    ("flow-chemistry", "flow_reactor"),
    ("forcing system", "gas_stream"),
    ("large-cold-plate", "cold_plate"),
    ("xrd|diffraction", "diffraction"),
    ("adr|demagnetization|helium-4|sorption insert|he-3|1 k|1k system", "helium_stack"),
]

EXPERIMENT_RULES = [
    ("whole_body|cryostimulation", "cryostimulation"),
    ("mri|magnetic resonance imaging", "mri"),
    ("torus_cryopump", "gas_pumping"),
    ("distillation", "distillation"),
    ("pellet|pipe_gun", "pellet_injection"),
    ("coil_cold_test|wire_mqe", "magnet_qualification"),
    ("stirling|heat-lift", "cooler_test"),
    ("vapour_pressure_scale", "metrology"),
    ("thermal_cycling|cold_operation", "thermal_test"),
    ("cryoem|cryo-em|protein molecules", "electron_microscopy"),
    ("cryofib|ion beam", "ion_milling"),
    ("ultramicrotomy|cryosection|frozen tissue|tokuyasu", "cryosection"),
    ("freez|vitrif|preserve|bank bacteria|archive|stored|storage", "preservation"),
    ("cryomill|grind|grinding|homogen|pulver|powder for rna", "milling"),
    ("lyophil|freeze-dry|freeze dry|sublimation", "lyophilization"),
    ("tensile|fatigue|strain|stretches|stretch|impact|brittleness|charpy", "mechanical"),
    ("wind|aerodynamics|aircraft", "aerodynamics"),
    ("telescope|mirror|alignment", "optical_alignment"),
    ("thermal cycling|temperature cycling|thermal shock|tvac|space-qualify|thermal-cycling", "thermal_test"),
    ("battery|fuel-cell|fuel cell|cold start|cold_cranking", "battery"),
    ("hydrogen_lad|liquefaction|liquid oxygen|propellant|liquefy", "fluid_transfer"),
    ("permeation|leak", "heat_leak"),
    ("boiloff|insulation|calorimetry|heat_capacity|heat-pulse|thermal transition|dsc|tg", "calorimetry"),
    ("sorption|bet|adsorption", "adsorption"),
    ("voc|pollutant|halocarbon|noble_gas|gas extraction|co2|water_cryo|trace gas", "gas_trapping"),
    ("resonance|resonator|frequency|srf|cavity|rf filter|ybco_rf", "resonance"),
    ("bolometer|microcalorimeter|scintillation|teo2|neutrino|gamma|radioactiv|radiation", "particle_detection"),
    ("neutron|diffraction|crystallography|xrd", "diffraction"),
    ("nerve|cryoanalgesia", "cryoneurolysis"),
    ("magnetometry|magnetization|dilatom|squid|torque|dhva", "magnetometry"),
    ("josephson|acoustic_thermo|watt|radiometry|thermometer|fixed_point", "metrology"),
    ("dlts|defect trap|vacancy", "capacitance"),
    ("etch|nanowire", "etching"),
    ("hall|resistance|resistivity|transport|rrr|current|critical-current", "transport"),
    ("mosfet|transistor|finfet|cmos|wafer|superconducting digital|logic", "transistor"),
    ("qubit|transmon|wiring_heat|cpw|ion_trap", "quantum"),
    ("raman|spectroscopy|matrix_isolation|epr|nmr|fermi|arpes", "spectroscopy"),
    ("photoluminesc|photon|photometry|photophysics|infrared|array|detector|ccd|h2rg", "photon_detection"),
    ("microscop|phase|crystal|droplet|ice_cream|icecream|fluid_inclusion", "microscopy"),
]


def experiment(catalog, ex):
    scenes, _, _, selections = _research()
    raw = scenes.get(ex["id"], {})
    text = " ".join(str(ex.get(k, "")) for k in ("id", "name", "plain_name"))
    mechanism = _choose(text, EXPERIMENT_RULES, "measurement")
    mechanism = {'bio_cryo_fluorescence_vitrified':'microscopy',
                 'quantum_mk_vector_field_transport':'quantum_transport'}.get(ex['id'],mechanism)
    # Resolve common overlapping words before the broad rules above.
    if "lyophil" in text.lower() or "freeze-dry" in text.lower(): mechanism = "lyophilization"
    if "cryoneurolysis" in text.lower(): mechanism = "cryoneurolysis"
    if "wiring_heat" in text.lower(): mechanism = "quantum_wiring"
    if "ice_nucleation" in text.lower() or "plate_freezing" in text.lower(): mechanism = "droplet_freezing"
    if "icecream" in text.lower(): mechanism = "microscopy"
    if "steel_deep" in text.lower(): mechanism = "heat_treatment"
    sample = raw.get("sample_shape") or raw.get("specimen") or ex.get("name")
    elements = raw.get("apparatus_elements") or raw.get("apparatus") or []
    if isinstance(elements, str): elements = [elements]
    urls = list(dict.fromkeys([s.get("url") for s in ex.get("sources", []) if s.get("url")]))
    visual = {"archetype": ex["id"], "mechanism": mechanism, "specimen": sample,
              "title": ex.get("plain_name") or ex["name"], "elements": elements,
              "steps": raw.get("steps") or ["Prepare the specimen using the cited procedure.",
                        "Establish the confirmed sample environment and required measurement connections.",
                        "Acquire the documented observable. The animation does not generate scientific measurements."],
              "source_urls": urls, "notes": "Representative procedural geometry. Required apparatus is separate from installed machine capabilities."}
    selected = selections.get(ex.get("industry"), {}).get("configuration_ids", [])
    reported = [str(s).lower() for s in ex.get("reported_equipment", []) if len(str(s)) > 3]
    named = [cid for cid, c in catalog.configurations.items()
             if any(n in f"{c.get('manufacturer','')} {c.get('model','')} {c.get('name','')}".lower() for n in reported)]
    preferred = list(dict.fromkeys(selected + named))
    return {"visualization": visual, "preferred_configuration_ids": preferred}


def configuration(catalog, cfg):
    _, machines, geometries, _ = _research()
    raw = machines.get(cfg["id"], {})
    geometry = geometries.get(cfg["id"], {})
    family = _choose(f"{cfg.get('family','')} {cfg.get('model','')} {raw.get('family','')}", MACHINE_RULES, "measurement_cryostat")
    # Family names, not industry labels, choose machine geometry.
    if cfg["equipment_id"] == "linkam_thms600": family = "optical_stage"
    if cfg["equipment_id"] == "bluefors_ld": family = "dilution"
    if cfg["equipment_id"] == "lakeshore_crx": family = "probe_station"
    if cfg["equipment_id"] in {"qd_ppms_dynacool", "qd_ppms_classic", "oxford_teslatronpt"}: family = "magnet"
    return {"family": family, "archetype": cfg["id"], "variant": cfg["id"],
            "title": cfg.get("model") or cfg.get("name"), "geometry": geometry,
            "elements": raw.get("apparatus") or raw.get("apparatus_elements") or [],
            "source_urls": list(dict.fromkeys([e.get("source_url") for c in cfg.get("capabilities", [])
                                               for e in catalog.evidence_for(c.get("evidence_ids", [])) if e.get("source_url")])),
            "notes": "Source-guided illustrative model; component sizes without published dimensions are schematic. Not manufacturer CAD."}
