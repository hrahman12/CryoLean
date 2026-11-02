import { useState } from 'react';
import { ArrowRight, BookOpen, CheckCircle2, MessageCircle, Scale, Sparkles } from 'lucide-react';
import type { ConfigurationDetails, ExperimentProfile, VerificationResult } from '../types/backend';

function checkReason(check:VerificationResult['checks'][number]|VerificationResult['coupled_checks'][number]){
  return check.explanation||('required' in check?check.required:check.name);
}
function explain(result:VerificationResult|null, experiment?:ExperimentProfile, configuration?:ConfigurationDetails|null){
  if(!result) return `Choose and confirm the requirements for ${experiment?.plain_name??'your experiment'}, then run the Lean check. I will explain the saved result without guessing.`;
  const failed=[...result.checks,...result.coupled_checks].filter(check=>check.outcome==='fail');
  const unknown=[...result.checks,...result.coupled_checks].filter(check=>['unknown','unsupported'].includes(check.outcome));
  if(result.verdict==='REQUIREMENTS_MET') return `Lean accepted every applicable mandatory condition for ${configuration?.name??result.equipment.configuration_id}. The exact evaluated input is preserved with result ${result.result_id}.`;
  if(failed.length) return `Lean rejected this setup because ${failed.slice(0,2).map(checkReason).join(' ')} Suggested fixes are shown only after Z3 proposes them and Lean verifies the exact candidate as REQUIREMENTS_MET.`;
  return `Lean needs more information. ${unknown.slice(0,2).map(checkReason).join(' ')} Missing facts remain unknown; CryoLean does not turn them into a pass.`;
}

export function VerificationIngredients({result,experiment,configuration,onProof}:{result:VerificationResult|null;experiment?:ExperimentProfile;configuration?:ConfigurationDetails|null;onProof:()=>void}){
  const [question,setQuestion]=useState('');
  const [answer,setAnswer]=useState('');
  const ask=()=>setAnswer(explain(result,experiment,configuration));
  return <section className="verification-ingredients" aria-labelledby="ingredients-title">
    <div className="ingredient-flow">
      <article><BookOpen/><span>DATASHEETS</span><strong>the facts</strong><small>Documented manufacturer capabilities and experiment sources.</small></article>
      <ArrowRight className="ingredient-arrow"/>
      <article><Scale/><span>LEAN</span><strong>the judge</strong><small>The real checker decides pass, fail, or missing information.</small></article>
      <ArrowRight className="ingredient-arrow"/>
      <article><Sparkles/><span>Z3</span><strong>suggests candidates</strong><small>Every proposed repair must return to Lean before it appears.</small></article>
    </div>
    <div className="verified-fixes-promise"><div><span>Lean · final step</span><h2 id="ingredients-title">Lean verifies every fix</h2><p>Only exact candidates that Lean returns as <strong>REQUIREMENTS_MET</strong> are shown as fixes. Otherwise CryoLean says “No verified solution found”.</p></div><span className="verified-only"><CheckCircle2/> verified fixes only</span></div>
    <div className="check-guide-grid">
      <article className="current-check"><span>Your check</span><h3>{experiment?.plain_name??'Choose an experiment'}</h3><p>{configuration?.name??'Choose a documented cryostat configuration.'}</p>{result?<><strong className={`result-word ${result.verdict}`}>{result.headline}</strong><p>{result.user_message}</p><button className="text-button" onClick={onProof}>Inspect Lean evidence <ArrowRight size={14}/></button></>:<small>Run “Check my setup” to create a real Lean result.</small>}</article>
      <article className="result-guide"><span><MessageCircle size={15}/> ASK ABOUT THIS RUN · LEAN DECIDES</span><h3>Understand the result</h3><p>This guide summarizes the current backend record. It cannot change requirements, machine specifications, or Lean’s verdict.</p><div className="guide-input"><input value={question} onChange={event=>setQuestion(event.target.value)} placeholder="Why did this setup pass, fail, or need information?"/><button onClick={ask}>Ask</button></div><button className="explain-check" onClick={ask}>Explain my check</button>{answer&&<div className="guide-answer" role="status">{answer}</div>}</article>
    </div>
  </section>;
}
