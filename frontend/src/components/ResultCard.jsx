import { HEADLINE, isVerified, VERDICT } from "../services/cryolean-client-raw.js";
import { humanize, keysLabel, unitsForDim, paramLabel, shortModel } from "../lib/format.js";
import QuantityInput from "./QuantityInput.jsx";
import { paramDims, effectiveParams, cleanDesc } from "./ProfileReview.jsx";

const TONE = { [VERDICT.MET]: "met", [VERDICT.NOT_MET]: "not-met", [VERDICT.NEED_INFO]: "need-info" };

/** Plain next step per verdict, following the backend's own message. */
function nextStepText(result) {
  if (result.verdict === VERDICT.MET) return "View the checks or save the result.";
  if (result.verdict === VERDICT.NOT_MET) return "See the conflict and review another setup.";
  return humanize(result.next_step);
}

export default function ResultCard({ result, profile, appliedParams, appliedFix, configIndex, busy, onSeeChecks, onChangeCryostat, onReviewProfile, onConfirmAndCheck, onAnswerParam, onReviewFix, onSave }) {
  const verified = isVerified(result);
  const tone = TONE[result.verdict] || "need-info";
  const confirmed = result.experiment?.confirmed;
  const open = [...(result.checks || []), ...(result.coupled_checks || [])].filter((c) => c.mandatory && c.applicable && (c.outcome === "unknown" || c.outcome === "unsupported"));
  const dims = paramDims(profile);
  const params = effectiveParams(profile, appliedParams || {});
  const missingParams = params.filter((p) => p.value == null);
  const machineGaps = open.filter((c) => c.kind === "requirement");
  const coupledGaps = open.filter((c) => c.kind === "coupled");
  const fixes = (result.suggestions?.verified_fixes || []).filter((f) => f.verified === true && f.lean_verdict === VERDICT.MET);
  const relaxations = result.suggestions?.requirement_relaxations || [];

  return (
    <div className={`result-card ${tone}`} data-testid="result" data-verdict={result.verdict}>
      <div className="result-head">
        <span className="result-icon" aria-hidden>{tone === "met" ? "✓" : tone === "not-met" ? "✕" : "?"}</span>
        <h3 data-testid="result-headline">{HEADLINE[result.verdict]}</h3>
        {verified && <span className="verified-badge" title="Lean returned REQUIREMENTS_MET for this exact configuration and experiment" data-testid="verified-badge">Verified by Lean</span>}
      </div>
      <p className="result-message" data-testid="result-message">{humanize(result.user_message)}</p>
      <p className="result-next">{nextStepText(result)}</p>

      {appliedFix && (
        <p className={`fix-note ${appliedFix.sameAsVerified ? "ok" : ""}`} data-testid="fix-note">
          {appliedFix.sameAsVerified ? "Applied the suggested change. Lean re-checked exactly the setup it had verified." : "Applied the suggested change and checked it again."}
        </p>
      )}

      {/* ---------- Need more information: specific questions ---------- */}
      {result.verdict === VERDICT.NEED_INFO && (
        <div className="questions" data-testid="questions">
          {!confirmed && (
            <div className="question">
              <p>Have you reviewed your experiment’s requirements?</p>
              <div className="row">
                <button className="btn primary small" disabled={busy} onClick={onConfirmAndCheck} data-testid="confirm-and-check">Confirm and check again</button>
                <button className="btn secondary small" onClick={onReviewProfile}>Review requirements</button>
              </div>
            </div>
          )}
          {confirmed && missingParams.map((p) => (
            <div className="question" key={p.name} data-testid={`answer-${p.name}`}>
              <p>We need this before we can finish the check: {p.description ? cleanDesc(p.description).toLowerCase() : paramLabel(p.name)}.</p>
              <QuantityInput
                units={unitsForDim(dims[p.name])}
                integer={dims[p.name] === "1"}
                busy={busy}
                submitLabel="Confirm and check again"
                testId={`answer-${p.name}`}
                onSubmit={(v) => onAnswerParam(p.name, typeof v === "number" ? { value: String(v), unit: "count" } : v)}
              />
            </div>
          ))}
          {confirmed && machineGaps.length > 0 && (
            <div className="question" data-testid="machine-gaps">
              <p>This machine’s documentation doesn’t say:</p>
              <ul className="plain-list">
                {machineGaps.map((c, i) => <li key={i}>{keysLabel(c.keys)}{c.outcome === "unsupported" ? " (can’t be checked yet)" : ""}</li>)}
              </ul>
              <p className="hint">Missing information never counts as a pass. Try a cryostat that documents these values.</p>
              <button className="btn secondary small" onClick={onChangeCryostat}>Change cryostat</button>
            </div>
          )}
          {confirmed && coupledGaps.length > 0 && missingParams.length === 0 && (
            <div className="question">
              <p>These checks can’t be completed yet:</p>
              <ul className="plain-list">{coupledGaps.map((c) => <li key={c.id}>{c.name}: {humanize(c.explanation)}</li>)}</ul>
            </div>
          )}
        </div>
      )}

      {/* ---------- Other options: Lean-verified suggestions only ---------- */}
      {result.verdict !== VERDICT.MET && (fixes.length > 0 || relaxations.length > 0) && (
        <div className="options" data-testid="other-options">
          <h4>Other options</h4>
          <ul>
            {fixes.map((f) => (
              <li key={f.fix_id} className="option">
                <div>
                  {f.kind === "alternative_configuration" ? (
                    <>
                      <div className="opt-title">Try {configIndex[f.configuration_id] ? `${configIndex[f.configuration_id].equipment.manufacturer} ${shortModel(configIndex[f.configuration_id].equipment.model)}` : f.name}</div>
                      <div className="opt-sub">{configIndex[f.configuration_id]?.configuration.name || f.name}</div>
                    </>
                  ) : (
                    <>
                      <div className="opt-title">{(f.changes || []).map((c) => `Change ${paramLabel(c.parameter)} from ${c.from} to ${c.to}`).join("; ")}</div>
                      <div className="opt-sub">Same cryostat · changes a value in your plan</div>
                    </>
                  )}
                  <div className="opt-verified">Lean checked this option: requirements met</div>
                </div>
                <button className="btn secondary small" onClick={() => onReviewFix(f)} data-testid={`review-${f.fix_id}`}>Review</button>
              </li>
            ))}
            {relaxations.map((r, i) => (
              <li key={`rel${i}`} className="option relax">
                <div>
                  <div className="opt-title">{r.description || r.explanation || "Relax a requirement"}</div>
                  <div className="opt-warn">This would change your experiment’s requirements. Only you can decide that; edit the requirement yourself if it is right.</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
      {result.verdict === VERDICT.NOT_MET && fixes.length === 0 && (
        <div className="row"><button className="btn secondary small" onClick={onChangeCryostat} data-testid="try-another">Try another cryostat</button></div>
      )}

      <div className="result-actions">
        <button className="link" onClick={onSeeChecks} data-testid="see-checks">See checks</button>
        <span className="save">
          Save report:
          <button className="link" onClick={() => onSave("pdf")} data-testid="save-pdf">PDF</button>
          <button className="link" onClick={() => onSave("json")} data-testid="save-json">JSON</button>
        </span>
      </div>
    </div>
  );
}

