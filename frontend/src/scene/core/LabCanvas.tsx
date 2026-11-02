import { Component, Suspense, useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Environment, Lightformer } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { RotateCcw, Play, Pause, Maximize2, Tags, Minus, Plus, ChevronLeft, ChevronRight, Box as BoxIcon, Layers, FlaskConical } from 'lucide-react';
import SceneManager from '../SceneManager';
import { sceneComponents, type SceneDefinition } from '../registry';
import type { ConfigurationDetails, EvidenceRecord } from '../../types/backend';
import { humanize } from '../../services/format';

export type SceneViewMode = 'outside' | 'inside' | 'experiment';
type Highlight = {id:string;outcome:'pass'|'fail'|'unknown'|null}|null;
class SceneBoundary extends Component<{children:ReactNode;fallback:ReactNode},{failed:boolean}> {
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  render(){return this.state.failed?this.props.fallback:this.props.children;}
}
function CameraRig({mode,reset,command,spin}:{mode:SceneViewMode;reset:number;command:{name:string;revision:number};spin:boolean}) {
  const controls=useRef<OrbitControlsImpl>(null);
  const {camera,invalidate}=useThree();
  useEffect(() => {
    camera.position.set(...(mode==='experiment'?[2,1.6,3.5]:mode==='inside'?[2.8,1.5,3.9]:[3.2,1.9,4.5]) as [number,number,number]);
    controls.current?.target.set(0,mode==='experiment'?.1:0,0);controls.current?.update();invalidate();
  },[camera,mode,reset,invalidate]);
  useEffect(() => {
    const c=controls.current;if(!c)return;
    if(command.name==='left'||command.name==='right') c.setAzimuthalAngle(c.getAzimuthalAngle()+(command.name==='left'?.3:-.3));
    if(command.name==='in'||command.name==='out') camera.position.sub(c.target).multiplyScalar(command.name==='in'?.85:1.18).clampLength(.9,12).add(c.target);
    c.update();invalidate();
  },[command,camera,invalidate]);
  return <OrbitControls ref={controls} makeDefault autoRotate={spin} autoRotateSpeed={.6} enableDamping={false} minDistance={.9} maxDistance={12} minPolarAngle={.08} maxPolarAngle={Math.PI*.85} />;
}
export default function LabCanvas({configuration,definition,viewMode,onViewMode,animating,onAnimating,highlight,onHighlight,onEvidence}: {
  experimentId:string;configuration:ConfigurationDetails|null;definition:SceneDefinition;viewMode:SceneViewMode;
  onViewMode:(mode:SceneViewMode)=>void;animating:boolean;onAnimating:(value:boolean)=>void;highlight:Highlight;
  onHighlight:(id:string,outcome:'pass'|'fail'|'unknown'|null)=>void;onEvidence:(records:EvidenceRecord[])=>void;
}) {
  const [labels,setLabels]=useState(false);
  const [spin,setSpin]=useState(false);
  const [reset,setReset]=useState(0);
  const [command,setCommand]=useState({name:'',revision:0});
  const [lost,setLost]=useState(false);
  const [fallback,setFallback]=useState(false);
  const [step,setStep]=useState(0);
  const [reduced,setReduced]=useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const stage=useRef<HTMLDivElement>(null);
  const canvas=useRef<HTMLCanvasElement|null>(null);
  const manualTextView=useRef(false);
  const onContextLost=useCallback((event:Event)=>{event.preventDefault();if(manualTextView.current)return;setLost(true);onAnimating(false);},[onAnimating]);
  useEffect(() => {
    const media=window.matchMedia('(prefers-reduced-motion: reduce)');
    const changed=()=>{setReduced(media.matches);if(media.matches)onAnimating(false);};
    media.addEventListener('change',changed);return()=>media.removeEventListener('change',changed);
  },[onAnimating]);
  useEffect(() => {setStep(0);onAnimating(false);},[definition.archetype,onAnimating]);
  useEffect(() => {
    if(!animating||reduced)return;
    const timer=setInterval(()=>setStep(s=>(s+1)%definition.steps.length),4000);
    return()=>clearInterval(timer);
  },[animating,reduced,definition.steps.length]);
  useEffect(() => {
    const el=canvas.current;if(!el)return;
    return()=>el.removeEventListener('webglcontextlost',onContextLost);
  },[reset,lost,fallback,onContextLost]);
  const components=sceneComponents(definition.family);
  const componentAliases: Record<string,string> = {cryo_chamber:'cold_stage',mxc_stage:'mxc_wiring_bundle',coax_wiring_bundle:'mxc_wiring_bundle',sample_puck:'sample_mount',vsm_module:'dc_wiring',eto_module:'dc_wiring',probe_arms:'dc_wiring'};
  const effectiveHighlight = highlight ? {...highlight,id:componentAliases[highlight.id]??highlight.id} : null;
  const selected=components.find(c=>c.id===effectiveHighlight?.id);
  const send=(name:string)=>setCommand(c=>({name,revision:c.revision+1}));
  const changeMode=(mode:SceneViewMode)=>{onViewMode(mode);onAnimating(false);};
  const diagramParts = definition.archetype==='cryosection' ? ['Frozen tissue on chuck','Cutting blade','Thin section on collection slide']
    : ['transport','magnetoresistance','nano_transport'].includes(definition.archetype) ? ['Current source → outer contacts',definition.archetype==='transport'?'Sample on cold stage':'Contacted sample in required magnetic field','Inner contacts → voltage measurement']
    : definition.archetype==='vsm' ? ['Oscillating sample in magnet region','Stationary pickup coils','Measurement electronics']
    : ['quantum','quantum_chip'].includes(definition.archetype) ? ['Signal wiring','Successive thermal anchors','Mixing chamber / sample mount']
    : ['Illumination / excitation','Optical path → cooled specimen','Collection optics → detector'];
  const diagram=<div className="scene-fallback" aria-label="Text diagram of the experimental setup"><span className="eyebrow">Apparatus overview</span>
    <div className="fallback-diagram">{diagramParts.map((part,index)=><div key={part}>{index>0&&<b>↓</b>}<span>{part}</span></div>)}</div>
    <ol className="fallback-steps">{definition.steps.map(s=><li key={s}>{s}</li>)}</ol>
    <p>{lost?'The graphics context was interrupted.':fallback?'Text view is selected.':'3D graphics are unavailable on this device.'} The catalog and real verification controls remain available.</p>
    {lost&&<button className="secondary-button" onClick={()=>{setLost(false);setReset(x=>x+1);}}>Retry 3D</button>}</div>;
  return <div className="lab-viewer" ref={stage} data-machine-family={definition.family} data-machine-scene={definition.machineVisual?.archetype}>
    <div className="view-switcher" role="group" aria-label="Apparatus view">{(['outside','inside','experiment'] as const).map((mode,index)=>{
      const Icon=[BoxIcon,Layers,FlaskConical][index];return <button key={mode} className={viewMode===mode?'active':''} aria-pressed={viewMode===mode} onClick={()=>changeMode(mode)}><Icon size={14}/>{mode==='outside'?'Outside':mode==='inside'?'Inside':'Experiment'}</button>;
    })}</div>
    {viewMode==='experiment'&&<p className="apparatus-scope">Required experiment apparatus · installation is checked separately</p>}
    <div className="stage-canvas" tabIndex={0} aria-label="3D apparatus. Left and right arrow keys orbit; plus and minus zoom. Drag to orbit, scroll to zoom." onKeyDown={e=>{
      const commands:Record<string,string>={ArrowLeft:'left',ArrowRight:'right','+':'in','=':'in','-':'out'};
      if(commands[e.key]){e.preventDefault();send(commands[e.key]);}
    }}>
      {fallback||lost||definition.family==='unmapped'?diagram:<SceneBoundary key={reset} fallback={diagram}><Canvas camera={{position:[3.2,1.65,4.6],fov:37,near:.05,far:50}}
        dpr={[1,1.6]} shadows frameloop={(animating||spin)&&!reduced?'always':'demand'} gl={{antialias:true,alpha:true,powerPreference:'high-performance'}} fallback={diagram}
        onCreated={({gl})=>{canvas.current=gl.domElement;gl.domElement.addEventListener('webglcontextlost',onContextLost);gl.setClearColor('#f1f3f7',0);}}>
        <ambientLight intensity={1.3}/><hemisphereLight args={['#e4edfa','#a8a2a1',1.3]} />
        <directionalLight position={[3,6,4]} intensity={3} castShadow shadow-mapSize={[1024,1024]} shadow-bias={-.0005}/>
        <directionalLight position={[-4,2,-1]} intensity={1.6} color="#d7d8f5"/>
        <Environment resolution={128}><Lightformer intensity={3} position={[3,3,2]} scale={[4,6,1]} color="#ffffff"/><Lightformer intensity={2} position={[-3,2,-2]} scale={[3,5,1]} color="#dfefff" rotation={[0,Math.PI/2,0]}/><Lightformer intensity={2.5} position={[0,5,0]} scale={[5,5,1]} rotation={[Math.PI/2,0,0]}/></Environment>
        <mesh position={[0,-1.23,0]} rotation={[-Math.PI/2,0,0]} receiveShadow><circleGeometry args={[4,64]}/><shadowMaterial transparent opacity={.12}/></mesh>
        <CameraRig mode={viewMode} reset={reset} command={command} spin={spin&&!reduced}/>
        <Suspense fallback={null}><SceneManager configuration={configuration} definition={definition} viewMode={viewMode} highlight={effectiveHighlight} animating={animating&&!reduced} labels={labels} onSelect={id=>onHighlight(id,null)}/></Suspense>
      </Canvas></SceneBoundary>}
    </div>
    <div className="scene-tools"><button className="icon-button" aria-label="Orbit left" onClick={()=>send('left')}><ChevronLeft size={17}/></button><button className="icon-button" aria-label="Orbit right" onClick={()=>send('right')}><ChevronRight size={17}/></button>
      <span className="tool-divider"/><button className="icon-button" aria-label="Zoom in" onClick={()=>send('in')}><Plus size={17}/></button><button className="icon-button" aria-label="Zoom out" onClick={()=>send('out')}><Minus size={17}/></button>
      <button className={`icon-button ${spin?'active':''}`} aria-label="Spin cryostat" aria-pressed={spin} disabled={reduced} onClick={()=>setSpin(v=>!v)}><RotateCcw size={16}/></button>
      <button className="icon-button" aria-label="Reset and fit camera" onClick={()=>{setReset(x=>x+1);setStep(0);onAnimating(false);}}><RotateCcw size={16}/></button>
      <button className={`icon-button ${labels?'active':''}`} aria-pressed={labels} aria-label="Toggle component labels" onClick={()=>setLabels(v=>!v)}><Tags size={16}/></button>
      <button className="icon-button" aria-label="Toggle fullscreen" onClick={()=>{if(document.fullscreenElement)void document.exitFullscreen();else void stage.current?.requestFullscreen().catch(()=>{});}}><Maximize2 size={16}/></button></div>
    <div className="scene-bottom"><button className="procedure-button" onClick={()=>{onViewMode('experiment');if(reduced)setStep(s=>(s+1)%definition.steps.length);else onAnimating(!animating);}}>
      {animating?<Pause size={14}/>:<Play size={14}/>} {reduced?'Step through the experiment':animating?'Pause the procedure':'See how the experiment works'}</button>
      <span className="scene-hint">Drag to orbit · Scroll to zoom</span></div>
    {(viewMode==='experiment'||animating)&&<div className="storyboard"><div><span className="eyebrow">Illustrative procedure · {step+1}/{definition.steps.length}</span><p>{definition.steps[step]}</p></div>
      <button className="icon-button" aria-label="Previous procedure step" onClick={()=>setStep(s=>(s-1+definition.steps.length)%definition.steps.length)}><ChevronLeft size={16}/></button>
      <button className="icon-button" aria-label="Next procedure step" onClick={()=>setStep(s=>(s+1)%definition.steps.length)}><ChevronRight size={16}/></button></div>}
    <details className="component-inspector" open={Boolean(selected)}><summary>Inspect a component <span>{components.length}</span></summary>
      <div className="component-buttons">{components.map(c=><button key={c.id} className={selected?.id===c.id?'active':''} onClick={()=>{onHighlight(c.id,null);onViewMode('inside');}}>{c.title}</button>)}</div>
      {selected&&<div className={`component-detail ${highlight?.outcome==='unknown'?'unknown':''}`}><strong>{selected.title}</strong><p>{selected.description}</p>
        {selected.keys.map(key=>{const cap=configuration?.capabilities.find(c=>c.key===key);return cap?<div className="component-fact" key={key}><span>{humanize(key)}</span><strong>{cap.value.kind==='unknown'?'Not documented':cap.display}</strong><small>{humanize(cap.install)}</small>
          <button className="text-button" onClick={()=>onEvidence(cap.evidence)}>Evidence</button></div>:null;})}</div>}
    </details>
    {definition.machineVisual?.geometry&&Object.keys(definition.machineVisual.geometry).length>0&&<details className="geometry-sources"><summary>Sourced internal construction</summary><p>{definition.machineVisual.geometry.notes??definition.machineVisual.notes}</p><ul>{definition.machineVisual.geometry.stages?.map((s:any,i:number)=><li key={i}><strong>{s.name}</strong>{s.temperature_K!==undefined?` · ${s.temperature_K} K`:''}{s.source_url&&<a href={s.source_url} target="_blank" rel="noreferrer"> Source ↗</a>}</li>)}</ul><p>Unpublished dimensions and component sizes are schematic. These geometry notes never supply specifications to the checker.</p></details>}
    <div className="scene-preferences"><label><input type="checkbox" checked={reduced} onChange={e=>{setReduced(e.target.checked);onAnimating(false);}}/> Reduce motion</label>
      <button className="text-button" onClick={()=>{const next=!fallback;manualTextView.current=next;setFallback(next);if(!next){setLost(false);setReset(x=>x+1);}}}>{fallback?'Show 3D':'Use text diagram'}</button></div>
  </div>;
}
