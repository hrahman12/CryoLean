// Picks which generated illustration represents a machine. Based only on the catalog's own words
// (family, model, description); purely visual.

const RULES = [
  ["dilution", /dilution|proteox|\bld\d{3}|\bxld|sorption (cryostat|insert)|he-3|adiabatic demagnet|\badr\b|1 k system/],
  ["plunge", /plunge|vitrobot|vitrification|cryotop|ethane/],
  ["microtome", /microtome|sectioning|cryostar|cryostat for frozen/],
  ["stage", /stage|thms|lts\d|linkam|microthermometry|heating\/freezing/],
  ["probe", /probe station|prober|wafer|hall (station|measurement)|fasthall|cpx|crx|probe-station/],
  ["magnet", /physical property|ppms|dynacool|teslatron|magnet|vti|squid|mpms|vsm|magnetometer|quantum hall|cfms|opticool/],
  ["optical", /optical|optistat|spectroscop|raman|montana|cryoadvance|attodry|window|snspd|photolumin/],
  ["dryer", /freeze dr|lyophil|freezone|epsilon|alpha 1|alpha 2/],
  ["freezer", /freezer|\bult\b|-86|-80 ?c|ultra-low|plasma|\bmdf\b|stirling ultracold|helmer|tsx|-150 c/],
  ["dewar", /dewar|shipper|storage|vapou?r[- ]phase|\bmve\b|heco|cryomed|cryofab|\blhe storage|liquid helium storage/],
  ["mill", /\bmill|grinder|cryomill|homogeni/],
  ["stage", /diffraction|xrd|ttk ?600|dilatometer/],
  ["cooler", /cryocooler|cold head|cryogenerator|gifford|\bgm\b|pulse-tube|cryotel|ricor|cryomech|al6\d0/],
  ["chamber", /chamber|thermal shock|thermal-vacuum|tvac|climatic|environmental|altitude|battery test|temperature forcing|thermal stream|cabinet/],
  ["bath", /bath|circulator|calibrat|comparison|fixed-point|triple point|charpy|brittleness|neslab|julabo|isotech|fluke/],
  ["cooler", /stirling/],
  ["facility", /facility|liquefier|refrigerator \(claude|claude cycle|wind tunnel|test stand|loop|collaboration|calorimeter|cryopump|kryotechnik|plant/],
];

export function artType(equipment) {
  if (!equipment) return "none";
  const text = `${equipment.family || ""} ${equipment.model || ""} ${equipment.manufacturer || ""}`.toLowerCase();
  for (const [type, re] of RULES) if (re.test(text)) return type;
  const desc = (equipment.description || "").toLowerCase();
  for (const [type, re] of RULES) if (re.test(desc)) return type;
  return "cryostat";
}

export const ART_LABEL = {
  dilution: "Dilution refrigerator",
  plunge: "Plunge freezer",
  microtome: "Cryostat microtome",
  stage: "Microscope cold stage",
  probe: "Cryogenic probe station",
  magnet: "Magnet measurement system",
  optical: "Optical cryostat",
  dryer: "Freeze dryer",
  freezer: "Low-temperature freezer",
  dewar: "Cryogenic dewar",
  mill: "Cryogenic mill",
  chamber: "Environmental test chamber",
  bath: "Temperature bath",
  cooler: "Cryocooler",
  facility: "Cryogenic test facility",
  cryostat: "Cryostat",
  none: "",
};
