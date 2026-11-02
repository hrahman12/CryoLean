import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import type { SceneDefinition } from './registry';
import { hasInstalled } from './registry';
import type { ConfigurationDetails } from '../types/backend';

type V=[number,number,number];
const steel='#b7c5d3',dark='#23384c',gold='#d9ad60',copper='#b97e4a',blue='#398be0',glass='#a8d4e8';
function C({p=[0,0,0],r=.3,h=.1,c=steel,a=1,rot}: {p?:V;r?:number;h?:number;c?:string;a?:number;rot?:V}){
  return <mesh position={p} rotation={rot} castShadow receiveShadow><cylinderGeometry args={[r,r,h,48]}/><meshStandardMaterial color={c} roughness={.25} metalness={.78} transparent={a<1} opacity={a} depthWrite={a===1}/></mesh>;
}
function B({p=[0,0,0],s=[1,.1,1],c=steel,a=1,rot}:{p?:V;s?:V;c?:string;a?:number;rot?:V}){
  return <mesh position={p} rotation={rot} castShadow receiveShadow><boxGeometry args={s}/><meshStandardMaterial color={c} metalness={.48} roughness={.3} transparent={a<1} opacity={a} depthWrite={a===1}/></mesh>;
}
function R({p=[0,0,0],r=.4,t=.025,c=steel,rot=[Math.PI/2,0,0]}:{p?:V;r?:number;t?:number;c?:string;rot?:V}){
  return <mesh position={p} rotation={rot} castShadow><torusGeometry args={[r,t,10,64]}/><meshStandardMaterial color={c} metalness={.85} roughness={.22}/></mesh>;
}
function W({points,c=copper,w=2}:{points:V[];c?:string;w?:number}){return <Line points={points} color={c} lineWidth={w}/>;}
function Ball({p,r=.05,c=blue}:{p:V;r?:number;c?:string}){return <mesh position={p} castShadow><sphereGeometry args={[r,16,12]}/><meshStandardMaterial color={c} roughness={.35} metalness={.15}/></mesh>;}
function Flange({y,r=.6}:{y:number;r?:number}){return <><C p={[0,y,0]} r={r} h={.065}/>{Array.from({length:12},(_,i)=><C key={i} p={[Math.cos(i*Math.PI/6)*(r-.08),y+.05,Math.sin(i*Math.PI/6)*(r-.08)]} r={.025} h={.045} c={dark}/>)}</>;}
function Panel({p=[1,-.7,0],w=.6}:{p?:V;w?:number}){return <group position={p}><B s={[w,.35,.42]} c='#e7eef5'/><B p={[0,.02,.22]} s={[w*.8,.23,.025]} c={dark}/><B p={[-w*.13,.04,.24]} s={[w*.32,.1,.01]} c='#86c4cd'/>{[0,.1].map(x=><Ball key={x} p={[w*.23,x-.04,.24]} r={.025} c={steel}/>)}</group>;}
function Port({p=[0,0,.65],rot=[Math.PI/2,0,0],r=.13}:{p?:V;rot?:V;r?:number}){return <group position={p} rotation={rot}><C r={r} h={.18}/><Flange y={.1} r={r*1.4}/><C p={[0,.14,0]} r={r*.75} h={.015} c={glass} a={.45}/></group>;}
function Rack({n=4,y=-.8}:{n?:number;y?:number}){return <>{Array.from({length:n},(_,i)=><group key={i}><B p={[-1.05,y+i*.28,-.5]} s={[.5,.2,.5]} c={i%2?dark:steel}/><B p={[-1.05,y+i*.28,-.24]} s={[.35,.1,.01]} c='#76b8c6'/></group>)}</>;}
function Bench(){return <><B p={[0,-.9,0]} s={[2.2,.12,1.3]} c={dark}/>{[-.9,.9].flatMap(x=>[-.45,.45].map(z=><B key={`${x}${z}`} p={[x,-1.06,z]} s={[.08,.3,.08]}/>))}</>;}
function Dewar({inside=false,wide=false}:{inside?:boolean;wide?:boolean}){return <><C p={[0,-.13,0]} r={wide?.75:.5} h={1.65} c='#d0dbe4' a={inside?.13:1}/><Flange y={.72} r={wide?.8:.57}/><C p={[0,-.97,0]} r={wide?.77:.54} h={.12} c={dark}/>{inside&&<><C p={[0,-.23,0]} r={wide?.62:.37} h={1.35} c={gold} a={.17}/><C p={[0,-.48,0]} r={wide?.5:.29} h={.05} c={copper}/></>}<Port p={[.52,.42,0]} rot={[0,0,Math.PI/2]} r={.09}/></>;}

