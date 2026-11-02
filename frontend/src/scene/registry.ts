import type { ConfigurationDetails, SceneVisualDescriptor } from '../types/backend';

export type MachineFamily = string;
export type Archetype = string;
export interface SceneDefinition { family: MachineFamily; familyLabel: string; archetype: Archetype; steps: string[]; visual?: SceneVisualDescriptor; machineVisual?: SceneVisualDescriptor }
export const EQUIPMENT_SCENES: Record<string, [MachineFamily, string]> = {
  leica_cm1950: ['microtome', 'Cryostat microtome'],
  linkam_thms600: ['optical_stage', 'Optical heating / cooling stage'],
  qd_ppms_dynacool: ['magnet', 'Physical property measurement system'],
  qd_ppms_classic: ['magnet', 'Liquid-helium magnet system'],
  oxford_teslatronpt: ['magnet', 'Magnet + temperature insert'],
  oxford_optistatdry: ['optical_cryostat', 'Optical cryostat'],
  lakeshore_janis_ccs: ['optical_cryostat', 'Optical cryostat'],
  lakeshore_crx: ['probe_station', 'Cryogenic probe station'],
  bluefors_ld: ['dilution', 'Dilution refrigerator'],
};
export const EXPERIMENT_SCENES: Record<string, Archetype> = {
  bio_cryosection_frozen_tissue: 'cryosection', bio_cryo_fluorescence_vitrified: 'microscopy',
  chem_low_temperature_raman: 'raman', chem_temperature_dependent_photoluminescence: 'photoluminescence',
  chem_phase_transition_pom: 'phase_transition', mat_electrical_resistance_low_temperature: 'transport',
  mat_magnetoresistance_10T: 'magnetoresistance', mat_magnetometry_vsm: 'vsm',
  quantum_mk_vector_field_transport: 'nano_transport', quantum_mxc_wiring_heat_budget: 'quantum',
  quantum_transmon_characterization: 'quantum_chip',
};
const STEPS: Record<Archetype, string[]> = {
  cryosection: ['Mount the frozen tissue block on the specimen chuck.', 'Advance the specimen past the cutting blade.', 'Collect the thin section on a slide. Section thickness is not to scale.'],
  microscopy: ['Keep the vitrified specimen on a cooled support.', 'Illuminate through the microscope objective.', 'Collect fluorescence through the same objective. Image formation is conceptual.'],
  raman: ['Excite the mounted specimen through an optical path.', 'Collect scattered light through the objective and separate it from excitation.', 'Send the collected light to a spectrometer. No measured spectrum is simulated.'],
  photoluminescence: ['Excite the cooled specimen with light.', 'The specimen emits light after excitation; the color is illustrative.', 'Collect the emission through a filter toward the detector. No emission energy is predicted.'],
  phase_transition: ['Mount a specimen between the illumination path and microscope objective.', 'Control the stage temperature while viewing through crossed polarizers.', 'Observe a conceptual change in crystalline texture. No transition temperature is predicted.'],
  transport: ['Mount the specimen and attach four separate contacts.', 'Source current through the two outer contacts.', 'Sense the voltage between the inner contacts. R = V / I; no readings are generated.'],
  magnetoresistance: ['Mount the contacted crystal in the magnet measurement region.', 'Apply the requested magnetic field while sourcing current through the outer leads.', 'Sense voltage through the inner leads as the field is varied. The required 10 T field is checked separately; no magnetoresistance curve is generated.'],
  nano_transport: ['Mount a representative hybrid nanodevice on a contacted chip carrier.', 'Cool the device with thermalized leads and align the required vector field.', 'Measure electrical transport through the device. The chip layout and field orientation are conceptual, not reconstructed lithography.'],
  vsm: ['Mount the sample on a probe in the magnetic measurement region.', 'Oscillate the probe relative to pickup coils.', 'Read the induced signal with the external measurement electronics. No magnetization values are predicted.'],
  quantum: ['Route signal wiring through successively colder stages.', 'Thermally anchor the representative cables before the sample.', 'Compare the modeled wiring load with documented stage cooling in the real backend. Cable counts are schematic.'],
  quantum_chip: ['Mount the transmon device in a representative microwave sample enclosure.', 'Route input and output coaxial cables through thermal anchors.', 'Apply and collect microwave signals. Chip geometry and signal propagation are conceptual; no coherence or frequency values are predicted.'],
  unmapped: ['No apparatus model has been mapped for this profile.', 'You can still review its sourced requirements and run the real checker.'],
};
export function getSceneDefinition(experimentId: string, equipmentId: string, visual?:SceneVisualDescriptor, machineVisual?:SceneVisualDescriptor): SceneDefinition {
  const [defaultFamily, defaultLabel] = EQUIPMENT_SCENES[equipmentId] ?? ['unmapped', 'Unmapped equipment'];
  const family=machineVisual?.family??defaultFamily;
  const familyLabel=machineVisual?.title??defaultLabel;
  const archetype=visual?.archetype??EXPERIMENT_SCENES[experimentId]??'unmapped';
  return {family,familyLabel,archetype,steps:visual?.steps??STEPS[archetype]??STEPS.unmapped,visual,machineVisual};
}
export function hasInstalled(configuration: ConfigurationDetails | null, key: string): boolean {
  const cap = configuration?.capabilities.find(c => c.key === key);
  return Boolean(cap && cap.install === 'installed' && cap.evidence_status !== 'unknown' && cap.evidence_status !== 'inferred_estimate'
    && cap.value.kind !== 'unknown' && (cap.value.kind !== 'flag' || cap.value.b === true) && (cap.value.kind !== 'count' || (cap.value.n ?? 0) > 0));
}
export interface SceneComponent { id: string; title: string; description: string; keys: string[]; position: [number, number, number] }
export function sceneComponents(family: MachineFamily): SceneComponent[] {
  const basic: SceneComponent[] = [
    {id:'cold_stage',title:'Cold stage',description:'The sample exchanges heat with this thermal support. Its operating envelope comes from the selected configuration.',keys:['temperature.range','temperature.base','temperature.chamber.range'],position:[0,-0.35,0.45]},
    {id:'sample_mount',title:'Sample position',description:'Clearance must be established from documented sample-space dimensions. This model does not establish physical fit.',keys:['sample.width.max','sample.length.max','sample.height.max','sample.bore_diameter','sample.diameter.max'],position:[0,0,0.45]},
    {id:'vacuum_shroud',title:'Sample environment',description:'Vacuum or a documented dry-gas purge can protect the cold sample. Its presence is checked separately.',keys:['vacuum.available','purge.gas'],position:[0.8,0.3,0.3]},
  ];
  if (family === 'microtome') return [basic[0],{...basic[1],position:[0.2,0.05,0.65]},
    {id:'specimen_head',title:'Specimen chuck',description:'The tissue block is held here for sectioning. Independent object cooling is an installed option only where documented.',keys:['temperature.specimen_head.range','mechanical.motorized_sectioning'],position:[0,0.3,0.5]}];
  if (['optical_stage','optical_cryostat','probe_station'].includes(family)) basic.push({id:'optical_windows',title:'Optical access',description:'An objective or beam needs a documented optical path and enough working distance.',keys:['optical_access','optical.window_aperture','optical.transmission_range'],position:[0,0.6,0.4]});
  if (family === 'magnet') basic.push({id:'magnet_solenoid',title:'Magnet assembly',description:'The magnet produces the field at the sample. Its maximum field and vector capability are separate sourced facts.',keys:['magnetic_field.max','magnetic_field.vector'],position:[0.55,-0.3,0.5]});
  if (family === 'dilution') basic.push({id:'mxc_wiring_bundle',title:'Mixing chamber & wiring',description:'Wiring contributes a heat load at the coldest stage. A coupled check compares its modeled load with documented cooling capacity.',keys:['electrical.coax_lines','cooling_power.at_20mK'],position:[0.35,-0.7,0.3]});
  else if (family === 'magnet' || family === 'probe_station') basic.push({id:'dc_wiring',title:'Electrical connections',description:'Measurement connections and installed modules must match the experiment. Required apparatus is illustrated separately.',keys:['electrical.dc_lines','module.electrical_transport','module.vsm','electrical.probe_arms'],position:[-0.45,0.8,0.4]});
  return basic;
}
