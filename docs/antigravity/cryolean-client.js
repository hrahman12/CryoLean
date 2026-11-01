// cryolean-client.js — drop-in client for the Antigravity frontend.
// Talks to the local Python backend through PyWebView (no web server):
//     python -m cryolean.desktop --frontend <path-to-antigravity-build>/index.html
// Every call resolves to the backend's `data` or throws a CryoLeanError (error.code, error.message).
// Verdicts ONLY come from the Lean checker in the backend; never compute or override one here.

export const VERDICT = Object.freeze({
  MET: "REQUIREMENTS_MET",              // "Requirements met"
  NOT_MET: "DOES_NOT_MEET_REQUIREMENTS", // "Doesn't meet requirements"
  NEED_INFO: "NEED_MORE_INFORMATION",    // "Need more information"
});

export class CryoLeanError extends Error {
  constructor(error) {
    super(error?.message ?? "CryoLean backend error");
    this.code = error?.code ?? "unknown"; // lean_unavailable | not_found | invalid_input | edit_refused | stale_result | research_refused | lean_rejected_input | internal_error
    this.verdict = null;                  // errors never carry a verdict
  }
}

/** Resolves when PyWebView has injected window.pywebview.api. */
export function ready() {
  if (window.pywebview?.api) return Promise.resolve();
  return new Promise((resolve) => window.addEventListener("pywebviewready", () => resolve(), { once: true }));
}

async function call(method, ...args) {
  await ready();
  const env = await window.pywebview.api[method](...args);
  if (!env || env.ok !== true) throw new CryoLeanError(env?.error);
  return env.data;
}

// ---------------------------------------------------------------- industries & experiments
export const listIndustries = (query = null) => call("list_industries", query);
export const registerIndustry = (name, description = "", industryId = null) => call("register_industry", name, description, industryId);
export const listExperiments = (industry = null) => call("list_experiments", industry);
export const getExperimentRequirements = (experimentId) => call("get_experiment_requirements", experimentId);
/** AI: natural language -> closest prepared profiles (closed set). Always ask the user to confirm. */
export const matchExperiment = (text, topK = 3) => call("match_experiment", text, topK);
/** Unregistered experiment: returns NEED_MORE_INFORMATION + research plan (+ optional untrusted AI draft). */
export const researchNewExperiment = (description, industry = "unspecified", researchText = null) =>
  call("research_new_experiment", description, industry, researchText);
/** Submits an UNTRUSTED candidate; it cannot be verified until approveCandidate(id, reviewer). */
export const registerExperiment = (document, evidence = [], submittedBy = "user", requestId = null) =>
  call("register_experiment", document, evidence, submittedBy, requestId);
export const approveCandidate = (candidateId, reviewedBy) => call("approve_candidate", candidateId, reviewedBy);

// ---------------------------------------------------------------- equipment
export const listEquipment = (manufacturer = null, family = null) => call("list_equipment", manufacturer, family);
export const getEquipmentDetails = (equipmentOrConfigurationId) => call("get_equipment_details", equipmentOrConfigurationId);
/** status: "installed_documented" | "proposed" | "undocumented" */
export const registerModification = (configurationId, status, changes, description = "") =>
  call("register_modification", configurationId, status, changes, description);

// ---------------------------------------------------------------- verification
/**
 * Lean verdict for one exact configuration, then Z3 suggestions (each re-checked by Lean).
 * @param {string} experimentId
 * @param {string} configurationId
 * @param {{parameters?: object, requirementEdits?: object[], confirmed?: boolean, suggestions?: boolean}} opts
 *   parameters: { name: {value: "200", unit: "uA"} }   (exact decimal strings, never floats)
 *   confirmed:  must be true after the user reviewed the requirements, otherwise NEED_MORE_INFORMATION.
 */
export const checkCompatibility = (experimentId, configurationId, opts = {}) =>
  call("check_compatibility", experimentId, configurationId, opts.parameters ?? null, opts.requirementEdits ?? null,
       opts.confirmed ?? false, opts.extraModifications ?? null, opts.suggestions ?? true);
export const findCompatibleEquipment = (experimentId, opts = {}) =>
  call("find_compatible_equipment", experimentId, opts.parameters ?? null, opts.requirementEdits ?? null,
       opts.confirmed ?? true, opts.maxResults ?? 10, opts.includeHypotheticalOptions ?? true);
export const compareEquipment = (experimentId, configurationIds, opts = {}) =>
  call("compare_equipment", experimentId, configurationIds, opts.parameters ?? null, opts.requirementEdits ?? null, opts.confirmed ?? true);
/** Throws CryoLeanError(code "stale_result") if the catalog or inputs changed since the check. */
export const getVerificationDetails = (resultId) => call("get_verification_details", resultId);