/** Distinct specialized instrument assemblies; no geometry supplies capability facts. */
export function SpecializedMachine({definition:d,configuration:cfg,inside}:{definition:SceneDefinition;configuration:ConfigurationDetails|null;inside:boolean}){
 const f=d.family,id=d.machineVisual?.variant??'',geometry=d.machineVisual?.geometry;
 const stages=geometry?.stages??[];
 const freezerTall=/upright|ULT|cryomed|kryo|metal|mve|binder/i.test((cfg?.family??'')+id);
 if(['freezer','freeze_substitution','cryo_room'].includes(f))return <group>
   <B p={[0,-.1,0]} s={[1.5,freezerTall?1.85:1.4,1.15]} c='#e6edf2'/><B p={[0,.0,.59]} s={[1.3,freezerTall?1.56:1.1,.035]} c={dark}/>
   <B p={[0,0,.62]} s={[1.18,freezerTall?1.43:.98,.025]} c={inside?'#b6c6d0':'#e6edf2'} a={inside?.1:1}/>
   <group position={inside?[-.8,0,.55]:[0,0,0]} rotation={[0,inside?-.8:0,0]}>{!inside&&<B p={[.54,0,.67]} s={[.04,.5,.06]} c={steel}/>}</group>
   {inside&&[-.48,-.15,.18,.51].map(y=><group key={y}><B p={[0,y,.07]} s={[1.1,.025,.8]} c={steel}/>{[-.32,0,.32].map(x=><B key={x} p={[x,y+.08,.15]} s={[.23,.13,.5]} c='#dce7ee'/>)}</group>)}
   <B p={[.37,.82,.63]} s={[.45,.22,.025]} c={dark}/><B p={[.32,.83,.65]} s={[.22,.12,.01]} c='#8bc1d2'/>
   {Array.from({length:7},(_,i)=><B key={i} p={[-.3+i*.1,-.88,.6]} s={[.055,.08,.02]} c='#647f93'/>)}
   {[-.6,.6].flatMap(x=>[-.43,.43].map(z=><C key={`${x}${z}`} p={[x,-1.1,z]} r={.06} h={.12} c={dark}/>))}
   {f==='freeze_substitution'&&<C p={[.8,-.3,-.2]} r={.24} h={.8}/>}
 </group>;
 if(f==='storage_dewar'||f==='calorimeter'||f==='particle_detector'||f==='neutron'||f==='measurement_cryostat'||f==='helium_stack')return <group>
   <Dewar inside={inside} wide={f==='particle_detector'||f==='storage_dewar'}/>
   <C p={[-.32,.98,-.12]} r={.13} h={.45} c={dark}/><C p={[.16,.9,-.1]} r={.06} h={.3}/>
   {inside&&<>
     {f==='storage_dewar'?Array.from({length:6},(_,i)=><group key={i} rotation={[0,i*Math.PI/3,0]}><B p={[.36,-.2,0]} s={[.18,1.12,.22]} c={steel}/>{[-.55,-.25,.05,.35].map(y=><B key={y} p={[.36,y,.01]} s={[.15,.06,.19]} c={dark}/>)}</group>)
     :f==='particle_detector'?Array.from({length:4},(_,i)=><group key={i}><C p={[0,.3-i*.26,0]} r={.27} h={.04} c={copper}/>{[-.14,.14].flatMap(x=>[-.14,.14].map(z=><B key={`${x}${z}`} p={[x,.19-i*.26,z]} s={[.19,.19,.19]} c='#e5e0c8' a={.6}/>))}</group>)
     :[.35,-.1,-.5].map((y,i)=><C key={y} p={[0,y,0]} r={.3-i*.05} h={.045} c={i===2?gold:steel}/>)}
     {f==='calorimeter'&&[.33,.36,.39,.42].map(r=><C key={r} p={[0,-.1,0]} r={r} h={1.12} c={gold} a={.13}/>)}
     <W points={[[.1,.9,0],[.1,.35,0],[.08,-.5,0]]} w={3}/>
   </>}
   {f==='neutron'&&<><Port p={[0,-.15,.52]} r={.16}/><Port p={[0,-.15,-.52]} r={.16}/></>}
   {f!=='storage_dewar'&&<><Panel p={[1,-.7,.2]}/><W points={[[.3,.8,0],[.85,.95,-.1],[1,-.55,0]]} c={dark} w={3}/></>}
 </group>;
 if(f==='thermal_vacuum')return <group>
   <group rotation={[0,0,Math.PI/2]}><C r={.8} h={1.9} c={steel} a={inside?.15:1}/><Flange y={-1} r={.87}/><Flange y={1} r={.87}/>{inside&&<C r={.7} h={1.8} c={dark} a={.2}/>}</group>
   <B p={[0,-.47,0]} s={[1.55,.08,.95]} c={copper}/>{[-.72,.72].map(x=><B key={x} p={[x,-.9,0]} s={[.17,.62,1.1]} c={dark}/>)}
   <Port p={[0,.62,.2]} rot={[0,0,0]} r={.16}/><Port p={[.55,.2,.68]}/>
   {inside&&<><B p={[.05,-.12,0]} s={[.45,.6,.4]} c={gold}/><B p={[.05,-.1,.22]} s={[.38,.48,.015]} c='#253b66'/></>}
   <Rack n={5}/><Panel p={[1.35,-.7,.1]}/><W points={[[.1,-.43,.4],[.8,-.6,.8],[1.4,-.6,.3]]} c={blue}/>
 </group>;
 if(f==='wind_tunnel')return <group><Bench/>
   <B p={[0,.15,-.35]} s={[2.1,1.45,.2]} c={steel}/><B p={[0,.15,.2]} s={[2.1,1.45,.1]} c={steel} a={inside?.1:.35}/>
   <B p={[0,.82,-.1]} s={[2.1,.18,.8]} c={dark}/><B p={[0,-.53,-.1]} s={[2.1,.18,.8]} c={dark}/>
   <R p={[-.83,.15,0]} r={.42} rot={[0,Math.PI/2,0]}/>{[0,1,2,3,4].map(i=><B key={i} p={[-.83,.15,0]} s={[.045,.72,.06]} rot={[i*Math.PI/5,0,0]} c={dark}/>)}
   <group scale={.6} position={[.2,.1,.05]}><Aircraft/></group><W points={[[.1,-.5,0],[.1,.1,0],[.3,.1,0]]}/><Panel p={[1.3,-.7,0]}/>
 </group>;
 if(f==='tensile')return <group><B p={[0,-.95,0]} s={[1.65,.16,1.1]} c={dark}/><B p={[0,1,0]} s={[1.45,.17,.6]}/>
   {[-.55,.55].map(x=><><C key={x} p={[x,0,0]} r={.065} h={1.9}/>{[-.85,-.3,.3,.85].map(y=><R key={`${x}${y}`} p={[x,y,0]} r={.085} c={dark}/>)}</>)}
   <B p={[0,.42,0]} s={[1.25,.16,.47]} c={dark}/><C p={[0,-.22,0]} r={.35} h={1.13} a={inside?.12:.9}/><Flange y={.37} r={.4}/>
   <B p={[0,.15,0]} s={[.22,.25,.18]} c={gold}/><B p={[0,-.51,0]} s={[.22,.2,.18]} c={gold}/><B p={[0,-.19,0]} s={[.055,.53,.035]}/>
   <Panel p={[1.1,-.65,.05]}/><W points={[[-.33,-.2,0],[-.85,-.2,.1],[-.85,-.65,-.2]]} c={glass} w={6}/>
 </group>;
 if(f==='mill')return <group><B p={[0,-.6,0]} s={[1.7,.6,1.2]} c='#f0f3f5'/><B p={[0,-.28,0]} s={[1.6,.05,1.05]} c={dark}/>
   <B p={[0,.18,-.51]} s={[1.7,.95,.14]} c={steel}/><B p={[0,.25,.45]} s={[1.6,.8,.04]} c={glass} a={inside?.1:.25}/>
   {[-.39,.39].map(x=><group key={x}><C p={[x,.13,0]} r={.24} h={.6} c={steel}/><Flange y={.46} r={.25}/><C p={[x,-.18,0]} r={.27} h={.1} c={dark}/>{inside&&<Ball p={[x,.1,0]} r={.12} c={gold}/>}</group>)}
   <Panel p={[.42,-.6,.67]} w={.5}/><C p={[-1,-.5,-.25]} r={.23} h={.8}/><W points={[[-1,-.1,-.25],[-.8,.6,-.2],[0,.5,0]]} c={glass} w={5}/>
 </group>;
 if(f==='freeze_dryer')return <group><B p={[0,-.6,0]} s={[1.7,.65,1.15]} c='#e7edf2'/><Panel p={[.35,-.58,.59]} w={.55}/>
   <C p={[0,.2,0]} r={.62} h={1.05} c={glass} a={inside?.12:.28}/><Flange y={-.34} r={.7}/><Flange y={.78} r={.7}/>
   {[-.12,.16,.44].map(y=><group key={y}><C p={[0,y,0]} r={.5} h={.045}/>{[-.27,0,.27].map(x=><C key={x} p={[x,y+.08,.1]} r={.09} h={.12} c='#e2b6a8'/>)}</group>)}
   <C p={[.93,-.4,-.1]} r={.25} h={.9} c={dark}/><W points={[[.6,.1,0],[.95,.1,0],[.95,-.3,-.1]]} c={steel} w={8}/>
 </group>;
 if(f==='sorption'||f==='gas_manifold'||f==='flow_reactor')return <group><Bench/>
   <B p={[0,.25,-.35]} s={[1.7,1.7,.16]} c='#e8eef3'/>{[-.56,0,.56].map(x=><group key={x}><C p={[x,-.4,.15]} r={.19} h={.75} c={steel}/><W points={[[x,-.1,.15],[x,.6,.15],[x,.65,-.1]]} c={copper} w={3}/><Ball p={[x,.5,.15]} r={.075} c={blue}/><C p={[x,.8,-.05]} r={.13} h={.06} c={dark} rot={[Math.PI/2,0,0]}/></group>)}
   <W points={[[-.75,.67,.1],[.75,.67,.1]]} w={4}/><Panel p={[1.1,-.7,0]}/>
   {f==='flow_reactor'&&<B p={[0,-.4,.45]} s={[.8,.1,.4]} c={glass} a={.6}/>}
 </group>;
 if(f==='propellant'||f==='distillation')return <group><Bench/>
   {[-.56,.56].map(x=><group key={x}><C p={[x,.1,0]} r={.33} h={1.4}/><Flange y={.85} r={.37}/><R p={[x,-.6,0]} r={.34} c={dark}/><W points={[[x,.9,0],[x,1.1,0],[0,1.1,0],[0,.1,.45]]} c={copper} w={5}/></group>)}
   <W points={[[-.6,-.5,.35],[.6,-.5,.35],[.7,-.5,.1]]} c={blue} w={5}/>{[-.3,.3].map(x=><Ball key={x} p={[x,-.5,.35]} r={.08} c={dark}/>)}<Panel p={[1.15,-.5,.1]}/>
 </group>;
 if(f==='cryocooler'||f==='cryopump'||f==='gas_stream')return <group>
   <C p={[0,-.65,0]} r={.65} h={.2} c={dark}/><C p={[0,-.15,0]} r={.4} h={.8}/><Flange y={.3} r={.46}/><C p={[0,.63,0]} r={.15} h={.63} c={gold}/><C p={[0,1,0]} r={.24} h={.1} c={copper}/>
   {Array.from({length:10},(_,i)=><R key={i} p={[0,-.5+i*.06,0]} r={.42} c={dark}/>)}
   <C p={[.63,-.17,0]} r={.2} h={.7} rot={[0,0,Math.PI/2]}/><B p={[.9,-.18,0]} s={[.25,.43,.45]} c={dark}/>
   <W points={[[.8,-.1,0],[1.25,.1,.1],[1.25,-.8,0],[-.6,-.8,0]]} c={steel} w={6}/><Panel p={[-1,-.6,0]}/>
   {f==='gas_stream'&&<C p={[0,1.2,.2]} r={.07} h={.7} rot={[Math.PI/3,0,0]}/>}
 </group>;
 if(f==='plunge_freezer'||f==='nerve_probe')return <group><Bench/>
   {f==='nerve_probe'?<><B p={[-.6,.3,-.2]} s={[.7,1.2,.65]} c='#e4edf3'/><Panel p={[-.6,.4,.17]}/><W points={[[-.3,.3,.1],[.4,.1,.4],[.7,-.25,.2]]} c={blue} w={7}/><C p={[.7,-.3,.2]} r={.045} h={.65} c={steel} rot={[0,0,.4]}/><Ball p={[.84,-.6,.2]} r={.12} c='#add7ed'/></>
   :<><C p={[0,-.55,0]} r={.54} h={.5} c={dark}/><C p={[0,-.3,0]} r={.42} h={.08} c={glass}/><B p={[-.55,.25,-.2]} s={[.12,1.7,.18]}/><B p={[-.25,.88,-.1]} s={[.7,.15,.4]} c={dark}/><W points={[[.05,.8,0],[.05,-.1,0]]} c={steel} w={4}/><R p={[.05,-.05,0]} r={.07} c={gold}/><Panel p={[.9,-.6,.1]}/></>}
 </group>;
 if(f==='mri')return <group><C r={.95} h={.7} c='#e7edf4' rot={[Math.PI/2,0,0]}/><C p={[0,0,.39]} r={.54} h={.04} c={dark} rot={[Math.PI/2,0,0]}/><C p={[0,0,.42]} r={.45} h={.05} c={glass} a={.35} rot={[Math.PI/2,0,0]}/><B p={[0,-.4,.9]} s={[.52,.12,1.8]} c='#e4edf3'/><B p={[0,-.75,1.2]} s={[.35,.65,.4]}/></group>;
 if(f==='srf'||f==='rf_fixture'||f==='nmr'||f==='metrology'||f==='detector'||f==='diffraction'||f==='dilatometer'||f==='etch'||f==='cold_plate'||f==='optical_bench')return <group>
   {['metrology','srf','nmr'].includes(f)?<Dewar inside={inside}/>:<Bench/>}
   {f==='srf'?<group>{[-.45,-.2,.05,.3,.55].map(y=><mesh key={y} position={[0,y,0]} scale={[.3,.18,.3]}><sphereGeometry args={[1,32,24]}/><meshStandardMaterial color={steel} metalness={.9} roughness={.15}/></mesh>)}<C r={.06} h={1.65}/></group>
   :f==='detector'?<><C p={[0,.05,0]} r={.26} h={1.2}/><B p={[.4,-.4,0]} s={[.75,.5,.6]} c={dark}/><C p={[0,.71,0]} r={.18} h={.15} c={gold}/></>
   :f==='etch'?<><C r={.62} h={.8} a={inside?.13:1}/><Flange y={.45} r={.67}/><C p={[0,0,0]} r={.42} h={.04} c={blue}/><Port p={[.62,0,0]} rot={[0,0,Math.PI/2]}/><W points={[[0,.45,0],[0,.95,0],[.8,.95,0]]} c={copper} w={5}/></>
   :f==='optical_bench'||f==='diffraction'?<><B p={[0,-.6,0]} s={[1.9,.13,1.05]} c={dark}/>{[-.65,0,.65].map(x=><group key={x}><C p={[x,-.15,0]} r={.06} h={.8}/><R p={[x,.3,0]} r={.2} rot={[0,Math.PI/2,0]}/></group>)}<W points={[[-1,.3,0],[1,.3,0]]} c={blue} w={2}/><C p={[0,-.3,0]} r={.32} h={.08} c={gold}/></>
   :f==='dilatometer'?<><C p={[0,0,0]} r={.28} h={1.4} rot={[0,0,Math.PI/2]} a={inside?.2:1}/><W points={[[-.8,0,0],[.8,0,0]]} c={copper} w={5}/><B p={[.9,0,0]} s={[.4,.45,.4]} c={dark}/></>
   :<>{[.5,.05,-.5].map((y,i)=><C key={y} p={[0,y,0]} r={.34-i*.04} h={.05} c={i===2?gold:steel}/>)}<C p={[0,.1,0]} r={.1} h={.7} c={copper}/><W points={[[.1,.6,0],[.1,-.5,0],[.7,-.6,0]]} w={3}/></>}
   <Panel p={[1.05,-.65,.1]}/><Rack n={3}/>
 </group>;
 return null;
}

