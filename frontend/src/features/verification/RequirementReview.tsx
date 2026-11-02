import { ArrowRight, BookOpen, SlidersHorizontal, LoaderCircle } from 'lucide-react';
import type { ExperimentRequirements, Quantity, RequirementEdit, Constraint, EvidenceRecord } from '../../types/backend';
import { constraintText, requirementKey, humanize, decimalPattern } from '../../services/format';
import type { SetupState } from './setup-state';

interface Props {
  profile: ExperimentRequirements | null; setup: SetupState; connected: boolean;
  onConfirm: (value: boolean) => void; onVerify: () => void;
  onParameter: (name: string, value: Quantity) => void; onEdit: (edit: RequirementEdit) => void;
  onEvidence: (evidence: EvidenceRecord[]) => void; onHighlight: (key: string) => void;
}
export function RequirementReview({ profile, setup, connected, onConfirm, onVerify, onParameter, onEdit, onEvidence, onHighlight }: Props) {
  const editsValid = setup.edits.every(e => [e.constraint.q, e.constraint.lo, e.constraint.hi].filter(Boolean).every(q => decimalPattern.test(String(q!.value))));
  const parametersValid = Object.values(setup.parameters).every(q => decimalPattern.test(q.value));
  const valid = editsValid && parametersValid;
  return <section className="requirements" aria-label="Review experiment requirements">
    <div className="section-heading"><span className="step-number">03</span><h3>Review the requirements</h3></div>
    {!profile ? <p role="status">Loading the experiment profile…</p> : <>
      <p className="muted small">These are the prepared procedure’s requirements. Confirm they match your experiment.</p>
      <div className="requirement-list">{profile.requirements.map((r, index) => {
        const key = requirementKey(r);
        const edit = setup.edits.find(e => e.key === key);
        const constraint = edit?.constraint ?? r.constraint;
        const evidence = profile.evidence.filter(e => r.evidence_ids?.includes(e.id));
        return <details className="requirement-row" key={`${key}-${index}`}>
          <summary><span><strong>{humanize(key.replaceAll('|', ' or '))}</strong><small>{constraintText(constraint)}</small></span>
            <span className="tag">{r.mandatory ? 'Required' : 'Optional'}</span></summary>
          <div className="requirement-detail"><p>{r.rationale}</p>
            {!!r.conditions?.length && <p className="muted">Conditional: the backend evaluates when this requirement applies.</p>}
            <div className="inline-actions"><button className="text-button" onClick={() => onHighlight(r.key ?? r.keys?.[0] ?? '')}>Locate component</button>
              <button className="text-button" onClick={() => onEvidence(evidence)}><BookOpen size={14} /> Sources</button></div>
            {!r.keys && (['q', 'lo', 'hi'] as const).filter(side => constraint[side]).map(side => {
              const q = constraint[side]!;
              return <label className="quantity-editor" key={side}><span>{side === 'q' ? 'Your requirement' : side === 'lo' ? 'Lower value' : 'Upper value'}</span>
                <input aria-label={`${key} ${side}`} inputMode="decimal" value={String(q.value)} onChange={event => onEdit({ key,
                  constraint: { ...constraint, [side]: { value: event.target.value, unit: q.unit } } as Constraint })} />
                <span>{q.unit}</span></label>;
            })}
            {edit && <p className="edited-note">User-entered requirement. The original source no longer establishes this value.</p>}
          </div>
        </details>;
      })}</div>
      {!!profile.coupled.length && <details className="coupled-review"><summary>Coupled physics · {profile.coupled.length} model{profile.coupled.length === 1 ? '' : 's'}</summary>
        {profile.coupled.map(c => <p key={c.model}><strong>{humanize(c.model)}</strong><br />{c.rationale}</p>)}</details>}
      {!!profile.params.length && <details className="parameter-panel"><summary><SlidersHorizontal size={15} /> Experiment parameters</summary>
        <p className="muted small">Edits are your proposed inputs and require confirmation again. Equipment specifications stay sourced.</p>
        {profile.params.map(p => {
          const q = setup.parameters[p.name] ?? p.value;
          const editable = q && typeof q === 'object' && p.name !== 'contraction_data_temperature';
          return <div className="parameter" key={p.name}>
            <label htmlFor={`param-${p.name}`}>{humanize(p.name)}</label>
            {editable ? <div className="quantity-editor"><input id={`param-${p.name}`} inputMode="decimal" value={String(q.value)}
              onChange={e => onParameter(p.name, { value: e.target.value, unit: q.unit })} /><span>{q.unit}</span></div>
              : <p className="muted small">{typeof q === 'string' ? q : 'Not supplied / derived from reference data'}</p>}
            <small>{p.description}</small>{setup.parameters[p.name] && <span className="edited-note">User-entered value</span>}
          </div>;
        })}</details>}
      {!!profile.missing_information?.length && <details className="scope-note"><summary>Procedure limitations</summary><ul>{profile.missing_information.map(m => <li key={m}>{m}</li>)}</ul></details>}
      {!valid && <p role="alert" className="error-text">Use exact decimal values before confirming.</p>}
      <label className="confirmation"><input type="checkbox" data-testid="confirm" checked={setup.confirmed} disabled={!valid || setup.pending !== null}
        onChange={event => onConfirm(event.target.checked)} /><span>I’ve reviewed these requirements.<small>They match the experiment I want to run.</small></span></label>
    </>}
    <button data-testid="verify" className="primary-button" disabled={!profile || !setup.confirmed || !valid || setup.pending !== null} onClick={onVerify}>
      {setup.pending !== null ? <><LoaderCircle size={18} className="spin" /> Checking this setup…</> : <>Check my setup <ArrowRight size={18} /></>}
    </button>
    {!connected && <p className="preview-note">Connect to the backend to run a new Lean check. No verdict is produced while it is unavailable.</p>}
    {setup.error && <div className="error-box" role="alert"><strong>Verification unavailable</strong><p>{setup.error}</p><span>No compatibility verdict was produced.</span></div>}
  </section>;
}
