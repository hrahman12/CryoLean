// Display helpers only. Nothing here decides or changes a verdict; values the user types are sent to the
// backend exactly as typed ({value: "<int or exact decimal>", unit}); conversion and checking happen there.
import vocabulary from "../../../data/capability_vocabulary.json";
import { checkQuestion as clientCheckQuestion } from "../services/cryolean-client-raw.js";

// ---------------------------------------------------------------- units
// Groups of interchangeable units (symbols exactly as the backend accepts them) with their size in SI.
export const UNIT_GROUPS = {
  temperature: { K: 1, mK: 1e-3, uK: 1e-6 },
  length: { m: 1, cm: 1e-2, mm: 1e-3, um: 1e-6, nm: 1e-9, inch: 0.0254 },
  mass: { kg: 1, g: 1e-3, mg: 1e-6, ug: 1e-9 },
  time: { h: 3600, min: 60, s: 1, ms: 1e-3 },
  current: { mA: 1e-3, uA: 1e-6, A: 1, nA: 1e-9, pA: 1e-12 },
  power: { W: 1, mW: 1e-3, uW: 1e-6, nW: 1e-9 },
  energy: { J: 1 },
  field: { T: 1, mT: 1e-3, uT: 1e-6, Oe: 1e-4 },
  field_rate: { T_per_s: 1, mT_per_s: 1e-3, uT_per_s: 1e-6, Oe_per_s: 1e-4 },
  pressure: { Pa: 1, mbar: 100, Torr: 133.322, uPa: 1e-6 },
  frequency: { GHz: 1e9, MHz: 1e6, kHz: 1e3, Hz: 1 },
  voltage: { V: 1, mV: 1e-3, uV: 1e-6, nV: 1e-9 },
  resistance: { Ohm: 1, kOhm: 1e3, MOhm: 1e6, mOhm: 1e-3, uOhm: 1e-6 },
  temperature_rate: { K_per_s: 1, K_per_min: 1 / 60, mK_per_min: 1e-3 / 60 },
  count: { count: 1 },
  fraction: { percent: 1e-2, ppm: 1e-6 },
  angle: { deg: 1, mdeg: 1e-3 },
  aperture: { NA: 1 },
  f_number: { f_number: 1 },
  volume: { m3: 1, L: 1e-3 },
  flow: { L_per_min: 1 },
  leak: { Pa_m3_per_s: 1, mbar_L_per_s: 0.1 },
  conductivity: { W_per_m_K: 1 },
  thermal_resistance: { K_per_W: 1 },
};

const UNIT_TO_GROUP = Object.fromEntries(
  Object.entries(UNIT_GROUPS).flatMap(([g, us]) => Object.keys(us).map((u) => [u, g])),
);

/** Units a value may be entered in, given the unit it is stored in. */
export function compatibleUnits(unit) {
  const g = UNIT_TO_GROUP[unit];
  return g ? Object.keys(UNIT_GROUPS[g]) : [unit];
}

/** Units for a coupled-model parameter dimension ("K", "W", "1", "m", ...). */
export function unitsForDim(dim) {
  const map = { K: "temperature", W: "power", 1: "count", m: "length", s: "time", A: "current", Ohm: "resistance", T: "field", V: "voltage", Pa: "pressure", Hz: "frequency" };
  const g = map[dim];
  return g ? Object.keys(UNIT_GROUPS[g]) : ["count"];
}

const SYMBOL = {
  uK: "µK", um: "µm", ug: "µg", uA: "µA", uW: "µW", uT: "µT", uPa: "µPa", uV: "µV",
  Ohm: "Ω", kOhm: "kΩ", MOhm: "MΩ", mOhm: "mΩ", uOhm: "µΩ",
  T_per_s: "T/s", mT_per_s: "mT/s", uT_per_s: "µT/s", Oe_per_s: "Oe/s",
  K_per_s: "K/s", K_per_min: "K/min", mK_per_min: "mK/min",
  count: "", percent: "%", ppm: "ppm", deg: "°", mdeg: "m°", inch: "in", m3: "m³",
  L_per_min: "L/min", Pa_m3_per_s: "Pa·m³/s", mbar_L_per_s: "mbar·L/s", W_per_m_K: "W/(m·K)", K_per_W: "K/W",
  f_number: "f/", NA: "NA",
};
export const unitSymbol = (u) => (u in SYMBOL ? SYMBOL[u] : u);

