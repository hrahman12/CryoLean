// "Save report": a short PDF and a JSON file built from the current, freshness-checked result.
// The report only restates what the backend returned; it adds no judgement of its own.
import { jsPDF } from "jspdf";
import { HEADLINE } from "../services/cryolean-client-raw.js";
import { checkQuestion, OUTCOME, humanize, keysLabel, paramLabel, EVIDENCE_KIND } from "./format.js";

function download(filename, blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

const stamp = (iso) => (iso || new Date().toISOString()).replace(/[:]/g, "-").replace(/\..*$/, "");
const baseName = (r) => `cryolean-${r.experiment?.id || "experiment"}-${r.equipment?.catalog_configuration_id || r.equipment?.configuration_id || "setup"}-${stamp(r.checked_at)}`;

// jsPDF's built-in fonts are Latin-1 only: map the few symbols the backend uses.
const latin = (s) => String(s ?? "")
  .replace(/[µμ]/g, "u").replace(/Ω/g, "Ohm").replace(/[≤]/g, "<=").replace(/[≥]/g, ">=").replace(/[−–—]/g, "-")
  .replace(/[“”]/g, '"').replace(/[‘’]/g, "'").replace(/…/g, "...").replace(/·/g, "*").replace(/✓/g, "yes").replace(/✕/g, "no")
  .replace(/[^\x00-\xFF]/g, "?");

export function buildReportJson(result, context) {
  return {
    report: "CryoLean compatibility report",
    generated_at: new Date().toISOString(),
    note: "Verdict computed by the Lean 4 checker in the CryoLean backend. The interface only displays it.",
    setup: { ...result.equipment, display_name: context.machineName },
    experiment: result.experiment,
    session: { parameters: context.parameters, requirement_edits: context.requirementEdits },
    verdict: result.verdict,
    headline: HEADLINE[result.verdict],
    user_message: result.user_message,
    next_step: result.next_step,
    checks: result.checks,
    coupled_checks: result.coupled_checks,
    missing_information: result.missing_information,
    failed_requirements: result.failed_requirements,
    references: result.references,
    verification: result.verification,
    verdict_card: result.verdict_card,
    fingerprint: result.fingerprint,
    result_id: result.result_id,
    checked_at: result.checked_at,
    lean_input: result.lean_input,
  };
}

export function saveJson(result, context) {
  const blob = new Blob([JSON.stringify(buildReportJson(result, context), null, 2)], { type: "application/json" });
  download(`${baseName(result)}.json`, blob);
}

export function savePdf(result, context) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const M = 48;
  let y = M;
  const need = (h) => { if (y + h > H - M) { doc.addPage(); y = M; } };
  const text = (s, { size = 10, bold = false, color = [30, 34, 40], gap = 4, indent = 0 } = {}) => {
    doc.setFont("helvetica", bold ? "bold" : "normal");
    doc.setFontSize(size);
    doc.setTextColor(...color);
    const lines = doc.splitTextToSize(latin(s), W - 2 * M - indent);
    for (const ln of lines) { need(size + 3); doc.text(ln, M + indent, y + size); y += size + 3; }
    y += gap;
  };
  const rule = () => { need(12); doc.setDrawColor(220); doc.line(M, y + 4, W - M, y + 4); y += 12; };

  text("CryoLean", { size: 20, bold: true, gap: 0 });
  text("Compatibility report", { size: 12, color: [110, 116, 125] });
  text(`Checked ${new Date(result.checked_at || Date.now()).toLocaleString()}`, { size: 9, color: [110, 116, 125] });
  rule();

  text("Setup", { size: 12, bold: true });
  text(`Machine: ${context.machineName}`);
  text(`Configuration: ${result.equipment?.configuration_name || result.equipment?.configuration_id}`);
  text(`Experiment: ${result.experiment?.plain_name || result.experiment?.name}`);
  if (result.experiment?.name && result.experiment.name !== result.experiment.plain_name) text(`(${result.experiment.name})`, { size: 9, color: [110, 116, 125] });
  text(`Requirements confirmed: ${result.experiment?.confirmed ? "yes" : "no"}`);
  const params = (result.experiment?.parameters || []).filter((p) => p.display != null);
  if (params.length) {
    text("Values used:", { bold: true, gap: 2 });
    params.forEach((p) => text(`- ${paramLabel(p.name)}: ${p.display}${p.origin === "user_entered" ? " (entered by you)" : ""}`, { indent: 10, gap: 1 }));
    y += 4;
  }
  rule();

  const colors = { REQUIREMENTS_MET: [20, 128, 74], DOES_NOT_MEET_REQUIREMENTS: [190, 40, 40], NEED_MORE_INFORMATION: [180, 110, 0] };
  text(HEADLINE[result.verdict], { size: 16, bold: true, color: colors[result.verdict] || [30, 34, 40] });
  text(humanize(result.user_message));
  text(`Next step: ${humanize(result.next_step)}`, { color: [80, 86, 95] });
  if (context.verified) text("Verified: Lean returned REQUIREMENTS_MET for this exact configuration and experiment.", { color: [20, 128, 74] });
  rule();

  text("Checks", { size: 12, bold: true });
  for (const c of [...(result.checks || []), ...(result.coupled_checks || [])]) {
    const o = OUTCOME[c.outcome] || { label: c.outcome };
    const what = c.kind === "coupled" ? c.name : keysLabel(c.keys);
    text(`${o.label.toUpperCase()}  ${checkQuestion(c)}  (${what})${c.mandatory ? "" : "  [optional]"}${c.applicable === false ? "  [not applicable]" : ""}`, { bold: true, gap: 1 });
    if (c.kind === "coupled") text(`${c.lhs?.display ?? ""} vs ${c.rhs?.display ?? ""}`, { indent: 10, gap: 1 });
    else text(`Required: ${String(c.required ?? "").replace(/^needs\s+/i, "")}; this machine: ${c.available}`, { indent: 10, gap: 1 });
    text(humanize(c.explanation), { indent: 10, size: 9, color: [90, 96, 105], gap: 1 });
    const ev = c.kind === "coupled" ? c.evidence || [] : c.capability_evidence || [];
    ev.slice(0, 2).forEach((e) => text(`Source: ${e.document_title || e.id}${e.location ? `, ${e.location}` : ""} (${EVIDENCE_KIND[e.evidence_status] || e.evidence_status || "source"})`, { indent: 10, size: 8, color: [110, 116, 125], gap: 1 }));
    y += 5;
  }
  if (result.missing_information?.length) {
    rule();
    text("Missing information", { size: 12, bold: true });
    result.missing_information.forEach((m) => text(`- ${m.includes(".") ? keysLabel(m.split("/")) : m}`, { indent: 10, gap: 1 }));
  }
  if (result.references?.length) {
    rule();
    text("References", { size: 12, bold: true });
    result.references.forEach((r) => text(`- ${r.citation || r.title || r.id}${r.doi ? `  doi:${r.doi}` : ""}${r.url ? `  ${r.url}` : ""}`, { indent: 10, size: 9, gap: 1 }));
  }
  rule();
  const card = result.verdict_card || {};
  text("Verification", { size: 12, bold: true });
  text(`Engine: ${result.verification?.concrete_evaluation?.engine || "Lean 4 checker"} (${result.verification?.concrete_evaluation?.lean_version || ""})`, { size: 9 });
  text(`Theorems: ${(card.theorems || []).join(", ")}`, { size: 9 });
  text(`Standard axioms only: ${card.axioms_standard_only ? "yes" : "no"} (audit ${card.axiom_audit || "unknown"})`, { size: 9 });
  text(`Lean source hash: ${card.source_hash || ""}`, { size: 8, color: [110, 116, 125] });
  text(`Lean input hash: ${card.lean_input_hash || ""}`, { size: 8, color: [110, 116, 125] });
  text(`Fingerprint: ${result.fingerprint || ""}`, { size: 8, color: [110, 116, 125] });
  text(`Result id: ${result.result_id || ""}`, { size: 8, color: [110, 116, 125] });
  text("This report checks a plan against the stated requirements and documented equipment data. It does not operate the machine or guarantee that the experiment will succeed.", { size: 8, color: [110, 116, 125] });

  download(`${baseName(result)}.pdf`, doc.output("blob"));
}

