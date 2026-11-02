import { useRef, type ReactNode } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line, Html } from '@react-three/drei';
import * as THREE from 'three';
import { hasInstalled, sceneComponents, type SceneDefinition } from './registry';
import type { ConfigurationDetails } from '../types/backend';
import type { SceneViewMode } from './core/LabCanvas';
import { ScientificExperiment, SpecializedMachine } from './ScientificModels';

type V = [number, number, number];
type Highlight = { id: string; outcome: 'pass' | 'fail' | 'unknown' | null } | null;
const steel = '#b7c4cf', white = '#e7edf0', navy = '#24324a', copper = '#c89453', gold = '#deb869';
function Cylinder({ at = [0,0,0], radius = .5, height = .1, color = steel, opacity = 1, open = false }: {at?: V; radius?:number;height?:number;color?:string;opacity?:number;open?:boolean}) {
  return <mesh position={at} castShadow receiveShadow><cylinderGeometry args={[radius,radius,height,48,1,open]} /><meshStandardMaterial color={color} roughness={.32} metalness={.55} transparent={opacity < 1} opacity={opacity} side={THREE.DoubleSide} depthWrite={opacity === 1} /></mesh>;
}
function Box({ at=[0,0,0], size, color=white, opacity=1, rotation }: {at?:V;size:V;color?:string;opacity?:number;rotation?:V}) {
  return <mesh position={at} rotation={rotation} castShadow receiveShadow><boxGeometry args={size} /><meshStandardMaterial color={color} roughness={.38} metalness={.24} transparent={opacity < 1} opacity={opacity} depthWrite={opacity === 1} /></mesh>;
}
function Wire({ points, color=copper, width=2 }: {points: V[];color?:string;width?:number}) { return <Line points={points} color={color} lineWidth={width} />; }
function Ring({ at, radius, color=steel, rotation=[Math.PI/2,0,0] }: {at:V;radius:number;color?:string;rotation?:V}) {
  return <mesh position={at} rotation={rotation} castShadow><torusGeometry args={[radius,.025,8,56]} /><meshStandardMaterial color={color} metalness={.75} roughness={.25} /></mesh>;
}
function Bolts({ y, radius, count=10 }: {y:number;radius:number;count?:number}) { return <>{Array.from({length:count},(_,i) => <Cylinder key={i} at={[Math.cos(i/count*Math.PI*2)*radius,y,Math.sin(i/count*Math.PI*2)*radius]} radius={.025} height={.04} color={navy} />)}</>; }
function Instrument({ at, color=navy }: {at: V;color?:string}) { return <group position={at}><Box size={[.6,.32,.44]} color={white} /><Box at={[0,0,.23]} size={[.5,.22,.02]} color={color} /><Box at={[-.08,.015,.245]} size={[.22,.09,.008]} color="#8cb4b9" /><Cylinder at={[.19,-.02,.25]} radius={.045} height={.03} /><Box at={[0,-.18,0]} size={[.42,.04,.28]} color={navy} /></group>; }

