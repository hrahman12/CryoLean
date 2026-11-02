import { CheckCircle2, CircleHelp, CircleX, ArrowRight, BookOpen, FileCheck2 } from 'lucide-react';
import { isVerified } from '../../services/cryolean-client';
import { getComponentForCheck } from '../../scene/mappings/constraint-to-component';
import type { Check, CoupledCheck, EvidenceRecord, VerificationResult, Quantity } from '../../types/backend';
import { humanize } from '../../services/format';

export function VerificationPanel({ result, onHighlight, onEvidence, onProof, onReview, onSearch, searching, onParameter, profileParameters }: {
  result: VerificationResult; onHighlight: (component: string, outcome: 'pass' | 'fail' | 'unknown' | null) => void;
  onEvidence: (records: EvidenceRecord[]) => void; onProof: () => void; onReview: () => void; onSearch: () => void;
  searching: boolean; onParameter: (name: string, q: Quantity) => void; profileParameters: Record<string, Quantity>;
}) {
  const tone = result.verdict === 'REQUIREMENTS_MET' && isVerified(result) ? 'pass' : result.verdict === 'DOES_NOT_MEET_REQUIREMENTS' ? 'fail' : 'unknown';
  const Icon = tone === 'pass' ? CheckCircle2 : tone === 'fail' ? CircleX : CircleHelp;
  const rows: (Check | CoupledCheck)[] = [...result.checks, ...result.coupled_checks];
  return <section className="result-panel" aria-live="polite">
    <div className={`verdict-summary ${tone}`} data-testid="verdict"><Icon size={26} /><span className="eyebrow">This experiment · this configuration</span>
      <h3>{result.headline}</h3><p>{result.user_message}</p></div>
    <div className="featured-context"><strong>Featured coverage: 180 pairings · 113 met · 1 needs information · 66 not met</strong><small>Full catalog: 44,880 pairs · 3,118 met (6.9%). This result remains the Lean verdict for the exact setup above.</small></div>
    <p className="muted small">{result.next_step}</p>
    <h4>See why</h4><div className="result-checks">{rows.map((check, index) => {
      const coupled = check.kind === 'coupled';
      const component = getComponentForCheck(check);
      const records = coupled ? check.evidence ?? [] : [...check.capability_evidence ?? [], ...check.requirement_evidence ?? []];
      return <details className={`check-row ${check.outcome}`} key={index}>
        <summary onClick={() => component && onHighlight(component.componentId, ['pass', 'fail'].includes(check.outcome) ? check.outcome as 'pass' | 'fail' : check.outcome === 'not_applicable' ? null : 'unknown')}>
          <span><strong>{coupled ? check.name ?? humanize(check.model) : check.keys.map(humanize).join(' or ')}</strong>
          <small>{coupled ? `${check.lhs?.display ?? 'Unknown'} ≤ ${check.rhs?.display ?? 'Unknown'}` : `${check.required} · ${check.available}`}</small></span>
          <span className={`outcome ${check.outcome}`}>{humanize(check.outcome)}</span></summary>
        <div className="requirement-detail"><p>{check.explanation}</p>
          {coupled && <><code className="equation">{check.equation}</code><ul>{check.assumptions?.map(a => <li key={a}>{a}</li>)}</ul></>}
          <button className="text-button" onClick={() => onEvidence(records)}><BookOpen size={14} /> Source evidence ({records.length})</button>
        </div></details>;
    })}</div>
    {!!result.missing_information.length && <details className="scope-note" open><summary>Information still needed</summary><ul>{result.missing_information.map(m => <li key={m}>{m}</li>)}</ul></details>}
    {result.suggestions?.parameter_changes?.filter(p => p.status === 'found'&&p.verified===true&&p.lean_verdict==='REQUIREMENTS_MET').map(p => <div className="suggestion" key={p.parameter}>
      <span className="eyebrow">A proposed input change</span><p>{humanize(p.parameter)}: {p.current} → {p.suggested}</p>
      <small>{p.verified && p.lean_verdict === 'REQUIREMENTS_MET' ? 'Lean accepted this candidate. Review and rerun it as your setup.' : 'Not established as compatible.'}</small>
      {profileParameters[p.parameter] && <button className="text-button" onClick={() => onParameter(p.parameter, { value: p.suggested, unit: profileParameters[p.parameter].unit })}>Review this change <ArrowRight size={14} /></button>}
    </div>)}
    <div className="result-actions"><button className="secondary-button" onClick={onSearch} disabled={searching}>{searching ? 'Searching the catalog…' : 'Find another machine'}<ArrowRight size={15} /></button>
      <button className="text-button" onClick={onProof}><FileCheck2 size={16} /> How we checked</button>
      <button className="text-button" onClick={onReview}>Review inputs & check again</button></div>
    <small className="muted">Result {result.result_id} · Scoped to the encoded requirements and supplied evidence.</small>
  </section>;
}