function Aircraft(){return <group><C r={.07} h={1.5} c={steel} rot={[Math.PI/2,0,0]}/><B s={[1.55,.035,.32]} rot={[0,.22,0]} c='#d7dfe6'/><B p={[0,.13,-.55]} s={[.04,.27,.3]} c={blue}/><B p={[0,.02,-.55]} s={[.6,.025,.18]} c={steel}/></group>;}
function Crystal({c='#97abcb',scale=[.25,.2,.2]}:{c?:string;scale?:V}){return <mesh scale={scale} position={[0,.08,0]} castShadow><octahedronGeometry args={[1,0]}/><meshStandardMaterial color={c} roughness={.2} metalness={.2}/></mesh>;}
function Chip({pattern='transistor'}:{pattern?:string}){return <group><B s={[.95,.05,.7]} c='#465889'/><B p={[0,.035,0]} s={[.7,.012,.48]} c='#222c51'/>{Array.from({length:pattern==='quantum'?5:8},(_,i)=><W key={i} points={[[-.4+i*.1,.06,-.2],[-.4+i*.1,.06,.1],[-.35+i*.1,.06,.1],[-.35+i*.1,.06,-.1]]} c={gold} w={2}/>)}{[-.52,.52].flatMap(x=>[-.25,-.08,.08,.25].map(z=><W key={`${x}${z}`} points={[[x,.02,z],[x*.7,.18,z],[x*.6,.05,z*.7]]} w={2}/>))}</group>;}