// ---------------------------------------------------------------- sessions (switching cryostats)
export const startSession = (experimentId) => call("start_session", experimentId);
export const updateSession = (sessionId, { parameters = null, requirementEdits = null, confirmed = null } = {}) =>
  call("update_session", sessionId, parameters, requirementEdits, confirmed);
/** Switch machine: keeps the experiment, invalidates the previous result. */
export const selectEquipment = (sessionId, configurationId) => call("select_equipment", sessionId, configurationId);
export const checkSession = (sessionId) => call("check_session", sessionId);
export const getSessionResult = (sessionId) => call("get_session_result", sessionId);

// ---------------------------------------------------------------- status & coverage
export const getResearchCoverage = () => call("get_research_coverage");
export const getLeanStatus = () => call("get_lean_status");
export const getPhysicalProperties = () => call("get_physical_properties");
/** Theorem names, their audited axioms, the Lean source hash and the forensics summary. */
export const getVerificationCard = () => call("get_verification_card");

// ---------------------------------------------------------------- campaign scheduling (Z3 proposes, Lean decides)
/**
 * Pack experiments into one cooldown of a cryostat.
 * runLength / durations[experimentId]: { value: 48, unit: "h" }   (units: s, min, h)
 * Returns { feasible_experiments, excluded_experiments (with Lean verdict + reason), cooldown, timeline,
 *           z3: { status: "sat"|"unsat"|..., makespan, conflicting_experiments, explanation },
 *           lean: { valid, reasons, slots, theorems }, schedule_ok }
 * Only `schedule_ok` (= Lean validSchedule) may be shown as "Schedule OK".
 */
export const scheduleCampaign = (configurationId, experimentIds, runLength, durations, { parameters = null, confirmed = false } = {}) =>
  call("schedule_campaign", configurationId, experimentIds, runLength, durations, parameters, confirmed);
export const checkSchedule = (leanInputDocument) => call("check_schedule", leanInputDocument);

// ---------------------------------------------------------------- Gatekeeper + Registry (new rules / new sheets)
/** Proposed Lean code. Admitted only if it compiles, has no sorry/axiom/native_decide, and uses standard axioms only. */
export const submitLeanRule = (name, source, proposer = "user") => call("submit_lean_rule", name, source, proposer);
export const listRegistry = () => call("list_registry");

// ---------------------------------------------------------------- Lanyon certified simulations
export const getLanyonStatus = () => call("get_lanyon_status");
/** Sends the prompt to Lanyon's servers (ask the user first). Long-running: show progress UI. */
export const runLanyonModel = (problem, instructions = null, name = null) => call("run_lanyon_model", problem, instructions, name);
export const importLanyonSession = (runDir) => call("import_lanyon_session", runDir);

// ---------------------------------------------------------------- UI helpers (display only)
export const HEADLINE = {
  REQUIREMENTS_MET: "Requirements met",
  DOES_NOT_MEET_REQUIREMENTS: "Doesn't meet requirements",
  NEED_MORE_INFORMATION: "Need more information",
};

/** Plain-language question for a check row (the "See checks" view). */
export function checkQuestion(check) {
  const k = (check.keys?.[0] ?? check.model ?? "");
  if (check.kind === "coupled") return check.name;
  if (k.startsWith("temperature") || k.startsWith("cooling_power")) return "Is it cold enough?";
  if (k.startsWith("sample")) return "Does the sample fit?";
  if (k.startsWith("magnetic_field")) return "Is the magnetic field right?";
  if (k.startsWith("optical")) return "Can you see the sample?";
  if (k.startsWith("electrical")) return "Does it have the connections?";
  if (k.startsWith("module")) return "Is the measurement module installed?";
  if (k.startsWith("vacuum") || k.startsWith("pressure") || k.startsWith("purge")) return "Can it keep frost and air away?";
  return k;
}

/** The only place a "verified" badge may appear: a Lean REQUIREMENTS_MET on this exact result. */
export function isVerified(result) {
  return result?.verdict === VERDICT.MET && result?.verification?.concrete_evaluation?.verified_by_lean === true;
}

/** The verdict card: verdict · reason · theorem names · axioms · source hash. Z3 output is a hint, never a verdict. */
export function verdictCard(result) {
  const c = result?.verdict_card;
  if (!c) return null;
  return {
    verdict: c.verdict,
    headline: HEADLINE[c.verdict],
    reason: c.reason,
    theorems: c.theorems,
    axioms: c.axioms,
    axiomsStandardOnly: c.axioms_standard_only,
    sourceHash: c.source_hash?.slice(0, 12),
    inputHash: c.lean_input_hash,
    note: c.z3_role,
  };
}
