"""API request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .analysis import AnalysisResult
from .enums import (
    CandidateLabel,
    DatasetProvenance,
    ImportRowStatus,
    Interpretation,
    JobStatus,
    LifeSavingRule,
    ReviewDecision,
    ReviewStatus,
    ValidationStatus,
)


# --- Common ---


class APIError(BaseModel):
    code: str
    message: str
    field_errors: dict[str, str] | None = None
    request_id: str | None = None


class PaginatedResponse(BaseModel):
    next_cursor: str | None = None
    total_count: int | None = None


# --- Datasets ---


class DatasetResponse(BaseModel):
    id: UUID
    name: str
    provenance: DatasetProvenance
    is_demo: bool
    created_at: datetime


# --- Reports ---


class ReportCreateRequest(BaseModel):
    dataset_id: UUID
    narrative: str = Field(min_length=1, max_length=20000)
    site: str | None = None
    report_type: str | None = None
    occurred_at: datetime | None = None
    source_report_id: str | None = None


class ReportSummary(BaseModel):
    id: UUID
    dataset_id: UUID
    source_report_id: str | None = None
    narrative_preview: str
    site: str | None = None
    report_type: str | None = None
    occurred_at: datetime | None = None
    created_at: datetime
    candidate_label: CandidateLabel | None = None
    interpretation: Interpretation | None = None
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    lsr_rules: list[LifeSavingRule] = Field(default_factory=list)
    review_reasons: list[str] = Field(default_factory=list)
    activity: str | None = None
    processing_status: str | None = None
    key_finding: str | None = None


class ReportListResponse(PaginatedResponse):
    items: list[ReportSummary]
    cohort_counts: dict[str, int] = Field(default_factory=dict)


class ReportDetailResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    source_report_id: str | None = None
    narrative: str
    site: str | None = None
    report_type: str | None = None
    occurred_at: datetime | None = None
    created_at: datetime
    current_analysis: AnalysisResult | None = None
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    latest_review: "ReviewResponse | None" = None
    revision_count: int = 1


# --- Reviews ---


class ReviewCreateRequest(BaseModel):
    analysis_id: UUID
    expected_review_version: int = 0
    decision: ReviewDecision
    corrected_label: CandidateLabel | None = None
    corrected_facts: dict | None = None
    corrected_rules: list[LifeSavingRule] | None = None
    reason: str = Field(min_length=1, max_length=2000)


class ReviewResponse(BaseModel):
    id: UUID
    report_id: UUID
    analysis_id: UUID
    review_version: int
    decision: ReviewDecision
    corrected_label: CandidateLabel | None = None
    corrected_facts: dict | None = None
    corrected_rules: list[LifeSavingRule] | None = None
    reason: str
    author_id: UUID | None = None
    created_at: datetime


# --- Clarifications ---


class ClarificationCreateRequest(BaseModel):
    analysis_id: UUID
    question: str
    answer: str = Field(min_length=1, max_length=5000)
    expected_revision_id: UUID | None = None


class ClarificationResponse(BaseModel):
    id: UUID
    report_id: UUID
    analysis_id: UUID
    question: str
    answer: str
    author_id: UUID | None = None
    created_at: datetime
    new_analysis_job_id: UUID | None = None


# --- Import ---


class ImportPreviewRequest(BaseModel):
    dataset_id: UUID


class ImportPreviewResponse(BaseModel):
    preview_id: UUID
    headers: list[str]
    row_count: int
    sample_rows: list[dict]
    parse_warnings: list[str] = Field(default_factory=list)


class ColumnMapping(BaseModel):
    narrative: str
    source_report_id: str | None = None
    site: str | None = None
    report_type: str | None = None
    occurred_at: str | None = None


class ImportValidateRequest(BaseModel):
    column_mapping: ColumnMapping


class ImportValidateResponse(BaseModel):
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    row_errors: list[dict] = Field(default_factory=list)


class ImportCommitRequest(BaseModel):
    mapping_hash: str
    idempotency_key: str


class ImportCommitResponse(BaseModel):
    batch_id: UUID
    accepted: int
    rejected: int
    duplicate: int
    jobs_created: int


class ImportStatusResponse(BaseModel):
    batch_id: UUID
    validation_status: ValidationStatus
    total_rows: int
    accepted: int
    rejected: int
    duplicate: int
    analyses_queued: int
    analyses_succeeded: int
    analyses_failed: int
    row_errors: list[dict] = Field(default_factory=list)


# --- Jobs ---


class JobStatusResponse(BaseModel):
    id: UUID
    status: JobStatus
    attempts: int
    last_error: str | None = None


# --- Insights ---



class SpatialAsset(BaseModel):
    id: str
    name: str
    short: str
    type: str
    glyph: str
    region: str
    lon: float
    lat: float
    review: int = 0
    gaps: int = 0
    total: int = 0

class SpatialUnmapped(BaseModel):
    id: str
    name: str
    why: str

class SpatialOverviewResponse(BaseModel):
    assets: list[SpatialAsset] = Field(default_factory=list)
    unmapped: list[SpatialUnmapped] = Field(default_factory=list)
    reports: list[dict] = Field(default_factory=list)

class InsightsOverviewResponse(BaseModel):
    total_eligible: int
    classified: int = 0
    positive_candidates: int
    negative_candidates: int
    unresolved: int
    reviewed: int
    awaiting_review: int = 0
    sif_awaiting_review: int = 0
    needs_information: int = 0
    classification_coverage: float | None = None
    report_density: float | None = None
    site_activity_table: list[dict] = Field(default_factory=list)
    activity_table: list[dict] = Field(default_factory=list)
    rule_distribution: dict[str, int] = Field(default_factory=dict)
    barrier_state_distribution: dict[str, int] = Field(default_factory=dict)
    hazard_distribution: dict[str, int] = Field(default_factory=dict)


class PatternGroup(BaseModel):
    id: str | None = None
    pattern_key: str
    activity: str | None = None
    hazard: str | None = None
    control_concept: str | None = None
    control_state: str | None = None
    report_count: int
    exposure: str | None = None
    gap_count: int = 0
    model_only_count: int = 0
    rule: str | None = None
    rule_mapping_status: str | None = None
    gap_kind: str | None = None
    gap_rationale: str | None = None
    clarifiable: bool = True
    overlap_note: str | None = None
    member_reports: list[dict] = Field(default_factory=list)
    representative_evidence: list[str] = Field(default_factory=list)
    is_failure_pattern: bool = False
    is_information_gap: bool = False


class InsightsPatternsResponse(PaginatedResponse):
    patterns: list[PatternGroup]


# --- Lab ---


class LabComparisonRequest(BaseModel):
    left_text: str = Field(min_length=1, max_length=20000)
    right_text: str = Field(min_length=1, max_length=20000)
    mode: str = "live"


class LabComparisonResponse(BaseModel):
    comparison_id: UUID
    left_analysis: AnalysisResult | None = None
    right_analysis: AnalysisResult | None = None
    changed_facts: list[dict] = Field(default_factory=list)
    created_at: datetime


# --- Health ---


class HealthResponse(BaseModel):
    status: str
    api: bool
    database: bool
    worker: bool
    version: str = "0.1.0"


# --- Exports ---


class ExportRequest(BaseModel):
    format: str = "csv"  # csv | json
    # same cohort filters as report list


# Resolve forward refs
ReportDetailResponse.model_rebuild()
