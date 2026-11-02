import { Canvas } from '@react-three/fiber';
import { OrbitControls, Line, Environment, Lightformer } from '@react-three/drei';
import type { SceneDefinition } from '../registry';
import { Component, useState, type ReactNode } from 'react';
import { ScientificSpecimen } from '../ScientificModels';
import { RotateCw } from 'lucide-react';
class SampleBoundary extends Component<{children:ReactNode},{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return {failed:true};}render(){return this.state.failed?<div className="sample-fallback">3D unavailable · {this.props.children?'Review the sourced procedure below.':''}</div>:this.props.children;}}

function Sample({definition}:{definition:SceneDefinition}) {
  if(definition.visual?.mechanism)return <group><mesh position={[0,-.14,0]} receiveShadow><cylinderGeometry args={[.8,.85,.1,64]}/><meshStandardMaterial color="#d7b46a" metalness={.8} roughness={.24}/></mesh><ScientificSpecimen definition={definition}/></group>;
  const kind=definition.archetype;
  const quantum=['quantum','quantum_chip'].includes(kind);
  const optical=['raman','photoluminescence','microscopy','phase_transition'].includes(kind);
  return <group rotation={[0,-.2,0]}>
    <mesh position={[0,-.17,0]} receiveShadow><cylinderGeometry args={[.8,.85,.12,48]}/><meshStandardMaterial color={quantum?'#adbfc9':optical?'#a6becb':'#cda45d'} metalness={.55} roughness={.3}/></mesh>
    {kind==='cryosection'?<><mesh position={[0,.05,0]} scale={[.48,.22,.35]}><icosahedronGeometry args={[1,2]}/><meshStandardMaterial color="#c77c92" roughness={.82}/></mesh><mesh position={[0,-.08,0]}><cylinderGeometry args={[.42,.42,.1,32]}/><meshStandardMaterial color="#e6edf2" metalness={.7}/></mesh></>
    :quantum?<><mesh position={[0,0,0]}><boxGeometry args={[.9,.05,.75]}/><meshStandardMaterial color="#484f8e" metalness={.4} roughness={.25}/></mesh>
      {[-.28,-.14,0,.14,.28].map((x,i)=><Line key={i} points={[[x,.04,-.3],[x,.04,-.08],[x+.06,.04,-.08],[x+.06,.04,.1],[x,.04,.1],[x,.04,.28]]} lineWidth={3} color="#dfbe6d"/>)}
      {[-.52,.52].map(x=>[-.28,-.1,.1,.28].map(z=><mesh key={`${x}${z}`} position={[x,-.01,z]}><boxGeometry args={[.12,.04,.04]}/><meshStandardMaterial color="#e8d08a" metalness={.85}/></mesh>))}</>
    :kind==='microscopy'?<><mesh rotation={[-Math.PI/2,0,0]}><torusGeometry args={[.34,.05,12,48]}/><meshStandardMaterial color="#cba370" metalness={.7}/></mesh><mesh position={[0,-.04,0]}><boxGeometry args={[.54,.02,.54]}/><meshStandardMaterial color="#80b9bc" transparent opacity={.6}/></mesh><mesh position={[0,.05,0]} scale={[.2,.03,.16]}><icosahedronGeometry args={[1,1]}/><meshStandardMaterial color="#97c49d"/></mesh></>
    :optical?<><mesh position={[0,-.05,0]}><boxGeometry args={[1.1,.025,.7]}/><meshStandardMaterial color="#c4e2e6" transparent opacity={.55}/></mesh><mesh position={[0,.1,0]} scale={kind==='phase_transition'?[.45,.05,.32]:[.4,.22,.3]}><octahedronGeometry args={[1,kind==='photoluminescence'?1:0]}/><meshStandardMaterial color={kind==='raman'?'#77a4b2':kind==='phase_transition'?'#a0a3cf':'#b3a1cf'} metalness={.25} roughness={.3}/></mesh></>
    :<><mesh position={[0,.01,0]}><boxGeometry args={[.7,.12,kind==='nano_transport'?.6:.23]}/><meshStandardMaterial color="#546477" metalness={.65} roughness={.23}/></mesh>
      {[-.28,-.09,.09,.28].map((x,i)=><Line key={i} points={[[x,.1,0],[x,.28,.18],[x*1.7,.04,.55]]} color={i===0||i===3?'#64a8c8':'#a293c3'} lineWidth={3}/>)}</>}
  </group>;
}
export default function SamplePreview({definition}:{definition:SceneDefinition}) {
  const [spin,setSpin]=useState(false);
  return <div className="sample-preview" aria-label="Illustrative 3D experiment specimen" data-scene-id={definition.archetype} data-mechanism={definition.visual?.mechanism}><SampleBoundary><Canvas dpr={[1,1.5]} frameloop={spin?'always':'demand'} camera={{position:[1.8,1.65,2.1],fov:40}} gl={{alpha:true,antialias:true}} fallback={<div className="sample-fallback">Experiment specimen</div>}>
    <ambientLight intensity={1.4}/><directionalLight position={[2,5,4]} intensity={2.6}/><directionalLight position={[-3,1,-1]} intensity={1.3} color="#a9d2f5"/>
    <Environment resolution={128}><Lightformer intensity={3} position={[2,3,2]} scale={[4,5,1]}/><Lightformer intensity={2} position={[-3,2,0]} rotation={[0,Math.PI/2,0]} scale={[3,4,1]}/></Environment>
    <Sample definition={definition}/><OrbitControls autoRotate={spin} autoRotateSpeed={.65} enableZoom enablePan={false} minDistance={1} maxDistance={6} enableDamping={false}/>
  </Canvas></SampleBoundary><div className="sample-callout">Your sample</div><button className={`sample-spin ${spin?'active':''}`} aria-label="Spin sample" aria-pressed={spin} onClick={()=>setSpin(v=>!v)}><RotateCw size={14}/>{spin?'Stop':'Spin'}</button><span>Illustrative specimen · drag to rotate · scroll to zoom</span></div>;
}
