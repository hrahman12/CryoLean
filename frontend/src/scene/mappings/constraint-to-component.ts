// src/scene/mappings/constraint-to-component.ts — Map formal backend constraints to 3D scene components

export interface ComponentHighlightInfo {
  componentId: string;
  name: string;
  description: string;
  category: 'thermal' | 'magnetic' | 'optical' | 'electrical' | 'mechanical' | 'vacuum';
}

export const CONSTRAINT_COMPONENT_MAP: Record<string, ComponentHighlightInfo> = {
  // Temperature & Cooling
  'temperature.range': {
    componentId: 'cold_stage',
    name: 'Thermal Sample Stage',
    description: 'Operating temperature envelope provided by the cooling engine.',
    category: 'thermal',
  },
  'temperature.base': {
    componentId: 'cold_stage',
    name: 'Base Temperature Anchor',
    description: 'Minimum reachable base temperature on the sample mounting stage.',
    category: 'thermal',
  },
  'temperature.specimen_head.range': {
    componentId: 'specimen_head',
    name: 'Specimen Head Cooling Element',
    description: 'Independent cryogenic cooling head for tissue specimen chuck.',
    category: 'thermal',
  },
  'temperature.chamber.range': {
    componentId: 'cold_stage',
    name: 'Refrigerated Chamber',
    description: 'Main insulated cryo-chamber maintaining cold ambient environment.',
    category: 'thermal',
  },
  'cooling_power.at_20mK': {
    componentId: 'mxc_wiring_bundle',
    name: 'Mixing Chamber Stage (20 mK)',
    description: 'Dilution refrigeration cooling capacity at 20 mK base stage.',
    category: 'thermal',
  },
  'cooling_power.at_4K': {
    componentId: 'cold_stage',
    name: 'Cold Stage',
    description: 'Cooling capacity at the documented operating point.',
    category: 'thermal',
  },

  // Magnetic Field
  'magnetic_field.max': {
    componentId: 'magnet_solenoid',
    name: 'Superconducting Solenoid Magnet',
    description: 'Superconducting magnet coil generating longitudinal magnetic field.',
    category: 'magnetic',
  },
  'magnetic_field.vector': {
    componentId: 'magnet_solenoid',
    name: 'Vector Rotation Magnet',
    description: 'Multi-axis superconducting magnet coils for 3D field tilting.',
    category: 'magnetic',
  },

  // Sample Geometry & Clearance
  'sample.diameter.max': {
    componentId: 'sample_mount',
    name: 'Sample Area / Platform',
    description: 'Maximum permissible physical diameter of the sample.',
    category: 'mechanical',
  },
  'sample.thickness.max': {
    componentId: 'sample_mount',
    name: 'Sample Height Clearance',
    description: 'Vertical clearance between sample stage and thermal/optical shroud.',
    category: 'mechanical',
  },
  'sample.dimensions': {
    componentId: 'sample_mount',
    name: 'Sample Space Enclosure',
    description: 'Available working volume inside the sample chamber.',
    category: 'mechanical',
  },

  // Optical Access
  'optical.transmission_range': {
    componentId: 'optical_windows',
    name: 'Optical Access Windows',
    description: 'Optical windows for excitation and detection; material and transmission come from the selected configuration.',
    category: 'optical',
  },
  'optical.window_aperture': {
    componentId: 'optical_windows',
    name: 'Optical Aperture',
    description: 'Clear optical aperture allowing light to reach and exit the sample.',
    category: 'optical',
  },

  // Electrical & Wiring
  'electrical.coax_lines': {
    componentId: 'mxc_wiring_bundle',
    name: 'High-Density Coaxial Wiring',
    description: 'Attenuated semi-rigid coaxial cables routed through thermal stages.',
    category: 'electrical',
  },
  'electrical.dc_lines': {
    componentId: 'dc_wiring',
    name: 'DC Measurement Loom',
    description: 'Twisted-pair loom for low-frequency and resistance measurements.',
    category: 'electrical',
  },
  'electrical.probe_arms': {
    componentId: 'dc_wiring',
    name: 'Micro-Manipulated Probes',
    description: 'Adjustable cryogenic probe arms contacting the chip pads.',
    category: 'electrical',
  },

  // Modules & Accessories
  'module.vsm': {
    componentId: 'dc_wiring',
    name: 'Vibrating Sample Magnetometer (VSM)',
    description: 'Linear motor transport head and detection pickup coil module.',
    category: 'mechanical',
  },
  'module.eto': {
    componentId: 'dc_wiring',
    name: 'Electrical Transport Option (ETO)',
    description: 'Precision DSP-based AC resistance bridge module.',
    category: 'electrical',
  },

  // Vacuum
  'vacuum.available': {
    componentId: 'vacuum_shroud',
    name: 'Vacuum Chamber Enclosure',
    description: 'High-vacuum seal preventing air condensation and thermal convection.',
    category: 'vacuum',
  },
};

