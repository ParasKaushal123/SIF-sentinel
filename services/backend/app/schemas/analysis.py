"""Pydantic models for the shared analysis contract.

These define the structured output from the analysis pipeline.
Frontend TypeScript types are generated from these via OpenAPI.
"""

from pydantic import BaseModel, Field

from .enums import (
    ActualOutcome,
    AnalysisMode,
    AvoidanceBasis,
    CandidateLabel,
    ClaimKind,
    ControlState,
    ControlTiming,
    EventState,
    ExposureAssessment,
    HazardKind,
    Interpretation,
    LifeSavingRule,
    ProcessingStatus,
    RuleControlIssue,
    RuleMappingStatus,
    RuleRelevance,
    SeriousMechanism,
)


class EvidenceSpan(BaseModel):
    id: str
    source_segment_id: str
    exact_quote: str
    start_utf16: int
    end_utf16: int
    claim_kind: ClaimKind
    rubric_reference: str | None = None


class ControlFinding(BaseModel):
    control_name: str
    state: ControlState
    timing: ControlTiming
    evidence_ids: list[str] = Field(default_factory=list)
    rationale: str | None = None


class HazardFinding(BaseModel):
    finding_id: str
    hazard_kind: HazardKind
    hazard_description: str
    serious_mechanism: SeriousMechanism
    exposure: ExposureAssessment
    controls: list[ControlFinding] = Field(default_factory=list)
    activity: str | None = None
    event_state: EventState
    actual_harm_evidence: str | None = None
    rationale_code: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class RuleFinding(BaseModel):
    rule_id: LifeSavingRule
    official_title: str
    relevance: RuleRelevance
    subclause_id: str | None = None
    control_issue: RuleControlIssue
    evidence_ids: list[str] = Field(default_factory=list)


class MissingFact(BaseModel):
    fact_id: str
    description: str
    importance: str  # why it matters for classification
    evidence_ids: list[str] = Field(default_factory=list)


class GroupingFields(BaseModel):
    activity_value: str | None = None
    activity_evidence_ids: list[str] = Field(default_factory=list)
    narrative_site_candidate: str | None = None
    narrative_site_evidence_ids: list[str] = Field(default_factory=list)
    supplied_site: str | None = None
    source_provenance: str | None = None
    site_conflict: bool = False


class AnalysisVersions(BaseModel):
    model: str
    prompt: str
    policy: str
    taxonomy: str


class AnalysisResult(BaseModel):
    """Top-level analysis result — the core contract between backend and frontend."""

    analysis_id: str
    report_revision_id: str
    mode: AnalysisMode
    processing_status: ProcessingStatus
    candidate_label: CandidateLabel | None = None
    interpretation: Interpretation | None = None
    review_reasons: list[str] = Field(default_factory=list)
    facts: list[HazardFinding] = Field(default_factory=list)
    lsr_findings: list[RuleFinding] = Field(default_factory=list)
    rule_mapping_status: RuleMappingStatus = RuleMappingStatus.NO_MATCH
    missing_facts: list[MissingFact] = Field(default_factory=list)
    clarification_question: str | None = None
    actual_outcome: ActualOutcome = ActualOutcome.NOT_STATED
    avoidance_basis: AvoidanceBasis = AvoidanceBasis.NOT_STATED
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    rationale_summary: str | None = None
    candidate_probability: float | None = None  # null unless calibrated model exists
    calibration_version: str | None = None
    versions: AnalysisVersions
    grouping: GroupingFields = Field(default_factory=GroupingFields)
