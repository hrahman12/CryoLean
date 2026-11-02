import { useEffect,useState } from 'react';
import { Play,Pause,RotateCcw,SkipForward,ArrowRight } from 'lucide-react';
import { ConfiguratorCards } from '../../components/ConfiguratorCards';
import { Dialog } from '../../components/Dialog';
import { Evidence } from '../../components/Evidence';
import { VerificationPanel } from '../verification/VerificationPanel';
import { SuggestedFixes } from '../verification/SuggestedFixes';
import { initialSetup } from '../verification/setup-state';
import { getSceneDefinition } from '../../scene/registry';
import type { SceneViewMode } from '../../scene/core/LabCanvas';
import type { Industry,ExperimentProfile,EquipmentItem,ConfigurationDetails,ExperimentRequirements,VerificationResult,VerifiedRepairSearch,EvidenceRecord,Quantity } from '../../types/backend';

interface Event {result:VerificationResult;note:string;repairs?:VerifiedRepairSearch;schedule?:any;tight_schedule?:any}
interface Recording {recorded_at:string;lean_source_hash:string;profiles:Record<string,ExperimentRequirements>;demos:Array<{id:string;title:string;events:Event[];validation?:any;before_approval?:any}>}
export function RecordedDemos({catalog,configurations,onUseLive}:{
  catalog:{industries:Industry[];experiments:ExperimentProfile[];equipment:EquipmentItem[]};configurations:Record<string,ConfigurationDetails>;
  onUseLive:(experimentId:string,configurationId:string,parameters:Record<string,Quantity>)=>void;
}){
 const [recording,setRecording]=useState<Recording|null>(null),[error,setError]=useState('');
 const [demo,setDemo]=useState(1),[step,setStep]=useState(0),[playing,setPlaying]=useState(false);
 const [view,setView]=useState<SceneViewMode>('inside'),[animating,setAnimating]=useState(false);
 const [dialog,setDialog]=useState<'why'|'proof'|'evidence'|'specs'|null>(null),[evidence,setEvidence]=useState<EvidenceRecord[]>([]);
 useEffect(()=>{let current=true;void fetch('/recordings.json').then(r=>{if(!r.ok)throw new Error('Recorded artifacts are unavailable.');return r.json();}).then(r=>{if(current)setRecording(r);}).catch(e=>{if(current)setError(e.message);});return()=>{current=false;};},[]);
 const chosen=recording?.demos[demo],event=chosen?.events[step];
 useEffect(()=>{if(!playing||!chosen)return;const timer=setTimeout(()=>{if(step<chosen.events.length-1)setStep(s=>s+1);else setPlaying(false);},6000);return()=>clearTimeout(timer);},[playing,step,chosen]);
 if(error)return <p role="alert">{error} No recorded result is substituted for a live check.</p>;
 if(!recording||!chosen||!event)return <p role="status">Loading genuine Lean recordings…</p>;
 const result=event.result,eid=result.experiment.id,cid=(result.equipment as any).catalog_configuration_id??result.equipment.configuration_id;
 const profile=recording.profiles[eid],experiment=catalog.experiments.find(e=>e.id===eid)??({...profile,plain_name:result.experiment.plain_name??profile.name,description:profile.name,confirmed:true} as ExperimentProfile);
 const config=configurations[cid],equipment=catalog.equipment.find(e=>e.configurations.some(c=>c.id===cid));
 const scene=getSceneDefinition(eid,equipment?.id??'',profile.visualization,config?.visualization);
 const parameters=Object.fromEntries((result.experiment.parameters??[]).filter(p=>p.value&&typeof p.value==='object').map(p=>[p.name,p.value])) as Record<string,Quantity>;
 const setup={...initialSetup,experimentId:eid,configurationId:cid,parameters,confirmed:true,result};
 const next=()=>{setPlaying(false);setStep(s=>(s+1)%chosen.events.length);};
 const useLive=(newEid=eid,newCid=cid)=>{if(!catalog.experiments.some(e=>e.id===newEid)){setError('This demonstration contains a separately reviewed research profile from the recorded scratch database. Select a prepared product profile for a new live check.');return;}onUseLive(newEid,newCid,parameters);};
 const showEvidence=(records:EvidenceRecord[])=>{setEvidence(records);setDialog('evidence');};
 const supported=catalog.experiments.some(e=>e.id===eid);
 return <>
   <div className="demo-playback" data-testid="recorded-controls"><label htmlFor="recorded-demo">Demo</label><select id="recorded-demo" value={demo} onChange={e=>{setDemo(Number(e.target.value));setStep(0);setPlaying(false);}}>{recording.demos.map((d,i)=><option key={d.id} value={i}>{d.title}{d.id==='b'?' · featured':''}</option>)}</select>
     <button aria-label={playing?'Pause demo':'Play demo'} onClick={()=>{if(step===chosen.events.length-1)setStep(0);setPlaying(v=>!v);setAnimating(true);}}>{playing?<Pause size={14}/>:<Play size={14}/>} {playing?'Pause':'Play'}</button><button onClick={()=>{setStep(0);setPlaying(true);}}><RotateCcw size={14}/> Replay</button><button onClick={()=>{setDemo((demo+1)%recording.demos.length);setStep(0);setPlaying(false);}}><SkipForward size={14}/> Next demo</button>
     <input type="range" aria-label="Recorded demo progress" min={0} max={chosen.events.length-1} value={step} onChange={e=>{setStep(Number(e.target.value));setPlaying(false);}}/>
     <span className="recorded-label">Recorded run · step {step+1}/{chosen.events.length} · {new Date(recording.recorded_at).toLocaleDateString()}</span>
     {supported&&<button onClick={()=>useLive()}>Use this setup live <ArrowRight size={14}/></button>}
   </div>
   <ConfiguratorCards industries={catalog.industries} experiments={supported?catalog.experiments:[...catalog.experiments,experiment]} equipment={catalog.equipment} industry={experiment.industry}
     experiment={experiment} profile={profile} configuration={config??null} equipmentItem={equipment} setup={setup} scene={scene}
     recorded backendAvailable={false} viewMode={view} animating={animating} highlight={null} onViewMode={setView} onAnimating={setAnimating}
     onIndustry={id=>{const e=catalog.experiments.find(e=>e.industry===id);if(e)useLive(e.id,e.preferred_configuration_ids?.[0]??cid);}}
     onExperiment={id=>useLive(id)} onEquipment={id=>useLive(eid,id)} onHighlight={()=>{}} onEvidence={showEvidence}
     onConfirm={()=>{}} onParameter={()=>{}} onEdit={()=>{}}
     onReview={next} onWhy={()=>setDialog('why')} onSearch={()=>useLive()} onSpecs={()=>setDialog('specs')} onCoverage={()=>{}} onDescribe={()=>useLive()}
     repairs={<><p className="recorded-note">Recorded: {event.note}</p>{event.repairs&&<SuggestedFixes recorded result={result} search={event.repairs} pending={false} error="" applying={null} onApply={next} onRetry={()=>setStep(0)} previous={null}/>}
       {event.schedule&&<details className="campaign-timeline" open><summary>Recorded campaign · {event.schedule.schedule_ok?'Lean-validated schedule':'Schedule not established'}</summary><p>Cooldown: {event.schedule.cooldown}. Completion: {event.schedule.z3.makespan}.</p><ol>{event.schedule.timeline.map((s:any,i:number)=><li key={i}><strong>{s.start} → {s.stop}</strong> {s.experiment_id}</li>)}</ol><p>20 h variant: {event.tight_schedule?.z3.status}</p><details><summary>Actual scheduler & Lean record</summary><pre>{JSON.stringify(event.schedule,null,2)}</pre></details></details>}
       {chosen.validation&&<details className="campaign-timeline"><summary>Research validation vs compatibility</summary><p>Source validation: {chosen.validation.ok?'passed':'not established'}. Before approval: {chosen.before_approval?.error?.code}. Compatibility verdict above comes from Lean.</p></details>}</>}/>
   <Dialog open={dialog!==null} title={dialog==='specs'?'Recorded machine configuration':dialog==='proof'?'Recorded Lean evidence':dialog==='evidence'?'Scientific sources':'Why this recorded result?'} onClose={()=>setDialog(null)}>
     <p className="recorded-note">Historical verification · {result.checked_at}. No new check was executed.</p>
     {dialog==='why'&&<VerificationPanel result={result} onEvidence={showEvidence} onProof={()=>setDialog('proof')} onHighlight={()=>{}} onReview={()=>useLive()} onSearch={()=>useLive()} searching={false} onParameter={()=>{}} profileParameters={{}}/>}
     {dialog==='proof'&&<><p>{result.verdict}</p><p>{result.verdict_card?.reason}</p><pre>{JSON.stringify({verification:result.verification,verdict_card:result.verdict_card,lean_input:result.lean_input},null,2)}</pre></>}
     {dialog==='evidence'&&<Evidence records={evidence}/>}
     {dialog==='specs'&&config?.capabilities.map(c=><details key={c.key}><summary>{c.key}: {c.display}</summary><Evidence records={c.evidence}/></details>)}
   </Dialog>
 </>;
}
