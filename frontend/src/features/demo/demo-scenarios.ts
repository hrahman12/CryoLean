import type { Quantity } from '../../types/backend';
// Only inputs. Real outcomes are validated by tests/test_frontend_contract.py.
export interface DemoScenario {
  id: string; title: string; topic: string; experimentId: string; configurationId: string; learningGoal: string;
  parameters?: Record<string, Quantity>;
}
export const DEMO_SCENARIOS: DemoScenario[] = [
  { id: 'demo-a', title: 'A · Compatible', topic: 'Phase-transition microscopy',
    experimentId: 'chem_phase_transition_pom', configurationId: 'linkam_thms600_lnp96_t96',
    learningGoal: 'Explore an optical-stage setup for a sourced temperature scan. Run the check to inspect its thermal and optical requirements.' },
  { id: 'demo-b', title: 'B · Incompatible', topic: 'A 10 T experiment on a 9 T magnet',
    experimentId: 'mat_magnetoresistance_10T', configurationId: 'qd_dynacool_9T_eto_res',
    learningGoal: 'Compare the requested field with the documented magnet. Then switch to the 14 T configuration and check again.' },
  { id: 'demo-c', title: 'C · Missing information', topic: 'A stronger magnet. Enough evidence?',
    experimentId: 'mat_magnetoresistance_10T', configurationId: 'qd_dynacool_14T_eto_vsm_hc',
    learningGoal: 'See why meeting the field requirement cannot establish whether the sample fits. Inspect the missing clearance evidence.' },
  { id: 'coupled', title: 'Coupled physics', topic: 'The hidden cost of cold wires',
    experimentId: 'quantum_mxc_wiring_heat_budget', configurationId: 'bluefors_ld400_hdw',
    learningGoal: 'Compare the wiring heat load with cooling capacity. Inspect the suggested flux-line change, review it, and rerun.' },
  { id: 'tissue', title: 'Frozen tissue', topic: 'From specimen to a thin section',
    experimentId: 'bio_cryosection_frozen_tissue', configurationId: 'leica_cm1950_genA_vacuum_motor_objcool',
    learningGoal: 'Inspect a cooled chamber, specimen chuck and cutting blade, then check the documented cryosectioning setup.' },
];