/** Specimen geometry changes with the scientific observable and actual profile. */
export function ScientificSpecimen({definition:d}:{definition:SceneDefinition}){
 const m=d.visual?.mechanism??'transport',id=d.archetype.toLowerCase();
 if(m==='mri'||m==='cryostimulation')return <group rotation={m==='mri'?[Math.PI/2,0,0]:[0,0,0]} scale={.6}><Ball p={[0,.75,0]} r={.16} c='#d5ad96'/><B p={[0,.3,0]} s={[.42,.6,.22]} c='#8fb2d3'/>{[-.13,.13].map(x=><C key={x} p={[x,-.25,0]} r={.075} h={.65} c='#8fb2d3'/>)}{[-.3,.3].map(x=><C key={x} p={[x,.25,0]} r={.05} h={.6} c='#d5ad96'/>)}</group>;
 if(id==='bio_cryo_fluorescence_vitrified')return <group><R r={.34} t={.045} c={copper}/><B s={[.48,.02,.48]} c='#6bb4a8' a={.5}/>{Array.from({length:7},(_,i)=><Ball key={i} p={[(i%3)*.13-.13,.035,Math.floor(i/3)*.12-.12]} r={.035} c='#a9dba9'/>)}</group>;
 if(id.includes('fluid_inclusion'))return <group><B s={[.75,.05,.55]} c={glass} a={.25}/><Crystal scale={[.35,.14,.24]} c='#ccd6e4'/><Ball p={[.03,.1,.05]} r={.065} c='#66a3c4'/></group>;
 if(id.includes('icecream'))return <group><mesh scale={[.5,.15,.4]}><sphereGeometry args={[1,32,16]}/><meshStandardMaterial color='#e7d7d0' roughness={.6}/></mesh>{[-.24,0,.24].map(x=><group key={x} position={[x,.1,0]}><Crystal scale={[.08,.035,.12]} c='#a6cce3'/></group>)}</group>;
 if(/nmr|epr|frozen_catalyst/.test(id))return <group><C p={[0,.27,0]} r={.08} h={.8} c={glass} a={.4}/><C p={[0,.1,0]} r={.06} h={.3} c='#aa926c'/><C p={[0,.7,0]} r={.09} h={.06} c={dark}/></group>;
 if(m==='quantum_transport')return <Chip pattern='quantum'/>;
 if(m==='quantum_wiring')return <group>{[-.05,.35].map(y=><C key={y} p={[0,y,0]} r={y>0?.5:.35} h={.055} c={gold}/>)}{Array.from({length:14},(_,i)=>{const a=i*Math.PI/7;return <W key={i} points={[[Math.cos(a)*.35,.55,Math.sin(a)*.35],[Math.cos(a)*.35,.36,Math.sin(a)*.35],[Math.cos(a)*.22,-.02,Math.sin(a)*.22],[Math.cos(a)*.16,-.18,Math.sin(a)*.16]]} c={i%2?copper:steel} w={3}/>;})}<B p={[0,-.21,0]} s={[.35,.06,.3]} c={dark}/></group>;
 if(id==='chem_temperature_dependent_photoluminescence')return <group><B s={[.8,.025,.6]} c={glass} a={.6}/><Crystal c='#ab8aca' scale={[.32,.16,.25]}/></group>;
 if(m==='aerodynamics')return <Aircraft/>;
 if(['quantum','quantum_wiring','transistor','capacitance','photon_detection','electron_microscopy','ion_milling','etching'].includes(m)){
   if(/array|ccd|h2rg|detector/.test(id))return <group><B s={[.9,.06,.8]} c={gold}/>{Array.from({length:36},(_,i)=><B key={i} p={[(i%6)*.11-.27,.05,Math.floor(i/6)*.11-.27]} s={[.09,.02,.09]} c={i%2?'#345482':'#7794ba'}/>)}</group>;
   if(m==='electron_microscopy'||m==='ion_milling')return <group><R r={.4} t={.045} c={gold}/>{Array.from({length:11},(_,i)=><group key={i}><W points={[[-.29+i*.058,0,-.28],[-.29+i*.058,0,.28]]} w={1} c={copper}/><W points={[[-.28,0,-.29+i*.058],[.28,0,-.29+i*.058]]} w={1} c={copper}/></group>)}<Crystal c='#8fc6ba' scale={[.15,.025,.12]}/></group>;
   return <Chip pattern={m}/>;
 }
 if(m==='cryosection')return <group><C r={.32} h={.1} c={steel}/><mesh position={[0,.15,0]} scale={[.33,.18,.26]}><icosahedronGeometry args={[1,2]}/><meshStandardMaterial color='#bd7e91' roughness={.85}/></mesh><B p={[0,.29,0]} s={[.46,.01,.3]} c='#edcfda'/></group>;
 if(m==='mechanical')return <group><B s={[.14,.03,.8]} c={steel}/>{[-.44,.44].map(z=><B key={z} p={[0,0,z]} s={[.38,.055,.3]} c={id.includes('composite')?'#45546b':steel}/>)}{id.includes('fatigue')&&<W points={[[0,.05,-.3],[.02,.05,0],[-.02,.05,.3]]} c={blue}/>}</group>;
 if(m==='optical_alignment')return id.includes('telescope')?<group><R r={.52} t={.05} c={gold}/>{[-.3,0,.3].map(x=><Crystal key={x} scale={[.17,.03,.16]} c='#c5d5e2'/>)}<C p={[0,.35,0]} r={.08} h={.7}/></group>:<mesh rotation={[-Math.PI/2,0,0]}><circleGeometry args={[.55,6]}/><meshStandardMaterial color='#dbe4ec' metalness={1} roughness={.08} side={THREE.DoubleSide}/></mesh>;
 if(m==='preservation'||m==='lyophilization'||m==='droplet_freezing'||m==='cryostimulation'){
   if(/oocyte|shoot_tip|droplet_vitri/.test(id))return <group><B s={[.08,.02,.9]} c='#cce7eb' a={.6}/><Ball p={[0,.07,.2]} r={.09} c='#e8bfab'/><Ball p={[0,.08,.32]} r={.035} c='#be7da1'/></group>;
   if(/tuna|tissue|breast|sediment|soil/.test(id))return <group>{[-.2,.15].map(x=><B key={x} p={[x,.05,0]} s={[.28,.18,.5]} c={id.includes('tuna')?'#b45568':id.includes('soil')?'#75695c':'#c997a9'}/>)}</group>;
   if(/seed|bud|blueber|litchi|strawberry/.test(id))return <group>{Array.from({length:9},(_,i)=><Ball key={i} p={[(i%3)*.25-.25,.08,Math.floor(i/3)*.25-.25]} r={id.includes('seed')?.06:.12} c={id.includes('blueber')?'#5a6fa6':id.includes('strawberry')?'#c56873':'#b49c6c'}/>)}</group>;
   if(/semen|straw/.test(id))return <group>{Array.from({length:8},(_,i)=><C key={i} p={[-.35+i*.1,.08,0]} r={.025} h={.8} c={i%2?glass:'#d4e8d8'} rot={[Math.PI/2,0,0]}/>)}</group>;
   return <group>{[-.28,0,.28].map(x=><group key={x}><C p={[x,.18,0]} r={.1} h={.4} c={glass} a={.5}/><C p={[x,.42,0]} r={.115} h={.08} c={id.includes('pbmc')?blue:'#c7a8d0'}/><C p={[x,.07,0]} r={.085} h={.16} c='#c2b6d9' a={.6}/></group>)}</group>;
 }
 if(m==='milling'||m==='heat_treatment')return <group>{Array.from({length:m==='milling'?12:3},(_,i)=><B key={i} p={[(i%4)*.18-.27,.05+Math.floor(i/4)*.06,(i%3)*.14-.14]} s={m==='milling'?[.12,.1,.13]:[.1,.07,.65]} rot={[0,i*.5,0]} c={id.includes('rubber')?'#39434e':id.includes('gummy')?'#d5a063':steel}/>)}</group>;
 if(m==='battery')return <group>{[-.27,0,.27].map(x=><group key={x}><C p={[x,.19,0]} r={.11} h={.45} c={id.includes('fuel')?'#9daeb8':'#447c8d'}/><C p={[x,.43,0]} r={.05} h={.03} c={gold}/></group>)}</group>;
 if(m==='particle_detection'||m==='magnet_qualification')return <group>{[-.2,.2].flatMap(x=>[-.2,.2].map(z=><B key={`${x}${z}`} p={[x,.16,z]} s={[.33,.33,.33]} c={id.includes('argon')?'#91c9d4':'#dfd8b7'} a={.6}/>))}<W points={[[-.4,.37,-.3],[.4,.37,-.3],[.4,.37,.3],[-.4,.37,.3],[-.4,.37,-.3]]} c={copper}/></group>;
 if(m==='resonance')return <group>{[-.35,0,.35].map(z=><mesh key={z} position={[0,.1,z]} scale={[.27,.27,.2]}><sphereGeometry args={[1,32,24]}/><meshStandardMaterial color={steel} metalness={.95} roughness={.13}/></mesh>)}<C p={[0,.1,0]} r={.07} h={1.2} rot={[Math.PI/2,0,0]}/></group>;
 if(m==='magnetometry')return <group><C r={.025} h={.9} c={steel}/><Crystal scale={[.16,.12,.1]} c={id.includes('graphite')?'#526474':'#7685aa'}/>{id.includes('dilat')&&<B p={[.28,.1,0]} s={[.03,.5,.35]} c={gold}/>}</group>;
 if(m==='transport')return <group><B s={id.includes('hall')?[.62,.04,.5]:[.72,.06,.21]} c={id.includes('niobium')?'#b4bdcc':'#4e627c'}/>{[-.27,-.09,.09,.27].map(x=><W key={x} points={[[x,.05,0],[x,.19,.2],[x*1.5,.03,.5]]} c={x<0?blue:gold} w={3}/>)}{id.includes('hall')&&<><B p={[0,.03,.22]} s={[.1,.05,.25]} c={gold}/><B p={[0,.03,-.22]} s={[.1,.05,.25]} c={gold}/></>}</group>;
 if(m==='thermal_test')return <group><B s={[.65,.55,.5]} c={id.includes('cubesat')?gold:steel}/>{[-.35,.35].map(x=><B key={x} p={[x,.0,.28]} s={[.06,.42,.01]} c={blue}/>)}<W points={[[.2,.28,0],[.5,.5,.2],[.7,.2,.2]]}/></group>;
 if(m==='gas_trapping'||m==='adsorption'||m==='gas_pumping'||m==='distillation'||m==='fluid_transfer')return <group><C p={[-.25,.25,0]} r={.08} h={.6} c={glass} a={.5}/><C p={[.25,.25,0]} r={.08} h={.6} c={glass} a={.5}/><W points={[[-.25,.55,0],[-.25,.7,0],[.25,.7,0],[.25,.55,0]]} c={copper} w={4}/>{Array.from({length:8},(_,i)=><Ball key={i} p={[i%2?.25:-.25,.03+i*.035,0]} r={.035} c='#a7a5b0'/>)}</group>;
 if(m==='calorimetry'||m==='heat_leak'||m==='metrology')return <group><C r={.3} h={.1} c={copper}/><C p={[0,.09,0]} r={.16} h={.07} c={id.includes('insulation')?'#e5d3a4':gold}/>{[.22,.27,.32].map(r=><R key={r} r={r} p={[0,.12,0]} c={steel}/>)}<W points={[[.12,.15,0],[.3,.32,.1],[.6,.07,.3]]} c={blue}/></group>;
 if(m==='cryoneurolysis')return <group><C r={.07} h={1.1} c='#d59ba7' rot={[0,0,Math.PI/2]}/><C p={[0,.35,0]} r={.025} h={.5}/><Ball p={[0,.05,0]} r={.17} c={glass}/></group>;
 return <group><B s={[.85,.025,.6]} c={glass} a={.5}/><Crystal c={m==='microscopy'?'#ba9dcc':m==='spectroscopy'?'#88bcc5':'#aa94bc'}/>{m==='microscopy'&&Array.from({length:5},(_,i)=><group key={i} position={[(i%3)*.16-.18,.01,Math.floor(i/3)*.18-.05]}><Crystal scale={[.09,.02,.07]} c='#cbd6e7'/></group>)}</group>;
}

