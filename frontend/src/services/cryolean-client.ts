import * as raw from './cryolean-client-raw.js';
import type { Industry, ExperimentProfile, EquipmentItem, ExperimentRequirements, ConfigurationDetails,
  LeanStatus, VerificationResult, Quantity, RequirementEdit, AlternativeCandidate } from '../types/backend';

export const { CryoLeanError, VERDICT, HEADLINE, isVerified, verdictCard, checkQuestion } = raw;
export function isDesktopBridgeAvailable(): boolean {
  return typeof window !== 'undefined' && Boolean((window as any).pywebview?.api);
}
export async function checkBridgeConnection(timeoutMs = 700): Promise<boolean> {
  if (isDesktopBridgeAvailable()) return true;
  try { await raw.ready(); return true; } catch { return isDesktopBridgeAvailable(); }
}
async function connected<T>(fn: () => Promise<T>, timeoutMs = 45000): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([fn(), new Promise<never>((_, reject) => {
      timer = setTimeout(() => reject(new raw.CryoLeanError({ code: 'timeout',
        message: 'The checker has not responded. No verdict was produced. Retry the check.' })), timeoutMs);
    })]);
  } finally { clearTimeout(timer); }
}
export interface CheckOpts {
  parameters?: Record<string, Quantity> | null;
  requirementEdits?: RequirementEdit[] | null;
  confirmed?: boolean;
  extraModifications?: unknown[] | null;
  suggestions?: boolean;
}
export const listIndustries = (query: string | null = null): Promise<{ industries: Industry[] }> => connected(() => raw.listIndustries(query));
export const listExperiments = (industry: string | null = null): Promise<{ experiments: ExperimentProfile[] }> => connected(() => raw.listExperiments(industry));
export const listEquipment = (): Promise<{ equipment: EquipmentItem[] }> => connected(() => raw.listEquipment());
export const getExperimentRequirements = (id: string): Promise<ExperimentRequirements> => connected(() => raw.getExperimentRequirements(id));
export const getEquipmentDetails = (id: string): Promise<{ configurations: ConfigurationDetails[] }> => connected(() => raw.getEquipmentDetails(id));
export const getLeanStatus = (): Promise<LeanStatus> => connected(() => raw.getLeanStatus());
export const getResearchCoverage = (): Promise<any> => connected(() => raw.getResearchCoverage());
export const matchExperiment = (text: string, topK = 3): Promise<{ matches: Array<{experiment_id: string; plain_name: string; name: string; industry: string; reason: string}> }> => connected(() => raw.matchExperiment(text, topK));
export async function checkCompatibility(experimentId: string, configurationId: string, opts: CheckOpts = {}): Promise<VerificationResult> {
  const result = await connected<VerificationResult>(() => raw.checkCompatibility(experimentId, configurationId, opts));
  if (!Object.values(raw.VERDICT).includes(result?.verdict) || result.verification?.concrete_evaluation?.verified_by_lean !== true) {
    throw new raw.CryoLeanError({ code: 'invalid_response', message: 'The backend did not return a confirmed Lean evaluation. No verdict is displayed.' });
  }
  return result;
}
export const getVerificationDetails = (id: string): Promise<VerificationResult> => connected(() => raw.getVerificationDetails(id));
export const getVerifiedRepairs = (id:string): Promise<import('../types/backend').VerifiedRepairSearch> => connected(()=>raw.getVerifiedRepairs(id),90000);
export const applyVerifiedRepair = (resultId:string,repairId:string): Promise<VerificationResult> => connected(()=>raw.applyVerifiedRepair(resultId,repairId));
export async function findCompatibleEquipment(experimentId: string, opts: CheckOpts): Promise<{ candidates: AlternativeCandidate[]; note: string }> {
  if (!opts.confirmed) throw new raw.CryoLeanError({code: 'confirmation_required', message: 'Review and confirm the requirements before searching.'});
  return connected(() => raw.findCompatibleEquipment(experimentId, { ...opts, includeHypotheticalOptions: false }));
}
export async function compareEquipment(experimentId: string, ids: string[], opts: CheckOpts): Promise<{ results: VerificationResult[]; comparison_table: any[] }> {
  if (!opts.confirmed) throw new raw.CryoLeanError({code: 'confirmation_required', message: 'Confirm the requirements before comparing machines.'});
  return connected(() => raw.compareEquipment(experimentId, ids, opts));
}
