import { useEffect, useState } from "react";
import { HEADLINE, verdictCard } from "../services/cryolean-client-raw.js";
import { checkQuestion, EVIDENCE_KIND, humanize, keysLabel, OUTCOME, paramLabel } from "../lib/format.js";

export default function ChecksDrawer({ result, machineName, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const all = [...(result.checks || []), ...(result.coupled_checks || [])];
  const required = all.filter((c) => c.mandatory && c.applicable);
  const optional = all.filter((c) => !c.mandatory && c.applicable);
  const notApplicable = all.filter((c) => !c.applicable);
  const conflicts = result.suggestions?.conflicts?.conflicts || [];

  return (
    <div className="overlay drawer-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="Checks" data-testid="checks-drawer">
        <div className="modal-head">
          <div>
            <div className="muted small">{machineName} · {result.experiment?.plain_name}</div>
            <h2>{HEADLINE[result.verdict]}</h2>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close" data-testid="close-checks">✕</button>
        </div>

        <Section title={`Required checks (${required.length})`}>
          {required.map((c, i) => <CheckRow key={i} c={c} />)}
          {required.length === 0 && <p className="muted">This experiment has no applicable required checks.</p>}
        </Section>
        {optional.length > 0 && <Section title={`Nice to have (${optional.length})`} note="These never block the result.">{optional.map((c, i) => <CheckRow key={i} c={c} />)}</Section>}
        {notApplicable.length > 0 && <Section title={`Doesn’t apply here (${notApplicable.length})`} note="A condition for these checks is not met, so they don’t count.">{notApplicable.map((c, i) => <CheckRow key={i} c={c} />)}</Section>}

        {conflicts.length > 0 && (
          <Section title="Why it fails" note="Explanation found by the Z3 solver. It is a hint; the result above comes from the Lean checker.">
            {conflicts.map((k, i) => <p key={i} className="conflict">{humanize(k.explanation)}</p>)}
          </Section>
        )}

        <Section title="What information did the check use?">
          <dl className="facts">
            <dt>Cryostat</dt><dd>{machineName}<div className="muted small">{result.equipment?.configuration_name}</div></dd>
            <dt>Experiment</dt><dd>{result.experiment?.plain_name}<div className="muted small">{result.experiment?.name}</div></dd>
            <dt>Requirements confirmed</dt><dd>{result.experiment?.confirmed ? "Yes" : "No"}</dd>
            {(result.experiment?.parameters || []).filter((p) => p.display != null).length > 0 && (
              <>
                <dt>Values</dt>
                <dd>
                  <ul className="plain-list">
                    {result.experiment.parameters.filter((p) => p.display != null).map((p) => (
                      <li key={p.name}>{paramLabel(p.name)}: {p.display}{p.origin === "user_entered" ? " (entered by you)" : ""}</li>
                    ))}
                  </ul>
                </dd>
              </>
            )}
            <dt>Source data</dt>
            <dd>
              {result.verification?.source_data_validation?.ok ? "Well formed and traceable" : "Validation problems found"}
              {(result.verification?.source_data_validation?.warnings || []).length > 0 && <div className="muted small">{result.verification.source_data_validation.warnings.length} warning(s)</div>}
            </dd>
          </dl>
          {(result.references || []).length > 0 && (
            <>
              <h4 className="sub">References</h4>
              <ul className="plain-list refs">
                {result.references.map((r, i) => (
                  <li key={i}>
                    {r.url ? <a href={r.url} target="_blank" rel="noreferrer">{r.citation || r.title || r.url}</a> : r.citation || r.title}
                    {r.doi && <span className="muted"> · doi:{r.doi}</span>}
                  </li>
                ))}
              </ul>
            </>
          )}
          {(result.verification?.physical_model_assumptions || []).length > 0 && (
            <>
              <h4 className="sub">Physics models used</h4>
              {result.verification.physical_model_assumptions.map((m) => (
                <details key={m.model} className="model">
                  <summary>{m.model.replace(/_/g, " ")} <span className="muted small">({m.status})</span></summary>
                  {m.equation && <code className="eq">{m.equation}</code>}
                  <ul className="plain-list small">{(m.assumptions || []).map((a, i) => <li key={i}>{a}</li>)}</ul>
                </details>
              ))}
            </>
          )}
        </Section>

        <VerificationCard result={result} />
      </aside>
    </div>
  );
}

const stripNeeds = (s) => String(s ?? "").replace(/^needs\s+/i, "");

function Section({ title, note, children }) {
  return (
    <section className="drawer-section">
      <h3>{title}</h3>
      {note && <p className="muted small">{note}</p>}
      {children}
    </section>
  );
}

function CheckRow({ c }) {
  const [open, setOpen] = useState(false);
  const o = OUTCOME[c.outcome] || { label: c.outcome, tone: "muted", icon: "·" };
  const evidence = c.kind === "coupled" ? c.evidence || [] : c.capability_evidence || [];
  const reqEvidence = c.kind === "coupled" ? [] : c.requirement_evidence || [];
  return (
    <div className={`check ${o.tone}`} data-testid="check-row" data-outcome={c.outcome}>
      <button className="check-head" onClick={() => setOpen((x) => !x)} aria-expanded={open}>
        <span className={`outcome ${o.tone}`}>{o.icon}</span>
        <span className="check-q">
          {checkQuestion(c)}
          <span className="check-what">{c.kind === "coupled" ? "Combined physics check" : keysLabel(c.keys)}</span>
        </span>
        <span className={`outcome-label ${o.tone}`}>{o.label}</span>
      </button>
      <div className="check-summary">
        {c.kind === "coupled"
          ? <>Calculated {c.lhs?.display ?? "?"} vs limit {c.rhs?.display ?? "?"}</>
          : <>Required: {stripNeeds(c.required)} · This machine: {c.available}</>}
      </div>
      {open && (
        <div className="check-detail">
          <p>{humanize(c.explanation)}</p>
          {c.kind === "coupled" && (
            <>
              {c.equation && <code className="eq">{c.equation}</code>}
              {(c.assumptions || []).length > 0 && <ul className="plain-list small">{c.assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul>}
            </>
          )}
          {c.kind !== "coupled" && c.requirement_rationale && <p className="muted small">Why it’s required: {c.requirement_rationale}</p>}
          <Evidence title="Equipment information used" items={evidence} />
          <Evidence title="Where the requirement comes from" items={reqEvidence} />
        </div>
      )}
    </div>
  );
}

function Evidence({ title, items }) {
  if (!items?.length) return null;
  return (
    <div className="evidence">
      <h5>{title}</h5>
      {items.map((e) => (
        <figure key={e.id} className="ev">
          {e.quote && <blockquote>“{e.quote}”</blockquote>}
          <figcaption>
            {e.source_url ? <a href={e.source_url} target="_blank" rel="noreferrer">{e.document_title || e.id}</a> : e.document_title || e.id}
            {e.location && <span> · {e.location}</span>}
            <span className="ev-kind"> · {EVIDENCE_KIND[e.evidence_status] || e.evidence_status || "source"}</span>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

function VerificationCard({ result }) {
  const card = verdictCard(result);
  if (!card) return null;
  return (
    <details className="drawer-section vcard" data-testid="verification-card">
      <summary><h3>How this was verified</h3></summary>
      <p className="small">The result comes from the Lean 4 checker evaluated on this exact cryostat configuration and experiment. Z3 and AI suggestions are hints Lean re-checks; they never decide a result.</p>
      <dl className="facts">
        <dt>Result</dt><dd>{card.headline}</dd>
        <dt>Reason</dt><dd>{humanize(card.reason)}</dd>
        <dt>Theorems</dt><dd><code className="wrap">{(card.theorems || []).join(", ")}</code></dd>
        <dt>Axioms</dt>
        <dd>
          {card.axiomsStandardOnly ? "Standard axioms only" : "Non-standard axioms present"}
          {result.verdict_card?.axiom_audit === "stale" && <div className="warn small">The axiom audit is out of date with the Lean sources (run scripts/audit_axioms.py).</div>}
        </dd>
        <dt>Lean source</dt><dd><code>{card.sourceHash}</code></dd>
        <dt>Lean input</dt><dd><code>{card.inputHash}</code></dd>
        <dt>Fingerprint</dt><dd><code className="wrap">{result.fingerprint}</code></dd>
        <dt>Checked</dt><dd>{result.checked_at ? new Date(result.checked_at).toLocaleString() : ""}</dd>
      </dl>
      <p className="muted small">{card.note}</p>
    </details>
  );
}
