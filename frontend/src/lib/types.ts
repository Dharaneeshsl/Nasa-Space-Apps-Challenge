export interface Citation {
  doc_id: string;
  paper_title?: string;
  page?: number;
}

export interface AnswerSentence {
  text: string;
  citations: Citation[];
}

export interface RankItem {
  doc_id?: string;
  raw_logit?: number;
  s_rel: number;
  s_corrob: number;
  s_source: number;
  weights: {
    w_rel: number;
    w_corrob: number;
    w_source: number;
  };
  rank_score: number;
  distinct_groups_count: number;
  has_contradiction: boolean;
  arithmetic_formula: string;
  source_type_caveat: string;
}

export interface AskResponse {
  status: 'answered' | 'insufficient' | 'needs_clarification' | 'no_corpus';
  generation_mode?: 'llm' | 'deterministic_fallback';
  answer_sentences: AnswerSentence[];
  tier?: 'INSUFFICIENT' | 'WEAK' | 'MODERATE' | 'STRONG' | 'CONFLICTING';
  tier_rationale?: string;
  rank_breakdown: RankItem[];
  normalized_relevance_scores: Record<string, number>;
  nearest_documents: Array<Record<string, any>>;
  missing_conditions: string[];
  refusal_reason?: string;
  uncalibrated: boolean;
  disclaimer: string;
}

export interface ExperimentItem {
  staging_id: number;
  experiment_series: string;
  run_id?: string;
  fuel: string;
  fuel_class: string;
  geometry: string;
  scale_dimension_raw?: string;
  O2_value?: number;
  O2_basis?: string;
  diluent?: string;
  pressure_raw_value?: number;
  pressure_raw_unit?: string;
  gravity_level: string;
  flow_regime?: string;
  flow_velocity_cm_s?: number;
  metric_name: string;
  metric_value_raw?: number;
  metric_uncertainty_raw?: number;
  metric_unit_raw: string;
  measurement_method?: string;
  pressure_std_kPa?: number;
  metric_value_std?: number;
  metric_unit_std?: string;
  conversion_provenance?: string;
  source_paper: string;
  source_page: string;
  curated_by: string;
  verified_by?: string;
  verified_date?: string;
  doc_id?: string;
}

export interface CompareCheck {
  name: string;
  result: 'pass' | 'warning' | 'failure';
  reason: string;
  values: Record<string, any>;
}

export interface CompareResponse {
  state: 'PASS' | 'PASS_WITH_WARNINGS' | 'GUARDRAIL_FAILURE';
  checks: CompareCheck[];
  series_a: string;
  series_b: string;
  metric_name?: string;
  metric_unit?: string;
  value_a?: number;
  value_b?: number;
  uncertainty_a?: number;
  uncertainty_b?: number;
  uncertainty_reported: boolean;
  provenance: Record<string, any>;
  harmonized_units: Record<string, string>;
  disclaimer: string;
}

export interface BriefSection {
  title: string;
  content: string;
  citations: Citation[];
  tier?: string;
}

export interface BriefResponse {
  question: string;
  scope_statement: string;
  key_findings: BriefSection[];
  conditions_of_validity: Record<string, any>;
  earth_analog_mapping: string;
  limitations_and_gaps: string;
  tier: string;
  disclaimer: string;
}

export interface StatusResponse {
  corpus_size: number;
  verified_rows: number;
  last_data_update?: string;
  tau_ce_mode: string;
  disclaimer: string;
}