// Machine assemblies are representative geometry. Only sourced installed options
// are added; experiment requirements are shown separately in the Experiment view.
function Magnet({ inside, config, color }: {inside:boolean;config:ConfigurationDetails|null;color:(id:string,base:string)=>string}) {
  const housing=config?.visualization?.geometry?.outer?.shape;
  const boxHousing=typeof housing==='string'&&housing.includes('box');
  return <group>
    <Cylinder at={[0,-.85,0]} radius={.87} height={.16} color={navy} />
    {boxHousing?<><Box at={[0,-.05,0]} size={[1.5,1.52,1.4]} color={white} opacity={inside?.08:1}/><Box at={[.9,-.25,-.25]} size={[.3,1.2,.9]} color={steel}/></>:<Cylinder at={[0,-.05,0]} radius={.77} height={1.52} color={white} opacity={inside?.14:1} open={inside} />}
    <Cylinder at={[0,.76,0]} radius={.83} height={.12} /><Bolts y={.84} radius={.7} />
    <Cylinder at={[0,.86,0]} radius={.22} height={.1} color={navy} />
    <Cylinder at={[0,1.03,0]} radius={.11} height={.28} />
    <group position={[-.45,.94,-.1]}><Cylinder radius={.16} height={.26} /><Box at={[0,.18,0]} size={[.25,.12,.23]} color={navy} /><Wire points={[[0,.16,0],[-.3,.3,0],[-.7,.1,0],[-.9,-1.3,-.1]]} width={4} color="#647487" /></group>
    {inside && <>
      {hasInstalled(config,'magnetic_field.max') && <group>{Array.from({length:16},(_,i) => <Ring key={i} at={[0,-.6+i*.045,0]} radius={.48} color={color('magnet_solenoid',copper)} />)}
        <Cylinder at={[0,-.23,0]} radius={.43} height={.77} color={color('magnet_solenoid',copper)} opacity={.17} open /></group>}
      <Cylinder at={[0,.1,0]} radius={.16} height={1.28} color={steel} opacity={.2} open />
      <Cylinder at={[0,-.48,0]} radius={.16} height={.1} color={color('cold_stage',gold)} />
      <Cylinder at={[0,-.4,0]} radius={.13} height={.025} color={color('sample_mount',gold)} />
      {Array.from({length:8},(_,i)=><Wire key={i} points={[[Math.cos(i*Math.PI/4)*.57,.72,Math.sin(i*Math.PI/4)*.57],[Math.cos(i*Math.PI/4)*.43,-.5,Math.sin(i*Math.PI/4)*.43]]} color={copper} width={1}/>)}
      {hasInstalled(config,'electrical.dc_lines') && [-.09,-.03,.03,.09].map((x,i) => <Wire key={i} points={[[x,1.15,0],[x,.4,.05],[x,-.36,.03]]} color={color('dc_wiring',i%2?'#8c93c7':'#609da7')} width={2} />)}
      {hasInstalled(config,'module.vsm') && <><Cylinder at={[0,.4,0]} radius={.012} height={1.1} color={color('vsm_module',steel)} /><Ring at={[0,-.13,0]} radius={.12} color={copper} /><Ring at={[0,-.35,0]} radius={.12} color={copper} /></>}
    </>}
    {[-.55,.55].flatMap(x => [-.45,.45].map(z => <Box key={`${x}${z}`} at={[x,-1.04,z]} size={[.12,.3,.12]} color={navy} />))}
    <Instrument at={[1.3,-.68,.2]} /><Wire points={[[.1,1,0],[.8,1.1,-.1],[1.4,.55,0],[1.35,-.6,.2]]} color={navy} width={3} />
  </group>;
}
function Microtome({inside,config,color}:{inside:boolean;config:ConfigurationDetails|null;color:(id:string,base:string)=>string}) {
  return <group><Box at={[0,-.48,0]} size={[1.55,1.28,1.25]} /><Box at={[0,-.4,.64]} size={[1.38,.9,.03]} color="#c8d5dc" />
    <Box at={[0,.18,0]} size={[1.5,.1,1.3]} color={navy} />
    <Box at={[0,.22,.1]} size={[1.25,.1,1.02]} color={color('cold_stage',steel)} />
    <Box at={[0,.45,-.44]} size={[1.45,.55,.16]} color={white} />
    {!inside && <Box at={[0,.48,.02]} size={[1.35,.04,1.03]} color="#d1e6ef" opacity={.35} rotation={[-.3,0,0]} />}
    <Cylinder at={[.18,.31,-.12]} radius={.18} height={.16} color={color('specimen_head',steel)} /><Box at={[.18,.43,-.12]} size={[.18,.12,.12]} color="#ad6e79" />
    <Box at={[.18,.34,.2]} size={[.53,.04,.12]} color={steel} rotation={[.2,0,0]} />
    <Box at={[-.4,.33,.1]} size={[.2,.04,.3]} color="#e3eee7" /><Ring at={[.91,0,0]} radius={.27} color={navy} rotation={[0,Math.PI/2,0]} />
    <Box at={[-.3,.8,-.47]} size={[.46,.27,.08]} color={navy} /><Box at={[-.3,.8,-.42]} size={[.34,.15,.01]} color="#91b8c4" />
    {hasInstalled(config,'temperature.specimen_head.range') && <Wire points={[[.18,.31,-.12],[.35,.26,-.3],[.5,.25,-.4]]} color={copper} />}
    {[-.55,.55].flatMap(x => [-.4,.4].map(z => <Cylinder key={`${x}${z}`} at={[x,-1.16,z]} radius={.08} height={.13} color={navy} />))}
  </group>;
}
function OpticalStage({inside,config,color}:{inside:boolean;config:ConfigurationDetails|null;color:(id:string,base:string)=>string}) {
  return <group><Box at={[0,-.75,0]} size={[1.8,.18,1.4]} color={navy} />
    <Box at={[0,-.36,0]} size={[1.15,.4,.9]} color={steel} /><Cylinder at={[0,-.11,0]} radius={.51} height={.16} color={navy} />
    <Cylinder at={[0,.03,0]} radius={.45} height={.12} color={steel} opacity={inside?.25:1} />
    <Cylinder at={[0,.06,0]} radius={.22} height={.13} color={color('cold_stage',copper)} /><Box at={[0,.15,0]} size={[.36,.015,.24]} color={color('sample_mount','#c4dedd')} opacity={.75} />
    {hasInstalled(config,'optical_access')&&<><Ring at={[0,.15,0]} radius={.25} color={navy}/><Cylinder at={[0,.15,0]} radius={.22} height={.01} color="#b7dbe2" opacity={.3}/></>}
    <Bolts y={.115} radius={.36} count={8} />
    {/lnp|ln2/i.test(config?.id??'') && <><Wire points={[[-.5,-.3,0],[-.9,-.35,0],[-1,-.5,-.5]]} width={5} color="#8199aa"/><Cylinder at={[-1,-.6,-.5]} radius={.2} height={.6}/></>}
    <Instrument at={[1.15,-.55,.25]} />
  </group>;
}
function OpticalCryostat({inside,config,color,probe}:{inside:boolean;config:ConfigurationDetails|null;color:(id:string,base:string)=>string;probe:boolean}) {
  const optical=hasInstalled(config,'optical_access');
  const probeCount=hasInstalled(config,'electrical.probe_arms') ? Math.min(6,config?.capabilities.find(c=>c.key==='electrical.probe_arms')?.value.n??0) : 0;
  const shape=config?.visualization?.geometry?.outer?.shape??'';
  return <group><Cylinder at={[0,-.83,0]} radius={probe?.9:.48} height={.16} color={navy} />
    {String(shape).includes('box')?<Box at={[0,-.05,0]} size={[1.4,.9,1.1]} color={white} opacity={inside?.12:1}/>:<Cylinder at={[0,-.05,0]} radius={probe?.78:.42} height={probe?.72:1.4} color={white} opacity={inside?.17:1} open={inside} />}
    <Cylinder at={[0,probe?.36:.71,0]} radius={probe?.83:.48} height={.08} /><Bolts y={probe?.42:.77} radius={probe?.7:.38} />
    <Cylinder at={[0,-.3,0]} radius={.15} height={.65} color={color('cold_stage',copper)} /><Cylinder at={[0,.05,0]} radius={.23} height={.04} color={color('sample_mount',gold)} />
    {optical && (probe ? <Ring at={[0,.44,0]} radius={.29} color={color('optical_windows',navy)} /> : [0,Math.PI/2,Math.PI,3*Math.PI/2].map((angle,i) => <group key={i} rotation={[0,angle,0]}><Ring at={[0,.1,.44]} radius={.17} rotation={[0,0,0]} color={color('optical_windows',navy)} /><Box at={[0,.1,.45]} size={[.25,.25,.008]} color="#badbdc" opacity={.35} /></group>))}
    {probe && Array.from({length:probeCount},(_,i) => <group key={i} rotation={[0,i*Math.PI*2/probeCount,0]}><Box at={[.55,.1,0]} size={[.35,.12,.17]} color={navy} /><Wire points={[[.45,.13,0],[.18,.15,0],[.07,.07,0]]} color={color('dc_wiring',copper)} width={3} /></group>)}
    <Cylinder at={[-.5,-.3,-.25]} radius={.16} height={.9} color={steel} /><Instrument at={[1.1,-.65,.25]} />
  </group>;
}
function Dilution({inside,config,color}:{inside:boolean;config:ConfigurationDetails|null;color:(id:string,base:string)=>string}) {
  const stageCount=Math.max(3,Math.min(7,config?.visualization?.geometry?.stages?.length||4));
  const plateYs=Array.from({length:stageCount},(_,i)=>.75-i*(1.4/(stageCount-1)));
  return <group><Cylinder at={[0,1.1,0]} radius={.85} height={.13} color={steel} /><Bolts y={1.19} radius={.72} />
    {!inside && <Cylinder at={[0,-.05,0]} radius={.78} height={2.15} color={white} opacity={.95} />}
    {plateYs.map((y,i) => <group key={i}><Cylinder at={[0,y,0]} radius={.69-i*(.32/(stageCount-1))} height={.06} color={color(i===stageCount-1?'mxc_wiring_bundle':'cold_stage',i<2?steel:copper)} /><Bolts y={y+.04} radius={.58-i*(.32/(stageCount-1))} count={8} /></group>)}
    {[0,Math.PI*2/3,Math.PI*4/3].map((a,i) => <group key={i}><Cylinder at={[Math.cos(a)*.54,.4,Math.sin(a)*.54]} radius={.025} height={1.3} color={steel} /><Cylinder at={[Math.cos(a)*.28,-.42,Math.sin(a)*.28]} radius={.018} height={.5} color={copper} /></group>)}
    <Cylinder at={[0,-.8,0]} radius={.18} height={.2} color={color('mxc_wiring_bundle',gold)} /><Box at={[0,-.94,0]} size={[.16,.05,.16]} color={color('sample_mount',navy)} />
    {hasInstalled(config,'electrical.coax_lines') && Array.from({length:12},(_,i) => { const x=-.32+(i%6)*.12,z=(i<6?-.1:.16); return <Wire key={i} points={[[x,1.17,z],[x,.78,z],[x*.85,.25,z],[x*.65,-.25,z],[x*.4,-.66,z],[x*.25,-.9,z]]} color={color('mxc_wiring_bundle',i%3===0?'#9fa9ba':copper)} width={2} />; })}
    <Cylinder at={[-.4,1.35,0]} radius={.17} height={.38} color={navy} /><Cylinder at={[.34,1.28,0]} radius={.12} height={.22} color={steel} />
  </group>;
}