export const COUPLED_MODEL_COMPONENT_MAP: Record<string, ComponentHighlightInfo> = {
  mxc_wiring_heat_budget: {
    componentId: 'mxc_wiring_bundle',
    name: 'MXC Thermalized Wiring Loom',
    description: 'Coupled heat conduction and dissipation from signal lines entering the 20 mK mixing chamber.',
    category: 'thermal',
  },
  joule_heating_vs_cooling_power: {
    componentId: 'cold_stage',
    name: 'Sample Stage Thermal Anchor',
    description: 'Joule dissipation (I²R) in sample versus available base stage cooling power.',
    category: 'thermal',
  },
  objective_working_distance_clearance: {
    componentId: 'optical_windows',
    name: 'Objective Working Distance Clearance',
    description: 'Physical clearance required for high-NA microscope objective through optical window.',
    category: 'optical',
  },
  differential_thermal_contraction: {
    componentId: 'sample_mount',
    name: 'Sample-to-Chuck Thermal Expansion Joint',
    description: 'Mismatch in integrated thermal contraction between substrate and mount.',
    category: 'mechanical',
  },
};

/** Resolves relevant component ID for a given check */
export function getComponentForCheck(check: { keys?: string[]; model?: string; kind?: string }): ComponentHighlightInfo | null {
  if (check.kind === 'coupled' && check.model && COUPLED_MODEL_COMPONENT_MAP[check.model]) {
    return COUPLED_MODEL_COMPONENT_MAP[check.model];
  }
  if (check.keys && check.keys.length > 0) {
    for (const k of check.keys) {
      if (k === 'optical_access') return CONSTRAINT_COMPONENT_MAP['optical.transmission_range'];
      if (k.startsWith('cooling_power')) return CONSTRAINT_COMPONENT_MAP['cooling_power.at_20mK'];
      if (k.startsWith('module.')) return {componentId:'dc_wiring',name:'Measurement interface',description:'The required measurement module is checked separately from the machine family.',category:'electrical'};
      if (k.startsWith('purge.') || k.startsWith('pressure.')) return CONSTRAINT_COMPONENT_MAP['vacuum.available'];
      if (CONSTRAINT_COMPONENT_MAP[k]) return CONSTRAINT_COMPONENT_MAP[k];
      // Prefix matching
      const prefix = k.split('.')[0];
      if (prefix === 'temperature') return CONSTRAINT_COMPONENT_MAP['temperature.range'];
      if (prefix === 'magnetic_field') return CONSTRAINT_COMPONENT_MAP['magnetic_field.max'];
      if (prefix === 'optical') return CONSTRAINT_COMPONENT_MAP['optical.transmission_range'];
      if (prefix === 'sample') return CONSTRAINT_COMPONENT_MAP['sample.diameter.max'];
      if (prefix === 'electrical') return CONSTRAINT_COMPONENT_MAP['electrical.dc_lines'];
      if (prefix === 'vacuum') return CONSTRAINT_COMPONENT_MAP['vacuum.available'];
    }
  }
  return null;
}
