// src/types/backend.ts — Typed models for CryoLean formal verification

export type Verdict = 
  | 'REQUIREMENTS_MET' 
  | 'DOES_NOT_MEET_REQUIREMENTS' 
  | 'NEED_MORE_INFORMATION';

export type CheckOutcome = 
  | 'pass' 
  | 'fail' 
  | 'unknown' 
  | 'unsupported' 
  | 'not_applicable';

export interface Quantity {
  value: string;
  unit: string;
}

export interface Constraint {
  kind: string;
  q?: Quantity;
  lo?: Quantity;
  hi?: Quantity;
  n?: number;
  b?: boolean;
  allowed?: string[];
  needed?: string[];
}
export interface RequirementEdit { key: string; constraint: Constraint }
export interface Requirement {
  key?: string;
  keys?: string[];
  constraint: Constraint;
  mandatory: boolean;
  rationale?: string;
  origin?: string;
  evidence_ids?: string[];
  conditions?: unknown[];
}
export interface ExperimentRequirements {
  id: string;
  industry: string;
  name: string;
  description?: string | null;
  requirements: Requirement[];
  params: Array<{ name: string; value: Quantity | string | null; origin: string; description?: string; evidence_ids?: string[] }>;
  coupled: Array<{ model: string; mandatory: boolean; rationale?: string }>;
  coupled_models?: Array<{ id: string; name?: string; assumptions?: string[]; [key: string]: any } | null>;
  evidence: EvidenceRecord[];
  sources?: Array<{ citation: string; url?: string; doi?: string }>;
  missing_information?: string[];
  industries?: string[];
  visualization?: SceneVisualDescriptor;
  preferred_configuration_ids?: string[];
}
export interface SceneVisualDescriptor {
  family?: string;
  archetype?: string;
  apparatus?: string;
  sample?: string;
  title?: string;
  steps?: string[];
  source_urls?: string[];
  notes?: string;
  mechanism?: string;
  specimen?: string;
  elements?: string[];
  geometry?: Record<string, any>;
  variant?: string;
}

export interface VerifiedFix {
  id:string;kind:'parameter_adjustment'|'alternative_equipment';title:string;reason:string;
  configuration_id:string;configuration_name:string;parameters:Record<string,Quantity>;
  changes:Array<{parameter:string;before:Quantity;after:Quantity}>;
  verified:true;lean_verdict:'REQUIREMENTS_MET';hypothetical:false;verified_at:string;
  verification:VerificationResult['verification'];verdict_card:VerificationResult['verdict_card'];
  fingerprint:string;lean_input:any;checks:Check[];coupled_checks:CoupledCheck[];references:VerificationResult['references'];
}
export interface VerifiedRepairSearch {
  result_id:string;fixes:VerifiedFix[];status:string;message:string;evaluated_candidates?:number;
  discarded?:Record<string,number>;search_scope?:string;
}
export interface Capability {
  key: string;
  install: string;
  value: { kind: string; b?: boolean; n?: number; [key: string]: any };
  display: string;
  evidence_status: string;
  evidence: EvidenceRecord[];
}
export interface ConfigurationDetails {
  id: string;
  name: string;
  equipment_id: string;
  manufacturer: string;
  model: string;
  family: string;
  configuration_basis?: unknown;
  capabilities: Capability[];
  unknown_capabilities: string[];
  optional_accessories_not_installed: string[];
  modifications: Array<{ status: string; description: string; [key: string]: any }>;
  visualization?: SceneVisualDescriptor;
}

export interface EvidenceRecord {
  id: string;
  quote: string;
  document_title: string;
  location: string;
  source_url: string;
  evidence_status?: string;
  accessed?: string;
}

export interface Check {
  kind: 'requirement';
  keys: string[];
  mandatory: boolean;
  applicable: boolean;
  outcome: CheckOutcome;
  required: string;
  available: string;
  explanation: string;
  property?: number;
  capability_evidence?: EvidenceRecord[];
  requirement_evidence?: EvidenceRecord[];
  per_key?: Array<{
    key: string;
    capability?: {
      install?: string;
      value?: any;
    };
  }>;
}

