import type { EquipmentItem, ExperimentProfile } from '../../types/backend';

// Presentation choices only: a useful catalog starting point is not a compatibility claim.
// Keep each researched procedure distinct even when its source plain_name is shared.
export const EXPERIMENT_PRESENTATION: Record<string, { title: string; configurationId: string }> = {
  bio_cryosection_frozen_tissue: { title: 'Frozen-tissue cryosectioning', configurationId: 'leica_cm1950_genA_vacuum_motor_objcool' },
  bio_cryo_fluorescence_vitrified: { title: 'Vitrified-specimen fluorescence microscopy', configurationId: 'linkam_thms600_lnp96_t96' },
  chem_low_temperature_raman: { title: 'Low-temperature Raman spectroscopy', configurationId: 'linkam_thms600_lnp96_t96' },
  chem_phase_transition_pom: { title: 'Polarized phase-transition microscopy', configurationId: 'linkam_thms600_lnp96_t96' },
  chem_temperature_dependent_photoluminescence: { title: 'Temperature-dependent photoluminescence', configurationId: 'oxford_optistatdry_blv' },
  mat_electrical_resistance_low_temperature: { title: 'Four-probe electrical resistance', configurationId: 'qd_dynacool_9T_eto_res' },
  mat_magnetoresistance_10T: { title: '10 T magnetoresistance', configurationId: 'qd_dynacool_9T_eto_res' },
  mat_magnetometry_vsm: { title: 'Vibrating-sample magnetometry', configurationId: 'qd_dynacool_12T_vsm' },
  quantum_mk_vector_field_transport: { title: 'Millikelvin vector-field nanodevice transport', configurationId: 'bluefors_ld400_hdw' },
  quantum_mxc_wiring_heat_budget: { title: 'Mixing-chamber wiring heat budget', configurationId: 'bluefors_ld400_hdw' },
  quantum_transmon_characterization: { title: 'Transmon qubit characterization', configurationId: 'bluefors_ld400_hdw' },
};
export function startingConfiguration(experimentId: string, equipment: EquipmentItem[], profile?:ExperimentProfile): string {
  const id = EXPERIMENT_PRESENTATION[experimentId]?.configurationId??profile?.preferred_configuration_ids?.find(cid=>equipment.some(e=>e.configurations.some(c=>c.id===cid)));
  return id && equipment.some(e => e.configurations.some(c => c.id === id)) ? id : '';
}
