import { lazy, Suspense, type ReactNode, useEffect, useState } from 'react';
import { ArrowRight, ChevronDown, CircleHelp, CheckCircle2, CircleX, Ruler, Settings2, Snowflake, Thermometer, LoaderCircle } from 'lucide-react';
import type { Industry, ExperimentProfile, EquipmentItem, ExperimentRequirements, ConfigurationDetails, EvidenceRecord } from '../types/backend';
import type { SetupState } from '../features/verification/setup-state';
import type { SceneDefinition } from '../scene/registry';
import { getSceneDefinition } from '../scene/registry';
import type { SceneViewMode } from '../scene/core/LabCanvas';
import { MachineThumbnail } from './MachineThumbnail';
import { InlineRequirementPanel } from './InlineRequirementPanel';
import type {Quantity,RequirementEdit} from '../types/backend';

const Viewer=lazy(()=>import('../scene/core/LabCanvas'));
const Sample=lazy(()=>import('../scene/core/SamplePreview'));
interface Props {
  repairs?:ReactNode;
  recorded?:boolean;
  backendAvailable?:boolean;
  industries:Industry[];experiments:ExperimentProfile[];equipment:EquipmentItem[];industry:string;
  experiment?:ExperimentProfile;profile:ExperimentRequirements|null;configuration:ConfigurationDetails|null;
  equipmentItem?:EquipmentItem;setup:SetupState;scene:SceneDefinition;viewMode:SceneViewMode;animating:boolean;
  highlight:{id:string;outcome:'pass'|'fail'|'unknown'|null}|null;
  onIndustry:(id:string)=>void;onExperiment:(id:string)=>void;onEquipment:(id:string)=>void;
  onViewMode:(mode:SceneViewMode)=>void;onAnimating:(value:boolean)=>void;
  onHighlight:(id:string,outcome:'pass'|'fail'|'unknown'|null)=>void;onEvidence:(records:EvidenceRecord[])=>void;
  onConfirm:(value:boolean)=>void;onParameter:(name:string,value:Quantity)=>void;onEdit:(edit:RequirementEdit)=>void;
  onReview:()=>void;onWhy:()=>void;onSearch:()=>void;onSpecs:()=>void;onCoverage:()=>void;onDescribe:()=>void;
}
export function ConfiguratorCards(p:Props) {
  const [recordedPassIds,setRecordedPassIds]=useState<string[]>([]);
  useEffect(()=>{let current=true;void fetch('/research/lean-verdict-heatmap.json').then(r=>r.ok?r.json():null).then(data=>{if(!current||!data)return;const row=data.experiments.indexOf(p.setup.experimentId),pass=data.verdict_index.REQUIREMENTS_MET;if(row<0){setRecordedPassIds([]);return}setRecordedPassIds(data.configurations.filter((_:string,index:number)=>data.matrix[row][index]===pass));}).catch(()=>{if(current)setRecordedPassIds([])});return()=>{current=false}},[p.setup.experimentId]);
  const supported=p.industries.filter(i=>p.experiments.some(e=>e.industry===i.id||(e as any).industries?.includes(i.id)));
  const choices=p.experiments.filter(e=>!p.industry||e.industry===p.industry||(e as any).industries?.includes(p.industry));
  const current=p.equipmentItem;
  const visibleExperiments=[p.experiment,...choices].filter((e,i,a):e is ExperimentProfile=>Boolean(e)&&a.findIndex(x=>x?.id===e?.id)===i).slice(0,3);
  const allConfigurations=p.equipment.flatMap(e=>e.configurations.map(c=>({...c,equipment:e})));
  const preferredIds=[p.setup.configurationId,...recordedPassIds,...(p.experiment?.preferred_configuration_ids??[])];
  const preferred=preferredIds.map(id=>allConfigurations.find(c=>c.id===id)).filter((c,i,a):c is NonNullable<typeof c>=>Boolean(c)&&a.findIndex(x=>x?.id===c?.id)===i).slice(0,3);
  const result=p.setup.result;
  const tone=result?.verdict==='REQUIREMENTS_MET'?'pass':result?.verdict==='DOES_NOT_MEET_REQUIREMENTS'?'fail':'unknown';
  const ResultIcon=tone==='pass'?CheckCircle2:tone==='fail'?CircleX:CircleHelp;
  return <main id="workspace" className="three-card-workspace">
    <section className="config-card experiment-card" aria-labelledby="experiment-card-title"><div className="card-step"><span>1</span><h2 id="experiment-card-title">Choose an industry</h2></div>
      <Suspense fallback={<div className="sample-preview loading-scene"><LoaderCircle className="spin"/></div>}><Sample definition={p.scene}/></Suspense>
      <div className="card-form">
        <label htmlFor="industry">Industry · {supported.length}</label><div className="select-wrap industry-select"><select id="industry" value={p.industry} onChange={e=>p.onIndustry(e.target.value)}><option value="">All supported industries</option>{supported.map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</select><ChevronDown size={20}/></div>
        <div className="experiment-quick-choices" aria-label="Featured experiments">{visibleExperiments.map(e=><button key={e.id} className={e.id===p.setup.experimentId?'selected':''} aria-pressed={e.id===p.setup.experimentId} onClick={()=>p.onExperiment(e.id)}>{e.plain_name??e.name}</button>)}</div>
        <button className="make-experiment-button" onClick={p.onDescribe}>Make your own experiment <ArrowRight size={15}/></button>
      </div>
    </section>
    <section className="config-card cryostat-card" aria-labelledby="cryostat-card-title"><div className="card-step"><span>2</span><h2 id="cryostat-card-title">Choose a cryostat</h2></div>
      <div className="cryostat-select"><label className="sr-only" htmlFor="cryostat">Documented configuration</label><div className="select-wrap"><select id="cryostat" data-testid="cryostat" value={p.setup.configurationId} onChange={e=>p.onEquipment(e.target.value)}><option value="" disabled>Choose a machine</option>{p.equipment.map(e=><optgroup key={e.id} label={`${e.manufacturer} · ${e.model}`}>{e.configurations.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</optgroup>)}</select><ChevronDown size={16}/></div></div>
      <div className="configurator-viewer"><Suspense fallback={<div className="loading-scene"><LoaderCircle className="spin"/> Preparing your cryostat…</div>}><Viewer experimentId={p.setup.experimentId} configuration={p.configuration} definition={p.scene} viewMode={p.viewMode} onViewMode={p.onViewMode} animating={p.animating} onAnimating={p.onAnimating} highlight={p.highlight} onHighlight={p.onHighlight} onEvidence={p.onEvidence}/></Suspense></div>
      <div className="machine-thumbnails" aria-label="Switch cryostat configuration">{preferred.map(c=>{
        const family=getSceneDefinition(p.setup.experimentId,c.equipment.id,p.experiment?.visualization,c.visualization??c.equipment.visualization).family;
        const recordedPass=recordedPassIds.includes(c.id);return <button key={c.id} className={`${c.id===p.setup.configurationId?'selected ':''}${recordedPass?'recorded-pass':''}`} aria-label={`Select ${c.equipment.manufacturer} ${c.name}${recordedPass?' — saved Lean pass':''}`} aria-pressed={c.id===p.setup.configurationId} onClick={()=>p.onEquipment(c.id)}><MachineThumbnail family={family}/><span>{c.equipment.manufacturer}</span><small>{recordedPass?'● Recorded Lean pass':c.equipment.model.split('(')[0].trim()}</small></button>;
      })}</div>
      <button className="machine-details-link" onClick={p.onSpecs}>{p.configuration?.name??'Machine details'} <CircleHelp size={14}/></button>
    </section>
    <section className="config-card check-card" aria-labelledby="check-card-title"><div className="card-step"><span>3</span><h2 id="check-card-title">Check the setup</h2></div>
      <InlineRequirementPanel profile={p.profile} configuration={p.configuration} setup={p.setup} onConfirm={p.onConfirm} onParameter={p.onParameter} onEdit={p.onEdit} onEvidence={p.onEvidence}/>
      {result?<div className={`simple-result ${tone}`} data-testid="verdict" aria-live="polite"><ResultIcon size={25}/><h3>{result.headline}</h3><p>{result.user_message}</p><button onClick={p.onWhy}>See why <ArrowRight size={15}/></button></div>
        :<p className="check-description">We’ll check every required condition against the documented machine specifications.</p>}
      {p.setup.error&&<div className="error-box" role="alert"><strong>Verification unavailable</strong><p>{p.setup.error}</p><span>No verdict was produced.</span></div>}
      <button className="primary-button check-primary" data-testid="review-setup" disabled={!p.profile||!p.configuration||p.setup.pending!==null||(!p.recorded&&!p.backendAvailable)} onClick={p.onReview}>{p.setup.pending!==null?<><LoaderCircle size={19} className="spin"/>Checking your setup…</>:<>{p.recorded?'Replay recorded run':'Check my setup'} <ArrowRight size={19}/></>}</button>
      <p className="confirmation-caption">{p.recorded?'Historical Lean run · no new verification is executed during playback.':!p.backendAvailable?'Backend unavailable. Reconnect to run a live check.':p.setup.confirmed?'Requirements reviewed. Ready for a fresh check.':'Review and confirm your requirements before we check.'}</p>
      {!result&&<div className="outcome-legend" aria-label="Possible verification outcomes"><div><CheckCircle2 size={27}/><span>Requirements<br/>met</span></div><div><CircleX size={27}/><span>Doesn’t meet<br/>requirements</span></div><div><CircleHelp size={27}/><span>Need more<br/>information</span></div></div>}
      {result&&<button className="find-cryostat-button" onClick={p.onSearch}>Find another cryostat <ArrowRight size={15}/></button>}
      {p.repairs}
      <span className="check-card-footer">Your experiment. Your machine. A clear answer.</span>
    </section>
  </main>;
}
