"""Reproduce the source-scoped group-B catalog additions (no shared files edited)."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
DAY = "2026-10-31"
evidence = []
vocabulary = {}
scenes = {}
equipment_scenes = {}

def write(path, value):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def q(value, unit="K"):
    return {"value": str(value), "unit": unit}

def ran(lo, hi, unit="K"):
    return {"kind": "range", "lo": q(lo, unit), "hi": q(hi, unit)}

def bound(kind, value, unit="K"):
    return {"kind": kind, "q": q(value, unit)}

def flag():
    return {"kind": "flag", "b": True}

def key(name, shape, unit, description):
    vocabulary[name] = {"shape": shape, "unit": unit, "description": description,
                        "status": "established", "better": {"range":"range", "min":"lower", "max":"higher", "flag":"flag", "count":"higher"}[shape]}

def ev(id, title, url, quote, claim, printed, location, status="manufacturer_specification", normalized=None):
    id = "expb_" + id
    rec = {"id": id, "claim": claim, "value_as_printed": printed, "normalized": normalized,
           "source_url": url, "document_title": title, "location": location, "quote": quote,
           "evidence_status": status, "accessed": DAY, "collected_by": "primary-source expansion B",
           "review_status": "source_read"}
    evidence.append(rec)
    return id

def cap(k, value, eid, status="manufacturer_specification", note=None):
    d = {"key": k, "value": value, "install": "installed", "evidence_status": status, "evidence_ids": [eid]}
    if note: d["note"] = note
    return d

def unknown(k, note):
    return {"key": k, "value": {"kind": "unknown"}, "install": "unknown", "evidence_status": "unknown", "evidence_ids": [], "note": note}

def req(k, constraint, eid, why):
    return {"key": k, "constraint": constraint, "mandatory": True,
            "origin": "experimental_observation", "rationale": why, "evidence_ids": [eid]}

def present(k, eid, why):
    return req(k, {"kind":"present"}, eid, why)

def point(k, value, eid, why, unit="K"):
    return req(k, {"kind":"point_within", "q": q(value, unit)}, eid, why)

def range_req(k, lo, hi, eid, why, unit="K"):
    return req(k, {"kind":"range_within", "lo":q(lo, unit), "hi":q(hi, unit)}, eid, why)

def limit(k, kind, value, eid, why, unit="K"):
    return req(k, {"kind":kind, "q":q(value, unit)}, eid, why)

def eq(slug, maker, model, family, title, url, capabilities, apparatus, description, status="manufacturer_specification", basis=None):
    id = "expansion_b_" + slug
    cid = id + "_documented"
    cfg = {"id":cid, "name":maker + " " + model, "configuration_basis":basis or "Documented catalog configuration; this is an equipment specification, not a claim of a physical installation.", "capabilities":capabilities}
    data = {"id":id, "manufacturer":maker, "model":model, "family":family, "description":description,
            "documents":[{"id":"expb_doc_"+slug, "title":title, "url":url, "accessed":DAY}], "configurations":[cfg]}
    write("data/cryostats/"+id+".json", data)
    equipment_scenes[cid] = {"equipment_id":id, "family":family, "archetype":family,
                             "apparatus":apparatus, "source_urls":[url], "geometry_status":"representative procedural geometry; not manufacturer CAD", "installed_options":basis or "Only the documented configuration named above."}
    return cid

def experiment(slug, industry, name, plain, title, url, eid, requirements, apparatus, sample, steps, limitations, equipment, description, archetype, conditions=None, params=None, doi=None):
    id = "expansion_b_" + slug
    source = {"citation":title, "url":url, "accessed":DAY}
    if doi: source["doi"] = doi
    data = {"id":id, "name":name, "plain_name":plain, "industry":industry, "description":description,
            "keywords":[plain, archetype, industry], "sources":[source], "reported_equipment":equipment,
            "reported_conditions":conditions or [], "requirements":requirements, "params":params or [], "coupled":[],
            "missing_information":limitations, "confirmed":True,
            "confirmation_note":"Source-specific requirements reviewed by the catalog author on "+DAY+". They describe the selected procedure, not a universal limit. Users must confirm them before a run; edits require confirmation again."}
    write("data/experiments/"+id+".json", data)
    scenes[id] = {"archetype":archetype, "apparatus":apparatus, "sample_shape":sample,
                  "distinctive_sample_shape":sample, "steps":steps, "source_urls":[url],
                  "scope":"Illustrative mechanism, never simulated scientific measurements or an installed-equipment claim."}
    return id

for name, desc in {
    "process.controlled_rate_freezing":"Programmed, controlled-rate biological sample freezing is documented.",
    "process.cryogenic_milling":"Mechanical sample comminution with documented cryogenic cooling.",
    "process.freeze_drying":"Vacuum freeze drying of pre-frozen bulk samples (not merely a cold condenser).",
    "process.dsc":"Differential scanning calorimetry with a heat-flow sensor and reference is available.",
    "process.deep_cryogenic_treatment":"Controlled sub-zero treatment of metal parts is documented.",
    "process.vitrification":"The documented carrier/protocol supports rapid cryoprotectant-assisted vitrification.",
    "process.ln2_immersion":"Direct liquid-nitrogen immersion of the documented sample carrier.",
    "process.circulating_bath":"Refrigerated circulating liquid bath, including its liquid work area.",
    "process.temperature_cycling":"A chamber with programmable temperature cycling is documented.",
    "module.dewpoint_control":"The complete humidified/dry gas mixing and dew-point measurement chain is installed.",
    "module.complex_resistivity":"A complex-resistivity measurement chain and sample electrodes are installed.",
    "module.sample_thermometry":"Independent sample thermocouple and logger are installed.",
    "module.eight_well_freezing_block":"The validated thermal-contact aluminum block for eight-well strips is installed.",
    "module.dynamic_nitrogen_purge":"Dynamic nitrogen purge of the calorimeter is documented.",
    "process.cryogenic_preconcentration":"Cryogenic trapping and focusing for gas analysis is documented.",
    "module.gc_ms":"An interfaced gas chromatograph and mass-selective detector are documented.",
}.items(): key(name, "flag", "", desc)
key("temperature.cooling_rate.range", "range", "mK_per_min", "Documented controlled cooling-rate magnitudes; do not substitute heating rates.")
key("temperature.heating_rate.range", "range", "mK_per_min", "Documented controlled heating-rate magnitudes.")
key("milling.frequency.range", "range", "Hz", "Documented grinding-jar vibration frequency, not electrical line frequency.")
key("milling.duration.max", "max", "s", "Documented programmable maximum milling duration (not a guarantee against sample warming).")
key("milling.jar_volume", "max", "L", "Nominal volume of the documented grinding jar.")
key("condenser.temperature.min", "min", "mK", "Lowest documented freeze-dryer collector/condenser temperature; never substitute for shelf/sample temperature.")
key("pressure.base", "min", "Pa", "Documented attainable operating vacuum; a lower pressure is more demanding.")
key("trap.precool.temperature", "min", "mK", "Lowest documented cold-focusing-trap precool setting for the selected installed method.")
key("trap.inject.temperature", "max", "mK", "Documented hot desorption/injection trap setpoint for the selected method.")
key("dwell.duration.max", "max", "s", "Maximum documented hold duration for the specified thermal process.")
key("carrier.oocyte.capacity", "count", "", "Maximum recommended number of oocytes on the documented vitrification carrier.")

PLANER = "https://planer.com/docs/freezers/K560_V2_0.pdf"
e_planer = ev("planer", "Planer Kryo 560-16, system specification", PLANER,
    "Range +30ºC to -180ºC", "Controlled-rate freezer: +30 to -180 C; system cooling magnitude 0.01–50 C/min; controller-only 99.9 C/min is not equipment performance.", "+30 to -180 C; cooling -0.01 to -50 C/min", "PDF pages 1–2; System Specification")
planer = eq("planer_kryo560", "Planer", "Kryo 560-16 with MRV, LNP4 and LAB 30", "controlled_rate_freezer", "Kryo 560-16 specification", PLANER,
    [cap("temperature.range",ran("93.15","303.15"),e_planer),cap("temperature.cooling_rate.range",ran("0.01","50","K_per_min"),e_planer),cap("process.controlled_rate_freezing",flag(),e_planer)],
    ["insulated square top-opening 16 L chamber", "basket of cryovials", "separate liquid-nitrogen dewar and delivery hose", "MRV controller showing a procedural cooling ramp"],
    "A real biological programmable freezer. Chamber and cooling specifications do not certify post-thaw viability.")

RETSCH = "https://www.retsch.com/files/15592/white-paper-cryogenic-preparation-of-sample-materials.pdf"
e_retsch = ev("retsch_protocols", "RETSCH: Cryogenic preparation of sample materials", RETSCH,
    "4 g 2 min 30 Hz", "The application table reports 4 g caoutchouc, 50 mL steel jar, 25 mm steel ball, 2 min at 30 Hz with LN2; gummy bears use MM400/CryoKit, 10 pieces, 1 min, 30 Hz. CryoMill continuously maintains nominal -196 C.", "Caoutchouc: 4 g, 2 min, 30 Hz; gummy bears: 10 pieces, 1 min, 30 Hz; LN2 nominal -196 C", "PDF pages 3–4, application table and mixer-mill discussion", "experimental_observation")
CRYOMILL = "https://www.retsch.com/products/milling/ball-mills/mixer-mill-cryomill/"
e_cryomill = ev("cryomill_spec", "RETSCH CryoMill technical data", CRYOMILL,
    "5 - 30 Hz", "CryoMill documents cryogenic grinding with continuous LN2 cooling, 5–30 Hz, jars through 50 mL, and maximum feed size 8 mm; soil is a listed sample material.", "5–30 Hz; 50 mL jar; continuous -196 C", "Technical Data and application examples")
cryomill = eq("retsch_cryomill", "RETSCH", "CryoMill, 50 mL steel jar and LN2 autofill", "cryogenic_mill", "CryoMill technical data", CRYOMILL,
    [cap("process.cryogenic_milling",flag(),e_cryomill),cap("temperature.base",bound("min","77.15"),e_retsch,"experimental_observation"),
     cap("milling.frequency.range",ran("5","30","Hz"),e_cryomill),cap("milling.jar_volume",bound("max","0.05","L"),e_cryomill)],
    ["single horizontal oscillating steel grinding jar", "large ball visible in cutaway", "insulated LN2 cooling jacket", "separate nitrogen autofill dewar"],
    "Single-station continuously cooled mixer mill. A milling apparatus, not a conventional sample cryostat. Nominal LN2 temperature is a published operating observation, not arbitrary temperature control.",basis="Documented 50 mL steel jar and LN2 autofill arrangement. Jar cooling does not establish volatile-analyte recovery or grind-size performance on every matrix.")

MM400 = "https://www.retsch.com/products/milling/ball-mills/mixer-mill-mm-400/"
e_mm = ev("mm400_spec", "RETSCH MM400 technical data", MM400,
    "3 - 30 Hz", "MM400 has two grinding stations, 3–30 Hz and 50 mL screw-top jars; cryogenic use requires separate LN2 precooling/CryoKit, not continuous active cooling.", "3–30 Hz; 50 mL jars; cryogenic grinding yes", "Technical Data; white paper provides CryoKit procedure")
mm400 = eq("retsch_mm400", "RETSCH", "MM 400 with CryoKit and two 50 mL steel jars", "cryogenic_mill", "MM 400 technical data", MM400,
    [cap("process.cryogenic_milling",flag(),e_mm),cap("milling.frequency.range",ran("3","30","Hz"),e_mm),cap("milling.jar_volume",bound("max","0.05","L"),e_mm),
     unknown("temperature.base","LN2 precooling is documented, but the source does not guarantee the sample remains at -196 C during MM400 milling.")],
    ["two side-by-side horizontal screw-top jars", "oscillating clamp arms", "separate insulated LN2 precooling container and tongs"],
    "A real twin-station mixer mill with an explicitly configured CryoKit. The bath is separate and the sample warms during milling.",basis="CryoKit and 50 mL steel jars are explicitly included as documented accessories; this is a selectable catalog configuration, not an installation claim.")

LTS = "https://www.linkam.co.uk/lts120-specifications"
e_lts = ev("lts120", "Linkam LTS120 specifications", LTS,
    "Temperature range -40°C to 120°C", "LTS120 spans -40 to120 C only with the optional water cooler below -25 C; optical microscope stage, 40x40 mm area, stability/accuracy <0.01 C, maximum heating/cooling 30 C/min.", "-40..120 C, optional water cooler below -25 C; stability <0.01 C", "Specifications")
lts = eq("linkam_lts120", "Linkam", "LTS120 with documented optional water chiller", "optical_cold_stage", "LTS120 specifications", LTS,
    [cap("temperature.range",ran("233.15","393.15"),e_lts),cap("optical_access",flag(),e_lts),cap("temperature.stability",bound("min","0.01"),e_lts),
     cap("sample.width.max",bound("max","40","mm"),e_lts),cap("sample.length.max",bound("max","40","mm"),e_lts),
     unknown("module.dewpoint_control","Gas valves are documented; an installed bubbler, flow controllers and hygrometer are not established."),
     unknown("temperature.cooling_rate.range","The maximum 30 C/min is documented, but a continuous controllable interval down to 1 C/min at -40 C is not specified on this page.")],
    ["flat rectangular Peltier stage under microscope", "hinged lid with round optical window", "microscope slide holding the selected specimen", "two water hoses to an external chiller"],
    "A flat optical temperature stage; the optional external chiller is explicitly part of this configuration.",basis="Optional water chiller explicitly included, as required by the source for operation below -25 C. Dew-point conditioning and microscope camera are unverified ancillary items.")

DSC = "https://www.linkam.co.uk/dsc600-specifications"
e_dsc = ev("dsc600", "Linkam DSC600 specifications", DSC,
    "Minimum heating rates of 0.1°C per minute", "DSC600 documents <-195 to600 C, heating0.1–130 C/min, DSC sample/reference crucibles and optical access. Lower bound -195 C is used conservatively.", "<-195..600 C; heating0.1..130 C/min", "Specifications")
dsc = eq("linkam_dsc600", "Linkam", "DSC600 with LN2 cooling", "calorimeter", "DSC600 specifications", DSC,
    [cap("temperature.range",ran("78.15","873.15"),e_dsc),cap("temperature.heating_rate.range",ran("0.1","130","K_per_min"),e_dsc),
     cap("process.dsc",flag(),e_dsc),cap("optical_access",flag(),e_dsc),unknown("module.dynamic_nitrogen_purge","A documented installed dynamic-N2 purge configuration has not been established from this specification.")],
    ["low flat DSC chamber", "separate sample and reference crucibles on heat-flow sensor", "LN2 supply hose", "optical aperture in chamber lid"],
    "An actual differential scanning calorimeter stage with distinct sample and reference pans. Heating-rate specifications are not reused as cooling-rate guarantees.")

THMSG = "https://www.linkam.co.uk/thmsg600"
e_thmsg = ev("thmsg600", "Linkam THMSG600 geology system", THMSG,
    "The sample is placed on 7mm quartz cover slip.", "Geology stage documents <-195 to600 C, stability<0.01 C, fluid-inclusion characterisation, 7 mm quartz support and LNP96 cooling0.01–150 C/min.", "<-195..600 C; 7 mm cover slip; cooling0.01..150 C/min", "THMSG600 Geology System")
thmsg = eq("linkam_thmsg600", "Linkam", "THMSG600 with LNP96 and T96", "geology_microthermometry_stage", "THMSG600 Geology System", THMSG,
    [cap("temperature.range",ran("78.15","873.15"),e_thmsg),cap("optical_access",flag(),e_thmsg),cap("temperature.stability",bound("min","0.01"),e_thmsg),
     cap("temperature.cooling_rate.range",ran("0.01","150","K_per_min"),e_thmsg)],
    ["small round silver geology stage on microscope", "7 mm quartz disc supporting a doubly polished mineral wafer", "optical viewing cone", "LN2 pump hoses"],
    "A microscope stage specifically for geological fluid and melt inclusions, visibly different from bulk refrigerators.")

FREEZONE = "https://cse.umn.edu/csd/subsample-preparation-and-analysis"
e_fz = ev("freezone_csd", "University of Minnesota CSD Facility: Subsample Preparation and Analysis", FREEZONE,
    "The CSD Facility has a Labconco FreeZone 6 Liter -50°C freeze drying system.", "The operating research facility identifies a real FreeZone6 L/-50 C system with three 10-inch shelves and6ports; soft sediment must first be frozen and is dried over multiple days.", "6 L, -50 C, three10-inch shelves,6ports", "Basic Preparation > Freeze Drying", "experimental_observation")
fz = eq("labconco_freezone6", "Labconco", "FreeZone 6 L -50 C (CSD Facility configuration)", "freeze_dryer", "CSD Facility freeze-drying equipment", FREEZONE,
    [cap("process.freeze_drying",flag(),e_fz,"experimental_observation"),cap("condenser.temperature.min",bound("min","223.15"),e_fz,"experimental_observation", "Collector rating, not shelf or sample temperature."),
     unknown("pressure.base","The facility page does not give an attainable vacuum specification.")],
    ["floor console containing refrigeration and collector", "transparent round vacuum drying chamber", "three stacked horizontal shelves", "side manifold valves and external vacuum line"],
    "A documented installed sediment-preparation system. Collector temperature is separate from the temperature of a frozen sample.",basis="The CSD laboratory explicitly reports this installed -50 C/6 L system with three10-inch shelves and6ports; pressure remains UNKNOWN.")

ESPEC = "https://espec.com/images/uploads/files/e_globaln-A4.pdf"
e_espec = ev("espec", "ESPEC Global-N temperature cycling chambers", ESPEC,
    "Temperature Range -70 to 180°C", "EGNX12-4NWL is a real380 L temperature/humidity chamber with -70 to180 C air range. Sample temperature, external complex-resistivity electronics and optional fittings are not thereby guaranteed.", "EGNX12-4NWL; -70..180 C;380 L", "PDF page7,380 L models,EGNX12-4NWL column")
espec = eq("espec_egnx12", "ESPEC", "EGNX12-4NWL Global-N", "freeze_thaw_chamber", "Global-N temperature cycling chamber specifications", ESPEC,
    [cap("temperature.range",ran("203.15","453.15"),e_espec),cap("process.temperature_cycling",flag(),e_espec),
     unknown("module.complex_resistivity","No installed electrodes, impedance spectrometer or sample wiring are established by the chamber brochure.")],
    ["large rectangular environmental cabinet", "thick front access door", "horizontal chamber shelves holding soil columns", "side cable-port position; external measurement instrument shown only when verified"],
    "An actual specialized climatic test chamber. Its air-temperature rating does not establish sample equilibration or electrical measurement capability.")

EPA = "https://www.epa.gov/system/files/documents/2023-12/sop-5188-entech-7200a-agilent-5977b_508-compliant.pdf"
e_epa = ev("epa_voc", "EPA J-AMCD-AAB-SOP-5188-0, Entech7200A/Agilent8890/5977B", EPA,
    "M3 Precool", "EPA's actual laboratory system couples an Entech7200A and Agilent8890/5977B GC-MSD. AppendixB screenshot shows Module3 precool -180 C, M2-to-M3 -160 C and injection80 C; Module2 injection230 C. Values were read from the screenshot, not inferred from PDF OCR.", "M3 Precool -180 C; M2->M3 -160 C; M3 Inject80 C", "PDF page59(index58), printed page57, AppendixB temperature-zone-control screenshot; sections1–2", "experimental_observation")
entech = eq("entech7200a_epa", "Entech / Agilent", "7200A + 8890/5977B GC-MSD (EPA SOP5188)", "cryogenic_gas_preconcentrator", "EPA installed VOC-analysis system and method", EPA,
    [cap("process.cryogenic_preconcentration",flag(),e_epa,"experimental_observation"),cap("module.gc_ms",flag(),e_epa,"experimental_observation"),
     cap("trap.precool.temperature",bound("min","93.15"),e_epa,"experimental_observation"),cap("trap.inject.temperature",bound("max","353.15"),e_epa,"experimental_observation")],
    ["steel whole-air sampling canister", "rectangular preconcentrator with three distinct small traps and LN2 plumbing", "adjacent gas chromatograph", "separate mass-selective detector"],
    "A real installed EPA research system; this is the documented method, not an assertion that every7200A installation includes a GC-MS. EPA labels the SOP internal research, not an officially approved EPA method.",basis="Actual EPA laboratory configuration from SOP5188, including Agilent8890/5977B and cryogenic focusing. Only demonstrated method setpoints are represented; no continuous temperature envelope is inferred.")

MESSER = "https://www.messer-us.com/hubfs/Messer%20US%20Website_2019/Resources/MESS-3145%20Metal%20Cryogenic%20Treatment%20Brochure.pdf"
e_messer = ev("messer", "Messer Metal Cryogenic Treatment brochure MESS-3145", MESSER,
    "24 to 72 hours", "Messer documents a real cabinet freezer for metal treatment and usual subzero treatment at -160 to-185 C for24–72h. Cabinet headline Fahrenheit/Celsius endpoints are rounded inconsistently: use conservative inner envelope -184..626.85 C instead of treating -300 F as exactly -185 C.", "Cabinet1200 F to-300 F; typicalprocess-160..-185 C for24..72h", "Typical treatment and cabinet freezer sections")
messer = eq("messer_metal_cabinet", "Messer", "Cabinet freezer for metal cryogenic treatment", "industrial_cryogenic_cabinet", "Messer Metal Cryogenic Treatment", MESSER,
    [cap("temperature.range",ran("89.15","900"),e_messer,note="Conservative inner envelope within printed -300 F..1200 F; not an exact conversion of rounded -185 C."),cap("process.deep_cryogenic_treatment",flag(),e_messer),
     unknown("dwell.duration.max","Typical treatment duration is documented, but a guaranteed maximum cabinet hold under the selected loaded condition is not specified.")],
    ["tall front-loading insulated steel cabinet", "guillotine style access door", "rack of metal tooling", "LN2 spray circulation and nitrogen supply pipe"],
    "A real manufacturer specialized industrial metal-treatment cabinet. No made-up SKU, load capacity or metallurgical outcome is assigned.")

CRYOTOP = "https://www.kitazato.co.jp/en/pdf/vitrification/Protocol-EN-Vitrification_for_Oocytes_Embryos.pdf"
e_cryotop = ev("cryotop", "Kitazato Vitrification Protocol for Oocytes / Embryos", CRYOTOP,
    "Plunge the Cryotop into liquid nitrogen within 1 second for vitrification.", "The protocol specifies Cryotop, cooling rack, LN2 container, maximum4oocytes/carrier, direct rapid plunge and submerged capping. It does not specify a temperature-controlled sample chamber.", "Maximum4oocytes/carrier; LN2 plunge within1s", "PDF pages3 and9; materials and rapid cooling/capping steps")
cryotop = eq("kitazato_cryotop", "Kitazato", "Cryotop with cooling rack and liquid-nitrogen container", "vitrification_plunge_system", "Kitazato Cryotop protocol", CRYOTOP,
    [cap("process.vitrification",flag(),e_cryotop),cap("process.ln2_immersion",flag(),e_cryotop),cap("carrier.oocyte.capacity",{"kind":"count","n":4},e_cryotop)],
    ["open LN2 container and cooling rack", "thin transparent carrier strip on colored handle", "four microscopic spherical oocytes magnified in an inset", "cover straw beside carrier"],
    "A real specialized cryogenic carrier and plunge arrangement, not a conventional programmable cryostat. No unsupported cooling-rate or clinical-success guarantee.",basis="Protocol-required Cryotop, cooling rack, liquid-nitrogen container and cover straw explicitly configured; medium and operator technique remain procedural prerequisites.")

BATH = "https://www.nist.gov/system/files/documents/ncnr/Circulating-Bath_Thermo-Scientific_NESLAB-RTE-7.pdf"
e_bath = ev("neslab_rte740", "Thermo Scientific NESLAB RTE instruction manual (NIST-hosted manufacturer document)", BATH,
    "-40°C to +200°C", "RTE740 is a real refrigerated circulating liquid bath. Manufacturer table gives -40 to200 C process-fluid range. The stated0.01 C stability applies at20 C water conditions, not automatically at a cryogenic sample.", "RTE740 processfluid-40..200 C", "PDF page9, printed page7, process-fluid temperature range and footnotes")
bath = eq("neslab_rte740", "Thermo Scientific", "NESLAB RTE740 refrigerated circulating bath", "refrigerated_circulating_bath", "NESLAB RTE manufacturer instruction manual", BATH,
    [cap("temperature.range",ran("233.15","473.15"),e_bath),cap("process.circulating_bath",flag(),e_bath),
     unknown("module.eight_well_freezing_block","The paper's custom aluminum freezing block is not an established included bath accessory."),
     unknown("module.sample_thermometry","An installed independent type-T sample thermocouple/logger is not established by the bath specification.")],
    ["rectangular liquid reservoir with insulated lid", "upright circulator/controller at rear", "immersed freezing-block position", "recirculation pump and rear tubing connections"],
    "A real Neslab refrigerated bath candidate for laboratory freezing experiments; the article does not identify its exact Neslab model, and the custom block/logger remain unverified.")

PBMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5180082/fullTextXML"
e_pbmc = ev("pbmc", "Angel et al.2016: Toward Optimal Cryopreservation and Storage for Achievement of High Cell Recovery and Maintenance of Cell Viability and T Cell Functionality", PBMC,
    "the cells were frozen at a controlled cooling rate of −1°C/min from +4°C to −80°C", "The primary study freezes1mL aliquots of PBMCs from+4 to-80 C at1 C/min in precooled MrFrosty containers. It later transfers them to nitrogen vapor below-135 C; that separate storage step is outside this initial-freeze profile.", "+4..-80 C at1 C/min;1mLaliquots", "Methods: Cryopreservation", "experimental_observation")
pbmc = experiment("bio_pbmc_controlled_freezing", "biology_and_biotechnology", "Controlled-rate freezing of peripheral blood mononuclear cells", "Preserve living immune cells", "Angel et al.2016, Biopreservation and Biobanking, DOI10.1089/bio.2016.0046", PBMC, e_pbmc,
    [present("process.controlled_rate_freezing",e_pbmc,"Freezing viable cell suspensions requires the selected cooling program, not simply a low base temperature."),
     range_req("temperature.range","193.15","277.15",e_pbmc,"Replicate the reported +4 to-80 C initial freezing window."),point("temperature.cooling_rate.range","1",e_pbmc,"Replicate the reported1 C/min cooling magnitude.","K_per_min")],
    ["cryovial basket in insulated freezer", "1mL cell suspension in each vial", "programmed chamber cooling and separate later storage vessel"], "small translucent screw-cap vials containing suspended spherical immune cells",
    ["Load precooled cryovials containing the prepared PBMC suspension.","Cool from+4 to-80 C at1 C/min.","Complete the initial freeze; evaluate subsequent nitrogen-vapor storage separately."],
    ["The study used MrFrosty containers; a programmable freezer is an alternative thermal implementation, not a published biological-equivalence result.","Cryomedium,1mL fill,cell density and post-thaw functional assays are essential procedural conditions outside Lean's current quantitative acceptance scope.","Subsequent storage below-135 C requires separate verified equipment."], ["ThermoFisher MrFrosty freezing containers"],
    "Initial PBMC preservation thermal program, distinct from frozen tissue slicing and fluorescence microscopy. Compatibility concerns the stated equipment requirements; no viability claim is fabricated.", "controlled_rate_freezing",doi="10.1089/bio.2016.0046")

e_vit = e_cryotop
vit = experiment("health_oocyte_vitrification", "healthcare_and_medicine", "Cryotop rapid vitrification of four oocytes", "Vitrify oocytes on a thin carrier", "Kitazato official vitrification protocol", CRYOTOP,e_vit,
    [present("process.vitrification",e_vit,"This procedure needs the actual vitrification carrier/process, not a chamber reaching the same nominal temperature."),present("process.ln2_immersion",e_vit,"Direct LN2 immersion is specified by the protocol."),req("carrier.oocyte.capacity",{"kind":"count_at_least","n":4},e_vit,"This selected protocol carries4oocytes; the manufacturer's maximum is4.")],
    ["Cryotop thin strip", "LN2 container and cooling rack", "forceps and cover straw", "equilibration drops beside the plunge area"], "four spherical oocytes on a tiny flat transparent carrier strip",
    ["Equilibrate oocytes in the prescribed media.","Load at most four oocytes on the carrier and plunge into LN2 within1s.","Cap with the tip submerged and transfer to LN2 storage."],
    ["Medium composition,timing,operator technique and warming are essential; Lean does not prove survival or clinical eligibility.","No sample chamber temperature range or guaranteed cooling rate has been invented for an open LN2 carrier."],["Kitazato Cryotop, cooling rack and LN2 container"],"Rapid cryoprotectant-assisted vitrification is physically different from slow freezing and frozen histological sectioning.","vitrification_plunge")

SNYDER = "https://journals.sagepub.com/doi/pdf/10.1177/1178223420972363"
e_snyder = ev("breast_cell_freeze", "Snyder et al.2020: Breast Cancer Cryoablation: Assessment of the Impact of Fundamental Procedural Variables in an In Vitro Human Breast Cancer Model", SNYDER,
    "or −25°C in a refrigerated circulating bath", "Primary in-vitro MCF7 experiment uses75uL/well in8well strips, aluminum blocks in Neslab/Thermo refrigerated baths,5min holds at-5,-10,-15,-20 or-25 C; an independent typeT logger tracks sample temperature.", "Selected arm:-25 C for5min,75uL/well; passive thaw", "PDF page3, Freezing protocol", "experimental_observation")
tumor = experiment("health_breast_cell_freeze_thaw", "healthcare_and_medicine", "In-vitro breast-cancer cell freeze–thaw injury at −25 C", "Study freezing injury in cancer cells", "Snyder et al.2020, DOI10.1177/1178223420972363",SNYDER,e_snyder,
    [present("process.circulating_bath",e_snyder,"The selected study uses liquid-bath thermal contact; a clinical cryoprobe is not assumed equivalent."),point("temperature.range","248.15",e_snyder,"Select the paper's -25 C bath arm."),
     present("module.eight_well_freezing_block",e_snyder,"The specified aluminum thermal-contact block is needed for the8well strip."),present("module.sample_thermometry",e_snyder,"Independent sample temperature logging is specified; bath setpoint alone is insufficient.")],
    ["refrigerated circulating bath", "aluminum block holding8well strip", "typeT thermocouple in representative well", "external sample-temperature logger"], "linear strip of eight small cup wells with a thin cell monolayer",
    ["Place the prepared8well strip into the precooled aluminum block.","Nucleate ice as specified and hold the selected -25 C freezing arm for5min.","Passively thaw and measure biological response with the study's assays."],
    ["The study names Neslab/Thermo but does not state its exact bath model; RTE740 is a real candidate, not falsely reported as the published instrument.","The custom freezing block and independent sample thermometry remain UNKNOWN unless documented for the selected configuration.","In-vitro cell results do not establish clinical tumor-ablation outcomes."],["Neslab/Thermo refrigerated circulating bath, exact model unspecified; Costar8well strips; OmegaHH806AU"],
    "A laboratory thermal-injury experiment with actual plate, bath and logger geometry. The verdict never substitutes a cryoprobe tip temperature for the cell sample temperature.","cell_freeze_thaw",doi="10.1177/1178223420972363")

gummy = experiment("food_gummy_cryogenic_homogenization", "food_and_agriculture", "Cryogenic homogenization of gummy confectionery for analysis", "Grind a sticky food sample", "RETSCH primary application: gummy bears inMM400/CryoKit", RETSCH,e_retsch,
    [present("process.cryogenic_milling",e_retsch,"The sample requires mechanical cryogenic comminution; a static cold chamber cannot meet this capability merely by temperature."),point("milling.frequency.range","30",e_retsch,"The published application runs at30Hz.","Hz"),limit("milling.jar_volume","at_least","0.05",e_retsch,"The published application explicitly uses50mL steel jars.","L")],
    ["twin jar mixer mill", "separate LN2 precooling container", "50mL steel jars with25mm balls"], "ten irregular gummy confectionery pieces changing into loose granules",
    ["Precool the closed jars and food using the documented CryoKit method.","Clamp jars and mill at30Hz for1min.","Recover homogenized sample for the planned food analysis."],
    ["The source's observed final fineness is an application result, not a universal guaranteed capability.","The MM400 does not continuously maintain LN2 temperature; no constant -196 C sample claim is made."],["RETSCHMM400,CryoKit,two50mL steel jars,25mm balls"],"Mechanical sample preparation for compositional analysis, distinct from observing ice crystals or removing water by sublimation.","food_cryomilling")

ICECREAM="https://www.sciencedirect.com/science/article/abs/pii/S0958694696000295"
e_icecream=ev("icecream", "Donhowe and Hartel1996: Recrystallization of ice in ice cream during controlled accelerated storage",ICECREAM,
    "Sample temperature was held constant (within ±0.01 °C)","Primary study observes thin-film vanilla ice cream by cold-stage microscopy for5days, mean temperatures -20 to-5 C and fluctuations0.01 to2 C.","-20..-5 C;±0.01 C constant-temperature arm;5days", "Publisher abstract", "experimental_observation")
icecream=experiment("food_icecream_recrystallization", "food_and_agriculture", "Cold-stage microscopy of ice-crystal recrystallization in ice cream", "Watch ice crystals grow in ice cream", "Donhowe and Hartel1996, DOI10.1016/S0958-6946(96)00029-5",ICECREAM,e_icecream,
    [range_req("temperature.range","253.15","268.15",e_icecream,"Selected study mean-temperature window -20 to-5 C."),present("optical_access",e_icecream,"Time-lapse microscopy must see the thin food film."),limit("temperature.stability","at_most","0.01",e_icecream,"The constant-temperature arm maintained the sample within±0.01 C.")],
    ["flat cold stage under microscope", "thin vanilla-ice-cream film between slides", "camera and calibrated specimen-temperature readout"],"thin creamy disc containing faceted ice crystals and rounded air cells",
    ["Mount a thin ice-cream film on the cold microscope stage.","Hold the selected temperature within the required stability and record images.","Measure changes in the ice-crystal size distribution."],
    ["Microscope,camera and cold glove-box arrangement are external to a bare stage configuration; optical access does not certify an installed camera.","A stage stability rating does not prove specimen equilibration over5days; calibration and the film preparation remain required."],["Cold-stage microscope housed in a refrigerated glove box, exact model not in accessible abstract"],"An optical food-structure experiment. Animation illustrates crystal shape changes and never invents measured growth rates.","icecream_microscopy",doi="10.1016/S0958-6946(96)00029-5")

STRAWBERRY="https://mdpi-res.com/d_attachment/processes/processes-13-02065/article_deploy/processes-13-02065.pdf"
e_straw=ev("strawberry", "Impact of Different Dehydration Methods on Drying Efficiency,Nutritional and Quality Attributes of Strawberry Slices,Processes2025,13,2065",STRAWBERRY,
    "The condenser temperature was −67 ◦C with 0.055 mBar vacuum pressure.","Primary freeze-drying arm uses slices pre-frozen -40 C for4h and LabconcoFreezone6plus with condenser -67 C and0.055mbar. Collector temperature is not sample temperature.","Condenser-67 C;vacuum0.055mbar;prefreeze-40 C4h", "Methods, freeze-drying arm and Table1", "experimental_observation")
straw=experiment("food_strawberry_lyophilization", "food_and_agriculture", "Freeze-drying of pre-frozen strawberry slices", "Freeze-dry strawberry slices", "Processes2025,13,2065; DOI10.3390/pr13072065",STRAWBERRY,e_straw,
    [present("process.freeze_drying",e_straw,"Requires actual vacuum sublimation equipment, not merely cold storage."),limit("condenser.temperature.min","at_most","206.15",e_straw,"Replicate the reported -67 C collector setting; do not treat it as shelf temperature."),limit("pressure.base","at_most","5.5",e_straw,"0.055mbar equals5.5Pa exactly.","Pa")],
    ["vacuum freeze dryer", "shelf tray of fruit slices", "cold water-vapor collector", "vacuum pump line and pressure gauge"],"red circular strawberry slices with pale seeds on a horizontal tray",
    ["Pre-freeze single-layer slices at-40 C for4h using a separate freezer.","Apply vacuum with the reported -67 C condenser and0.055mbar condition.","Recover dried slices and perform the reported quality assays."],
    ["The selected -50 C FreeZone candidate does not meet the study's -67 C collector requirement; no compatible configuration is manufactured.","The source's pre-freezer and sample/shelf temperature history require separate equipment evidence.","Pressure capability of the documented CSD FreeZone configuration is UNKNOWN."],["LabconcoFreezone6plus;separateprefreezer"],"Food preservation by vacuum sublimation. No physical drying result is generated by the 3D illustration.","fruit_freeze_drying",doi="10.3390/pr13072065")

SOILURL=CRYOMILL
e_soil=ev("soil_milling", "RETSCH CryoMill: soil sample preparation and cryogenic mechanism",SOILURL,
    "waste, soil, chemical products", "The manufacturer explicitly lists soil among cryomilling samples. Its primary white paper describes LN2 preparation to reduce loss of volatile components. This is a documented preparation method, not a pollutant-recovery validation study.","LN2 nominal-196 C;soil listed;volatile preservation motivation", "Sample materials; linked cryogenic-preparation white paper", "manufacturer_specification")
soil=experiment("env_soil_cryogenic_preparation", "environmental_science", "Cryogenic soil homogenization before volatile-contaminant analysis", "Prepare soil while limiting heat exposure", "RETSCH CryoMill primary technical/application documentation",SOILURL,e_soil,
    [present("process.cryogenic_milling",e_soil,"Actual comminution with cryogenic cooling is essential."),limit("temperature.base","at_most","77.15",e_retsch,"Select the manufacturer's nominal LN2-cooled CryoMill procedure; a warm mixer mill does not establish this operating condition.")],
    ["single cooled steel grinding jar", "soil particles and grinding ball", "LN2 jacket and autofill line"],"brown heterogeneous soil granules in a horizontal steel jar",
    ["Select and document soil aliquot and contamination controls.","Precool and cryogenically homogenize using the documented LN2 method.","Extract and assay target contaminants using an independently validated analytical method."],
    ["No specific contaminant recovery,grind time,feed mass or detection limit is established by this manufacturer method.","Matrix-specific validation is required; a hardware PASS does not establish analytical recovery."],["RETSCHCryoMill"],"Manufacturer-documented cryogenic environmental sample preparation. Numeric LN2 operation comes from the primary white paper, not invented pollutant performance.","soil_cryomilling")

INP="https://acp.copernicus.org/articles/23/12707/2023/"
e_inp=ev("inp", "Production of ice-nucleating particles(INPs)by fast-growing phytoplankton,ACP2023,23,12707–12729",INP,
    "Temperature control was maintained to within", "The primary study uses an LTS350 microscope stage for2uL marine-aerosol droplets,+5 to-40 C,1 C/min cooling,5 C/min heating,25cycles and approximately-39 C dewpoint with a nitrogen mixer and hygrometer.","+5..-40 C at1 C/min;dewpoint~-39 C;2uLdroplet", "Section2.2,ice-nucleation measurements", "experimental_observation")
inp=experiment("env_marine_aerosol_ice_nucleation", "environmental_science", "Immersion freezing of marine-aerosol droplets", "Measure when a cloud droplet freezes", "ACP2023,DOI10.5194/acp-23-12707-2023",INP,e_inp,
    [range_req("temperature.range","233.15","278.15",e_inp,"Replicate the +5 to-40 C cycle."),present("optical_access",e_inp,"Images identify each discrete freezing event."),point("temperature.cooling_rate.range","1",e_inp,"The cooling ramp is1 C/min.","K_per_min"),present("module.dewpoint_control",e_inp,"The source requires gas mixing and hygrometer control to prevent evaporation/condensation; stage gas ports alone are insufficient.")],
    ["sealed optical cold stage", "2uL droplet over aerosol spot on foil", "dry and humidified nitrogen mixing lines", "dewpoint sensor and microscope camera"],"single hemispherical water droplet over a small dark aerosol spot",
    ["Place the collected aerosol beneath a2uL droplet.","Condition the gas dewpoint and cool +5 to-40 C at1 C/min.","Record the freezing event,rewarm and repeat the reported cycles."],
    ["Published equipment is LTS350; LTS120 is a different real candidate and its full gas/dewpoint assembly remains UNKNOWN.","The stage's maximum cooling rate is not proof of an arbitrary controlled ramp at the cold endpoint."],["LinkamLTS350;OlympusBX51M;QImagingcamera;EdgeTechDewPrimeII"],"Atmospheric ice-nucleation experiment with a droplet,gas conditioning and optical observation.","cloud_droplet_freezing",doi="10.5194/acp-23-12707-2023")

voc=experiment("env_whole_air_voc_cryofocusing", "environmental_science", "Cryogenic preconcentration of whole-air volatile organic compounds", "Trap trace air pollutants before GC-MS", "EPA research SOPJ-AMCD-AAB-SOP-5188-0,AppendixB",EPA,e_epa,
    [present("process.cryogenic_preconcentration",e_epa,"The procedure requires gas traps and programmed cryofocusing,not a generic cold sample chamber."),present("module.gc_ms",e_epa,"An interfaced GC-MSD is explicitly part of the actual research system."),limit("trap.precool.temperature","at_most","93.15",e_epa,"Module3 precool is-180 C in the selected long-method screenshot."),limit("trap.inject.temperature","at_least","353.15",e_epa,"Module3 injection setting is80 C; desorption is part of the same trap method.")],
    ["whole-air canister", "three-module cryogenic preconcentrator", "LN2 trap-cooling plumbing", "GC column and mass-selective detector"],"trace gas molecules moving through a narrow coiled focusing capillary",
    ["Connect the prepared whole-air canister and verify the method's QC prerequisites.","Dehydrate,trap and cryofocus using the documented module setpoints.","Heat the focusing trap for injection and analyze by the interfaced GC-MSD."],
    ["This is the EPA's internal laboratory research SOP,not an officially approved EPA method or a guarantee of regulatory method compliance.","Calibration,recovery,water removal and detection limits require the method's separate QC; no fake chromatogram is generated."],["Entech7200A,Entech7016D,Agilent8890/5977B"],"Trace-air analytical system with cold trapping and hot desorption; it does not expose a bulk experiment to the trap's entire thermal cycle.","voc_cryofocusing")

INCLUSION="https://mdpi-res.com/d_attachment/minerals/minerals-13-00365/article_deploy/minerals-13-00365.pdf"
e_incl=ev("fluid_inclusions", "Zhou et al.2023: Characteristics and Geological Significance of CO2-Rich Fluid Inclusions in DakalasuNo.1Pegmatite Dyke,Altay",INCLUSION,
    "the field of −56.6 to 0.0 ◦C", "Primary paper uses doubly polished ~0.2mm mineral sections and a LinkamTHMSG600 calibrated±0.2 C over-56.6..0 C. Selected low-temperature microthermometry window is sourced from that calibration and observation method.","~0.2mmsections;calibration-56.6..0 C", "Methods,petrography and microthermometry", "experimental_observation")
inclusions=experiment("geo_fluid_inclusion_microthermometry", "geology_and_oceanography", "Low-temperature microthermometry of CO2-rich mineral inclusions", "Watch trapped fluid change phase in rock", "Zhou et al.2023,Minerals13,365,DOI10.3390/min13030365",INCLUSION,e_incl,
    [range_req("temperature.range","216.55","273.15",e_incl,"Selected calibrated low-temperature window -56.6 to0 C,not the unrelated high-temperature homogenization procedure."),present("optical_access",e_incl,"Fluid inclusions are observed through a doubly polished mineral wafer." )],
    ["geology microscope cold stage", "doubly polished quartz/beryl wafer on quartz disc", "microscope objective and calibrated temperature readout"],"thin angular transparent mineral wafer containing tiny ellipsoidal fluid bubbles",
    ["Locate inclusions in the doubly polished mineral wafer.","Freeze and rewarm through the calibrated -56.6 to0 C window.","Observe phase changes and record temperatures with the required laboratory calibration."],
    ["The publication also performs higher-temperature work; this profile deliberately covers only its calibrated low-temperature leg.","A manufacturer's stability figure does not independently prove the publication's calibration uncertainty; calibration must be supplied by the lab."],["LinkamTHMSG600 heating-cooling stage"],"Earth-science phase-change microscopy of trapped fluids,with a mineral wafer rather than a generic sensor puck.","fluid_inclusion_microscopy",doi="10.3390/min13030365")

PERMA="https://www.ornl.gov/publication/remote-sensing-freeze-thaw-transitions-arctic-soils-using-complex-resistivity-method"
e_perma=ev("permafrost", "Wu,Hubbard,Ulrich and Wullschleger2013: Remote sensing of freeze-thaw transitions in Arctic soils using the complex resistivity method",PERMA,
    "controlled temperature environments at 4 ºC and -20 ºC", "The primary study induces Arctic-soil column freeze–thaw transitions at+4 and-20 C and measures complex resistivity. Temperature cycling alone does not supply the impedance instrumentation.","+4and-20 C temperature environments", "ORNL author/institutional publication abstract", "experimental_observation")
perma=experiment("geo_permafrost_complex_resistivity", "geology_and_oceanography", "Complex-resistivity monitoring of Arctic-soil freeze–thaw", "Track frozen soil using electrical response", "Wu et al.2013,VadoseZoneJournal,DOI10.2136/vzj2012.0062",PERMA,e_perma,
    [range_req("temperature.range","253.15","277.15",e_perma,"The reported soil-column environments alternate between-20 and+4 C."),present("process.temperature_cycling",e_perma,"The procedure must induce repeatable freeze–thaw transitions."),present("module.complex_resistivity",e_perma,"The sample needs electrodes and complex-resistivity instrumentation; a temperature chamber alone cannot establish the measurement.")],
    ["environmental freeze-thaw chamber", "vertical Arctic soil column", "four electrode bands and measurement leads", "external impedance measurement chain,unverified unless configuration documents it"],"tall brown cylindrical soil core with horizontal electrode rings",
    ["Prepare and wire the soil column using the study's measurement method.","Cycle the environment between+4 and-20 C and allow sample equilibration.","Record complex-resistivity response through freezing and thawing."],
    ["ESPEC is a real thermal-environment candidate; its brochure does not document the study's electrodes or impedance spectrometer.","Environmental air range is not proof of a particular soil core's equilibration time; no invented freeze front or measured conductivity is displayed."],["Temperature-controlled soil-column environment and complex-resistivity system; exact chamber model unspecified in institutional abstract"],"A geophysical soil-core measurement with electrodes,not optical cloud-droplet imaging.","permafrost_resistivity",doi="10.2136/vzj2012.0062")

sediment=experiment("geo_soft_sediment_lyophilization", "geology_and_oceanography", "Freeze-drying soft sediment before geological analysis", "Prepare a friable sediment core sample", "University of Minnesota CSD Facility freeze-drying method",FREEZONE,e_fz,
    [present("process.freeze_drying",e_fz,"Vacuum sublimation preserves a friable sediment preparation; a refrigerator by itself is insufficient."),limit("condenser.temperature.min","at_most","223.15",e_fz,"Replicate the CSD facility's documented -50 C collector configuration; this is a selected facility-method requirement,not a universal sediment eutectic temperature.")],
    ["six-liter freeze dryer", "sample cups on adjustable vacuum-chamber shelves", "collector and vacuum line"],"small foil-covered glass cups containing irregular laminated sediment crumbs",
    ["Freeze the sediment subsamples in separate suitable equipment.","Dry the frozen open-surface subsamples in the documented freeze dryer over multiple days.","Confirm dryness and use the friable material for the selected geological analysis."],
    ["The facility gives no numeric vacuum,shelf-temperature,time-to-dry or mass-specific capacity; these remain unquantified rather than invented.","Collector rating is not a frozen sample-temperature measurement.","Complete drying must be checked experimentally; the verdict only covers the stated facility hardware prerequisites."],["CSD installed LabconcoFreeZone6L/-50 C,three10inch shelves,6ports"],"A documented geological sample-preparation method,with sediment cups rather than fruit slices.","sediment_freeze_drying")

steel=experiment("manufacturing_steel_deep_cryo_treatment", "manufacturing_and_industrial_processing", "Deep cryogenic treatment of steel tooling", "Treat a steel tool below zero", "Messer primary Metal Cryogenic Treatment process documentation",MESSER,e_messer,
    [present("process.deep_cryogenic_treatment",e_messer,"The protocol requires a controlled treatment of metal tooling,not only a cold measurement stage."),point("temperature.range","113.15",e_messer,"Select the warm end(-160 C)of the documented typical treatment interval,avoiding the brochure's rounded Fahrenheit/Celsius mismatch."),limit("dwell.duration.max","at_least","24",e_messer,"Select24h from the reported typical24–72h treatment; the candidate's loaded hold-duration specification is not established.","h")],
    ["industrial insulated treatment cabinet", "metal tooling rack", "nitrogen circulation supply", "time-temperature controller"],"several silver cutting-tool inserts and a fluted steel drill on a rack",
    ["Load previously heat-treated tools using a documented material-specific recipe.","Apply the selected-160 C,24h cryogenic treatment leg.","Warm according to the validated process and measure the actual material properties."],
    ["This is a source-scoped process profile; material-specific cooling/warming ramps and prior heat treatment are not supplied by the generic brochure.","The cabinet's verified loaded maximum dwell remains UNKNOWN.","No hardness,wear improvement or phase-transformation result is fabricated."],["Messer cabinet freezer for metal cryogenic treatment"],"An industrial thermal treatment of tool steel,scientifically different from rubber comminution and DSC characterization.","steel_cryogenic_treatment")

rubber=experiment("manufacturing_rubber_cryomilling", "manufacturing_and_industrial_processing", "LN2 cryomilling of elastomeric rubber", "Pulverize an elastic rubber specimen", "RETSCH primary caoutchouc CryoMill application",RETSCH,e_retsch,
    [present("process.cryogenic_milling",e_retsch,"A grinding ball and cryogenic mechanical comminution are essential."),limit("temperature.base","at_most","77.15",e_retsch,"The published CryoMill protocol uses continuous nominal-196 C operation."),point("milling.frequency.range","30",e_retsch,"The caoutchouc application runs at30Hz.","Hz"),limit("milling.jar_volume","at_least","0.05",e_retsch,"The documented setup uses a50mL stainless-steel jar.","L")],
    ["single horizontal cooled steel jar", "25mm steel grinding ball", "rubber feed pieces", "continuous LN2 jacket"],"four grams of black irregular rubber chips becoming brittle fragments",
    ["Load4g caoutchouc with the documented25mm ball in the50mL jar.","Precool and mill for2min at30Hz with continuous LN2 cooling.","Recover material and independently assess the required fineness."],
    ["Published final fineness is an observed application result,not a guaranteed capability for every elastomer.","The generic LN2 temperature is not a substitute for a measured glass-transition temperature of a new material."],["RETSCHCryoMill,50mL steeljar,25mm steelball,LN2"],"Cryogenic brittle fracture and comminution of an elastomer,with a mechanically moving jar and ball.","rubber_cryomilling")

RUBBERDSC="https://analyzing-testing.netzsch.com/_Resources/Persistent/1/1/3/a/113a82aa25c66d466843e79a134e449ecb15ac00/DSC_214_Polyma_en_web.pdf"
e_rubberdsc=ev("rubber_dsc", "NETZSCH DSC214Polyma primary application brochure: Low-Temperature Performance of Rubber",RUBBERDSC,
    "Sample mass: 15.41 mg", "Manufacturer's primary SBR rubber measurement heats15.41mg from-100 to220 C at10K/min twice in dynamic nitrogen. DSC signal and purge are essential; thermal range alone is not a DSC instrument.","SBR15.41mg;-100..220 C;10K/min;dynamicN2", "PDF page16,Low-Temperature Performance of Rubber,figure caption", "experimental_observation")
rubberdsc=experiment("manufacturing_sbr_rubber_dsc", "manufacturing_and_industrial_processing", "Differential scanning calorimetry of SBR rubber", "Measure a rubber thermal transition", "NETZSCH DSC214Polyma primary SBR rubber application",RUBBERDSC,e_rubberdsc,
    [present("process.dsc",e_rubberdsc,"The experiment needs differential heat-flow sensing against a reference."),range_req("temperature.range","173.15","493.15",e_rubberdsc,"Replicate the reported -100 to220 C heating window."),point("temperature.heating_rate.range","10",e_rubberdsc,"Replicate the10K/min heating ramp.","K_per_min"),present("module.dynamic_nitrogen_purge",e_rubberdsc,"Dynamic nitrogen atmosphere is part of the reported measurement; do not assume it is installed on every calorimeter.")],
    ["DSC sample and reference pans", "rubber specimen on heat-flow sensor", "controlled LN2 cooling and nitrogen purge", "temperature-program controller"],"tiny black SBR rubber disc inside one shallow round aluminum DSC pan",
    ["Weigh15.41mg SBR into the sample pan and prepare the reference.","Run the reported -100 to220 C heating program at10K/min with dynamicN2.","Repeat the thermal program and interpret actual measured heat-flow data."],
    ["The paper reports NETZSCHDSC214Polyma; LinkamDSC600 is a different real candidate,not falsely labeled as the reported instrument.","An installed dynamic nitrogen purge is not established for the Linkam configuration and stays UNKNOWN.","Animations never display fabricated thermograms or transition temperatures."],["NETZSCHDSC214Polyma;15.41mgSBR;dynamicN2"],"Calorimetric material characterization with paired pans,not a generic magnetic-coil cryostat.","rubber_calorimetry")

CRYOSPHERE="https://asia.atricure.com/sites/default/files/devices-ifu/IFU-0036.C.pdf"
e_cryoice=ev("cryoice", "AtriCure cryoSPHERE CRYOS/CRYOS-L IFU-0036.C,March2025",CRYOSPHERE,
    "typical operating ranges between -50°C (-58F) to -70°C (-94°F)","The official IFU documents cryoSPHERE with cryoICE BOX and an external N2O cylinder,peripheral-nerve freezing,typical probe operation -50 to-70 C,and a120s default ablation timer. These are probe settings,not ambient or tissue temperatures.","Typical probe-50..-70 C;120s default;N2O cylinder notprovided", "Page1,System Description,Indications,and step11")
key("process.nerve_cryoneurolysis","flag","","Documented peripheral-nerve freezing with the specified surgical cryoprobe.")
key("probe.temperature.range","range","mK","Documented cryoprobe operating temperature envelope,distinct from tissue temperature and console ambient range.")
key("probe.freeze_duration.range","range","s","Conservatively documented supported freeze durations; a single-point interval records one established timer setting.")
key("module.direct_visualization","flag","","Documented installed direct-visualization equipment for the selected procedure; never inferred from a console specification.")
cryoice=eq("atricure_cryosphere", "AtriCure", "cryoSPHERE CRYOS with cryoICE BOX", "nerve_cryoablation_probe", "AtriCure cryoSPHERE official IFU",CRYOSPHERE,
    [cap("process.nerve_cryoneurolysis",flag(),e_cryoice),cap("probe.temperature.range",ran("203.15","223.15"),e_cryoice,note="Typical probe operating envelope; not a guaranteed tissue-temperature range."),
     cap("probe.freeze_duration.range",ran("120","120","s"),e_cryoice,note="Single documented120s default setting; no unsupported minimum or maximum duration inferred."),
     unknown("module.direct_visualization","The candidate console/probe does not establish an installed thoracoscopic visualization chain.")],
    ["compact cryoICE BOX console with timer", "external N2O cylinder and delivery hose", "long narrow bent probe with spherical ball tip", "representative rib and intercostal nerve model; visualization system unverified"],
    "A real specialized N2O surgical cryoprobe configuration. Probe temperature is kept separate from tissue and room temperature; no pain-relief or clinical-eligibility result is inferred.",basis="The IFU specifies cryoSPHERE with cryoICE BOX; an external N2O cylinder is a required separately supplied utility. A thoracoscopic visualization chain is not asserted installed.")
NERVE="https://escholarship.org/content/qt9qv3x483/qt9qv3x483_noSplash_14462970dec59270c3a1dc7d725b12cd.pdf"
e_nerve=ev("nerve_trial", "Graves et al.2019: Intraoperative intercostal nerve cryoablation during the Nuss procedure reduces length of stay and opioid requirement:A randomized clinical trial",NERVE,
    "cryoprobe to the intercostal nerves for 2 min to achieve a temperature of −60 °C", "The primary randomized study uses an AtriCure cryosurgical system for intercostal nerve cryoanalgesia under thoracoscopic visualization. It reports one2min cycle at-60 C for each targeted nerve; this describes the cryoprobe procedure,not uniform measured nerve-tissue temperature.","Cryoprobe-60 C for2min;onecycle;thoracoscopicvisualization", "Methods1.4,printed page4", "experimental_observation")
nerve=experiment("health_intercostal_nerve_cryoneurolysis", "healthcare_and_medicine", "Intercostal-nerve cryoneurolysis for postoperative analgesia research", "Study nerve cryoanalgesia", "Graves et al.2019,randomized Nuss-procedure clinical trial",NERVE,e_nerve,
    [present("process.nerve_cryoneurolysis",e_nerve,"The procedure requires a nerve-contact cryoprobe; a cold tissue bath or freezing carrier is not equivalent."),point("probe.temperature.range","213.15",e_nerve,"The selected study reports-60 C cryoprobe operation; this is never mapped to console ambient or uniform tissue temperature."),point("probe.freeze_duration.range","120",e_nerve,"The reported application lasts2min=120s.","s"),present("module.direct_visualization",e_nerve,"The primary study performs the procedure under thoracoscopic visualization; a console alone does not establish this installed chain.")],
    ["N2O cryosurgical console", "long fine cryoprobe with target-contact tip", "rib and intercostal nerve model", "thoracoscopic visualization,unverified for candidate"], "thin yellow intercostal nerve following the underside of a curved pale rib",
    ["Identify the study's nerve target under the required visualization.","Illustrate the published probe-temperature and timing condition.","Review the trial's measured recovery and analgesia outcomes from the source; generate no synthetic outcome."],
    ["This scientific equipment profile is not a clinical eligibility check or instructions for performing surgery.","The study predates the consulted cryoSPHERE IFU; the selected probe is a documented modern candidate,not falsely identified as the exact historical probe.","Typical probe temperature does not establish tissue temperature or a nerve's response;direct visualization remains UNKNOWN for the bare candidate configuration."],["AtriCure cryosurgical system;thoracoscopy;exact historical probe model not established here"],
    "Cryogenic nerve-conduction intervention research is distinct from oocyte vitrification and the in-vitro cancer-cell bath experiment.","nerve_cryoanalgesia")

# Every primary industry has its own three distinct profiles. Additional scientifically
# valid cross-industry membership is listed separately,without renamed duplicates.
industries = [
    {"id":"biology_and_biotechnology","experiment_ids":["bio_cryosection_frozen_tissue","bio_cryo_fluorescence_vitrified",pbmc],"configuration_ids":["leica_cm1950_genA_vacuum_motor_objcool","linkam_thms600_lnp96_t96",planer],"shortfalls":[]},
    {"id":"chemistry_and_pharmaceuticals","experiment_ids":["chem_low_temperature_raman","chem_phase_transition_pom","chem_temperature_dependent_photoluminescence"],"configuration_ids":["linkam_thms600_lnp96_t96","oxford_optistatdry_blv","lakeshore_ccs_100"],"shortfalls":[]},
    {"id":"healthcare_and_medicine","experiment_ids":[nerve,vit,tumor],"configuration_ids":[cryoice,cryotop,bath],"shortfalls":["The nerve-probe candidate does not establish an installed thoracoscopic visualization chain; the in-vitro freezing experiment's custom aluminum block and independent logger are not established in the candidate bath configuration. Preserve UNKNOWN."]},
    {"id":"food_and_agriculture","experiment_ids":[gummy,icecream,straw],"configuration_ids":[mm400,lts,fz],"shortfalls":["The documented -50 C FreeZone candidate does not satisfy the strawberry procedure's -67 C collector requirement; no fictitious compatible unit is substituted."]},
    {"id":"environmental_science","experiment_ids":[soil,inp,voc],"configuration_ids":[cryomill,lts,entech],"shortfalls":["LTS120 lacks documented installed dewpoint conditioning and a guaranteed 1 C/min ramp at -40 C in the consulted specification; the complete published LTS350 assembly is not silently assumed.","The soil method is manufacturer-documented sample preparation,not a matrix-specific pollutant recovery study."]},
    {"id":"geology_and_oceanography","experiment_ids":[inclusions,perma,sediment],"configuration_ids":[thmsg,espec,fz],"shortfalls":["The ESPEC chamber has no documented installed complex-resistivity electrodes/electronics; temperature cycling does not establish the measurement chain."]},
    {"id":"manufacturing_and_industrial_processing","experiment_ids":[steel,rubber,rubberdsc],"configuration_ids":[messer,cryomill,dsc],"shortfalls":["Messer loaded maximum hold duration is not specified; Linkam installed dynamic nitrogen purge is not established. These mandatory conditions remain UNKNOWN."]},
]

# Add manufacturer confirmation without silently installing the pump/accessories
# mentioned by the manufacturer. The CSD installed assembly remains the candidate.
FZSPEC="https://documents.thermofisher.com/TFS-Assets/ANZ/brochures/labconco-console-freeze-dryers.pdf"
e_fzspec=ev("freezone_manufacturer", "Labconco FreeZone6,12and18Liter Console Freeze Dryers manufacturer specifications",FZSPEC,
    "system to cool collector to -50° C", "Labconco specifies -50 C and -84 C collector variants and separately required vacuum pump/drying accessory. The manufacturer's requirement for a pump ultimate vacuum is not an achieved system-vacuum specification.","Collector-50 C or-84 C;vacuum pump/drying accessory notincluded", "PDF pages1–2,Specification and Ordering Information")
fz_file=ROOT/"data/cryostats/expansion_b_labconco_freezone6.json"
fz_doc=json.loads(fz_file.read_text(encoding="utf-8"))
fz_doc["documents"].append({"id":"expb_doc_freezone_manufacturer","url":FZSPEC,"title":"Labconco manufacturer specification,hosted by ThermoFisher","accessed":DAY})
for c in fz_doc["configurations"][0]["capabilities"]:
    if c["key"]=="condenser.temperature.min":c["evidence_ids"].append(e_fzspec)
write("data/cryostats/expansion_b_labconco_freezone6.json",fz_doc)

DSCLNP="https://www.linkam.co.uk/dsc600"
e_dsclnp=ev("dsc600_lnp", "Linkam Optical DSC600 system description",DSCLNP,
    "The optional LNP96 is required to achieve temperatures down to < -195°C.", "The manufacturer explicitly requires optional LNP96 cooling to reach the low-temperature range; the selected catalog configuration includes this option.","DSC600+LNP96 for<-195 C", "System description,final paragraph")
dsc_file=ROOT/"data/cryostats/expansion_b_linkam_dsc600.json"
dsc_doc=json.loads(dsc_file.read_text(encoding="utf-8"))
dsc_doc["documents"].append({"id":"expb_doc_dsc600_lnp","url":DSCLNP,"title":"OpticalDSC600 system and LNP96 cooling requirement","accessed":DAY})
dsc_doc["configurations"][0]["configuration_basis"]="DSC600 stage,T96 controller,and documented optionalLNP96 explicitly included to reach the cryogenic range. This is a catalog configuration,not a claim of a lab installation."
write("data/cryostats/expansion_b_linkam_dsc600.json",dsc_doc)
equipment_scenes[dsc]["installed_options"]=dsc_doc["configurations"][0]["configuration_basis"]

existing_scene_details={
    "bio_cryosection_frozen_tissue":("frozen_tissue_sectioning",["clinical cryostat microtome","specimen chuck and blade","glass slide receiving a thin section"],"irregular tissue embedded in a white OCT block,with a curling thin ribbon",["Equilibrate the frozen tissue block at the confirmed chamber/head settings.","Advance the microtome and cut the selected15um tissue section.","Collect the section on a slide for the reported microscopy workflow."]),
    "bio_cryo_fluorescence_vitrified":("cryo_fluorescence_grid",["optical cryogenic microscope stage","vitrified support grid","objective and fluorescence excitation/emission paths"],"small perforated circular microscopy grid containing vitrified cellular material",["Transfer the vitrified support grid while preserving its cryogenic state.","Keep the specimen below the confirmed devitrification threshold and illuminate it.","Collect actual fluorescence images and correlate them with the intended microscopy workflow."]),
    "chem_low_temperature_raman":("raman_solution_freezing",["LN2 optical stage","15mm quartz crucible with aqueous sample","Raman excitation and collection objective"],"round transparent quartz crucible containing a freezing aqueous lithium-chloride sample",["Load the paper's aqueous sample into the quartz crucible.","Apply the confirmed freezing/melting temperature program.","Collect real Raman spectra through the optical window."]),
    "chem_phase_transition_pom":("wax_polarized_microscopy",["optical temperature stage","synthetic wax specimen","crossed polarizers and microscope camera"],"thin wax specimen with branching crystalline domains visible under crossed polarizers",["Mount the synthetic wax specimen for polarized microscopy.","Apply the reported203–393K temperature window.","Observe actual crystal-growth morphology without generating synthetic measurements."]),
    "chem_temperature_dependent_photoluminescence":("pedot_photoluminescence",["vacuum optical cryostat","cold finger supporting fused-silica substrate","excitation beam and luminescence collection optics"],"square25x25x2mm fused-silica substrate carrying a thin PEDOT:PSS film",["Mount and evacuate the optical sample space.","Apply the confirmed4–300K temperature program.","Measure the actual temperature-dependent photoluminescence spectrum."]),
}
for exp_id,(archetype,apparatus,sample,steps) in existing_scene_details.items():
    doc=json.loads((ROOT/("data/experiments/"+exp_id+".json")).read_text(encoding="utf-8"))
    scenes[exp_id]={"archetype":archetype,"apparatus":apparatus,"sample_shape":sample,"distinctive_sample_shape":sample,"steps":steps,
                    "source_urls":[s["url"] for s in doc["sources"] if s.get("url")],"scope":"Descriptor for an existing sourced profile; no experiment data or verification semantics changed."}

# Existing vocabulary entries keep their canonical shape/unit and provenance.
existing_keys=json.loads((ROOT/"data/capability_vocabulary.json").read_text(encoding="utf-8"))["keys"]
vocabulary={k:v for k,v in vocabulary.items() if k not in existing_keys}

write("data/evidence/expansion_b.json", evidence)
write("research/expansion/b_manifest.json", {"group":"b","accessed":DAY,"industries":industries,"vocabulary":vocabulary,
      "experiment_scenes":scenes,"equipment_scenes":equipment_scenes,
      "cross_industry_membership":[{"experiment_id":"bio_cryosection_frozen_tissue","industry_ids":["biology_and_biotechnology","healthcare_and_medicine"],"reason":"The same frozen-tissue sectioning operation supports biological research and diagnostic histology. Reuse avoids a renamed duplicate."}],
      "verification_semantics":"No engine changes. Per-function flags are open-world: omitted flags are UNKNOWN,never a fabricated documented absence. Every matrix verdict must come from existing Lean,not these scene descriptors.",
      "notes":["Three configurations per industry are distinct real instruments relevant to at least one procedure. Cross pairings deliberately include missing capabilities and failures; membership is not suitability.","16newprofiles+5existing unique profiles cover21distinctindustry/profile slots. Additional cross-industry relevance is optional and does not inflate this count.","No new coupled-physics law was introduced. Phenomena not modeled by existing backend are reported as scope limitations,not simulated proofs."]})
print(json.dumps({"new_experiments":len([k for k in scenes if k.startswith('expansion_b_')]),"scene_descriptors":len(scenes),"new_configurations":len(equipment_scenes),"evidence":len(evidence),"proposed_keys":len(vocabulary),"industry_slots":sum(len(x['experiment_ids']) for x in industries)}))
