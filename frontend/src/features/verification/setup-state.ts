import type { VerificationResult, Quantity, RequirementEdit } from '../../types/backend';

export interface SetupState {
  experimentId: string;
  configurationId: string;
  parameters: Record<string, Quantity>;
  edits: RequirementEdit[];
  confirmed: boolean;
  revision: number;
  pending: number | null;
  result: VerificationResult | null;
  error: string | null;
}
export const initialSetup: SetupState = {
  experimentId: 'mat_electrical_resistance_low_temperature', configurationId: 'qd_dynacool_9T_eto_res',
  parameters: {}, edits: [], confirmed: false, revision: 0, pending: null, result: null, error: null,
};
export type SetupAction =
  | { type: 'experiment'; id: string; configurationId?: string; parameters?: Record<string, Quantity> }
  | { type: 'equipment'; id: string }
  | { type: 'parameter'; name: string; quantity: Quantity }
  | { type: 'edit'; edit: RequirementEdit }
  | { type: 'confirm'; value: boolean }
  | { type: 'invalidate' }
  | { type:'apply-fix';originalResultId:string;configurationId:string;parameters:Record<string,Quantity>;result:VerificationResult }
  | { type: 'start'; revision: number }
  | { type: 'success'; revision: number; result: VerificationResult }
  | { type: 'error'; revision: number; message: string };
export function setupReducer(state: SetupState, action: SetupAction): SetupState {
  const cleared = { ...state, revision: state.revision + 1, pending: null, result: null, error: null };
  switch (action.type) {
    case 'experiment': return { ...cleared, experimentId: action.id, configurationId: action.configurationId ?? state.configurationId,
      parameters: action.parameters ?? {}, edits: [], confirmed: false };
    case 'equipment': return { ...cleared, configurationId: action.id };
    case 'parameter': return { ...cleared, confirmed: false, parameters: { ...state.parameters, [action.name]: action.quantity } };
    case 'edit': return { ...cleared, confirmed: false, edits: [...state.edits.filter(e => e.key !== action.edit.key), action.edit] };
    case 'confirm': return { ...cleared, confirmed: action.value };
    case 'invalidate': return cleared;
    case 'apply-fix':
      if(state.result?.result_id!==action.originalResultId||action.result.verdict!=='REQUIREMENTS_MET'
        ||action.result.experiment.id!==state.experimentId
        ||((action.result.equipment as any).catalog_configuration_id??action.result.equipment.configuration_id)!==action.configurationId
        ||action.result.verification.concrete_evaluation.verified_by_lean!==true) return state;
      return {...cleared,configurationId:action.configurationId,parameters:action.parameters,confirmed:true,result:action.result};
    case 'start': return state.confirmed && action.revision === state.revision && state.pending === null
      ? { ...state, pending: action.revision, result: null, error: null } : state;
    case 'success':
      if (state.pending !== action.revision || state.revision !== action.revision || !state.confirmed) return state;
      if (action.result.experiment.id !== state.experimentId || ((action.result.equipment as any).catalog_configuration_id??action.result.equipment.configuration_id) !== state.configurationId) {
        return { ...state, pending: null, error: 'The response does not match this setup. Please check again.' };
      }
      return { ...state, pending: null, result: action.result, error: null };
    case 'error': return state.pending === action.revision && state.revision === action.revision
      ? { ...state, pending: null, result: null, error: action.message } : state;
  }
}
