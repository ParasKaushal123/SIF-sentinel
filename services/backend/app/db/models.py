"""SQLAlchemy ORM models for all database tables."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provenance: Mapped[str] = mapped_column(String(50), nullable=False)  # synthetic, public_real, authorized_internal
    usage_permission: Mapped[str | None] = mapped_column(String(255))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    reports: Mapped[list["Report"]] = relationship(back_populates="dataset")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    role: Mapped[str] = mapped_column(String(50), default="reviewer")  # viewer, reviewer, admin
    password_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    source_report_id: Mapped[str | None] = mapped_column(String(255))
    current_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    current_analysis_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    supplied_site: Mapped[str | None] = mapped_column(String(255))
    report_type: Mapped[str | None] = mapped_column(String(100))
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    dataset: Mapped["Dataset"] = relationship(back_populates="reports")
    revisions: Mapped[list["ReportRevision"]] = relationship(back_populates="report", order_by="ReportRevision.revision_number")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="report")
    reviews: Mapped[list["Review"]] = relationship(back_populates="report")
    clarifications: Mapped[list["Clarification"]] = relationship(back_populates="report")

    __table_args__ = (
        Index("ix_reports_dataset_id", "dataset_id"),
        UniqueConstraint("dataset_id", "source_report_id", name="uq_reports_dataset_source"),
    )


class ReportRevision(Base):
    __tablename__ = "report_revisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(50), default="original")  # original, clarification
    author_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report: Mapped["Report"] = relationship(back_populates="revisions")
    segments: Mapped[list["SourceSegment"]] = relationship(back_populates="revision")

    __table_args__ = (
        UniqueConstraint("report_id", "revision_number", name="uq_revision_number"),
        Index("ix_revisions_report_id", "report_id"),
    )


class SourceSegment(Base):
    __tablename__ = "source_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    report_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_revisions.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # original, clarification
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    revision: Mapped["ReportRevision"] = relationship(back_populates="segments")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id"), nullable=False)
    report_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_revisions.id"), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    analysis_mode: Mapped[str] = mapped_column(String(50), default="live")
    model_version: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(100))
    policy_version: Mapped[str | None] = mapped_column(String(100))
    taxonomy_version: Mapped[str | None] = mapped_column(String(100))
    processing_status: Mapped[str] = mapped_column(String(50), default="queued")
    candidate_label: Mapped[str | None] = mapped_column(String(50))
    interpretation: Mapped[str | None] = mapped_column(String(50))
    payload_json: Mapped[dict | None] = mapped_column(JSONB)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report: Mapped["Report"] = relationship(back_populates="analyses")

    __table_args__ = (
        UniqueConstraint("input_fingerprint", name="uq_analysis_fingerprint"),
        Index("ix_analyses_report_id", "report_id"),
        Index("ix_analyses_status", "processing_status"),
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id"), nullable=False)
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id"), nullable=False)
    review_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    corrected_label: Mapped[str | None] = mapped_column(String(50))
    corrected_facts: Mapped[dict | None] = mapped_column(JSONB)
    corrected_rules: Mapped[dict | None] = mapped_column(JSONB)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report: Mapped["Report"] = relationship(back_populates="reviews")

    __table_args__ = (
        Index("ix_reviews_report_id", "report_id"),
        Index("ix_reviews_analysis_id", "analysis_id"),
    )


class Clarification(Base):
    __tablename__ = "clarifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id"), nullable=False)
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_segment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report: Mapped["Report"] = relationship(back_populates="clarifications")


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(64))
    column_mapping: Mapped[dict | None] = mapped_column(JSONB)
    validation_status: Mapped[str] = mapped_column(String(50), default="pending")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    accepted_rows: Mapped[int] = mapped_column(Integer, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ImportRow(Base):
    __tablename__ = "import_rows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_fields: Mapped[dict | None] = mapped_column(JSONB)
    row_status: Mapped[str] = mapped_column(String(50), default="pending")
    error_codes: Mapped[list | None] = mapped_column(JSONB)
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_import_rows_batch_id", "batch_id"),
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # analyze_report, analyze_lab
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    lease_owner: Mapped[str | None] = mapped_column(String(100))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_error_code: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_jobs_status_available", "status", "available_at"),
    )


class DuplicateLink(Base):
    __tablename__ = "duplicate_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id"), nullable=False)
    canonical_report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(50), default="suspected")
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    before_ref: Mapped[dict | None] = mapped_column(JSONB)
    after_ref: Mapped[dict | None] = mapped_column(JSONB)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    split_manifest_hash: Mapped[str | None] = mapped_column(String(64))
    model_versions: Mapped[dict | None] = mapped_column(JSONB)
    label_provenance: Mapped[str | None] = mapped_column(String(50))
    metrics_json: Mapped[dict | None] = mapped_column(JSONB)
    support_counts: Mapped[dict | None] = mapped_column(JSONB)
    run_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LabRun(Base):
    __tablename__ = "lab_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    left_text: Mapped[str] = mapped_column(Text, nullable=False)
    right_text: Mapped[str] = mapped_column(Text, nullable=False)
    left_analysis_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    right_analysis_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    mode: Mapped[str] = mapped_column(String(50), default="live")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
