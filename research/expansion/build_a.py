"""Reviewable expansion A seeds; does not edit the shared vocabulary or engine.

Run from the repository root. New capability definitions are proposals in the
manifest; the integration owner merges them before building the catalog.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-10-31"
EVIDENCE = {}
EQUIPMENT = []
EXPERIMENTS = []
VOCAB = {}
SCENES = {}
MACHINES = {}


def evidence(slug, title, url, claim, quote, location, status="experimental_observation", doi=None):
    eid = "expa_" + slug
    rec = dict(id=eid, document_title=title, source_url=url, claim=claim,
               quote=quote, location=location, evidence_status=status, accessed=DATE,
               verification="Primary source inspected; bounded catalog transcription, not an independent engineering certification.")
    if doi:
        rec["doi"] = doi
    EVIDENCE[eid] = rec
    return eid


def q(value, unit="K"):
    return {"value": str(value), "unit": unit}


def define(key, shape="flag", unit="", description=None):
    VOCAB[key] = dict(shape=shape, unit=unit, better={"flag": "flag", "range": "range", "max": "higher", "min": "lower"}[shape],
                      status="established", description=description or key.replace("module.", "Documented installed function: ").replace("_", " "))
    return key


def cap(key, value, eid, status=None):
    return dict(key=key, value=value, install="installed", evidence_status=status or EVIDENCE[eid]["evidence_status"], evidence_ids=[eid])


def rng(key, lo, hi, eid, unit="K"):
    return cap(key, dict(kind="range", lo=q(lo, unit), hi=q(hi, unit)), eid)


def minimum(key, value, eid, unit="K"):
    return cap(key, dict(kind="min", q=q(value, unit)), eid)


def maximum(key, value, eid, unit="K"):
    return cap(key, dict(kind="max", q=q(value, unit)), eid)


def flag(key, eid):
    if key not in ("vacuum.available", "optical_access", "module.heat_capacity"):
        define(key)
    return cap(key, {"kind": "flag", "b": True}, eid)


def unknown(key):
    return dict(key=key, value={"kind": "unknown"}, install="unknown", evidence_status="unknown", evidence_ids=[])


def req(key, constraint, eid, rationale, origin=None):
    return dict(key=key, constraint=constraint, mandatory=True, applicable=True,
                origin=origin or EVIDENCE[eid]["evidence_status"], rationale=rationale, evidence_ids=[eid])


def point(key, value, eid, rationale, unit="K"):
    return req(key, dict(kind="point_within", q=q(value, unit)), eid, rationale)


def base(value, eid, rationale):
    return req("temperature.base", dict(kind="at_most", q=q(value)), eid, rationale)


def required_flag(key, eid, rationale):
    if key not in ("vacuum.available", "optical_access", "module.heat_capacity"):
        define(key)
    return req(key, {"kind": "present"}, eid, rationale)


def scene(archetype, sample, elements, steps):
    return dict(archetype=archetype, sample_shape=sample, apparatus_elements=elements,
                steps=steps, geometry_status="Representative procedural geometry; not manufacturer CAD or a dimensional installation drawing.")


def equipment(slug, owner, model, family, description, capabilities, eids, geometry):
    eqid, cfgid = "expa_" + slug, "expa_" + slug + "_documented"
    docs = [{"id": eid + "_doc", "url": EVIDENCE[eid]["source_url"], "title": EVIDENCE[eid]["document_title"], "accessed": DATE} for eid in eids]
    EQUIPMENT.append(dict(id=eqid, manufacturer=owner, model=model, family=family, description=description,
                          documents=docs, configurations=[dict(id=cfgid, name=model + " — documented configuration",
                          configuration_basis="Source-specific reported apparatus/capabilities only. Facility access and present availability are not asserted.", capabilities=capabilities)]))
    MACHINES[cfgid] = geometry
    return cfgid


def experiment(slug, industry, name, description, requirements, eids, reported, geometry, limits, reported_equipment):
    eid = "expa_" + slug
    sources = [dict(citation=EVIDENCE[e]["document_title"], url=EVIDENCE[e]["source_url"], accessed=DATE, **({"doi": EVIDENCE[e]["doi"]} if "doi" in EVIDENCE[e] else {})) for e in eids]
    EXPR = dict(id=eid, name=name, plain_name=name, industry=industry, description=description,
                keywords=[slug.replace("_", " "), geometry["archetype"].replace("_", " ")],
                sources=sources, reported_conditions=reported, reported_equipment=reported_equipment,
                requirements=requirements, params=[], coupled=[], missing_information=limits, confirmed=True,
                confirmation_note="Curated bounded procedure from the cited source. User must confirm applicability before an interactive verification. Passing encoded checks does not establish unmodeled performance.",
                verification_scope="Temperature plus the named indispensable measurement/handling functions; no extrapolation of undocumented performance, pressure, calibration, cleanliness or full facility safety.")
    EXPERIMENTS.append(EXPR)
    SCENES[eid] = geometry
    return eid


# Aerospace: an aerodynamic flow facility, a liquid-propellant system and a
# guarded heat-leak calorimeter have different boundary conditions and hardware.
ntf = evidence("ntf", "NASA National Transonic Facility virtual tour", "https://www.nasa.gov/langley/virtual-tour/ntf/",
    "NTF is a nitrogen/air closed-circuit cryogenic aerodynamic wind tunnel; current tour lists Mach 0.2–1.2 and -250–130 F. Temperature bounds below are conservatively rounded inward to 117–327 K.",
    "Speed: Mach 0.2 to 1.2", "Quick Facts")
crm = evidence("crm", "NASA Common Research Model: Experimental Approach", "https://www.nasa.gov/common_research_model/high-speed-crm/experimental-approach/",
    "The documented CRM aerodynamic campaign varied tunnel temperature between 117 and 302 K to reach Reynolds numbers 5, 19.8 and 30 million. This is a source-specific aircraft model test, not a generic cryostat experiment.",
    "the tunnel temperature was varied between 302 K and 117 K", "Experimental approach, NTF test conditions")
sm = evidence("smirf", "NASA Small Multi-Purpose Research Facility", "https://www.nasa.gov/setmo/facilities/smirf/",
    "SMiRF has conducted liquid-hydrogen liquid-acquisition-device tests and supports tank chilldown/transfer. Reported minimum -424 F is about 19.817 K; 20 K is a conservatively rounded cold-reach requirement. Source gives 20–80 psi tank pressure but this catalog does not infer a specimen pressure rating from it.",
    "Successful LADs tests have been conducted using liquid hydrogen", "Facility description, liquid acquisition devices")
lad = evidence("lad_operating_point", "Hartwig et al., Screen Channel Liquid Acquisition Device Outflow Tests in Liquid Hydrogen", "https://ntrs.nasa.gov/api/citations/20140010818/downloads/20140010818.pdf",
    "The reported SMiRF experiment used fixed liquid saturation temperatures 20.3, 21.4, 22.9 and 24.2 K. The selected catalog fixture represents only the demonstrated 20.3 K point, not a continuous controllable interval. Section 5.4 identifies the actual SMiRF tank, LAD channels, heaters, outflow controls and thermometry; this was inverted 1-g vertical outflow, not microgravity.",
    "fixed fluid saturation", "Sections 5.4 and 6.1 / Table 3, apparatus and fixed fluid temperatures")
cc = evidence("creek", "NASA Creek Road Cryogenics Complex", "https://www.nasa.gov/centers-and-facilities/glenn/creek-road-cryogenics-complex/",
    "The 20–90 K calorimeter uses separate warm/cold boundary temperatures and a vacuum vessel. SMiRF thermal shroud temperature is a background boundary, not the liquid-hydrogen sample temperature. Calorimeter vacuum capability is 1e-7 Torr or better.",
    "20 K to 90 K Calorimeter", "20 K to 90 K Calorimeter section")
cal = evidence("mli", "Chato et al., Design and Operation of a Calorimeter for Advanced Multilayer Insulation Testing", "https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20170003927.pdf",
    "NASA's guarded calorimeter was designed for insulation heat-leak tests with nominal 20 K inner and 90 K outer boundaries and a calibrated rod measuring conducted heat flow. These are two simultaneous boundaries, not a uniform 20–90 K sample range.",
    "Design and Operation of a Calorimeter for Advanced Multilayer Insulation Testing", "Title and calorimeter design description")
define("flow.mach.range", "range", "1", "Documented controlled Mach-number interval in the aerodynamic test section")
define("temperature.cold_boundary.range", "range", "K", "Controlled cold-side boundary temperature of a guarded insulation calorimeter")
define("temperature.warm_boundary.range", "range", "K", "Controlled warm-side boundary temperature of a guarded insulation calorimeter")
a1 = equipment("nasa_ntf", "NASA Langley Research Center", "National Transonic Facility, cryogenic nitrogen mode", "cryogenic_wind_tunnel",
    "Specialized pressure-shell aerodynamic facility, not a laboratory sample dewar. Temperature bounds are conservative conversions of the cited tour's limits; coupled Mach/Reynolds/pressure feasibility is not asserted.",
    [rng("temperature.range", 117, 327, ntf), rng("flow.mach.range", "0.2", "1.2", ntf, "1"), flag("module.aerodynamic_force_pressure_test", crm)], [ntf, crm],
    scene("cryogenic_wind_tunnel", "full-span swept wing and fuselage on a sting", ["closed return duct", "large fan", "rectangular test section", "nitrogen injection pipes", "sting balance", "pressure tap tubing"], ["Inject nitrogen and establish flow", "Hold aerodynamic conditions around model", "Acquire force and surface-pressure channels"]))
a2 = equipment("nasa_smirf", "NASA Glenn Research Center", "SMiRF reported 20.3 K liquid-hydrogen LAD outflow configuration", "cryogenic_propellant_loop",
    "Reported NASA 1-g inverted vertical LAD outflow apparatus. This entry records the demonstrated fixed 20.3 K fluid point; the facility's separate minimum-temperature statement is not used to establish specimen-temperature control. No microgravity capability is inferred.",
    [rng("temperature.range", "20.3", "20.3", lad), flag("module.liquid_hydrogen_handling", lad), flag("module.propellant_acquisition_transfer", lad), flag("vacuum.available", cc)], [sm, lad, cc],
    scene("cryogenic_propellant_loop", "screen-channel liquid acquisition device inside a spherical tank", ["vacuum test vessel", "insulated hydrogen tank", "LAD screen", "chilldown transfer line", "receiver tank", "flow and pressure sensors"], ["Cool and fill the test tank", "Draw liquid through the LAD and transfer line", "Measure acquisition/transfer behavior"]))
a3 = equipment("nasa_20_90_calorimeter", "NASA Glenn Research Center", "20 K / 90 K guarded insulation calorimeter", "guarded_calorimeter",
    "A specialized heat-leak calorimeter with distinct warm and cold boundaries. Boundary points are not transcribed as a uniform specimen temperature range.",
    [rng("temperature.cold_boundary.range", 20, 20, cal), rng("temperature.warm_boundary.range", 90, 90, cal), flag("module.guarded_heat_flow_calorimetry", cal), flag("vacuum.available", cc), minimum("pressure.base", "0.0000001", cc, "Torr")], [cal, cc],
    scene("guarded_calorimeter", "cylindrical multilayer insulation sleeve", ["vacuum bell jar", "20 K inner cylinder", "90 K guard shell", "calibrated conduction rod", "radiation shields", "thermometry pairs"], ["Evacuate and cool both boundaries", "Wait for steady heat flow through insulation", "Infer heat leak from calibrated rod gradient"]))
e_a1 = experiment("crm_aerodynamics", "aerospace_and_space_exploration", "Cryogenic aircraft-model force and pressure testing, 117–302 K",
    "Reproduce the bounded NASA Common Research Model aerodynamic temperature sweep; aerodynamic force/pressure instrumentation is essential.",
    [req("temperature.range", dict(kind="range_within", lo=q(117), hi=q(302)), crm, "The reported campaign used 117–302 K tunnel conditions."), required_flag("module.aerodynamic_force_pressure_test", crm, "A cold sample chamber cannot substitute for a flow tunnel, sting balance and pressure acquisition.")], [crm, ntf],
    [dict(key="temperature.range", as_printed="between 302 K and 117 K", evidence_id=crm)], MACHINES[a1],
    ["Source campaign pressure/Reynolds correlations, model blockage, balance calibration and aeroelastic loading are not yet encoded as coupled checks."], ["NASA National Transonic Facility"])
e_a2 = experiment("hydrogen_lad_transfer", "aerospace_and_space_exploration", "Liquid-hydrogen screen-channel LAD outflow test at 20.3 K",
    "Reproduce the documented 20.3 K fluid condition for NASA SMiRF inverted 1-g vertical screen-channel LAD outflow. This requires an actual propellant acquisition/outflow apparatus.",
    [point("temperature.range", "20.3", lad, "Section 6.1 reports fixed fluid saturation temperatures including 20.3 K; cold reach alone cannot satisfy this operating-point requirement."), required_flag("module.liquid_hydrogen_handling", lad, "Actual liquid-hydrogen handling is essential."), required_flag("module.propellant_acquisition_transfer", lad, "The experiment requires screen-channel LAD outflow plumbing and controlled flow.")], [lad, sm],
    [dict(key="temperature.range", as_printed="fixed fluid saturation temperatures of 20.3, 21.4, 22.9, and 24.2K", evidence_id=lad)], MACHINES[a2],
    ["Tank pressure, mass-flow setpoint, screen bubble-point and detailed LAD geometry must match the selected row of Table 3. This profile does not infer a continuous controllable temperature interval or orbital microgravity behavior."], ["NASA SMiRF 487-gallon LAD test tank"])
e_a3 = experiment("mli_guarded_heat_leak", "aerospace_and_space_exploration", "Multilayer-insulation heat-leak calorimetry with 20 K / 90 K boundaries",
    "Measure steady heat leakage through multilayer spacecraft/tank insulation between separate cryogenic boundaries with calibrated conduction calorimetry.",
    [point("temperature.cold_boundary.range", 20, cal, "Nominal inner cold boundary is 20 K."), point("temperature.warm_boundary.range", 90, cal, "Nominal outer warm boundary is 90 K."), required_flag("module.guarded_heat_flow_calorimetry", cal, "Guarded geometry and a calibrated heat-flow rod are indispensable."), required_flag("vacuum.available", cc, "The documented calorimeter is a vacuum apparatus.")], [cal, cc],
    [dict(key="boundary_temperatures", as_printed="nominal 20 K inner and 90 K outer boundaries", evidence_id=cal)], MACHINES[a3],
    ["Insulation layer count, contact compression, residual gas pressure and rod calibration determine heat leak; no predicted insulation performance is fabricated."], ["NASA 20 K to 90 K calorimeter"])


# Astronomy: a detector bench, a mirror metrology facility and an integrated
# telescope optical test chamber differ even when all employ vacuum shrouds.
mit = evidence("mitten", "Bowens et al., The Michigan Infrared Test Thermal ELT N-band (MITTEN) Cryostat", "https://arxiv.org/abs/2012.06620",
    "MITTEN characterizes 8–13 um mid-IR detectors; interior below 40 K, optical bench 16 K, internal source and Offner relay. The paper says filter/aperture mechanisms will be added, so they are not labeled installed. Bench temperature is not asserted to be the detector setpoint.",
    "optical bench maintains a temperature of 16 K", "Abstract", doi="10.48550/arXiv.2012.06620")
xr = evidence("xrcf", "NASA Marshall Optics and X-Ray and Cryogenic Facility", "https://www.nasa.gov/marshall/optics/",
    "XRCF evaluates large optical mirrors/structures down to 20 K; this is a cryogenic optical metrology facility, not an arbitrary microscope cryostat.",
    "20 Kelvin", "X-Ray and Cryogenic Facility description")
sbmd = evidence("sbmd_operating_point", "UAH, Subscale Beryllium Mirror Demonstrator Testing Support, Final Report 521134-FR", "https://ntrs.nasa.gov/api/citations/20010070993/downloads/20010070993.pdf",
    "The September 2000 SBMD-3 optical test at XRCF measured a 0.532 m beryllium mirror in vacuum near 38 K; Table 4 reports mean temperature 37.87 K. This is an actual mirror measurement point, distinct from the generic facility's cold-reach figure. The procedure requires thermal drift below 2 K/hour and no gradients above 3 K; those bounds are not a universal facility guarantee.",
    "37.87 K", "Pages 2–4 procedure; page 9 / Table 4, actual cold optical test")
xi = evidence("xrcf_interferometry", "NASA Marshall Optical Systems Capabilities", "https://www.nasa.gov/wp-content/uploads/2015/04/opticalsystems.pdf?emrc=602655",
    "NASA describes XRCF's two interferometers measuring structural distortions in cryogenic mirrors, vacuum typically below 1e-6 Torr. This supports the mirror-interferometry function, not a universal nanometer-accuracy guarantee.",
    "interferometers", "X-Ray and Cryogenic Facility optical metrology description")
cha = evidence("chamber_a", "NASA Apollo-Era Test Chamber Now James Webb Space Telescope Ready", "https://www.nasa.gov/universe/nasas-apollo-era-test-chamber-now-james-webb-space-telescope-ready/",
    "Chamber A's helium shroud is approximately 11 K and supports Webb testing near its 37 K operating temperature and 20 K survival condition. The 11 K shroud is not labeled a specimen-temperature capability.",
    "37 kelvins", "Cryogenic shroud and telescope operating temperatures")
web = evidence("webb_optics", "NASA Science, Webb's Mirrors", "https://science.nasa.gov/mission/webb/webbs-mirrors/",
    "Webb's integrated telescope underwent cryogenic optical tests in Chamber A using artificial stars to assess optical alignment. This is distinct from testing one mirror's surface figure.",
    "artificial stars", "Cryogenic telescope mirror and optical alignment testing")
define("temperature.optical_bench.range", "range", "K", "Documented optical-bench operating temperature, distinct from detector sample or radiation shroud")
b1 = equipment("mitten", "University of Michigan", "MITTEN mid-infrared detector cryostat, reported 2020 apparatus", "detector_dewar",
    "Two-stage pulse-tube cooled optical bench with internal source and Offner relay. Future filter-wheel/aperture additions in the source are not treated as installed. The 16 K figure belongs to the bench.",
    [rng("temperature.optical_bench.range", 16, 16, mit), flag("module.mid_ir_detector_characterization", mit), flag("module.internal_offner_relay", mit), flag("vacuum.available", mit)], [mit],
    scene("detector_dewar", "rectangular mid-infrared detector array at an Offner image plane", ["horizontal vacuum dewar", "two-stage pulse tube", "16 K optical bench", "internal source", "three-reflection Offner relay", "detector electronics"], ["Cool the optical bench and control background", "Illuminate detector through the internal relay", "Acquire dark and illuminated response frames"]))
b2 = equipment("nasa_xrcf", "NASA Marshall Space Flight Center / UAH", "XRCF SBMD-3 reported 37.87 K mirror optical-test configuration", "thermal_vacuum",
    "Historical September 2000 beryllium-mirror optical test at XRCF. The specimen point is the mean temperature in Table 4, not the cold shroud or the generic facility's base temperature. Temperature-gradient qualification for an arbitrary new optic remains unknown.",
    [rng("temperature.range", "37.87", "37.87", sbmd), flag("module.cryogenic_mirror_interferometry", sbmd), flag("vacuum.available", sbmd), unknown(define("temperature.gradient.max", "min", "K", "Maximum spatial temperature gradient/difference across the test specimen; lower is better"))], [xr, xi, sbmd],
    scene("thermal_vacuum", "circular lightweighted beryllium mirror on three titanium bipods", ["long horizontal vacuum chamber", "cryogenic shroud", "mirror support tripod", "WaveScope Shack-Hartmann sensor", "point diffraction interferometer", "vibration-isolated sensor pallet"], ["Cool and thermally stabilize the mounted mirror", "Measure the wavefront and point-diffraction fringes", "Recover cold surface figure and radius of curvature"]))
b3 = equipment("nasa_chamber_a", "NASA Johnson Space Center", "Chamber A integrated Webb optical test configuration", "telescope_vacuum_chamber",
    "Reported integrated telescope optical test configuration around 37 K, with colder shroud. This entry does not imply the chamber's shroud temperature is the telescope temperature.",
    [rng("temperature.range", 37, 37, cha), flag("module.integrated_telescope_optical_test", web), flag("vacuum.available", cha)], [cha, web],
    scene("telescope_vacuum_chamber", "segmented primary telescope with secondary tripod and focal-plane package", ["large vertical vacuum chamber", "helium and nitrogen shrouds", "suspended telescope assembly", "secondary support tripod", "artificial star source", "autocollimation optical path"], ["Cool the assembled telescope under vacuum", "Project artificial stars through the full optical train", "Measure cold alignment and image formation"]))
e_b1 = experiment("mid_ir_array_characterization", "astronomy_and_astrophysics", "Mid-infrared array dark and illuminated characterization on a 16 K bench",
    "MITTEN's detector-characterization procedure uses a cold optical bench and internal Offner relay to evaluate dark/illuminated detector response; 16 K is the bench condition.",
    [point("temperature.optical_bench.range", 16, mit, "The paper reports the optical bench at 16 K; detector temperature is separately controlled/not quantified here."), required_flag("module.mid_ir_detector_characterization", mit, "Detector acquisition/readout is essential."), required_flag("module.internal_offner_relay", mit, "The reported controlled illumination uses the internal source/Offner relay.")], [mit],
    [dict(key="temperature.optical_bench.range", as_printed="16 K optical bench", evidence_id=mit)], MACHINES[b1],
    ["Detector operating temperature, read noise, dark current and source radiometry remain device-specific; no paper performance values are converted into guaranteed equipment specifications."], ["MITTEN"])
e_b2 = experiment("mirror_cold_figure", "astronomy_and_astrophysics", "Beryllium-mirror cold surface-figure metrology near 38 K (reported 37.87 K)",
    "Reproduce the temperature condition of the SBMD-3 mirror wavefront/point-diffraction measurement at XRCF; the reported mean specimen temperature is 37.87 K.",
    [point("temperature.range", "37.87", sbmd, "Table 4 reports the actual cold mirror mean temperature 37.87 K; cold reach does not prove this specimen operating point."), required_flag("module.cryogenic_mirror_interferometry", sbmd, "A calibrated wavefront/point-diffraction optical path is essential."), required_flag("vacuum.available", sbmd, "The reported mirror measurement uses vacuum."), req("temperature.gradient.max", dict(kind="at_most", q=q(3)), sbmd, "The published procedure permits no specimen gradients exceeding 3 K. Qualification of this bound for a proposed optic remains UNKNOWN until supported.")], [sbmd, xr, xi],
    [dict(key="temperature.range", as_printed="37.87 K (Table 4, nominal 38 K test)", evidence_id=sbmd)], MACHINES[b2],
    ["The 3 K maximum specimen gradient is a mandatory requirement whose equipment qualification remains UNKNOWN. The separate published thermal drift limit below 2 K/hour, support deformation, vibration, aperture and optical calibration also require a test-specific plan; no generic 20 K cold-reach claim satisfies this procedure."], ["NASA XRCF / UAH SBMD-3 optical test system"])
e_b3 = experiment("telescope_cold_alignment", "astronomy_and_astrophysics", "Integrated telescope artificial-star optical alignment near 37 K",
    "Test the complete primary-secondary-instrument optical train under cryogenic vacuum; this is an end-to-end telescope measurement rather than a single mirror surface test.",
    [point("temperature.range", 37, cha, "The chamber source identifies approximately 37 K as Webb's operating test regime; encoded 37 K is a nominal point."), required_flag("module.integrated_telescope_optical_test", web, "Artificial-star alignment through the complete telescope is indispensable."), required_flag("vacuum.available", cha, "Cryogenic optical testing is performed under vacuum.")], [cha, web],
    [dict(key="temperature.range", as_printed="approximately 37 kelvins", evidence_id=cha)], MACHINES[b3],
    ["The nominal 37 K point is not a tolerance band. Full alignment error budget, chamber geometry, metrology calibration and vibration isolation are not proven by these scalar checks."], ["NASA Chamber A"])


# Transportation: mechanical monotonic failure, cyclic fatigue and gas
# permeation probe different material mechanisms for cryogenic fuel systems.
pn = evidence("304l", "PNNL, Effect of Hydrogen on Tensile Properties of 304L Stainless Steel at Cryogenic Temperatures", "https://www.pnnl.gov/publications/effect-hydrogen-tensile-properties-304l-stainless-steel-cryogenic-temperatures",
    "PNNL reports 304L specimens thermally precharged with internal hydrogen and tensile tested at 20, 77 and 113 K. This is not a 700 bar in-situ hydrogen-pressure experiment.",
    "evaluated at 20 K, 77 K, and 113 K", "Publication abstract, tensile testing temperatures")
craft = evidence("craft", "Washington State University HYPER, CRyogenic Accelerated Fatigue Testing", "https://hydrogen.wsu.edu/craft/",
    "Operational CRAFT uses an MTS Acumen 12 frame with a custom cryogenic cell for tensile/compression/fatigue testing of polymer composites in 20 K liquid hydrogen or 77 K liquid nitrogen. Cryocooler theoretical 4 K minimum is not transcribed as demonstrated 4 K fatigue testing. Frequency maximum 100 Hz; 0.57 L cell.",
    "liquid nitrogen (77 K) or liquid hydrogen (20 K)", "CRAFT overview and System and Test Specifications")
ccc = evidence("ccc", "Washington State University HYPER, Cubic Cryo Chamber", "https://hydrogen.wsu.edu/ccc/",
    "CCC's actual thin-polymer helium-permeation apparatus modulates the test cell and ongoing permeation test between 20 and 200 K with a PT415 cryocooler and PID-controlled heaters. The separate general specification reports about 5 K cold reach for another MLI/thermal-resistor configuration; it is not used as proof of 5 K permeation. Disc specimens are 4.73 inch diameter and 0.001–0.05 inch thick.",
    "20 – 200 K", "2016–2020 Kjell Westra: Helium Permeation Through Thin Polymer Films; controlled test-cell temperature")
br = evidence("bremen", "University of Bremen MAPEX, ZwickRoell HB 100 cryogenic testing machine", "https://www.uni-bremen.de/en/mapex-cf/instrument-database/show/76?cHash=e27ad4f95c225e8b3c8b2d5476ebf893",
    "University owner describes actual ZwickRoell HB 100 installed for static/dynamic tensile, compression, bending and fracture testing with a liquid-helium continuous-flow cryostat reaching 10 K. The model name is not used to infer an unquoted load rating.",
    "10K", "Instrument capabilities / cryogenic continuous-flow insert")
c1 = equipment("wsu_craft", "Washington State University HYPER / MTS", "CRAFT, liquid-hydrogen 20 K test-cell configuration", "tensile_tester",
    "Actual fully electric load frame with cryogenic specimen cell. This selected configuration is the reported 20 K hydrogen bath; cryocooler-only 4 K reach is not equated with loaded-specimen operation.",
    [rng("temperature.range", 20, 20, craft), minimum("temperature.base", 20, craft), maximum("mechanical.cycling_frequency.max", 100, craft, "Hz"), flag("module.cryogenic_tensile_test", craft), flag("module.cryogenic_fatigue_test", craft), flag("module.liquid_hydrogen_handling", craft)], [craft],
    scene("tensile_tester", "dog-bone polymer coupon gripped vertically in a liquid-hydrogen cell", ["twin-column electric load frame", "actuator", "upper and lower grips", "bellows-sealed pull rod", "small vacuum cryogenic cell", "thermal strap"], ["Mount coupon and cool the bath", "Apply programmed monotonic or cyclic load", "Record force and extension with temperature"]))
define("mechanical.cycling_frequency.max", "max", "Hz", "Documented maximum cyclic loading frequency of the mechanical test frame")
c2 = equipment("wsu_ccc", "Washington State University HYPER", "Cubic Cryo Chamber, controlled 20–200 K thin-film helium-permeation configuration", "permeation_cell",
    "Actual helium-permeation test cell with PT415 cooling and closed-loop PID heaters modulating the specimen and ongoing test over 20–200 K. The general CCC's separate approximately 5 K cold-reach figure is not assigned to this operating interval.",
    [rng("temperature.range", 20, 200, ccc), flag("module.cryogenic_gas_permeation", ccc), maximum("sample.diameter.max", "4.73", ccc, "inch"), flag("vacuum.available", ccc)], [ccc],
    scene("permeation_cell", "thin circular membrane dividing upstream and downstream gas volumes", ["cubic vacuum chamber", "cold membrane flange", "hydrogen/helium inlet", "downstream leak detector", "cryocooler", "pressure transducers"], ["Clamp and cool the membrane", "Apply test gas to upstream face", "Measure downstream permeation/leak response"]))
c3 = equipment("bremen_hb100", "ZwickRoell / University of Bremen", "HB 100 with installed liquid-helium continuous-flow cryostat", "tensile_tester",
    "Owner-reported static/dynamic materials tester reaching 10 K through a continuous-flow helium insert. Force capacity, pressure rating and hydrogen-compatible enclosure are not inferred from its product name.",
    [minimum("temperature.base", 10, br), unknown("temperature.range"), flag("module.cryogenic_tensile_test", br), flag("module.cryogenic_fatigue_test", br)], [br],
    scene("tensile_tester", "metal dog-bone specimen on a helium-cooled pull rod", ["servohydraulic load frame", "helium flow cryostat", "long pull rod", "grip pair", "extensometer", "helium transfer hose"], ["Mount the metallic specimen", "Cool with controlled helium flow", "Load the specimen and acquire deformation"]))
e_c1 = experiment("hydrogen_304l_tensile", "automotive_and_transportation", "Hydrogen-precharged 304L stainless-steel tensile test at 20 K",
    "Measure monotonic tensile behavior of hydrogen-precharged stainless steel relevant to liquid-hydrogen transport/storage materials; charging precedes the cryogenic tensile test.",
    [point("temperature.range", 20, pn, "The selected reported specimen test point is 20 K; a base-temperature bound alone cannot establish this operating point."), required_flag("module.cryogenic_tensile_test", pn, "A calibrated load frame and cryogenic specimen grips are essential.")], [pn],
    [dict(key="temperature.range", as_printed="20 K (also 77 K and 113 K investigated)", evidence_id=pn)],
    scene("tensile_tester", "slender steel dog-bone with a narrow gauge section", ["cryogenic pull rod", "two tensile grips", "hydrogen-precharged steel coupon", "load cell", "extensometer", "cold cell"], ["Confirm ex-situ hydrogen precharge", "Cool the gripped coupon to 20 K", "Pull monotonically and record stress/strain response"]),
    ["Hydrogen precharge concentration/profile, specimen geometry, load capacity, strain rate and temperature stability must be confirmed. No in-situ high-pressure hydrogen capability is assumed."], ["Cryogenic tensile testing apparatus described by PNNL"])
e_c2 = experiment("hydrogen_composite_fatigue", "automotive_and_transportation", "Liquid-hydrogen polymer-composite cyclic fatigue at 20 K",
    "Characterize fatigue damage under repeated mechanical loading of a polymer composite in the 20 K liquid-hydrogen environment documented for CRAFT.",
    [point("temperature.range", 20, craft, "The documented liquid-hydrogen test-bath point is 20 K; cold reach alone cannot satisfy specimen operation at that point."), required_flag("module.cryogenic_fatigue_test", craft, "Cyclic force/extension testing is indispensable."), required_flag("module.liquid_hydrogen_handling", craft, "The selected exposure is actual liquid hydrogen, beyond a helium-cooled coupon.")], [craft],
    [dict(key="temperature.range", as_printed="liquid hydrogen (20 K)", evidence_id=craft)],
    scene("tensile_tester", "polymer-composite dog-bone coupon with visibly cyclic gauge displacement", ["electric actuator", "bellows pull rod", "liquid-hydrogen test bath", "composite coupon", "force sensor", "cyclic extension trace"], ["Immerse and thermalize the composite", "Apply repeated tensile loading", "Count cycles and measure degradation"]),
    ["Frequency, load ratio, cycle count, coupon geometry and measured fatigue life are protocol-specific and not synthesized from the frame's 100 Hz maximum."], ["WSU CRAFT"])
e_c3 = experiment("cryogenic_membrane_permeation", "automotive_and_transportation", "Helium permeability of thin cryogenic tank-barrier polymers at 20 K",
    "Measure helium transport/leak rate through PET, PEEK or PEI thin-film tank barriers at the low endpoint of the actual CCC's controlled 20–200 K permeation procedure. This is distinct from a cold-reach demonstration and from mechanical-strength testing.",
    [point("temperature.range", 20, ccc, "The source explicitly says the test cell and ongoing permeation test are modulated over 20–200 K; this profile selects the documented 20 K endpoint."), required_flag("module.cryogenic_gas_permeation", ccc, "Separate upstream/downstream volumes and a leak detector are essential.")], [ccc],
    [dict(key="temperature.range", as_printed="test cell (and any ongoing permeation test) ... 20 – 200 K", evidence_id=ccc), dict(key="sample.diameter.max", as_printed="4.73 in membrane discs", evidence_id=ccc)], MACHINES[c2],
    ["Temperature stability, helium differential pressure, permeation area, background leak and detector calibration need confirmation. The source reports rates below detector sensitivity below 100 K, so an undetectable signal must not be represented as measured zero permeability. The separate approximately 5 K hardware reach is not an established permeation condition."], ["WSU Cubic Cryo Chamber thin-polymer helium-permeation apparatus"])


# Defense/security: IR photometry, micro-JT thermal stabilization and cryogenic
# microwave transmission are different measurements. Historical research rigs
# are labeled as such rather than assigned an invented commercial model.
drs = evidence("drs", "DRS, Far-Infrared Blocked Impurity Band Detector Development", "https://ntrs.nasa.gov/api/citations/20070030828/downloads/20070030828.pdf?attachment=true",
    "DRS used a custom Janis liquid-helium dewar with a liquid-nitrogen intermediate shield, optical port, gravity-operated cold shutter and controlled 5–20 K detector stage. For far-IR tests, filters were not installed and silicon replaced the KRS5 window.",
    "Operating temperature may be", "Page 4, custom Janis dewar / detector characterization apparatus")
jt = evidence("nist_jt", "NIST, Microcryocooler for Terahertz Detectors", "https://www.nist.gov/programs-projects/microcryocooler-terahertz-detectors",
    "The NIST/Colorado DARPA prototype achieved 77 K but exhibited temperature oscillations below about 140 K. The source motivates THz weapons screening and IR detection, but does not establish stable operation or a completed characterized THz detector instrument.",
    "temperature oscillations occur below about 140 K", "Phase II prototype status")
rf = evidence("ybco_filter", "Sabataitis et al., YBCO High-Temperature Superconducting Filters on M-Plane Sapphire Substrates", "https://ntrs.nasa.gov/citations/19970019925",
    "NASA/CWRU reported measured insertion loss of 4.0 GHz YBCO hairpin/edge-coupled filters at 77 K. The abstract establishes a cryogenic microwave transmission test fixture; cryostat manufacturer/model and calibration chain are not identified.",
    "bandpass filters at 4.0 GHz", "Abstract, fabrication and measured 77 K insertion loss")
define("rf.frequency.range", "range", "GHz", "Documented measurement frequency interval or explicitly reported operating point of the installed RF fixture")
d1 = equipment("drs_janis_bib", "Janis Research / DRS", "Custom DRS BIB-detector liquid-helium dewar, reported 2007 configuration", "detector_dewar",
    "Historical reported detector apparatus, not a current manufacturer product guarantee. Selected far-IR configuration has a silicon window and no installed optical filter stack.",
    [rng("temperature.range", 5, 20, drs), flag("module.far_ir_detector_photometry", drs), flag("module.cold_dark_shutter", drs), flag("optical_access", drs)], [drs],
    scene("detector_dewar", "small BIB detector die in a leadless chip-carrier socket", ["liquid-helium reservoir", "liquid-nitrogen shield", "5–20 K detector stage", "silicon optical window", "gravity-operated cold shutter", "detector socket wiring"], ["Cool the detector and close the shutter", "Acquire dark response", "Open shutter and acquire far-infrared response"]))
d2 = equipment("nist_micro_jt", "NIST / University of Colorado", "DARPA phase-II mixed-refrigerant micro-JT prototype", "micro_jt_cooler",
    "Research prototype reached 77 K with sub-140 K temperature oscillations. Stable 77 K detector operation and integrated THz readout are explicitly UNKNOWN; this is not a commercially qualified detector system.",
    [rng("temperature.range", 77, 77, jt), flag("module.micro_jt_cooling", jt), unknown(define("module.stable_thz_detector_operation"))], [jt],
    scene("micro_jt_cooler", "micromachined cold-tip chip beside a THz absorber mount", ["planar recuperator", "microfabricated cold tip", "high-pressure feed", "low-pressure return", "temperature sensor", "unqualified detector mounting position"], ["Drive mixed refrigerant through the recuperator", "Expand refrigerant at the micro cold tip", "Measure cooldown and temperature oscillations"]))
d3 = equipment("nasa_ybco_fixture", "NASA Lewis Research Center / Case Western Reserve University", "Reported 77 K, 4 GHz YBCO filter transmission fixture", "cryogenic_rf_fixture",
    "Actual reported 1996 cryogenic microwave measurement configuration; source does not name the cryostat manufacturer or calibration hardware. It is not relabeled as an available commercial machine.",
    [rng("temperature.range", 77, 77, rf), rng("rf.frequency.range", 4, 4, rf, "GHz"), flag("module.cryogenic_microwave_transmission", rf)], [rf],
    scene("cryogenic_rf_fixture", "planar meander hairpin microstrip on a sapphire rectangle", ["77 K cold fixture", "sapphire filter chip", "two coaxial feedthroughs", "RF input launch", "RF output launch", "external network analyzer"], ["Cool the filter fixture", "Sweep around the 4 GHz bandpass", "Measure insertion loss against the reference filter"]))
e_d1 = experiment("bib_detector_photometry", "defense_and_security", "Far-infrared BIB detector dark and illuminated response, 5–20 K",
    "Characterize a far-infrared blocked-impurity-band detector using the DRS reported cold-shutter and optical-port method, relevant to cooled sensing technology.",
    [req("temperature.range", dict(kind="range_within", lo=q(5), hi=q(20)), drs, "The detector stage is controlled across 5–20 K."), required_flag("module.far_ir_detector_photometry", drs, "Detector illumination/readout apparatus is essential."), required_flag("module.cold_dark_shutter", drs, "A cold shutter provides the dark-reference state.")], [drs],
    [dict(key="temperature.range", as_printed="5–20 K detector stage", evidence_id=drs)], MACHINES[d1],
    ["Spectral band, optical background, detector bias, absolute radiometry and calibrated responsivity/noise are source- and detector-specific; none are fabricated as a pass condition."], ["DRS custom Janis dewar"])
e_d2 = experiment("thz_microcooler_stability", "defense_and_security", "77 K micro-JT cooler stabilization for a terahertz detector",
    "Evaluate whether the documented mixed-refrigerant microcooler can support stable 77 K THz-detector operation. Its known temperature oscillation issue must remain visible.",
    [point("temperature.range", 77, jt, "NIST reports 77 K was achieved."), required_flag("module.micro_jt_cooling", jt, "This selected procedure evaluates the micro-JT architecture."), required_flag("module.stable_thz_detector_operation", jt, "Stable integrated detector operation is required by the application but not established by reaching 77 K; this must stay UNKNOWN until supported.")], [jt],
    [dict(key="temperature.range", as_printed="77 K achieved; oscillations below about 140 K", evidence_id=jt)], MACHINES[d2],
    ["Stable 77 K operation, loaded cooling power and integrated THz detector readout are unestablished. A demonstrated unloaded cold tip is not a verified detector system."], ["NIST/Colorado phase-II micro-JT prototype"])
e_d3 = experiment("ybco_rf_filter", "defense_and_security", "77 K microwave insertion-loss measurement of a 4 GHz YBCO filter",
    "Measure cryogenic bandpass transmission of a superconducting sapphire microstrip filter for low-loss microwave receiver technology; this is distinct from IR/THz photometry.",
    [point("temperature.range", 77, rf, "The reported filter characterization is at 77 K."), point("rf.frequency.range", 4, rf, "The documented bandpass center is 4.0 GHz.", "GHz"), required_flag("module.cryogenic_microwave_transmission", rf, "RF transmission launches, coax and measurement readout are indispensable.")], [rf],
    [dict(key="rf.frequency.range", as_printed="4.0 GHz", evidence_id=rf)], MACHINES[d3],
    ["Network-analyzer bandwidth around the center frequency, de-embedding, connector power handling and the exact cryostat model are not given in the inspected abstract. The source's measured insertion loss is an observation, not a guarantee."], ["NASA/CWRU reported 77 K filter transmission setup"])


# Nuclear/fusion: superconducting cable tests, full magnet qualification and
# vacuum pumping use different specimens and actuation/readout systems.
it = evidence("iter_magnet", "ITER, World's largest superconducting magnet test facility now operational", "https://www.iter.org/worlds-largest-superconducting-magnet-test-facility-now-operational-iter",
    "The 2026 ITER magnet cold-test facility is operational with the first coil cooled to 4 K. ITER explicitly says it cannot reproduce every in-machine condition; no full reactor-environment equivalence is claimed.",
    "4 K", "First coil cold test / facility operating regime")
sl = evidence("sultan", "EPFL Swiss Plasma Center, SULTAN Test Facility", "https://www.epfl.ch/research/domains/swiss-plasma-center/sultan-test-facility/",
    "SULTAN's present owner lists 10.8 T background field, 4.5–50 K sample temperature and sample current up to 100 kA for conductor/joint DC/AC testing. The 94 x 144 mm well and about 300 mm uniform region constrain sample layout. Separate maxima are not proven simultaneously feasible by scalar checks.",
    "10.8 T", "Facility technical specifications")
cp = evidence("iter_pump", "ITER, Let there be cold", "https://www.iter.org/node/20687/let-there-be-cold",
    "ITER reports the pre-production torus cryopump cooled to approximately 5 K on 1 August 2025, followed by gas injection to test pumping. This is commissioning with test gases; tritium pumping is not asserted.",
    "5 K", "Cryopump test-facility commissioning, 2025")
n1 = equipment("iter_magnet_facility", "ITER Organization", "ITER Magnet Cold Test Facility, first-coil 4 K configuration", "magnet_test_facility",
    "Real large cryogenic magnet qualification facility, operational 2026. The recorded 4 K point belongs to the coil; irradiation/plasma-equivalent conditions are not part of this configuration.",
    [rng("temperature.range", 4, 4, it), flag("module.full_magnet_cold_qualification", it)], [it],
    scene("magnet_test_facility", "large D-shaped superconducting toroidal-field coil", ["large vacuum cryochamber", "D-shaped coil support", "helium distribution pipes", "high-current leads", "quench voltage taps", "lifting lid"], ["Cool the full coil to 4 K", "Apply the qualified cold-test current program", "Record electrical and thermal behavior"]))
n2 = equipment("epfl_sultan", "EPFL Swiss Plasma Center", "SULTAN conductor and joint test facility", "conductor_test_facility",
    "Owner-specified conductor test facility; separate field, current and temperature envelopes do not constitute a verified coupled load line.",
    [rng("temperature.range", "4.5", 50, sl), maximum("magnetic_field.max", "10.8", sl, "T"), maximum("electrical.current.max", 100000, sl, "A"), flag("module.high_current_conductor_test", sl)], [sl],
    scene("conductor_test_facility", "paired cable-in-conduit conductor legs joined at the bottom", ["split superconducting background magnet", "rectangular test well", "U-shaped conductor sample", "high-current transformer loop", "helium flow lines", "voltage tap pairs"], ["Flow helium through the conductor sample", "Apply background field and ramp sample current", "Measure voltage onset and critical-current behavior"]))
n3 = equipment("iter_cryopump_test", "ITER Organization", "ITER torus cryopump test facility, pre-production 5 K configuration", "cryopump_test_facility",
    "Actual commissioning apparatus with a pre-production cryopump and test-gas injection near 5 K. No tritium-compatible qualification or unreported pumping speed is invented.",
    [rng("temperature.range", 5, 5, cp), flag("module.cryopump_gas_injection_test", cp), flag("vacuum.available", cp)], [cp],
    scene("cryopump_test_facility", "radial cold cryosorption panels behind a circular inlet valve", ["large test vacuum vessel", "cryopump cold panels", "helium supply and return", "gas injection manifold", "isolation valve", "vacuum gauges"], ["Cool the cryopump surfaces", "Inject a metered test-gas load", "Observe pressure and pumping response"]))
e_n1 = experiment("iter_coil_cold_test", "nuclear_engineering_and_fusion", "Full superconducting fusion-magnet cold qualification at 4 K",
    "Cold-test a complete ITER superconducting magnet coil, a different scale and protocol from a short conductor sample.",
    [point("temperature.range", 4, it, "ITER reports cooling the first coil to 4 K."), required_flag("module.full_magnet_cold_qualification", it, "The full-coil cryochamber, current leads, support and protection system are indispensable.")], [it],
    [dict(key="temperature.range", as_printed="4 K", evidence_id=it)], MACHINES[n1],
    ["Full design current, coil-specific support/load cases, quench protection, helium pressure and availability are not certified. ITER states that in-machine conditions cannot all be reproduced."], ["ITER Magnet Cold Test Facility"])
e_n2 = experiment("cicc_critical_current", "nuclear_engineering_and_fusion", "Fusion cable-in-conduit critical-current characterization at 4.5 K and 10.8 T",
    "Apply transport current to a helium-cooled superconducting conductor in SULTAN's background field and measure onset of resistive voltage.",
    [point("temperature.range", "4.5", sl, "SULTAN's documented lower operating point is 4.5 K."), req("magnetic_field.max", dict(kind="at_least", q=q("10.8", "T")), sl, "The selected boundary test requests the documented 10.8 T field."), required_flag("module.high_current_conductor_test", sl, "A conductor transformer/current circuit and voltage-tap measurement are required.")], [sl],
    [dict(key="temperature.range", as_printed="4.5–50 K", evidence_id=sl), dict(key="magnetic_field.max", as_printed="10.8 T", evidence_id=sl)], MACHINES[n2],
    ["Requested sample current, helium mass flow/pressure, field uniform region, joint layout and electrothermal stability require confirmation; the catalog does not assert independent maxima coexist for every sample."], ["EPFL SULTAN"])
e_n3 = experiment("torus_cryopump_gas_test", "nuclear_engineering_and_fusion", "Fusion torus cryopump gas-injection test near 5 K",
    "Measure response to test-gas injection on a precooled pre-production ITER cryopump, following the actual commissioning sequence.",
    [point("temperature.range", 5, cp, "The reported commissioning cold point is approximately 5 K; encoded 5 K is nominal."), required_flag("module.cryopump_gas_injection_test", cp, "A cryopump test stand with controlled gas admission is indispensable."), required_flag("vacuum.available", cp, "The pumping measurement needs a vacuum vessel.")], [cp],
    [dict(key="temperature.range", as_printed="approximately 5 K", evidence_id=cp)], MACHINES[n3],
    ["Gas composition/flow, sorbent capacity, regeneration, pumping speed and tritium suitability are not established by the scalar model."], ["ITER cryopump test facility"])


# Particle physics: RF losses in a resonator, two-phase ionization detection and
# sub-kelvin phonon calorimetry are distinct experiments and instrument shapes.
fn = evidence("fnal_vts", "Fermilab, SRF Technology and Materials", "https://technology.fnal.gov/capabilities/srf-technology-and-materials/",
    "Fermilab VTS has three liquid-helium test dewars for bare SRF cavities, high-power RF over several frequencies, and helium bath temperatures as low as 1.4 K, with diagnostic thermometry/second sound.",
    "1.4 K", "Vertical Test Stand capability")
fv = evidence("fnal_2k", "PI Loop Resonance Control for the Dark Photon Experiment at 2 K Using a 2.6 GHz SRF Cavity", "https://arxiv.org/abs/2307.10433",
    "The authors report 2.6 GHz SRF cavities operated at 2 K in the Fermilab vertical test facility. This supplies an actual operating point and RF measurement context, rather than extrapolating from a cooler's base temperature.",
    "2 K", "Title and abstract", doi="10.48550/arXiv.2307.10433")
warp = evidence("warp", "Benetti et al., First results from a Dark Matter search with liquid Argon at 87 K", "https://arxiv.org/abs/astro-ph/0701286",
    "The WARP collaboration reports a 2.3 litre natural-liquid-argon chamber at 87 K with simultaneous VUV scintillation and electron signals extracted through the liquid-gas boundary. Abstract source does not establish gas purity, HV margin or full calibration.",
    "a small 2.3 litre test chamber", "Abstract", doi="10.1016/j.astropartphys.2007.08.002")
cu = evidence("cuore", "INFN Laboratori Nazionali del Gran Sasso, CUORE", "https://www.lngs.infn.it/it/cuore?cookie_08fa49e35a0857da952fcd871a3a3923=accepted",
    "CUORE operates 988 TeO2 crystals arranged in 19 towers as cryogenic bolometers at approximately 10 mK. Energy deposition is inferred from thermal pulses; radiopurity and shielding are essential to rare-event sensitivity but no sensitivity is promised here.",
    "CUORE", "CUORE bolometer and cryostat description")
p1 = equipment("fnal_vts", "Fermilab", "Vertical Test Stand, reported 2 K 2.6 GHz SRF configuration", "srf_test_stand",
    "Bare-cavity vertical RF test apparatus, not a dilution refrigerator. Selected 2 K/2.6 GHz operating point is reported by the experiment; the broader facility can reach 1.4 K.",
    [rng("temperature.range", 2, 2, fv), minimum("temperature.base", "1.4", fn), rng("rf.frequency.range", "2.6", "2.6", fv, "GHz"), flag("module.srf_cavity_rf_test", fn)], [fn, fv],
    scene("srf_test_stand", "elliptical niobium RF cavity hanging vertically in a helium bath", ["deep helium dewar", "niobium elliptical cavity", "RF input coupler", "pickup antenna", "vertical insert flange", "temperature and second-sound sensors"], ["Pump the helium bath to the selected cold point", "Drive the cavity on resonance", "Measure RF response, detuning or ringdown"]))
p2 = equipment("warp_2l3", "WARP Collaboration / INFN LNGS", "WARP 2.3 litre two-phase liquid-argon prototype", "noble_liquid_detector",
    "Historical reported dark-matter detector configuration, not a commercial dewar recommendation. It includes the liquid-gas charge extraction and VUV light readout central to the measurement.",
    [rng("temperature.range", 87, 87, warp), flag("module.dual_phase_argon_charge_light", warp)], [warp],
    scene("noble_liquid_detector", "short cylindrical liquid-argon target under a gaseous extraction region", ["nested argon vessel", "liquid-gas interface", "drift and extraction electrodes", "VUV photosensors", "high-voltage feedthrough", "cryogenic fill line"], ["Condense and purify argon", "Drift ionization electrons to the liquid-gas boundary", "Record prompt scintillation and extracted-charge light"]))
p3 = equipment("cuore", "CUORE Collaboration / INFN LNGS", "CUORE TeO2 bolometer cryostat, reported 10 mK configuration", "bolometer_array",
    "Large low-background dilution-refrigerator installation containing TeO2 bolometer towers. This is distinct from a generic small dilution refrigerator; source-specific installed detector function is recorded.",
    [rng("temperature.range", "0.01", "0.01", cu), flag("module.teo2_bolometer_calorimetry", cu)], [cu],
    scene("bolometer_array", "nineteen towers of cubic tellurium-dioxide absorber crystals", ["nested copper vacuum shields", "pulse-tube cold heads", "dilution stage", "suspended tower plate", "TeO2 crystal tower array", "thermistor wiring and lead shield"], ["Cool the absorber towers to about 10 mK", "Deposit particle energy in an absorber", "Measure the small thermistor temperature pulse"]))
e_p1 = experiment("srf_2k_resonance", "physics_and_particle_accelerators", "2 K, 2.6 GHz superconducting RF-cavity resonance characterization",
    "Measure and stabilize the resonance response of a bare superconducting RF cavity in a vertical helium test stand, following the reported Fermilab experiment.",
    [point("temperature.range", 2, fv, "The paper operates the cavity at 2 K."), point("rf.frequency.range", "2.6", fv, "The cavity resonance is 2.6 GHz.", "GHz"), required_flag("module.srf_cavity_rf_test", fn, "Cavity RF coupling, pickup and resonance acquisition are indispensable.")], [fv, fn],
    [dict(key="temperature.range", as_printed="2 K", evidence_id=fv), dict(key="rf.frequency.range", as_printed="2.6 GHz", evidence_id=fv)], MACHINES[p1],
    ["Q0, RF field/power, coupler calibration, microphonics, quench onset and cryogenic dynamic heat loads are not inferred from a temperature/frequency match."], ["Fermilab VTS"])
e_p2 = experiment("argon_charge_scintillation", "physics_and_particle_accelerators", "Two-phase liquid-argon ionization and scintillation detection at 87 K",
    "Detect particle interactions through prompt VUV scintillation and an electron signal extracted across a liquid-gas argon boundary, as in the 2.3 litre WARP prototype.",
    [point("temperature.range", 87, warp, "The reported liquid-argon target is at 87 K."), required_flag("module.dual_phase_argon_charge_light", warp, "The detector needs drift/extraction electrodes and VUV readout, not simply liquid argon cooling.")], [warp],
    [dict(key="temperature.range", as_printed="87 K", evidence_id=warp), dict(key="target_volume", as_printed="2.3 litre test chamber", evidence_id=warp)], MACHINES[p2],
    ["Argon purity, electron lifetime, HV field, extraction efficiency and backgrounds are not quantified in this bounded profile; no dark-matter discrimination or sensitivity claim follows from passing it."], ["WARP 2.3 litre prototype"])
e_p3 = experiment("teo2_bolometer", "physics_and_particle_accelerators", "TeO2 crystal bolometer particle-energy calorimetry near 10 mK",
    "Measure energy deposits using thermal pulses from cryogenic TeO2 absorber crystals in CUORE's low-background bolometer array.",
    [point("temperature.range", "0.01", cu, "The source reports approximately 10 mK operating temperature; this is a nominal point."), required_flag("module.teo2_bolometer_calorimetry", cu, "Absorbers, thermistors and low-noise thermal readout are indispensable.")], [cu],
    [dict(key="temperature.range", as_printed="10 mK", evidence_id=cu)], MACHINES[p3],
    ["Bolometer heat capacity, thermal-link conductance, noise, energy calibration, cooling budget, radiopurity and shielding are not proven by these encoded checks."], ["CUORE"])


# General research: neutron diffraction, physisorption and relaxation
# calorimetry investigate structure, surface area and heat capacity respectively.
oc = evidence("orange", "NIST NCNR, Orange Cryostats", "https://www.nist.gov/ncnr/neutron-instruments/sample-environment/equipment/liquid-helium-cryostats/orange-cryostats",
    "NIST OC50 is a top-loading helium exchange-gas cryostat with 50 mm sample well, 1.5–300 K range, and compatibility with instruments other than HFBS, including BT-1. It is an actual neutron sample environment, not an optical dewar.",
    "OC50", "OC50 specifications and instrument compatibility")
bt = evidence("bt1", "NIST NCNR, BT-1 high-resolution neutron powder diffractometer specifications", "https://ncnr.nist.gov/instruments/bt1/bt1_spec.html",
    "BT-1 provides high-resolution neutron powder diffraction with cryogenic sample environments. The equipment entry is explicitly the integrated BT-1 + OC50 configuration; the bare Orange cryostat alone does not perform diffraction.",
    "High Resolution Powder Diffractometer", "Instrument title and sample environment specifications")
ga = evidence("gav4s8", "Investigation of the magnetic ground state of GaV4S8 using powder neutron diffraction", "https://arxiv.org/abs/2104.09912",
    "The authors use powder neutron diffraction at 1.5 K to investigate the magnetic ground state of GaV4S8. NIST BT-1 + OC50 is presented as a candidate apparatus with relevant capabilities, not falsely identified as the paper's reported machine.",
    "1.5 K", "Abstract and low-temperature magnetic structure discussion", doi="10.48550/arXiv.2104.09912")
tri = evidence("tristar", "Micromeritics, Minimum Surface Area Measurements with Physisorption Analyzers", "https://micromeritics.com.cn/en/resources/minimum-surface-area-measurements-with-micromeritics-physisorption-analyzers/",
    "The manufacturer documents nitrogen adsorption at 77 K on TriStar II / TriStar II Plus physisorption analyzers. The selected configuration is TriStar II Plus 3030 with liquid-nitrogen bath, not an invented cryostat modification.",
    "77 K", "Nitrogen measurement protocol / instrument comparison", "manufacturer_specification")
bet = evidence("bet", "RSC supplementary information c9cc00626e: gas sorption methods", "https://www.rsc.org/suppdata/c9/cc/c9cc00626e/c9cc00626e1.pdf",
    "The authors report nitrogen adsorption at 77 K on a Micromeritics TriStar II Plus with BET analysis after sample activation. The procedure is physisorption of activated porous solids, not cold imaging or calorimetry.",
    "TriStar II Plus", "Gas sorption experimental methods")
hc = evidence("qd_hc", "Quantum Design Heat Capacity Option, 1084-500 Rev. J0", "https://www.qdusa.com/siteDocs/productBrochures/1084-500_PPMS_Heat_Capacity.pdf",
    "Manufacturer describes high-vacuum thermal-pulse relaxation calorimetry on a puck. Nominal operational range 1.8–400 K, 3 x 3 mm maximum footprint. Accuracy specification is for zero field over 2–300 K; performance is not generalized to all fields/materials.",
    "1.8 to 400 K; 0 to 16 T", "Heat Capacity Specifications and method", "manufacturer_specification")
s1 = equipment("nist_bt1_oc50", "NIST NCNR", "BT-1 powder diffractometer with OC50 Orange cryostat", "neutron_cryostat",
    "Actual owner-documented integrated instrument/sample-environment combination. The neutron measurement role belongs to BT-1, not to the cryostat alone.",
    [rng("temperature.range", "1.5", 300, oc), maximum("sample.bore_diameter", 50, oc, "mm"), flag("module.neutron_powder_diffraction", bt)], [oc, bt],
    scene("neutron_cryostat", "powder-filled cylindrical sample can centered in a neutron beam", ["top-loading Orange helium cryostat", "long sample stick", "thin sample can", "incident neutron slit", "scattered-beam detector arc", "helium exchange-gas space"], ["Load powder and cool through helium exchange gas", "Illuminate the sample with the neutron beam", "Collect diffraction intensities around the detector arc"]))
s2 = equipment("tristar_3030", "Micromeritics", "TriStar II Plus 3030, nitrogen 77 K physisorption configuration", "gas_adsorption_analyzer",
    "Specialized cryogenic gas-sorption instrument with liquid-nitrogen sample bath, manifold and volumetric measurement; not a generic scientific cryostat.",
    [rng("temperature.range", 77, 77, tri), flag("module.nitrogen_physisorption_bet", tri)], [tri],
    scene("gas_adsorption_analyzer", "porous powder in a long-stem glass adsorption tube", ["gas manifold cabinet", "three glass sample tubes", "liquid-nitrogen Dewar", "sample bulbs", "pressure transducers", "vacuum pump line"], ["Activate/degas and weigh the powder", "Immerse sample tube in the 77 K bath", "Dose nitrogen and collect the adsorption isotherm"]))
s3 = "qd_dynacool_14T_eto_vsm_hc"
MACHINES[s3] = scene("physical_property_system", "small solid crystal on a suspended calorimeter platform", ["vertical PPMS sample chamber", "superconducting magnet", "pulse-tube cold head", "heat capacity puck", "suspended platform", "heater and thermometer wires"], ["Mount sample on the calorimeter puck", "Apply a controlled heat pulse", "Fit heating/cooling relaxation with addenda subtraction"])
e_s1 = experiment("magnetic_powder_neutrons", "scientific_research", "Magnetic powder neutron diffraction of GaV4S8 at 1.5 K",
    "Probe low-temperature magnetic order through neutron diffraction from a powder sample. BT-1 + OC50 is a documented candidate combination, not asserted to be the paper's original instrument.",
    [point("temperature.range", "1.5", ga, "The selected magnetic-structure measurement is at 1.5 K."), required_flag("module.neutron_powder_diffraction", ga, "A neutron beamline/detector and suitable cryogenic beam geometry are indispensable.")], [ga, oc, bt],
    [dict(key="temperature.range", as_printed="1.5 K", evidence_id=ga)], MACHINES[s1],
    ["Neutron wavelength, scattering geometry, magnetic phase history, sample amount, absorption and instrument resolution must match the study; these are not inferred from cooling alone."], ["Neutron powder diffraction apparatus in the cited study"])
e_s2 = experiment("nitrogen_bet_adsorption", "scientific_research", "Nitrogen adsorption isotherm and BET surface-area analysis at 77 K",
    "Determine surface area of an activated porous solid through volumetric nitrogen adsorption in a liquid-nitrogen bath, following the published TriStar II Plus method.",
    [point("temperature.range", 77, bet, "The reported nitrogen adsorption temperature is 77 K."), required_flag("module.nitrogen_physisorption_bet", bet, "Metered gas dosing, pressure readout and adsorption manifold are indispensable.")], [bet, tri],
    [dict(key="temperature.range", as_printed="N2 adsorption at 77 K", evidence_id=bet)], MACHINES[s2],
    ["Activation protocol, dead-volume calibration, relative-pressure fitting range, sample mass and BET validity for the chosen adsorbent must be confirmed; no surface-area result is fabricated."], ["Micromeritics TriStar II Plus"])
e_s3 = experiment("relaxation_heat_capacity", "scientific_research", "Zero-field heat-pulse relaxation calorimetry, 2–300 K",
    "Measure heat capacity versus temperature using a vacuum microcalorimeter and relaxation fit in the manufacturer-specified zero-field accuracy range.",
    [req("temperature.range", dict(kind="range_within", lo=q(2), hi=q(300)), hc, "The selected measurement range is the brochure's 2–300 K zero-field accuracy interval."), required_flag("module.heat_capacity", hc, "An installed calorimeter puck/heater/thermometer and relaxation acquisition are essential.")], [hc],
    [dict(key="temperature.range", as_printed="±5% for 2 K to 300 K, zero field", evidence_id=hc)], MACHINES[s3],
    ["Sample must fit the 3 x 3 mm platform; thermal contact, addenda calibration and relaxation model suitability require confirmation. Accuracy is not promised outside the cited zero-field scope."], ["PPMS DynaCool with Heat Capacity option"])


INDUSTRIES = [
    dict(id="aerospace_and_space_exploration", experiment_ids=[e_a1, e_a2, e_a3], configuration_ids=[a1, a2, a3], shortfalls=[]),
    dict(id="astronomy_and_astrophysics", experiment_ids=[e_b1, e_b2, e_b3], configuration_ids=[b1, b2, b3], shortfalls=[]),
    dict(id="automotive_and_transportation", experiment_ids=[e_c1, e_c2, e_c3], configuration_ids=[c1, c2, c3], shortfalls=[]),
    dict(id="defense_and_security", experiment_ids=[e_d1, e_d2, e_d3], configuration_ids=[d1, d2, d3], shortfalls=["Three real specialized research configurations are documented, but two are historical paper setups without a commercial cryostat model. The NIST micro-JT prototype is not validated for stable integrated THz operation; its corresponding mandatory check intentionally remains UNKNOWN. No three commercially purchasable complete defense instruments are claimed."]),
    dict(id="nuclear_engineering_and_fusion", experiment_ids=[e_n1, e_n2, e_n3], configuration_ids=[n1, n2, n3], shortfalls=[]),
    dict(id="physics_and_particle_accelerators", experiment_ids=[e_p1, e_p2, e_p3], configuration_ids=[p1, p2, p3], shortfalls=[]),
    dict(id="scientific_research", experiment_ids=[e_s1, e_s2, e_s3], configuration_ids=[s1, s2, s3], shortfalls=[]),
]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    for item in EQUIPMENT:
        write_json(ROOT / "data" / "cryostats" / ("expansion_a_" + item["id"][5:] + ".json"), item)
    for item in EXPERIMENTS:
        write_json(ROOT / "data" / "experiments" / ("expansion_a_" + item["id"][5:] + ".json"), item)
    write_json(ROOT / "data" / "evidence" / "expansion_a.json", list(EVIDENCE.values()))
    write_json(ROOT / "research" / "expansion" / "a_manifest.json", dict(
        schema_version=1, group="a", accessed=DATE, industries=INDUSTRIES,
        vocabulary_proposals=VOCAB, experiment_scenes=SCENES, equipment_scenes=MACHINES,
        source_urls=sorted({e["source_url"] for e in EVIDENCE.values()}),
        verification_limits=["All pairings must be evaluated by the unchanged Lean engine; this manifest does not assign outcomes.",
        "Per-function flags represent specifically documented installed apparatus roles. Missing roles stay UNKNOWN; source silence is not a documented absence.",
        "Reported single operating points are zero-width intervals and not invented wide temperature ranges. Base-temperature checks express only documented cold reach.",
        "Thermal shroud, optical bench, warm/cold calorimeter boundaries and specimen temperature are separate quantities.",
        "Facility access/current availability and full engineering safety are not asserted. Historical research apparatus remains explicitly labeled.",
        "No new coupled-physics model is asserted. Per-profile missing_information enumerates performance and coupled effects outside this bounded catalog model."],
        temperature_semantic_audit=[
            "304L tensile and polymer fatigue require temperature.range point_within 20 K; base <=20 K is not sufficient. CRAFT's actual 20 K bath is the only operating point recorded in that selected fixture.",
            "Bremen HB100 retains documented 10 K cold reach, while temperature.range is explicitly UNKNOWN; no 20 K operating interval is inferred.",
            "LAD outflow now uses Hartwig et al.'s actual SMiRF 20.3 K fixed fluid point (Table 3), rather than rounding the facility minimum to a supposed 20 K operating condition.",
            "CCC helium permeation uses the source's explicit PID-controlled 20–200 K test-cell interval and selects 20 K. The approximately 5 K general hardware minimum is not presented as a 5 K permeation experiment.",
            "Mirror metrology uses SBMD-3's observed 37.87 K mean mirror temperature (Table 4), distinct from generic XRCF 20 K cold reach. Required specimen gradient <=3 K remains mandatory UNKNOWN for the proposed instrument/optic combination.",
            "All newly recorded historical operating points carry experimental_observation provenance; only inspected manufacturer specifications use manufacturer_specification."],
        expected_experiments=21, expected_configuration_choices=21, new_equipment_records=len(EQUIPMENT)))
    lines = ["# Expansion A — primary-source catalog findings", "", "Research date: " + DATE + ".", "", "This group adds 21 distinct procedure profiles across seven industries and 20 specialized equipment records, reusing the already documented installed DynaCool heat-capacity configuration for the final choice. The manifest selects three experiments and three configurations per industry. These are candidate pairings, not suitability endorsements; Lean must evaluate every pairing.", "", "## Modeling boundaries", "", "Single reported operating points are stored as zero-width intervals. A quoted minimum is stored as cold reach, not a fabricated continuous controlled range. Facility shrouds, optical benches and calorimeter boundary temperatures are distinct quantities. Mandatory apparatus-function flags prevent temperature-only compatibility. Missing roles remain UNKNOWN because an incomplete source is not evidence of absence. The NIST micro-JT prototype's stable integrated THz-detector operation is a mandatory UNKNOWN.", "", "The selected scope checks documented temperatures and essential functions. Cryogenic pressure safety, radiation background, electrothermal load lines, dimensional fit and calibration are not universally formalized. Every profile records its specific limits. Passing the bounded profile must not be described as full engineering qualification.", "", "## Industry coverage", ""]
    for industry in INDUSTRIES:
        lines += ["### " + industry["id"], "", "Experiments:"]
        for exid in industry["experiment_ids"]:
            ex = next(x for x in EXPERIMENTS if x["id"] == exid)
            lines.append("- `" + exid + "`: " + ex["name"])
        lines += ["", "Configuration candidates:"]
        for cfg in industry["configuration_ids"]:
            lines.append("- `" + cfg + "`")
        for gap in industry["shortfalls"]:
            lines += ["", "Shortfall: " + gap]
        lines.append("")
    lines += ["## Inspected primary sources", ""]
    for eid, rec in EVIDENCE.items():
        lines += ["### `" + eid + "`", "", "[" + rec["document_title"] + "](" + rec["source_url"] + ")", "", rec["claim"], "", "Source location: " + rec["location"] + ". Evidence type: `" + rec["evidence_status"] + "`.", ""]
    lines += ["## Final temperature semantic audit", "", "The tensile and fatigue procedures require an actual 20 K operating point, not a base-temperature inequality. CRAFT records its reported 20 K bath; Bremen's 10 K minimum remains a cold-reach capability with an explicitly UNKNOWN operating interval. LAD outflow uses the directly documented SMiRF 20.3 K fixed fluid point from Hartwig et al. Table 3. CCC permeation uses its explicitly controlled 20–200 K specimen interval, selecting 20 K; its separate approximately 5 K hardware minimum is not a claimed permeation test condition. Mirror metrology uses the reported SBMD-3 mean mirror temperature of 37.87 K, with the published maximum 3 K specimen-gradient requirement remaining mandatory UNKNOWN until qualified. No observed operating point is labeled as a manufacturer specification.", "", "## Reproduction", "", "Run `python research/expansion/build_a.py` to regenerate only this group's new files. The integration owner must merge `vocabulary_proposals` from `a_manifest.json` before building the shared SQLite catalog and evaluating the 63 pairings in this group's seven 3×3 grids. No outcome is hardcoded by the generator.", ""]
    (ROOT / "research" / "expansion" / "a_sources.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(EXPERIMENTS)} experiments, {len(EQUIPMENT)} equipment records, {len(EVIDENCE)} evidence records, {len(VOCAB)} vocabulary proposals.")
