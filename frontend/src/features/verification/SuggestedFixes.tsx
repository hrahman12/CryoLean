import { CheckCircle2, ArrowRight, LoaderCircle, RefreshCw } from 'lucide-react';
import type { VerifiedFix, VerifiedRepairSearch, VerificationResult } from '../../types/backend';
import { humanize } from '../../services/format';

export function SuggestedFixes({result,search,pending,error,applying,onApply,onRetry,previous,recorded=false}:{
  result:VerificationResult;search:VerifiedRepairSearch|null;pending:boolean;error:string;applying:string|null;
  onApply:(fix:VerifiedFix)=>void;onRetry:()=>void;previous:VerificationResult|null;
  recorded?:boolean;
}){
  const fixes=search?.result_id===result.result_id?search.fixes.filter(f=>f.verified===true&&f.lean_verdict==='REQUIREMENTS_MET'&&f.hypothetical===false):[];
  const appliedChanges=((result as any).repair_application?.changes??[]) as VerifiedFix['changes'];
  return <section className="suggested-fixes" aria-label="Suggested fixes" data-testid="suggested-fixes">
    <h3>{result.verdict==='REQUIREMENTS_MET'?'Verified setup':'Suggested fixes'}</h3>
    {previous&&appliedChanges.map(c=><p className="applied-change" key={c.parameter}><strong>{humanize(c.parameter)}:</strong> {String(c.before.value)} {c.before.unit} → <strong>{c.after.value} {c.after.unit}</strong></p>)}
    {previous&&previous.equipment.configuration_id!==result.equipment.configuration_id&&<p className="applied-change">Machine: {previous.equipment.configuration_id} → {result.equipment.configuration_id}</p>}
    {previous&&<details className="repair-comparison"><summary>Original → revised setup</summary><p>Original: {previous.headline}</p><p>{previous.user_message}</p><p>Rechecked: {result.headline}</p><p>{result.user_message}</p><small>Original record {previous.result_id} is preserved. Scientific requirements are unchanged.</small></details>}
    {result.verdict==='REQUIREMENTS_MET'?<><p className="verified-summary"><CheckCircle2 size={16}/> Lean accepted all applicable mandatory conditions.</p><div className="verified-conditions">{result.checks.filter(c=>c.mandatory&&c.applicable).slice(0,3).map((c,i)=><div key={i}><strong>{humanize(c.keys.join(' / '))}</strong><p>{c.required}</p><small>{c.available}</small></div>)}{result.coupled_checks.filter(c=>c.mandatory&&c.applicable).map((c,i)=><div key={`coupled-${i}`}><strong>{c.name}</strong><p>{c.lhs?.display} ≤ {c.rhs?.display}</p><small>Accepted by Lean within the stated model assumptions.</small></div>)}</div></>:<>
      {pending&&<p role="status"><LoaderCircle className="spin" size={16}/> Z3 is searching. Lean is checking every candidate…</p>}
      {error&&<p role="alert">{error} <button onClick={onRetry}>Retry search</button></p>}
      {!pending&&!error&&search&&!fixes.length&&<div className="no-solution" data-testid="no-verified-solution"><strong>No verified solution found</strong><p>{result.verdict==='NEED_MORE_INFORMATION'?'The missing evidence still prevents acceptance.':'No candidate in the documented search space passed every requirement.'}</p><small>{search.evaluated_candidates??0} candidates checked. Scientific requirements were preserved.</small><button className="text-button" onClick={onRetry}><RefreshCw size={13}/> Search again</button></div>}
      {fixes.map(f=><article className="verified-fix" key={f.id} data-testid="verified-fix"><span className="fix-badge"><CheckCircle2 size={14}/> Lean-verified PASS</span><h4>{humanize(f.title)}</h4><p>{f.reason}</p>
        {f.changes.length?<dl>{f.changes.map(c=><div key={c.parameter}><dt>{humanize(c.parameter)}</dt><dd>{String(c.before.value)} {c.before.unit} → <strong>{c.after.value} {c.after.unit}</strong></dd></div>)}</dl>:<p className="fix-machine">{f.configuration_name}</p>}
        <details><summary>Verified values & Lean evidence</summary><p>Checked {new Date(f.verified_at).toLocaleString()}</p><dl>{Object.entries(f.parameters).map(([name,q])=><div key={name}><dt>{humanize(name)}</dt><dd>{typeof q==='object'?`${q.value} ${q.unit}`:String(q)}</dd></div>)}</dl><p>Requirements unchanged. Documented configuration: {f.configuration_id}</p><code>Input: {f.verification.concrete_evaluation.lean_input_hash}</code><code>Checker: {f.verdict_card?.source_hash}</code><p>{f.verdict_card?.theorems.join(', ')}</p>{f.coupled_checks.map((c,i)=><p key={i}>{c.explanation}</p>)}<details><summary>Exact evaluated documents</summary><pre>{JSON.stringify(f.lean_input,null,2)}</pre></details></details>
        <button className="apply-fix-button" data-testid="apply-fix" disabled={applying!==null} onClick={()=>onApply(f)}>{applying===f.id?<><LoaderCircle size={15} className="spin"/>Rechecking with Lean…</>:<>{recorded?'Replay recorded fix':'Apply Fix'} <ArrowRight size={15}/></>}</button>
      </article>)}
    </>}
  </section>;
}