function Experiment({archetype,animating,time}:{archetype:SceneDefinition['archetype'];animating:boolean;time:React.MutableRefObject<number>}) {
  const moving=useRef<THREE.Group>(null);
  const signal=useRef<THREE.Mesh>(null);
  useFrame((_,delta) => {
    if (!animating) return;
    time.current += Math.min(delta,.05);
    if(signal.current){
      if(['transport','magnetoresistance','nano_transport'].includes(archetype)) signal.current.position.x = -.24 + ((time.current*.4)%1)*.48;
      else if(archetype==='quantum'||archetype==='quantum_chip') signal.current.position.y = 1.05-((time.current*.25)%1)*1.9;
      else signal.current.position.y=.05+((time.current*.5)%1)*.47;
    }
    if(moving.current) {
      if(archetype==='cryosection') moving.current.position.z=Math.sin(time.current*1.8)*.15;
      if(archetype==='vsm') moving.current.position.y=Math.sin(time.current*3)*.12;
      if(archetype==='phase_transition') moving.current.rotation.z=Math.sin(time.current*.7)*.12;
    }
  });
  if (['transport','magnetoresistance','nano_transport'].includes(archetype)) return <group position={[0,.05,0]}>
    <Cylinder radius={.72} height={.1} color={gold} /><Box at={[0,.08,0]} size={[.95,.03,.63]} color={white} />
    {archetype==='nano_transport' ? <group><Box at={[0,.13,0]} size={[.5,.035,.4]} color="#54537c"/>
      <Wire points={[[-.2,.16,0],[.2,.16,0]]} color={gold} width={5}/>{[-.09,0,.09].map((x,i)=><Box key={i} at={[x,.17,.08]} size={[.025,.015,.12]} color={copper}/>)}</group>
      : <Box at={[0,.13,0]} size={[.62,.065,.2]} color="#4b5365" rotation={[0,0,.015]} />}
    {archetype==='magnetoresistance' && <group>{[-.38,-.31,-.24,.34,.41,.48].map((y,i)=><Ring key={i} at={[0,y,0]} radius={.79} color={copper}/>)}
      <Wire points={[[.87,-.4,0],[.87,.6,0],[.8,.5,0],[.87,.6,0],[.94,.5,0]]} color="#7797b1" width={3}/></group>}
    {archetype==='nano_transport' && <><Ring at={[0,-.24,0]} radius={.82} color={copper}/><Ring at={[0,-.08,0]} radius={.82} color={steel} rotation={[0,0,Math.PI/2]}/><Ring at={[0,-.08,0]} radius={.82} color="#b0a2c8" rotation={[0,Math.PI/2,0]}/></>}
    {animating&&<mesh ref={signal} position={[-.24,.19,0]}><sphereGeometry args={[.028,12,12]}/><meshBasicMaterial color="#6d9eb1"/></mesh>}
    {[-.24,-.08,.08,.24].map((x,i) => <group key={i}><Cylinder at={[x,.18,0]} radius={.025} height={.02} color={steel} /><Wire points={[[x,.18,0],[x,.37,.1],[x*1.9,.22,.5],[x*2,.14,.68]]} color={i===0||i===3?'#467f98':'#9383b5'} width={4} />
      <Box at={[x*1.9,.14,.54]} size={[.08,.03,.09]} color={gold} /></group>)}
    {Array.from({length:12},(_,i) => <Cylinder key={i} at={[Math.cos(i/12*Math.PI*2)*.62,.1,Math.sin(i/12*Math.PI*2)*.62]} radius={.025} height={.04} color={steel} />)}
    <Instrument at={[-1.15,-.15,.1]} color="#467f98" /><Instrument at={[1.15,-.15,.1]} color="#9383b5" />
    <Wire points={[[-.48,.14,.68],[-.9,.2,.8],[-1.15,-.05,.34]]} color="#467f98" width={3} /><Wire points={[[.16,.14,.68],[.8,.24,.8],[1.15,-.05,.34]]} color="#9383b5" width={3} />
    <Html position={[0,-.55,.6]} center><span className="apparatus-label">{archetype==='magnetoresistance'?'Magnetoresistance · four contacts in an applied field':archetype==='nano_transport'?'Hybrid nanodevice · representative vector-field geometry':'Four-probe resistance · outer current / inner voltage'}</span></Html>
  </group>;
  if(archetype==='cryosection') return <group><Box at={[0,-.25,0]} size={[1.5,.18,1.3]} color={steel} />
    <group ref={moving}><Cylinder at={[0,.03,-.15]} radius={.24} height={.3} color={navy} />
      <mesh position={[0,.25,-.15]} scale={[.25,.16,.18]}><icosahedronGeometry args={[1,2]} /><meshStandardMaterial color="#b97d8d" roughness={.85} /></mesh>
      <Box at={[0,.3,-.15]} size={[.48,.02,.3]} color="#e6c6cd" /></group>
    <Box at={[0,.19,.22]} size={[.9,.035,.21]} color={steel} rotation={[.2,0,0]} /><Box at={[0,.08,.48]} size={[.6,.016,.3]} color="#e1eeeb" opacity={.75} />
    <Box at={[0,.095,.45]} size={[.32,.008,.16]} color="#cc95a8" opacity={.65} /><Html position={[0,-.5,.6]} center><span className="apparatus-label">Tissue block → blade → collection slide</span></Html></group>;
  if (archetype==='vsm') return <group><group ref={moving}><Cylinder at={[0,.5,0]} radius={.035} height={1.6} color={steel} /><Box at={[0,-.32,0]} size={[.12,.16,.1]} color={navy} /></group>
    {[-.5,-.1].map(y => Array.from({length:5},(_,i) => <Ring key={`${y}${i}`} at={[0,y+i*.028,0]} radius={.23} color={copper} />))}
    <Cylinder at={[0,-.3,0]} radius={.6} height={1.05} color={steel} opacity={.13} open /><Instrument at={[1.1,-.3,0]} /><Wire points={[[.22,-.1,0],[.6,-.1,.1],[1.1,-.2,.23]]} color={copper} />
    <Html position={[0,-.75,.5]} center><span className="apparatus-label">Oscillating sample · stationary pickup coils</span></Html></group>;
  if(archetype==='quantum'||archetype==='quantum_chip') return <group><Dilution inside config={null} color={(_,base)=>base} />
    {animating&&<mesh ref={signal} position={[.15,1,0]}><sphereGeometry args={[.04,12,12]}/><meshBasicMaterial color="#cd8a6f"/></mesh>}
    {[-.3,-.15,0,.15,.3].map((x,i) => <Wire key={i} points={[[x,1.2,0],[x,.75,0],[x*.8,.25,0],[x*.6,-.2,0],[x*.3,-.9,0]]} color={copper} width={3} />)}
    {archetype==='quantum_chip'&&<group position={[.85,-.7,.45]}><Box size={[.62,.08,.5]} color={gold}/><Box at={[0,.05,0]} size={[.43,.018,.32]} color="#565487"/>
      <Wire points={[[-.15,.07,-.1],[-.15,.07,.08],[-.05,.07,.08],[-.05,.07,-.06],[.05,.07,-.06],[.05,.07,.08],[.15,.07,.08]]} color={gold} width={3}/>
      <Wire points={[[-.29,.06,0],[-.45,.1,0],[-.65,.1,-.25]]} color={copper} width={3}/></group>}
    <Html position={[0,-1.2,.5]} center><span className="apparatus-label">{archetype==='quantum_chip'?'Representative chip inset · not a measured device layout':'Representative wiring & thermal anchors'}</span></Html></group>;
  if(['raman','photoluminescence','microscopy','phase_transition'].includes(archetype)) {
    const spectroscopy=archetype==='raman'||archetype==='photoluminescence';
    return <group><Box at={[0,-.3,0]} size={[1.15,.16,.9]} color={steel} /><Cylinder at={[0,-.17,0]} radius={.3} height={.1} color={copper} />
      <Box at={[0,-.07,0]} size={[.55,.018,.35]} color="#d8e6e5" opacity={.7} /><group ref={moving}>
        {archetype==='raman' ? <mesh position={[0,-.015,0]} scale={[.14,.045,.1]}><octahedronGeometry args={[1,0]}/><meshStandardMaterial color="#839ca2" metalness={.35} roughness={.3}/></mesh>
        : archetype==='microscopy' ? <><Ring at={[0,-.035,0]} radius={.12} color={copper}/><Box at={[0,-.02,0]} size={[.16,.008,.16]} color="#79a695" opacity={.75}/></>
        : <Box at={[0,-.04,0]} size={[.24,.02,.18]} color={archetype==='phase_transition'?'#a79bc7':'#bba185'} />}
        {archetype==='phase_transition' && [-.08,0,.08].flatMap(x=>[-.05,.03].map((z,i)=><mesh key={`${x}${z}`} position={[x,-.02,z]} rotation={[0,x*8,0]} scale={[.05,.008,.04]}><octahedronGeometry args={[1,0]}/><meshStandardMaterial color={i?'#cab488':'#8e98bc'} roughness={.6}/></mesh>))}
      </group>
      <Cylinder at={[0,.53,0]} radius={.16} height={.5} color={navy} /><Cylinder at={[0,.22,0]} radius={.105} height={.12} color={steel} />
      {animating&&<mesh ref={signal} position={[.04,.1,.025]}><sphereGeometry args={[.025,12,12]}/><meshBasicMaterial color={archetype==='raman'?'#b69bc7':'#d6aa76'}/></mesh>}
      <Box at={[.45,.9,0]} size={[1.2,.16,.4]} color={white} /><Box at={[.8,.2,-.2]} size={[.16,1.4,.22]} color={white} />
      {spectroscopy && <><Box at={[-1,.62,0]} size={[.45,.28,.32]} color={navy} /><Wire points={[[-.78,.62,0],[0,.62,0],[0,.03,0]]} color={animating?'#50a690':'#91b0ac'} width={animating?4:2} />
        <Wire points={[[.04,.03,.025],[.04,.63,.025],[.9,.63,.025],[1.1,.25,.15]]} color={archetype==='raman'?'#b8a0ce':'#dbad69'} width={animating?4:2} />
        {archetype==='raman'?<><Box at={[1.15,.13,.14]} size={[.7,.4,.5]} color={navy}/><Box at={[.94,.15,.4]} size={[.04,.22,.01]} color={steel}/><Ring at={[.62,.63,0]} radius={.08} rotation={[0,Math.PI/2,0]} color={steel}/></>
          : <><Instrument at={[1.15,.1,.14]} color="#a58569"/><Box at={[.6,.63,.02]} size={[.04,.19,.19]} color="#bba4ca" opacity={.6}/>
            <mesh position={[0,.02,0]}><sphereGeometry args={[.11,16,16]}/><meshBasicMaterial color="#d9a86d" transparent opacity={animating?.2:.05}/></mesh></>}
      </>}
      {archetype==='microscopy'&&<><Box at={[-.8,.72,0]} size={[.35,.23,.3]} color="#6c8b82"/><Wire points={[[-.6,.72,0],[0,.72,0],[0,0,0]]} color="#83b8a7" width={3}/>
        <Wire points={[[.035,0,.02],[.035,.74,.02],[.65,.74,.02]]} color="#ca9db4" width={3}/><Box at={[.78,.74,.02]} size={[.28,.22,.25]} color={navy}/></>}
      {archetype==='phase_transition'&&<><Cylinder at={[0,-.6,0]} radius={.13} height={.32} color={navy}/><Wire points={[[0,-.45,0],[0,-.05,0],[0,.2,0]]} color="#b7a6cf" width={3}/></>}
      {archetype==='phase_transition' && <><Ring at={[0,-.45,0]} radius={.2} color={navy} /><Ring at={[0,.15,0]} radius={.2} color={navy} /></>}
      <Html position={[0,-.85,.6]} center><span className="apparatus-label">{archetype==='raman'?'Excitation → scattered light → spectrometer':archetype==='photoluminescence'?'Excitation → sample emission → detector':archetype==='microscopy'?'Cooled specimen · excitation & fluorescence collection':'Illumination · cooled stage · crossed polarizers'}</span></Html>
    </group>;
  }
  return null;
}

