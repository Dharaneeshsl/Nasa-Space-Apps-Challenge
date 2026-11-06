"""Pydantic schemas for CombustionLens API.

Enforces strict typing, JSON serializability, null preservation,
and inclusion of the mandatory non-operational safety disclaimer.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

DISCLAIMER_TEXT = (
    "Generated from published NASA research for informational/research purposes. "
    "Not validated for operational flight or terrestrial fire safety decisions."
)


class Citation(BaseModel):
    doc_id: str
    paper_title: Optional[str] = None
    page: Optional[int] = None
    source_url: Optional[str] = None


class AnswerSentence(BaseModel):
    text: str
    citations: List[Citation] = Field(default_factory=list)


class RankItem(BaseModel):
    doc_id: Optional[str] = None
    raw_logit: Optional[float] = None
    s_rel: float
    s_corrob: float
    s_source: float
    weights: Dict[str, float]
    rank_score: float
    distinct_groups_count: int
    has_contradiction: bool
    arithmetic_formula: str
    source_type_caveat: str


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    status: str  # 'answered' | 'insufficient' | 'needs_clarification' | 'no_corpus'
    generation_mode: Optional[str] = None  # 'llm' | 'deterministic_fallback'
    answer_sentences: List[AnswerSentence] = Field(default_factory=list)
    tier: Optional[str] = None  # 'INSUFFICIENT' | 'WEAK' | 'MODERATE' | 'STRONG' | 'CONFLICTING'
    tier_rationale: Optional[str] = None
    rank_breakdown: List[RankItem] = Field(default_factory=list)
    normalized_relevance_scores: Dict[str, float] = Field(default_factory=dict)
    nearest_documents: List[Dict[str, Any]] = Field(default_factory=list)
    missing_conditions: List[str] = Field(default_factory=list)
    refusal_reason: Optional[str] = None
    uncalibrated: bool = False
    disclaimer: str = DISCLAIMER_TEXT


class ExperimentItem(BaseModel):
    staging_id: int
    experiment_series: str
    run_id: Optional[str] = None
    fuel: str
    fuel_class: str
    geometry: str
    scale_dimension_raw: Optional[str] = None
    O2_value: Optional[float] = None
    O2_basis: Optional[str] = None
    diluent: Optional[str] = None
    pressure_raw_value: Optional[float] = None
    pressure_raw_unit: Optional[str] = None
    gravity_level: str
    flow_regime: Optional[str] = None
    flow_velocity_cm_s: Optional[float] = None
    metric_name: str
    metric_value_raw: Optional[float] = None
    metric_uncertainty_raw: Optional[float] = None
    metric_unit_raw: str
    measurement_method: Optional[str] = None
    pressure_std_kPa: Optional[float] = None
    metric_value_std: Optional[float] = None
    metric_unit_std: Optional[str] = None
    conversion_provenance: Optional[str] = None
    source_paper: str
    source_page: str
    curated_by: str
    verified_by: Optional[str] = None
    verified_date: Optional[str] = None
    doc_id: Optional[str] = None


class CompareRequest(BaseModel):
    id_a: int
    id_b: int


class CompareCheck(BaseModel):
    name: str
    result: str  # 'pass' | 'warning' | 'failure'
    reason: str
    values: Dict[str, Any]


class CompareResponse(BaseModel):
    state: str  # 'PASS' | 'PASS_WITH_WARNINGS' | 'GUARDRAIL_FAILURE'
    checks: List[CompareCheck]
    series_a: str
    series_b: str
    metric_name: Optional[str] = None
    metric_unit: Optional[str] = None
    value_a: Optional[float] = None
    value_b: Optional[float] = None
    uncertainty_a: Optional[float] = None
    uncertainty_b: Optional[float] = None
    uncertainty_reported: bool = False
    provenance: Dict[str, Any]
    harmonized_units: Dict[str, str]
    disclaimer: str = DISCLAIMER_TEXT


class BriefRequest(BaseModel):
    question: str


class BriefSection(BaseModel):
    title: str
    content: str
    citations: List[Citation] = Field(default_factory=list)
    tier: Optional[str] = None


class BriefResponse(BaseModel):
    question: str
    scope_statement: str
    key_findings: List[BriefSection]
    conditions_of_validity: Dict[str, Any]
    earth_analog_mapping: str
    limitations_and_gaps: str
    tier: str
    disclaimer: str = DISCLAIMER_TEXT


class StatusResponse(BaseModel):
    corpus_size: int
    verified_rows: int
    last_data_update: Optional[str] = None
    tau_ce_mode: str
    disclaimer: str = DISCLAIMER_TEXT