/** Number from an int, decimal string or "a/b" string. Display only. */
export function toNumber(v) {
  if (typeof v === "number") return v;
  if (typeof v !== "string") return NaN;
  const m = v.match(/^\s*(-?\d+(?:\.\d+)?)\s*\/\s*(\d+)\s*$/);
  if (m) return Number(m[1]) / Number(m[2]);
  return Number(v);
}

export function fmtNumber(n, digits = 4) {
  if (!Number.isFinite(n)) return "?";
  if (n === 0) return "0";
  const a = Math.abs(n);
  if (a >= 1e6 || a < 1e-4) return n.toExponential(2).replace(/\.?0+e/, "e");
  const s = Number(n.toPrecision(Math.max(digits, Math.ceil(Math.log10(a)) + 1)));
  return s.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

/** "253150 mK" -> "253.15 K (−20 °C)"; "12000 mT" -> "12 T"; picks a readable unit of the same kind. */
export function fmtQuantity(q) {
  if (q == null) return "not given";
  if (typeof q === "string") return q;
  if (typeof q !== "object" || !("value" in q)) return String(q);
  const { value, unit } = q;
  const n = toNumber(value);
  if (!Number.isFinite(n)) return `${value} ${unitSymbol(unit)}`.trim();
  const g = UNIT_TO_GROUP[unit];
  if (!g || ["count", "fraction", "angle", "aperture", "f_number", "flow", "leak", "conductivity", "thermal_resistance", "energy"].includes(g)) {
    if (unit === "f_number") return `f/${fmtNumber(n)}`;
    if (unit === "NA") return `NA ${fmtNumber(n)}`;
    return `${fmtNumber(n)}${unit === "percent" ? "" : " "}${unitSymbol(unit)}`.trim();
  }
  const units = UNIT_GROUPS[g];
  const si = n * units[unit];
  const ordered = Object.entries(units).filter(([u]) => !["Oe", "Oe_per_s", "inch", "Torr", "mbar"].includes(u)).sort((a, b) => b[1] - a[1]);
  let best = unit;
  if (g !== "time" && g !== "pressure" && si !== 0) {
    for (const [u, s] of ordered) {
      if (Math.abs(si) >= s) { best = u; break; }
      best = u;
    }
  }
  const shown = `${fmtNumber(si / units[best])} ${unitSymbol(best)}`;
  if (g === "temperature" && si >= 150 && si <= 700) {
    const c = si - 273.15;
    return `${shown} (${fmtNumber(Math.round(c * 100) / 100)} °C)`.replace("-", "−");
  }
  return shown;
}

/** Exact decimal check for user input: integers or decimals, never exponent notation. */
export const isExactDecimal = (s) => /^-?\d+(\.\d+)?$/.test(String(s).trim());

// ---------------------------------------------------------------- requirement keys
const VOCAB = vocabulary.keys || {};

function sentenceCase(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

/** Plain label for a capability key, from the vocabulary description. */
export function keyLabel(key) {
  if (!key) return "";
  const d = VOCAB[key]?.description;
  if (d) {
    const t = d.replace(/^(documented|installed|measured)\s+/i, "").replace(/\s*\((sectioning cryostats|[^)]*only)\)\s*$/i, "");
    return sentenceCase(t);
  }
  return sentenceCase(key.replace(/\.(max|min)$/, (m) => (m === ".max" ? " (maximum)" : " (minimum)")).replace(/[._]/g, " "));
}

export const keysLabel = (keys) => (keys || []).map(keyLabel).join(" or ");

/** Replace raw keys quoted in backend sentences ('magnetic_field.max') with their plain label. */
export function humanize(text) {
  if (!text) return text;
  return text.replace(/'([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)'/g, (_m, k) => {
    const l = keyLabel(k);
    return l ? `“${l.charAt(0).toLowerCase()}${l.slice(1)}”` : k;
  });
}

const PARAM_WORDS = { operating_temperature: "operating temperature", n_flux_lines: "number of flux lines", n_drive_lines: "number of drive lines", n_output_lines: "number of output lines" };
export const paramLabel = (name) => PARAM_WORDS[name] || (name || "").replace(/_/g, " ");

/** Plain-language rendering of a requirement's constraint, before any check has run. */
export function constraintText(c) {
  if (!c) return "";
  switch (c.kind) {
    case "at_most": return `${fmtQuantity(c.q)} or lower`;
    case "at_least": return `at least ${fmtQuantity(c.q)}`;
    case "point_within": return `must reach ${fmtQuantity(c.q)}`;
    case "range_within": return `must cover ${fmtQuantity(c.lo)} to ${fmtQuantity(c.hi)}`;
    case "range": return `between ${fmtQuantity(c.lo)} and ${fmtQuantity(c.hi)}`;
    case "present": return "must be available";
    case "absent": return "must not be present";
    case "flag_is": return c.b ? "must be yes" : "must be no";
    case "count_at_least": return `at least ${c.n}`;
    case "count_equals": return `exactly ${c.n}`;
    case "enum_in": return `one of: ${(c.values || c.xs || []).map((x) => String(x).replace(/_/g, " ")).join(", ")}`;
    case "set_contains": return `must include ${(c.needed || []).map((x) => String(x).replace(/_/g, " ")).join(", ")}`;
    default: return c.kind.replace(/_/g, " ");
  }
}

export function conditionText(cond) {
  if (!cond) return "";
  if (cond.kind === "param_at_most") return `when the ${paramLabel(cond.name)} is ${fmtQuantity(cond.q)} or lower`;
  if (cond.kind === "param_at_least") return `when the ${paramLabel(cond.name)} is at least ${fmtQuantity(cond.q)}`;
  if (cond.kind === "cap_flag") return `when “${keyLabel(cond.key).toLowerCase()}” is ${cond.b ? "yes" : "no"}`;
  return cond.kind;
}

/** Which parts of a constraint the user may edit, as [field, label]. */
export function editableFields(c) {
  if (!c) return [];
  if (["at_most", "at_least", "point_within"].includes(c.kind)) return [["q", "Value"]];
  if (["range_within", "range"].includes(c.kind)) return [["lo", "From"], ["hi", "To"]];
  if (["count_at_least", "count_equals"].includes(c.kind)) return [["n", "Number"]];
  return [];
}

// ---------------------------------------------------------------- checks
const CATEGORY = [
  [/^(temperature|cooling_power|thermal|cooldown\.temperature)/, "Is it cold enough?"],
  [/^sample/, "Does the sample fit?"],
  [/^magnetic_field/, "Is the magnetic field right?"],
  [/^optical/, "Can you see the sample?"],
  [/^(electrical|wiring|rf|connection)/, "Does it have the connections?"],
  [/^(module|accessory|option)/, "Is the needed equipment installed?"],
  [/^(vacuum|pressure|purge|humidity|atmosphere)/, "Can it keep frost and air away?"],
  [/^(time|cooldown|ramp|rate|hold)/, "Is it fast and steady enough?"],
  [/^(cryogen|gas|fluid|liquid)/, "Does it use the right cryogen or gas?"],
];

/** Plain question for a check row. Uses the canonical client first, then a broader fallback. */
export function checkQuestion(check) {
  if (check.kind === "coupled") return check.name;
  const q = clientCheckQuestion(check);
  if (q && q.endsWith("?")) return q;
  const k = check.keys?.[0] || "";
  for (const [re, text] of CATEGORY) if (re.test(k)) return text;
  return `Does it have the right ${keysLabel(check.keys).toLowerCase()}?`;
}

export const OUTCOME = {
  pass: { label: "Yes", tone: "pass", icon: "✓" },
  fail: { label: "No", tone: "fail", icon: "✕" },
  unknown: { label: "Not documented", tone: "info", icon: "?" },
  unsupported: { label: "Can’t be checked yet", tone: "info", icon: "?" },
  not_applicable: { label: "Doesn’t apply", tone: "muted", icon: "–" },
};

export const EVIDENCE_KIND = {
  manufacturer_specification: "Manufacturer specification",
  experimental_observation: "Published measurement",
  reference_data: "Reference data",
  user_entered: "Entered by you",
  certified_simulation: "Certified simulation",
  inferred_estimate: "Estimate (not trusted)",
  unknown: "Unknown",
};

export function industryShortName(name) {
  return (name || "").replace(/ and /g, " & ");
}

/** Model name without the long parenthetical notes the catalog keeps for provenance. */
export function shortModel(model) {
  return (model || "").replace(/\s*\(.*?\)\s*/g, " ").replace(/\s+/g, " ").trim();
}