export default function SceneManager({ configuration, definition, viewMode, highlight, animating, labels, onSelect }: {
  configuration: ConfigurationDetails | null; definition: SceneDefinition; viewMode: SceneViewMode; highlight: Highlight;
  animating: boolean; labels: boolean; onSelect: (id:string)=>void;
}) {
  const time=useRef(0);
  const color=(id:string,base:string) => highlight?.id===id ? highlight.outcome==='fail'?'#c36363':highlight.outcome==='unknown'?'#9c93ad':'#82adb8' : base;
  const inside=viewMode==='inside';
  const outer=configuration?.visualization?.geometry?.outer;
  const scales:Record<string,number>={mm:.001,cm:.01,m:1,inch:.0254};
  const length=(q:any)=>typeof q?.value==='number'&&scales[q.unit]!==undefined?q.value*scales[q.unit]:null;
  const height=length(outer?.height),width=length(outer?.width_or_diameter);
  const dimensionsExact=!/lower bound|at least|not published/i.test(outer?.height?.location??'');
  const aspect=height&&width&&dimensionsExact?Math.max(.7,Math.min(1.3,height/width/1.4)):1;
  return <group scale={viewMode==='experiment'?[1,1,1]:[1,aspect,1]}>
    {viewMode==='experiment' ? definition.visual?.mechanism?<ScientificExperiment definition={definition} animating={animating}/>:<Experiment archetype={definition.archetype} animating={animating} time={time} /> : <>
      {definition.family==='microtome' && <Microtome inside={inside} config={configuration} color={color} />}
      {definition.family==='magnet' && <Magnet inside={inside} config={configuration} color={color} />}
      {definition.family==='optical_stage' && <OpticalStage inside={inside} config={configuration} color={color} />}
      {definition.family==='optical_cryostat' && <OpticalCryostat inside={inside} config={configuration} color={color} probe={false} />}
      {definition.family==='probe_station' && <OpticalCryostat inside={inside} config={configuration} color={color} probe />}
      {definition.family==='dilution' && <Dilution inside={inside} config={configuration} color={color} />}
      {!['microtome','magnet','optical_stage','optical_cryostat','probe_station','dilution'].includes(definition.family)&&<SpecializedMachine definition={definition} configuration={configuration} inside={inside}/>}
      {sceneComponents(definition.family).map(c => <group key={c.id} position={c.position}>
        {(labels || highlight?.id===c.id) && <Html center distanceFactor={7} zIndexRange={[6,0]}><button aria-label={`Inspect ${c.title}`} className={`hotspot ${highlight?.id===c.id?highlight.outcome??'selected':''}`} onClick={() => onSelect(c.id)}>{highlight?.id===c.id ? c.title : '+'}</button></Html>}
        {highlight?.id===c.id && <mesh><sphereGeometry args={[.13,16,16]} /><meshBasicMaterial color={color(c.id,'#94b9c3')} transparent opacity={.15} wireframe={highlight.outcome==='unknown'} depthTest={false} /></mesh>}
      </group>)}
    </>}
  </group>;
}