export function ScientificExperiment({definition:d,animating}:{definition:SceneDefinition;animating:boolean}){
 const m=d.visual?.mechanism??'measurement',motion=useRef<THREE.Group>(null),signal=useRef<THREE.Mesh>(null);
 useFrame(({clock})=>{if(!animating)return;const t=clock.elapsedTime;if(motion.current){if(['mechanical','milling','cryosection','magnetometry'].includes(m))motion.current.position.y=Math.sin(t*2)*.06;else if(m==='resonance')motion.current.rotation.y=t*.15;}if(signal.current)signal.current.position.x=Math.sin(t*1.3)*.55;});
 const rfSpectroscopy=/nmr|epr|frozen_catalyst/.test(d.archetype);
 const optical=!rfSpectroscopy&&['spectroscopy','photon_detection','optical_alignment','microscopy','diffraction','electron_microscopy','ion_milling','etching'].includes(m);
 return <group><Bench/><C p={[0,-.6,0]} r={.65} h={.08} c={gold}/><group ref={motion} position={[0,-.48,0]}><ScientificSpecimen definition={d}/></group>
   {optical&&<><C p={[0,.6,0]} r={.15} h={.7} c={dark}/><C p={[0,.18,0]} r={.1} h={.16}/><B p={[.75,.45,-.3]} s={[.13,1.45,.18]}/><B p={[.35,.95,-.2]} s={[.95,.15,.4]} c={steel}/><W points={[[-1,.45,0],[0,.45,0],[0,-.32,0],[.85,.45,.2]]} c={m==='spectroscopy'?'#65b5bc':'#c0a6df'} w={3}/><Panel p={[1,-.6,.2]}/>{m==='diffraction'&&<R p={[0,-.15,0]} r={.8} rot={[0,Math.PI/2,0]} c={dark}/>}</>}
   {['quantum','quantum_wiring','quantum_transport'].includes(m)&&<>{[.8,.4,0].map((y,i)=><C key={y} p={[0,y,0]} r={.65-i*.1} h={.05} c={i===2?copper:steel}/>)}{[-.4,-.2,0,.2,.4].map(x=><W key={x} points={[[x,.95,0],[x,.8,0],[x*.8,.4,0],[x*.6,0,0],[x*.3,-.4,0]]} w={3}/>)}<Rack n={5}/></>}
   {(rfSpectroscopy||m==='quantum_transport'||d.archetype==='mat_magnetoresistance_10T')&&<>{[-.5,-.4,-.3,.3,.4,.5].map(y=><R key={y} p={[0,y,0]} r={.74} c={copper}/>)}<Panel p={[1,-.5,.2]}/></>}
   {['transport','transistor','capacitance','magnetometry'].includes(m)&&<><Panel p={[-1,-.55,0]}/><Panel p={[1,-.55,0]}/>{[-.3,.3].map(x=><W key={x} points={[[x,-.4,.2],[x*2,-.2,.5],[x*3,-.5,.15]]} c={x<0?blue:gold} w={3}/>)}{m==='magnetometry'&&[-.4,.4].map(y=><R key={y} p={[0,y,0]} r={.5} c={copper}/>)}</>}
   {['mechanical','heat_treatment'].includes(m)&&<>{[-.7,.7].map(x=><C key={x} p={[x,0,0]} r={.06} h={1.65}/>)}<B p={[0,.78,0]} s={[1.7,.13,.5]}/><B p={[0,.2,0]} s={[.35,.3,.3]} c={dark}/><Panel p={[1,-.6,0]}/></>}
   {['preservation','lyophilization','milling','thermal_test','battery','droplet_freezing'].includes(m)&&<><B p={[0,.05,-.6]} s={[1.7,1.25,.12]} c={steel}/><B p={[0,.68,0]} s={[1.7,.1,1.25]} c={steel}/><B p={[0,.05,.61]} s={[1.7,1.2,.02]} c={glass} a={.12}/><Panel p={[1.05,-.55,.25]}/></>}
   {['heat_leak','calorimetry','adsorption','gas_trapping','gas_pumping','fluid_transfer','distillation','metrology'].includes(m)&&<><C p={[0,-.05,0]} r={.68} h={1.2} c={glass} a={.12}/><Flange y={.6} r={.72}/>{[-.4,.4].map(x=><W key={x} points={[[x,.65,0],[x,.95,0],[x*2,.95,0],[x*2,-.5,0]]} c={copper} w={3}/>)}<Panel p={[1,-.6,.2]}/></>}
   {animating&&<mesh ref={signal} position={[0,.25,.35]}><sphereGeometry args={[.035,12,12]}/><meshBasicMaterial color={blue}/></mesh>}
 </group>;
}
