"""Rebuild lane C's source data. No shared vocabulary or verifier files are edited."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-10-31"
EVIDENCE = []
EQUIPMENT = []
EXPERIMENTS = []
SCENES = {}
EQUIPMENT_SCENES = {}
VOCAB = {}

SOURCES = {
    "nasa_insulation": ("Cryogenics Test Laboratory at NASA Kennedy Space Center: Thermal Insulation Systems Testing (21 April 2015)", "https://ntrs.nasa.gov/api/citations/20150011030/downloads/20150011030.pdf?attachment=true"),
    "asap": ("Micromeritics Application Note 136: Using the ASAP 2020 for Determining the Hydrogen Adsorption Capacity of Powders and Porous Materials", "https://downloads.micromeritics.com/Appnotes/Using-the-ASAP-2020-for-Determining-the-Hydrogen-Adsorption-Capacity-of-Powders-and-Porous-Materials.pdf"),
    "npl": ("National Physical Laboratory: Cryogenic testing services", "https://www.npl.co.uk/products-services/advanced-materials/cryogenic-testing-services"),
    "agt": ("Pan et al. (2021), Acoustic measurement of the triple point of neon TNe and thermodynamic calibration of a transfer standard for accurate cryogenic thermometry", "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=931816"),
    "pjvs": ("INRIM: Quantum voltage standard laboratory", "https://www.inrim.it/en/research/scientific-sectors/quantum-electronics/laboratories/quantum-voltage-standard-laboratory-0"),
    "locr": ("Houston and Livigni (2001), Comparison of Two Cryogenic Radiometers at NIST, J. Res. NIST 106, 641-647", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4862825/"),
    "snspd": ("Vyhnalek, Tedder and Nappier (2018), Performance and characterization of a modular superconducting nanowire single photon detector system for space-to-Earth optical communications links", "https://ntrs.nasa.gov/api/citations/20180002074/downloads/20180002074.pdf"),
    "qd": ("Thomas et al. (2024), Deterministic storage and retrieval of telecom light from a quantum dot single-photon source interfaced with an atomic quantum memory, Science Advances 10, eadi7346", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11014446/fullTextXML"),
    "atto": ("attocube: attoDRY800 optical cryostat specifications", "https://www.attocube.com/en/products/cryostats/closed-cycle-cryostats/attodry800-optical-cryostat"),
    "resonator": ("Wiens et al. (2020), A simplified cryogenic optical resonator apparatus providing ultra-low frequency drift, Review of Scientific Instruments 91, 045112", "https://arxiv.org/html/2004.01552v3"),
    "mosfet": ("Zhang et al. (2021), Characterization and Modeling of Native MOSFETs Down to 4.2 K", "https://arxiv.org/html/2104.03094"),
    "dlts": ("Scheffler et al. (2023), Comparison of the Properties of Defect States in Nitrogen-Containing n- and p-Type Float-Zone Silicon: A Combined Deep-Level Transient Spectroscopy and Minority-Carrier Transient Spectroscopy Study", "https://onlinelibrary.wiley.com/doi/full/10.1002/pssa.202200633"),
    "hall": ("Lake Shore: MeasureReady FastHall Station catalog, revision 062526", "https://www.lakeshore.com/docs/default-source/default-document-library/fasthall-station.pdf?sfvrsn=5c63af14_24"),
    "hall_method": ("Lake Shore: Hall Measurements with MeasureLINK-MCS Software", "https://test.lakeshore.com/docs/default-source/default-document-library/hall-measurements-with-measurelink-mcs-software.pdf?sfvrsn=d569e01b_6"),
    "cpx": ("Lake Shore: CPX cryogenic probe station specifications", "https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-cpx-cryogenic-probe-station"),
}


def q(value, unit="mK"):
    return {"value": str(value), "unit": unit}


def rng(lo, hi, unit="mK"):
    return {"kind": "range", "lo": q(lo, unit), "hi": q(hi, unit)}


def flag():
    return {"kind": "flag", "b": True}


def bound(kind, value, unit):
    return {"kind": kind, "q": q(value, unit)}


def ev(eid, source, quote, claim, normalized=None, status="experimental_observation", location=""):
    eid = "expc_" + eid
    title, url = SOURCES[source]
    EVIDENCE.append({"id": eid, "claim": claim, "value_as_printed": quote, "normalized": normalized,
                     "quote": quote, "source_url": url, "document_title": title, "location": location,
                     "applies_to": "Only the apparatus/procedure identified in this record; no inference of unlisted functions.",
                     "evidence_status": status, "accessed": DATE})
    return eid


def newkey(key, description, shape="flag", unit=None, better="flag"):
    VOCAB[key] = {"shape": shape, "unit": unit, "description": description, "status": "established", "better": better}
    return key


for key, desc in {
    "module.boiloff_calorimetry": "Installed steady-state liquid-cryogen boiloff calorimetry measurement apparatus",
    "module.volumetric_hydrogen_sorption": "Installed volumetric hydrogen dosing and adsorption-isotherm measurement system",
    "module.cryogenic_tensile": "Installed cryogenic specimen grips, mechanical load frame and tensile measurement apparatus",
    "module.acoustic_gas_thermometry": "Installed acoustic resonator, transducers and readout for primary gas thermometry",
    "module.resistance_thermometry_bridge": "Installed resistance-thermometer measurement bridge in the documented configuration",
    "module.programmable_josephson_voltage": "Installed programmable Josephson junction array and microwave/bias electronics for voltage metrology",
    "module.electrical_substitution_radiometry": "Installed absorbing cavity, electrical heater, thermometry and optical-power substitution readout",
    "module.snspd_detection": "Installed superconducting nanowire single-photon detector and operating bias/readout electronics",
    "module.photon_timing": "Installed time-correlated photon counting or time-tagging instrument",
    "module.calibrated_photon_flux": "Installed calibrated optical power measurement and attenuation path for detector characterization",
    "module.quantum_dot_excitation": "Installed pulsed optical excitation and collection apparatus for a quantum-dot emitter",
    "module.hbt_correlation": "Installed two-detector beam-splitter correlation apparatus for second-order photon autocorrelation",
    "module.optical_resonance_interrogation": "Installed laser frequency scanning and transmission readout of a cryogenic optical resonator",
    "module.semiconductor_parameter_analyzer": "Installed source/measure analyzer for semiconductor DC characteristics",
    "module.capacitance_transient_spectroscopy": "Installed capacitance-transient measurement and trap-filling electronics for DLTS",
    "module.hall_measurement": "Installed Hall sourcing, voltage measurement, switching and analysis instrumentation",
    "module.liquid_nitrogen_bath": "Documented flooded liquid-nitrogen sample bath in this configuration",
    "module.electrical_probing": "Cryogenic instrument supports contacting electronic samples with electrical probe arms",
}.items():
    newkey(key, desc)
newkey("temperature.warm_boundary.range", "Controlled warm boundary temperature range for insulation calorimetry", "range", "mK", "range")
newkey("pressure.operating.range", "Documented pressure interval used by the sample/resonator gas handling system", "range", "Pa", "range")
newkey("electrical.reference_voltage.max", "Largest magnitude reference voltage produced by a documented voltage standard", "max", "V", "higher")


def cap(key, value, evidence_id, status="experimental_observation"):
    return {"key": key, "value": value, "install": "installed", "evidence_status": status, "evidence_ids": [evidence_id]}


def unknown(key):
    return {"key": key, "value": {"kind": "unknown"}, "install": "unknown", "evidence_status": "unknown", "evidence_ids": []}


def eq(eid, cfgid, manufacturer, model, family, name, source, caps, basis, apparatus, steps):
    title, url = SOURCES[source]
    EQUIPMENT.append({"id": eid, "manufacturer": manufacturer, "model": model, "family": family,
                      "description": name + ". Source-backed comparison configuration; grouping is not a suitability claim.",
                      "documents": [{"id": "doc_" + eid, "title": title, "url": url, "accessed": DATE}],
                      "configurations": [{"id": cfgid, "name": name, "configuration_basis": basis, "capabilities": caps}]})
    EQUIPMENT_SCENES[cfgid] = {"family": family, "archetype": family, "apparatus": apparatus, "steps": steps,
                               "provenance": [{"title": title, "url": url}],
                               "fidelity": "Source-guided representative geometry; published apparatus, not manufacturer CAD. Only this named configuration is asserted."}


def req(key, constraint, eid, rationale, origin="experimental_observation"):
    return {"key": key, "constraint": constraint, "mandatory": True, "origin": origin,
            "rationale": rationale + " These are this profile's reviewed procedure conditions, not a universal requirement for the scientific field.", "evidence_ids": [eid]}


def present(key, eid, rationale):
    return req(key, {"kind": "present"}, eid, rationale)


def point(key, value, eid, rationale, unit="mK"):
    return req(key, {"kind": "point_within", "q": q(value, unit)}, eid, rationale)


def span(key, lo, hi, eid, rationale, unit="mK"):
    return req(key, {"kind": "range_within", "lo": q(lo, unit), "hi": q(hi, unit)}, eid, rationale)


def ex(eid, name, plain, industry, source, requirements, reported, equipment, missing, archetype, apparatus, specimen, steps, profile_type="published_procedure"):
    title, url = SOURCES[source]
    EXPERIMENTS.append({"id": eid, "name": name, "plain_name": plain, "industry": industry,
                        "description": plain + ". A bounded, source-grounded procedure profile; compatibility covers the listed checks and does not guarantee measured scientific performance.",
                        "profile_type": profile_type, "keywords": [archetype, industry],
                        "sources": [{"id": "src_" + source, "citation": title, "url": url, "accessed": DATE}],
                        "reported_conditions": reported, "reported_equipment": equipment,
                        "requirements": requirements, "params": [], "coupled": [], "missing_information": missing,
                        "confirmed": True, "confirmation_note": "Profile author reviewed these exact sourced conditions on " + DATE + ". The application must still require the user's review/confirmation; all edits invalidate confirmation."})
    SCENES[eid] = {"archetype": archetype, "apparatus": apparatus, "specimen": specimen, "distinctive_specimen": specimen,
                   "measurement": plain, "steps": steps, "source_url": url,
                   "fidelity": "Representative procedural scene. Its specimen and external instruments are experiment requirements, not evidence that the selected machine has those options installed."}


def obs(key, printed, eid, normalized=None):
    return {"key": key, "as_printed": printed, "normalized": normalized, "evidence_id": eid}


# ENERGY / HYDROGEN: thermal leakage, molecular sorption, and mechanical fracture.
e_boil = ev("nasa_boiloff", "nasa_insulation", "steady-state boiloff calorimetry", "NASA insulation calorimeters use LN2 boiloff as their energy measurement.", flag(), location="p.1 technical note 1")
e_boundaries = ev("nasa_boundaries", "nasa_insulation", "78 K (cold) and 293 K (warm)", "Standard NASA cryogenic insulation test boundary temperatures.", {"cold": q("78000"), "warm": q("293000")}, location="p.1 technical note 2")
e_boundary_range = ev("nasa_boundary_range", "nasa_insulation", "between 78 K and 353 K", "Documented controlled thermal-boundary span, not a sample-stage specification.", rng("78000", "353000"), location="p.1 technical note 2")
e_nasa_vac = ev("nasa_vacuum", "nasa_insulation", "below 1x10-5torr to 760 torr", "Insulation testing permits both evacuated and non-evacuated environments.", flag(), location="p.1 technical note 3")
eq("expc_nasa_cryostat100", "expc_nasa_cryostat100_standard", "NASA Kennedy Space Center", "Cryostat-100", "cryogenic_insulation_test",
   "NASA Cryostat-100 cylindrical absolute insulation calorimeter, standard 78 K / 293 K boundaries", "nasa_insulation",
   [cap("temperature.range", rng("78000", "353000"), e_boundary_range), cap("temperature.warm_boundary.range", rng("78000", "353000"), e_boundary_range), cap("module.boiloff_calorimetry", flag(), e_boil), cap("vacuum.available", flag(), e_nasa_vac)],
   "Published NASA CTL instrument. temperature.range denotes the controlled cold boundary, not a general-purpose experimental sample stage. The separately checked warm boundary is essential. Published 2015 facility apparatus; current booking availability is unverified.",
   ["one-metre cylindrical insulation sleeve", "LN2 cold mass", "warm vacuum jacket", "boiloff vent and flow meter"],
   ["Wrap the cylindrical cold mass with the insulation specimen.", "Establish cold and warm boundary temperatures and chamber pressure.", "Measure steady boiloff to determine transmitted heat."])
ex("expc_energy_insulation_boiloff", "Steady-state insulation heat-leak measurement at 78 K / 293 K (NASA Cryostat-100 procedure)", "Measure heat leaking through cryogenic tank insulation", "energy_and_hydrogen", "nasa_insulation",
   [point("temperature.range", "78000", e_boundaries, "Replicate NASA's standard cold boundary."), point("temperature.warm_boundary.range", "293000", e_boundaries, "Independently control the warm boundary; a cold cryostat alone is insufficient."), present("module.boiloff_calorimetry", e_boil, "The calorimetric boiloff measurement train is essential, rather than temperature capability alone.")],
   [obs("thermal_boundaries", "78 K cold / 293 K warm", e_boundaries)], ["Cryostat-100"], ["Insulation thickness, residual gas pressure, steady-state criteria and boiloff calibration must be chosen for the specimen; this profile does not predict conductivity or certify a tank."],
   "cryogenic_insulation_test", ["cylindrical blanket sleeve", "cold LN2 cylinder", "warm shell", "boiloff flow meter"], "Multilayer insulation or foam sleeve around a cryogenic storage cold mass", ["Establish a temperature gradient.", "Heat crosses the insulation and evaporates liquid nitrogen.", "The calibrated gas flow measures heat leak."])

e_h2 = ev("asap_hydrogen", "asap", "hydrogen adsorption capacity", "ASAP 2020 performs hydrogen adsorption measurement with volumetric dosing.", flag(), "manufacturer_specification", "p.1 introduction")
e_h2_bath = ev("asap_cryo_bath", "asap", "cryogenic temperatures (liquid nitrogen or liquid argon)", "The documented cryogenic H2 method uses a cryogen bath; no arbitrary continuous temperature range is asserted.", flag(), "manufacturer_specification", "p.1 sample tube guidance")
e_h2_free = ev("asap_free_space", "asap", "Calculated Free-space options", "Free-space determination is part of volumetric adsorption analysis.", flag(), "manufacturer_specification", "p.1")
eq("expc_asap2020", "expc_asap2020_hydrogen_ln2", "Micromeritics", "ASAP 2020, hydrogen-analysis software and LN2 sample bath", "cryogenic_sorption",
   "Micromeritics ASAP 2020 hydrogen adsorption setup with liquid-nitrogen bath", "asap",
   [cap("module.volumetric_hydrogen_sorption", flag(), e_h2, "manufacturer_specification"), cap("module.liquid_nitrogen_bath", flag(), e_h2_bath, "manufacturer_specification"), unknown("temperature.range")],
   "Exact application-note configuration: hydrogen-capable software, standard fritted sample tube and cryogenic isothermal jacket. The note does not specify a guaranteed sample-temperature interval, so temperature.range is UNKNOWN; a bath's boiling point is not silently treated as specimen temperature. Preparation/degas equipment is included in the method, not a hypothetical retrofit.",
   ["bench gas-analysis manifold", "pressure transducers", "fritted glass powder tube", "LN2 Dewar", "isothermal jacket"], ["Degas the powder using the source procedure.", "Surround the analysis tube with the cryogenic bath.", "Dose hydrogen and infer uptake from pressure and free space."])
ex("expc_energy_hydrogen_sorption", "Cryogenic volumetric hydrogen adsorption isotherm in porous powder (ASAP 2020 application method)", "Measure hydrogen uptake by a porous storage material", "energy_and_hydrogen", "asap",
   [present("module.volumetric_hydrogen_sorption", e_h2, "Absolute-pressure hydrogen dosing and uptake analysis are essential."), present("module.liquid_nitrogen_bath", e_h2_bath, "Select the liquid-nitrogen implementation of the documented cryogenic method; liquid argon is a separate user choice.")],
   [obs("sample_environment", "Cryogenic bath: liquid nitrogen or liquid argon", e_h2_bath), obs("free_space", "Calculated Free-space", e_h2_free)], ["ASAP 2020"], ["The application note requires the measured bath temperature to be entered; no exact specimen setpoint is claimed here.", "Sample-specific degassing compatibility, mass, free-space correction, gas purity and the pressure table require confirmation. This profile is not a hydrogen-tank charging procedure."],
   "cryogenic_sorption", ["glass powder bulb", "LN2 Dewar", "dosing manifold", "pressure sensor"], "Porous carbon or other powder adsorbent, measured by hydrogen gas uptake", ["Prepare and degas the powder.", "Dose known hydrogen quantities into the cold sample tube.", "Use equilibrium pressure and free-space correction to build the adsorption isotherm."], "documented_method_class")

e_tensile = ev("npl_tensile", "npl", "tensile testing", "NPL documents cryogenic tensile testing of metals and fibre-reinforced polymer composites.", flag(), "manufacturer_specification", "Cryogenic mechanical testing")
e_20k = ev("npl_20k", "npl", "mechanical characterisation at 77 K, 40 K, 20 K and 4 K", "NPL explicitly documents mechanical characterization at 20 K.", rng("20000", "20000"), "manufacturer_specification", "Fusion energy; Hydrogen section describes helium cooling with active temperature control")
eq("expc_npl_mechanical", "expc_npl_helium_tensile_20k", "National Physical Laboratory (UK)", "Helium-cooled cryogenic mechanical testing facility", "cryogenic_tensile",
   "NPL helium-cooled tensile test configuration at 20 K for hydrogen-system materials", "npl", [cap("temperature.range", rng("20000", "20000"), e_20k, "manufacturer_specification"), cap("module.cryogenic_tensile", flag(), e_tensile, "manufacturer_specification")],
   "Real specialized NPL facility, using documented helium cooling and active temperature control. The selected comparison configuration is the explicitly listed20 K test condition, not an inferred continuous4–77 K operating range. No load capacity or strain rate is invented.",
   ["mechanical load frame", "helium-cooled specimen chamber", "opposing tensile grips", "load cell and strain readout"], ["Grip a metal or composite coupon.", "Cool and stabilize the gauge region near 20 K.", "Apply tensile loading and record stress and strain."])
ex("expc_energy_tensile_20k", "Cryogenic tensile characterization of hydrogen-system metal or composite at 20 K (NPL method class)", "Test how a hydrogen-system material stretches and fails near 20 K", "energy_and_hydrogen", "npl",
   [point("temperature.range", "20000", e_20k, "Select the documented20 K mechanical test condition relevant to liquid-hydrogen service."), present("module.cryogenic_tensile", e_tensile, "Cryogenic grips, a mechanical load path and force/strain measurement are essential.")],
   [obs("temperature.range", "20 K", e_20k, q("20000"))], ["NPL cryogenic mechanical testing facility"], ["This is a documented test-method class, not a complete ASTM/ISO test recipe.", "Coupon dimensions, load range, strain rate, extensometry and gauge-length temperature uniformity must be agreed with the facility; no strength prediction is made."],
   "cryogenic_tensile", ["dog-bone specimen", "upper and lower grips", "cryogenic chamber", "load cell"], "Metal or fibre-reinforced composite coupon for liquid-hydrogen components", ["Mount the coupon between cryogenic grips.", "Cool the gauge section and establish the temperature.", "Pull the coupon while measuring force and extension."], "documented_method_class")

# METROLOGY: acoustic thermometry, Josephson voltage, optical watt.
e_agt = ev("agt_resonator", "agt", "helium-filled, copper-walled, quasi-spherical", "The primary acoustic gas thermometer uses a helium-filled copper quasi-sphere.", flag(), location="p.4")
e_agt_p = ev("agt_pressure", "agt", "pressures ranging from 30 kPa to 120 kPa", "Observed acoustic helium pressure interval; it is not a pressure-vessel rating.", rng("30000", "120000", "Pa"), location="p.18 impurity check and p.11 acoustic measurements")
e_agt_bridge = ev("agt_bridge", "agt", "reading cSPRT-1 with an F18 bridge", "The documented apparatus includes resistance thermometry bridge readout.", flag(), location="p.6 section2.1")
e_agt_temp = ev("agt_neon_result", "agt", "TNe = (24.55515 ± 0.00024)", "Measured thermodynamic neon triple-point temperature in kelvin; NOT a cryostat control specification or the exact AGT setpoint.", {"result": q("24.55515", "K"), "standard_uncertainty": q("0.00024", "K")}, location="p.1 abstract, units K continue next line")
eq("expc_lne_agt", "expc_lne_cnam_agt_2019", "LCM-LNE-Cnam research apparatus", "Pan et al. cryogen-free primary acoustic gas thermometer", "cryogenic_calibration",
   "LCM-LNE-Cnam acoustic gas thermometer,2019 published configuration", "agt", [cap("module.acoustic_gas_thermometry", flag(), e_agt), cap("module.resistance_thermometry_bridge", flag(), e_agt_bridge), cap("pressure.operating.range", rng("30000", "120000", "Pa"), e_agt_p), unknown("temperature.range")],
   "Published complete research apparatus at LCM-LNE-Cnam with Cryomech PT405 pulse-tube cooler, copper quasi-sphere and F18 bridge. No guaranteed temperature-control interval is supplied by the paper; the neon thermodynamic result is not reused as a machine capability. Historical published apparatus, not a claim of commercial availability.",
   ["pulse-tube cryostat", "two gold-plated shields", "quasi-spherical copper helium resonator", "microphone and acoustic drive", "gas-pressure manifold"], ["Purify and fill the resonator with helium.", "Measure acoustic and microwave resonances at controlled pressures.", "Infer thermodynamic temperature and calibrate the resistance thermometer."])
ex("expc_metrology_acoustic_thermometry", "Primary helium acoustic thermometry near the neon triple point (Pan et al.2019 runs)", "Calibrate a resistance thermometer using the speed of sound in helium", "metrology_and_calibration", "agt",
   [present("module.acoustic_gas_thermometry", e_agt, "A purpose-built acoustic primary thermometer is essential, rather than an arbitrary cold sample chamber."), present("module.resistance_thermometry_bridge", e_agt_bridge, "The transfer-thermometer bridge is part of the published calibration apparatus."), span("pressure.operating.range", "30000", "120000", e_agt_p, "Reproduce the documented helium pressure series.", "Pa")],
   [obs("reported_neon_triple_point_result", "24.55515 ±0.00024 K (result, not control range)", e_agt_temp), obs("pressure.operating.range", "30–120 kPa", e_agt_p)], ["Cryomech PT405", "F18 bridge", "helium-filled quasi-spherical resonator"], ["The exact T* control setpoint, gas purity, acoustic boundary-layer corrections and complete uncertainty budget must be reviewed from the paper. The neon result is deliberately not a temperature capability.", "This profile checks the documented apparatus function and pressure series; it does not certify traceability, uncertainty or a new thermodynamic temperature."],
   "cryogenic_calibration", ["copper quasi-sphere", "acoustic transducers", "pressure vessel", "resistance bridge"], "Helium gas resonator and a Pt-Co resistance thermometer transfer standard", ["Drive helium acoustic modes.", "Measure mode frequencies over a pressure series.", "Extrapolate the speed of sound and transfer temperature calibration."])

e_pjvs = ev("pjvs_function", "pjvs", "approximately 70,000 junctions connected in series and cooled to 4.2 K", "The INRIM national DC standard uses a real series Josephson array in liquid helium.", flag(), location="Primary DC voltage standard paragraph")
e_pjvs_v = ev("pjvs_10v", "pjvs", "capable of generating quantized voltages up to 10 V", "Documented magnitude of the quantized reference voltage.", bound("max", "10", "V"), location="Primary DC voltage standard paragraph")
eq("expc_inrim_pjvs", "expc_inrim_pjvs_4p2k", "Istituto Nazionale di Ricerca Metrologica", "National primary DC Programmable Josephson Voltage Standard", "superconducting_standard",
   "INRIM liquid-helium PJVS national DC standard,4.2 K,10 V", "pjvs", [cap("temperature.range", rng("4200", "4200"), e_pjvs), cap("module.programmable_josephson_voltage", flag(), e_pjvs), cap("electrical.reference_voltage.max", bound("max", "10", "V"), e_pjvs_v)],
   "Owner-described national primary standard including the Josephson junction array and its drive electronics, not a bare helium vessel. Separate pulse-driven AC/JAWS platform is not silently included. Operational4.2 K point only; no continuous range inferred.",
   ["liquid-helium Dewar", "immersed Josephson-array chip", "microwave feed", "low-thermal-emf leads", "reference voltmeter"], ["Cool the junction array in liquid helium.", "Irradiate and bias the array on quantized voltage steps.", "Compare a DC transfer reference or precision voltmeter."])
ex("expc_metrology_josephson_dc", "DC transfer-reference calibration against an INRIM4.2 K programmable Josephson standard", "Realize and compare a quantum-accurate DC voltage reference", "metrology_and_calibration", "pjvs",
   [point("temperature.range", "4200", e_pjvs, "Use the documented liquid-helium operating condition."), present("module.programmable_josephson_voltage", e_pjvs, "A PJVS array and its microwave/bias control are essential."), req("electrical.reference_voltage.max", {"kind": "at_least", "q": q("10", "V")}, e_pjvs_v, "Choose the documented 10 V comparison range; this is a procedure selection rather than a need for every voltage calibration.")],
   [obs("temperature.range", "4.2 K", e_pjvs, q("4200")), obs("electrical.reference_voltage.max", "up to 10 V", e_pjvs_v, q("10", "V"))], ["INRIM PJVS national DC standard"], ["Specific microwave frequency, array bias margins, thermal-emf cancellation, leakage control and measurement uncertainty require the laboratory procedure. Passing compatibility is not a calibration certificate."],
   "superconducting_standard", ["Josephson array chip", "microwave coax", "cryogenic probe", "DC reference terminals"], "Series array of approximately 70,000 Josephson junctions and a DC transfer standard", ["Establish the superconducting array at 4.2 K.", "Select quantized voltage steps with frequency and bias.", "Measure the transfer standard's difference from the reference."])

e_esr = ev("locr_esr", "locr", "electrical substitution", "LOCR infers optical power by controlled electrical substitution.", flag(), location="section3")
e_locr_t = ev("locr_5p4k", "locr", "approximately 5.4 K", "LOCR's observed absorbing-cavity temperature is approximately5.4 K, not HACR's temperature.", rng("5400", "5400"), location="section3")
e_locr_opt = ev("locr_path", "locr", "horizontal optical path", "LOCR provides horizontal optical input and a translation stage for transfer detectors.", flag(), location="section2")
eq("expc_nist_locr", "expc_nist_locr_2001", "NIST / Cambridge Research & Instrumentation", "Laser-Optimized Cryogenic Radiometer (LOCR)", "cryogenic_radiometer",
   "NIST LOCR optical-watt realization,2001 comparison apparatus, approximately5.4 K", "locr", [cap("temperature.range", rng("5400", "5400"), e_locr_t), cap("module.electrical_substitution_radiometry", flag(), e_esr), cap("optical_access", flag(), e_locr_opt)],
   "Complete historic published NIST Boulder LOCR reference apparatus with horizontal cavity and electrical feedback. The5.4 K value is an approximate observed operating condition, represented as this procedure point rather than a manufacturer's general control interval. Current facility availability is unverified.",
   ["horizontal receiving cavity", "helium-temperature cold mount", "heater and thermometer leads", "laser shutter", "translation stage with three-diode trap"], ["Illuminate the absorbing cavity.", "Reduce electrical heating to hold its temperature constant.", "Substitute a photodiode trap into the calibrated optical beam."])
ex("expc_metrology_optical_watt", "Silicon photodiode-trap responsivity transfer using NIST LOCR at approximately5.4 K", "Calibrate an optical detector by electrical-substitution radiometry", "metrology_and_calibration", "locr",
   [point("temperature.range", "5400", e_locr_t, "Replicate the paper's approximate absorbing-cavity operating condition; this point is not a required tolerance."), present("module.electrical_substitution_radiometry", e_esr, "A calibrated heater, absorber and constant-temperature substitution readout are essential."), present("optical_access", e_locr_opt, "The calibrated laser must reach the receiving cavity and transfer detector.")],
   [obs("temperature.range", "approximately5.4 K (absorbing cavity)", e_locr_t), obs("measurement", "electrical substitution", e_esr)], ["NIST LOCR"], ["Laser wavelength, beam power, underfilling aperture, window transmission and electrical/optical nonequivalence require separate review; the published uncertainty and responsivity are not predicted by this verdict."],
   "cryogenic_radiometer", ["black receiving cavity", "heater", "photodiode trap", "beam splitter and shutter"], "Three-photodiode silicon trap detector, compared with a cryogenic black cavity", ["Measure optical heating of the cold cavity.", "Replace optical heat with electrical heat at constant temperature.", "Transfer the measured optical watt to the silicon photodiode trap."])

# PHOTONICS: detector response, emitter photon statistics, optical frequency reference.
e_snspd = ev("snspd_two_detector", "snspd", "two-detector Opus One™ system", "NASA's real measured Opus One configuration has two detector channels.", flag(), location="p.2 section2")
e_snspd_t = ev("snspd_2p5k", "snspd", "temperature of 2.5 K", "Documented operating point of NASA's 2018 detector system.", rng("2500", "2500"), location="p.2 section2")
e_tcspc = ev("snspd_tcspc", "snspd", "multi-channel time-correlated single-photon counting (TCSPC) card", "The published setup includes external TCSPC counting electronics.", flag(), location="p.2 section2")
e_flux = ev("snspd_calibration", "snspd", "a calibrated 1550 nm InGaAs power meter", "The real detector-characterization setup contains a calibrated power meter and attenuated1550 nm optical path.", flag(), location="p.2 section2")
eq("expc_nasa_opus_one", "expc_nasa_opus_one_2018_setup", "Quantum Opus / NASA Glenn published apparatus", "Opus One two-detector optical-communications characterization setup", "optical_detector",
   "NASA 2018 Opus One two-detector setup with external TCSPC and calibrated1550 nm input", "snspd", [cap("temperature.range", rng("2500", "2500"), e_snspd_t), cap("module.snspd_detection", flag(), e_snspd), cap("module.photon_timing", flag(), e_tcspc), cap("module.calibrated_photon_flux", flag(), e_flux)],
   "The exact published NASA test setup includes the named two-channel Opus One, external laser/attenuators/power meter, polarization controllers and TCSPC. These external instruments are asserted only for this published lab configuration, not for an unconfigured factory Opus One. Detector composition is not guessed.",
   ["3U19-inch rack detector cryostat", "two fibre inputs", "bias/readout electronics", "attenuated laser and power-meter tap", "TCSPC card"], ["Cool the nanowires to the documented operating point.", "Inject a calibrated weak optical signal.", "Count and time the output pulses while varying bias."])
ex("expc_photonics_snspd_characterization", "1550 nm SNSPD system detection-efficiency and timing characterization at 2.5 K (NASA 2018)", "Measure the efficiency and timing of a cryogenic photon detector", "photonics_and_telecommunications", "snspd",
   [point("temperature.range", "2500", e_snspd_t, "Use the published2.5 K detector operating point."), present("module.snspd_detection", e_snspd, "The cold instrument must contain functional superconducting nanowires and bias/readout."), present("module.photon_timing", e_tcspc, "Output pulses require external time-correlated counting."), present("module.calibrated_photon_flux", e_flux, "Efficiency measurement needs a calibrated incident photon flux, not an uncalibrated animation.")],
   [obs("temperature.range", "2.5 K", e_snspd_t, q("2500")), obs("optical_input", "1550 nm calibrated optical path", e_flux)], ["Opus One", "TCSPC card"], ["Bias-current limits, polarization, dark/background counts, input attenuation and detector-specific calibration must be reviewed. Efficiency and jitter are measured results, not guaranteed compatibility outputs."],
   "optical_detector", ["meandered nanowire detector", "fibre-coupled cold mount", "bias tee", "TCSPC electronics"], "Two superconducting nanowire detectors receiving attenuated1550 nm photons", ["Calibrate and attenuate the1550 nm beam.", "A photon creates a resistive hotspot and voltage pulse.", "Count pulses and build a timing histogram against the laser trigger."])

e_qd_t = ev("qd_4k", "qd", "cooled to 4 K", "Actual temperature and named cryostat of the2024 QD photon-source setup.", rng("4000", "4000"), location="Methods: QD single-photon source operation")
e_qd_excite = ev("qd_excitation", "qd", "optical parametric oscillator (OPO)", "The published QD setup contains pulsed optical excitation, objective and collection optics.", flag(), location="Methods: QD single-photon source operation")
e_hbt = ev("qd_hbt", "qd", "50:50 fiber beam splitter", "Two-detector photon statistics measurement is part of the actual published apparatus.", flag(), location="Methods: QD single-photon source operation")
e_qd_tt = ev("qd_time_tagger", "qd", "time tagger", "The published photon-correlation setup includes external time tagging.", flag(), location="Methods: QD single-photon source operation")
eq("expc_thomas_qd_setup", "expc_attodry800_qd_hbt_2024", "attocube / Thomas et al. published apparatus", "attoDRY800 telecom quantum-dot source with HBT detector chain", "optical_emitter",
   "Thomas 2024 attoDRY800, 4 K QD source, excitation optics and two-detector HBT chain", "qd", [cap("temperature.range", rng("4000", "4000"), e_qd_t), cap("optical_access", flag(), e_qd_excite), cap("module.quantum_dot_excitation", flag(), e_qd_excite), cap("module.hbt_correlation", flag(), e_hbt), cap("module.photon_timing", flag(), e_qd_tt)],
   "Exact published4 K source configuration: attoDRY800,3-axis piezo stack, in-cryostat objective, OPO excitation, fibre collection,50:50 splitter, two SNSPD inputs and time tagger. The SNSPDs are external detection equipment; this does not say the4 K sample cryostat cools the detectors. The warm rubidium quantum memory is excluded from the selected source-only experiment.",
   ["optical-table-integrated cryostat", "cold objective over QD on piezo stack", "pump/collection optics", "50:50 fibre splitter", "two external SNSPD channels and time tagger"], ["Cool and align the QD under the internal objective.", "Excite the QD and spectrally filter the emitted telecom light.", "Split the photons and measure two-detector coincidences."])
ex("expc_photonics_qd_autocorrelation", "Telecom quantum-dot single-photon-source autocorrelation at 4 K (Thomas et al.2024 source subsystem)", "Measure the single-photon purity of a semiconductor quantum-dot emitter", "photonics_and_telecommunications", "qd",
   [point("temperature.range", "4000", e_qd_t, "Replicate the published4 K emitter sample environment."), present("optical_access", e_qd_excite, "Excitation and collection need a real optical path to the emitter."), present("module.quantum_dot_excitation", e_qd_excite, "Pulsed excitation and collection optics are essential."), present("module.hbt_correlation", e_hbt, "A beam splitter and two detector paths are essential to g(2) measurement."), present("module.photon_timing", e_qd_tt, "The published setup measures correlations with a time tagger.")],
   [obs("temperature.range", "4 K", e_qd_t, q("4000")), obs("measurement", "second-order autocorrelation", e_hbt)], ["attoDRY800", "Swabian Instruments time tagger"], ["The source-only profile does not certify the paper's warm atomic-memory interface.", "QD material preparation, pump spectral width, filter response, detector efficiency and coincidence calibration need separate review; g(2)(0) is not hardcoded."],
   "optical_emitter", ["quantum-dot chip", "cold objective", "piezo stack", "50:50 splitter", "two photon counters"], "Semiconductor quantum-dot emitter producing telecom photons; its photons are split into two coincidence channels", ["Pulsed light excites the4 K quantum dot.", "Filtered emitted photons enter a50:50 beam splitter.", "Two detector timestamps form the second-order correlation histogram."])

e_res_t = ev("resonator_temperatures", "resonator", "temperatures between $1.5$ K and 3.6 K", "Documented resonator experiment temperature interval; use exact1.5–3.6 K values.", rng("1500", "3600"), location="Abstract (math formatting normalized from HTML)")
e_res_scan = ev("resonator_scan", "resonator", "repeatedly measure the line center frequency", "The published apparatus interrogates resonance with scanning or detuning methods; PDH locking was explicitly not implemented.", flag(), location="sectionIII.3")
e_res_opt = ev("resonator_optical", "resonator", "single-mode polarization-maintaining fiber", "Actual fibre-coupled cryogenic optical breadboard.", flag(), location="sectionIII.2")
eq("expc_wiens_resonator", "expc_leiden_cf1k_si5_2020", "Leiden Cryogenics / Wiens et al. published apparatus", "CF-1K with Si5 cryogenic optical resonator breadboard", "optical_resonator",
   "Wiens 2020 Leiden CF-1K, 1.5–3.6 K silicon-resonator apparatus", "resonator", [cap("temperature.range", rng("1500", "3600"), e_res_t), cap("optical_access", flag(), e_res_opt), cap("module.optical_resonance_interrogation", flag(), e_res_scan)],
   "Exact published CF-1K pulse-tube/Joule-Thomson apparatus with Si5 resonator and frequency-interrogation instrumentation. The50 mm silicon resonator and optical breadboard are installed components of the paper's apparatus, not catalog options assumed on a bare CF-1K. No achieved stability is promoted to a guaranteed machine specification.",
   ["pulse-tube/Joule-Thomson cryostat", "vertical50 mm silicon resonator on three supports", "cold optical breadboard", "motorized mirrors", "transmission detector and frequency-reference optics"], ["Cool the supported silicon resonator.", "Align fibre-injected light through motorized mirrors.", "Scan the resonance and record line-center drift."])
ex("expc_photonics_silicon_frequency", "Cryogenic silicon optical-resonator frequency interrogation across1.5–3.6 K (Wiens et al.2020)", "Measure frequency drift of a cryogenic silicon optical reference", "photonics_and_telecommunications", "resonator",
   [span("temperature.range", "1500", "3600", e_res_t, "Replicate the paper's temperature interval."), present("optical_access", e_res_opt, "Laser injection and transmitted-light detection need real optical paths."), present("module.optical_resonance_interrogation", e_res_scan, "Frequency scans, transmission detection and a frequency reference are essential; a bare optical cryostat is insufficient.")],
   [obs("temperature.range", "1.5–3.6 K", e_res_t), obs("specimen", "50 mm vertical silicon resonator", e_res_opt)], ["Leiden Cryogenics CF-1K"], ["Frequency-comb/maser reference, vibration transfer, optical heating and resonator mounting require separate review. No frequency-stability result is encoded as a compatibility guarantee.", "The paper explicitly says the cryogenic PDH lock was not implemented; the scene uses repeated line scans or detuning interrogation."],
   "optical_resonator", ["vertical silicon spacer with two mirrors", "three-point support", "fibre collimator", "motorized mirrors", "transmission photodiode"], "50 mm long vertical silicon Fabry-Perot reference resonator", ["Cool the silicon spacer through the measurement interval.", "Sweep the probe laser through its optical resonance.", "Track line centers to determine frequency drift."])

# SEMICONDUCTORS: DC transistor transport, semiconductor defect spectroscopy, Hall transport.
e_mos_t = ev("mosfet_temperatures", "mosfet", "within the temperature range from 300 K to 4.2 K", "Published native MOSFET characterization temperature span.", rng("4200", "300000"), location="Abstract (math spacing removed)")
e_mos_analyzer = ev("mosfet_analyzer", "mosfet", "DC characteristics were performed by a Keysight B1500A semiconductor device analyzer", "The paper needs external precision source/measure analysis rather than temperature capability alone.", flag(), location="sectionII (math spacing removed)")
e_dlts = ev("dlts_function", "dlts", "Samples were investigated by both DLTS", "Deep-level transient spectroscopy was performed with a capacitance meter and contacted Schottky diodes.", flag(), location="section4 Experimental Section")
e_dlts_t = ev("dlts_temperatures", "dlts", "measurement temperatures from 300 K down to 36 K", "Published DLTS measurement span in a closed-cycle helium cryostat.", rng("36000", "300000"), location="section4 Experimental Section (HTML nonbreaking spaces normalized)")
e_hall = ev("hall_function", "hall", "FastHall™ method (no physical field reversal) — van der Pauw samples", "The integrated system supports van der Pauw Hall measurements with sourcing, readout and switching.", flag(), "manufacturer_specification", "p.7 specifications")
e_hall_bath = ev("hall_ln2_bath", "hall", "sample is in a flooded LN2 bath", "The optional installed LN2 sample platform supplies the documented cryogenic sample environment.", flag(), "manufacturer_specification", "p.4 LN2 option")
e_hall_field = ev("hall_ln2_field", "hall", "With LN₂ option: 0.75 T", "Nominal field magnitude of the LN2 option, not the room-temperature1 T magnet.", bound("max", "750", "mT"), "manufacturer_specification", "p.7 specifications")
e_cpx_t = ev("cpx_temperature", "cpx", "4.4 K to 475 K", "CPX standard controlled temperature range; lower-temperature options are not included.", rng("4400", "475000"), "manufacturer_specification", "Temperature table: standard up to6 probe-arm configuration")
e_cpx_func = ev("cpx_probing", "cpx", "Maximum probes: 6", "CPX is an electrical probe station; capacity is not proof of six installed arms.", flag(), "manufacturer_specification", "Probing configurations")
e_cpx_holder = ev("cpx_holder", "cpx", "31.8 mm (1.25 in) maximum sample size, grounded", "Included SH-1.25-G holder sample diameter bound, conservative relative to chamber capacity.", bound("max", "31800", "um"), "manufacturer_specification", "Included sample holder")
e_cpx_vac = ev("cpx_vacuum", "cpx", "Room temperature", "The vacuum table describes standard and optional pumped vacuum configurations; actual pressure varies with stage temperature.", flag(), "manufacturer_specification", "Vacuum table")
eq("expc_lakeshore_cpx", "expc_lakeshore_cpx_standard", "Lake Shore Cryotronics", "CPX liquid-helium split-flow probe station", "probe_station_flow",
   "Lake Shore CPX standard4.4–475 K split-flow probe station with included31.8 mm holder", "cpx", [cap("temperature.range", rng("4400", "475000"), e_cpx_t, "manufacturer_specification"), cap("module.electrical_probing", flag(), e_cpx_func, "manufacturer_specification"), cap("sample.diameter.max", bound("max", "31800", "um"), e_cpx_holder, "manufacturer_specification"), cap("vacuum.available", flag(), e_cpx_vac, "manufacturer_specification"), unknown("electrical.probe_arms"), unknown("module.semiconductor_parameter_analyzer"), unknown("module.capacitance_transient_spectroscopy")],
   "Documented standard CPX cooling configuration, included sample holder and vacuum system. Up to six arms is capacity, so installed arm count remains UNKNOWN. Optional PS-LT/PS-VLT stages, high-vacuum upgrade,67 GHz probes, fibre probes and external analyzers are not asserted installed. The selected sample holder limits the supported diameter to31.8 mm.",
   ["bench chamber with radial manipulators", "three nested radiation shields", "helium split-flow transfer line", "sample puck under top viewport", "separate instrument console"], ["Load the chip on the grounded sample holder.", "Pump down and cool the sample and radiation shields through separate flows.", "Land the configured probes and connect external measurement electronics."])
eq("expc_lakeshore_fasthall", "expc_lakeshore_fasthall_ln2", "Lake Shore Cryotronics", "MeasureReady FastHall Station with HMS-TT-ADD-LN2", "hall_station",
   "Lake Shore FastHall Station with installed LN2 bath option and 0.75 T wide-gap magnet", "hall", [cap("module.hall_measurement", flag(), e_hall, "manufacturer_specification"), cap("module.liquid_nitrogen_bath", flag(), e_hall_bath, "manufacturer_specification"), cap("magnetic_field.max", bound("max", "750", "mT"), e_hall_field, "manufacturer_specification"), unknown("temperature.range")],
   "Real manufacturer-documented complete configuration comprising HMS-TT-MAN plus the explicitly installed HMS-TT-ADD-LN2 reservoir/funnel/sample platform and 0.75 T magnet. The LN2 option is named in the selected configuration, not silently attached to the base station. No guaranteed specimen temperature interval is inferred from the existence of a liquid-nitrogen bath. No optional gate-bias source is included.",
   ["wide-gap permanent magnet", "pour-filled LN2 sample reservoir", "insertable four-contact sample card", "M91 source/readout/switching controller"], ["Mount and check contacts on the sample card.", "Fill the LN2 reservoir around the sample.", "Apply source/measure sequences in the 0.75 T field and calculate Hall properties."])
ex("expc_semiconductor_native_mosfet", "Native silicon MOSFET DC transfer and output characterization,4.2–300 K (Zhang et al.2021)", "Measure transistor turn-on and leakage from room temperature to liquid helium", "semiconductors_and_electronics", "mosfet",
   [span("temperature.range", "4200", "300000", e_mos_t, "Replicate the published device temperature span."), present("module.semiconductor_parameter_analyzer", e_mos_analyzer, "An installed semiconductor source/measure analyzer and appropriate four-wire fixture are essential; a bare cryostat is insufficient.")],
   [obs("temperature.range", "300 K to4.2 K", e_mos_t), obs("measurement", "DC transfer/output curves; four-wire method", e_mos_analyzer)], ["liquid nitrogen/helium Dewar", "Keysight B1500A"], ["The source used a wired Dewar, not a named cryogenic probe station. Substituting a station requires confirming installed analyzer, wiring/fixture, bias compliance and self-heating.", "Probe-arm capacity alone does not prove source/drain/gate/body connections are installed; this remains part of analyzer/fixture review."],
   "semiconductor_transistor", ["MOSFET chip", "gate/source/drain wiring", "cryogenic sample mount", "source-measure analyzer"], "SMIC0.18 micrometre native n-MOSFET, with separate gate and drain bias paths", ["Cool the transistor and establish terminal connections.", "Sweep gate voltage while measuring drain current.", "Repeat drain/output sweeps and extract turn-on and leakage characteristics."])
ex("expc_semiconductor_dlts", "Deep-level transient spectroscopy of nitrogen-containing float-zone silicon Schottky diodes,36–300 K", "Measure semiconductor defect traps through capacitance transients", "semiconductors_and_electronics", "dlts",
   [span("temperature.range", "36000", "300000", e_dlts_t, "Replicate the published DLTS temperature scan."), present("module.capacitance_transient_spectroscopy", e_dlts, "A capacitance bridge/meter and trap-filling transient measurement electronics are essential; electrical probe arms alone do not supply DLTS.")],
   [obs("temperature.range", "300 K down to36 K", e_dlts_t)], ["closed-cycle helium cryostat", "Boonton7200 capacitance meter"], ["Trap-filling/reverse bias, rate window, excitation pulse widths, diode contact quality and leakage must be reviewed; no defect activation energy is predicted.", "The source's separate80–310 K optically excited MCTS apparatus is not merged into this DLTS profile."],
   "semiconductor_dlts", ["Schottky diode with metal top contact", "ohmic backside contact", "capacitance meter", "bias pulse generator"], "Nitrogen-containing n- or p-type float-zone silicon Schottky diode", ["Fill traps with an electrical bias pulse.", "Measure capacitance relaxation as trapped carriers are emitted.", "Scan temperature to separate defect signatures by emission rate."])
ex("expc_semiconductor_cryo_hall", "Cryogenic van der Pauw Hall analysis in an LN2 bath at nominal 0.75 T (FastHall documented method class)", "Measure carrier type, density and mobility in a cold semiconductor", "semiconductors_and_electronics", "hall",
   [present("module.hall_measurement", e_hall, "The measurement requires Hall sourcing, voltage readout, switching and analysis."), present("module.liquid_nitrogen_bath", e_hall_bath, "Use the explicitly documented flooded-LN2 sample environment."), req("magnetic_field.max", {"kind": "at_least", "q": q("750", "mT")}, e_hall_field, "Select the manufacturer's nominal 0.75 T LN2 setup; this is not a universal minimum Hall field.", "manufacturer_specification")],
   [obs("sample_environment", "flooded LN2 bath", e_hall_bath), obs("magnetic_field.max", "0.75 T with LN2 option", e_hall_field, q("750", "mT"))], ["FastHall Station", "M91", "HMS-TT-ADD-LN2"], ["This is a manufacturer-documented measurement method, not a single published material dataset.", "Specimen temperature must be measured; the bath's nominal boiling point is not treated as a guaranteed sample setpoint.", "Sample dimensions/thickness, ohmic-contact quality and excitation current must be confirmed. No mobility or carrier density is invented."],
   "semiconductor_hall", ["four-corner-contact square chip", "wide-gap magnet poles", "LN2 bath", "source/voltage switching matrix"], "Semiconductor van der Pauw sample with four edge contacts in a magnetic field", ["Apply current between a selected contact pair.", "Measure transverse Hall voltage in the cold magnetic field.", "Permute contacts and calculate carrier sign, concentration and mobility."], "documented_method_class")


INDUSTRIES = [
    {"id": "energy_and_hydrogen", "experiment_ids": ["expc_energy_insulation_boiloff", "expc_energy_hydrogen_sorption", "expc_energy_tensile_20k"], "configuration_ids": ["expc_nasa_cryostat100_standard", "expc_asap2020_hydrogen_ln2", "expc_npl_helium_tensile_20k"], "shortfalls": []},
    {"id": "metrology_and_calibration", "experiment_ids": ["expc_metrology_acoustic_thermometry", "expc_metrology_josephson_dc", "expc_metrology_optical_watt"], "configuration_ids": ["expc_lne_cnam_agt_2019", "expc_inrim_pjvs_4p2k", "expc_nist_locr_2001"], "shortfalls": []},
    {"id": "photonics_and_telecommunications", "experiment_ids": ["expc_photonics_snspd_characterization", "expc_photonics_qd_autocorrelation", "expc_photonics_silicon_frequency"], "configuration_ids": ["expc_nasa_opus_one_2018_setup", "expc_attodry800_qd_hbt_2024", "expc_leiden_cf1k_si5_2020"], "shortfalls": []},
    {"id": "semiconductors_and_electronics", "experiment_ids": ["expc_semiconductor_native_mosfet", "expc_semiconductor_dlts", "expc_semiconductor_cryo_hall"], "configuration_ids": ["lakeshore_crx_vf", "expc_lakeshore_cpx_standard", "expc_lakeshore_fasthall_ln2"], "shortfalls": ["No inspected primary source establishes an installed B1500A/SMU or DLTS electronics on the two catalog probe-station configurations. These pairings must remain UNKNOWN where their mandatory functions are undocumented, or FAIL where temperature is insufficient. An instrument's inclusion here does not imply suitability."]},
    {"id": "quantum_computing_and_sensing", "experiment_ids": ["quantum_transmon_characterization", "quantum_mk_vector_field_transport", "quantum_mxc_wiring_heat_budget"], "configuration_ids": ["bluefors_ld250_manual_v2", "bluefors_ld400_hdw", "oxford_teslatronpt_6_1_1T_vector"], "shortfalls": ["Reuses existing reviewed profiles. The heat-budget profile is an engineering validation experiment rather than a separate quantum-device measurement. Standard TeslatronPT vector VTI is relevant to vector-field transport but may be too warm for the selected millikelvin procedure; Lean must retain the actual result."]},
    {"id": "materials_and_nanotechnology", "experiment_ids": ["mat_electrical_resistance_low_temperature", "mat_magnetoresistance_10T", "mat_magnetometry_vsm"], "configuration_ids": ["qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc", "oxford_teslatronpt_8T"], "shortfalls": []},
]


def write(path, value):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


for obj in EQUIPMENT:
    write("data/cryostats/expansion_c_" + obj["id"].removeprefix("expc_") + ".json", obj)
for obj in EXPERIMENTS:
    write("data/experiments/expansion_c_" + obj["id"].removeprefix("expc_") + ".json", obj)
write("data/evidence/expansion_c.json", EVIDENCE)
write("research/expansion/c_manifest.json", {"lane": "c", "accessed": DATE, "industries": INDUSTRIES,
       "proposed_vocabulary_keys": VOCAB, "experiment_scenes": SCENES, "equipment_scenes": EQUIPMENT_SCENES,
       "sources": {k: {"title": v[0], "url": v[1]} for k, v in SOURCES.items()},
       "semantics": "Per-function flags are open-world: omitted/unknown is UNKNOWN, never false. No changes to Lean or Z3 acceptance semantics. Published complete apparatus is distinguished from unconfigured commercial platforms. Group membership never means suitable."})
print(f"Wrote {len(EXPERIMENTS)} profiles, {len(EQUIPMENT)} equipment records, {len(EVIDENCE)} evidence records and the C manifest.")