export interface CoupledCheck {
  kind: 'coupled';
  model: string;
  name?: string;
  outcome: CheckOutcome;
  lhs: {
    display: string;
    value?: any;
  };
  rhs: {
    display: string;
    value?: any;
  };
  equation: string;
  assumptions: string[];
  slot_resolution?: Record<string, string>;
  evidence?: EvidenceRecord[];
  explanation?: string;
  mandatory?: boolean;
  applicable?: boolean;
}

export interface VerdictCardData {
  verdict: Verdict;
  headline: string;
  reason: string;
  theorems: string[];
  axioms: Record<string, string[]>;
  axiomsStandardOnly: boolean;
  sourceHash: string;
  inputHash: string;
  note: string;
}

export interface SuggestionConflict {
  explanation: string;
  requirements: string[];
  facts: string[];
}

export interface ParameterChange {
  parameter: string;
  current: string;
  suggested: string;
  status?: string;
  lean_verdict: Verdict;
  verified: boolean;
}

export interface AlternativeCandidate {
  configuration_id: string;
  z3_status: 'satisfiable' | 'needs_options' | 'pending_information' | string;
  added_options: string[];
  hypothetical: boolean;
  lean_verdict: Verdict;
  verified: boolean;
  z3_unknown_items?: string[];
  failing_items?: string[];
  name?: string;
  lean_summary?: string;
}

export interface Suggestions {
  conflicts?: {
    status: string;
    conflicts: SuggestionConflict[];
  };
  parameter_changes?: ParameterChange[];
  requirement_relaxations?: any[];
  alternatives?: AlternativeCandidate[];
}

export interface VerificationResult {
  verdict: Verdict;
  headline: string;
  user_message: string;
  next_step: string;
  equipment: {
    id: string;
    manufacturer: string;
    configuration_id: string;
    modifications_applied?: any[];
  };
  experiment: {
    id: string;
    name?:string;
    plain_name?:string;
    industry: string;
    confirmed: boolean;
    parameters?: any[];
  };
  checks: Check[];
  coupled_checks: CoupledCheck[];
  missing_information: string[];
  failed_requirements: string[];
  verification: {
    generic_theorems?: {
      status: string;
      key_theorems: string[];
    };
    concrete_evaluation: {
      engine: string;
      verified_by_lean: boolean;
      lean_input_hash: string;
      verdict: Verdict;
      lean_version?: string;
    };
    source_data_validation?: {
      ok: boolean;
      errors: string[];
      warnings: string[];
    };
    physical_model_assumptions?: Array<{
      model: string;
      equation: string;
      assumptions: string[];
    }>;
  };
  verdict_card?: {
    verdict: Verdict;
    reason: string;
    theorems: string[];
    axioms: Record<string, string[]>;
    axioms_standard_only: boolean;
    axiom_audit: string;
    source_hash: string;
    lean_input_hash: string;
    z3_role: string;
  };
  suggestions?: Suggestions;
  references?: Array<{
    type: string;
    citation: string;
    doi?: string;
  }>;
  fingerprint: string;
  result_id: string;
  lean_input?: any;
  checked_at?: string;
  catalog_version?: string;
}

export interface Industry {
  id: string;
  name: string;
  status: 'known' | 'registered' | 'researched' | string;
}

export interface ExperimentProfile {
  id: string;
  plain_name: string;
  name: string;
  industry: string;
  description: string | null;
  confirmed: boolean;
  industries?: string[];
  visualization?: SceneVisualDescriptor;
  preferred_configuration_ids?: string[];
}

export interface EquipmentConfiguration {
  id: string;
  name: string;
  visualization?:SceneVisualDescriptor;
}

export interface EquipmentItem {
  id: string;
  manufacturer: string;
  model: string;
  family: string;
  description: string;
  configurations: EquipmentConfiguration[];
  visualization?: SceneVisualDescriptor;
}

export interface LeanTheorem {
  name: string;
  file: string;
  line: number;
}

export interface LeanStatus {
  lean_available: boolean;
  version: string;
  selftest_passed: boolean;
  theorem_count: number;
  theorems: LeanTheorem[];
  unsafe_markers: string[];
}

export interface VerificationCardResponse {
  theorems: string[];
  axioms: Record<string, string[]>;
  lean_source_hash: string;
  forensics_summary?: any;
}
