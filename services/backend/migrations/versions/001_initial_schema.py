"""Initial schema — all 14 tables.

Revision ID: 001
Revises: None
Create Date: 2026-09-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- datasets ---
    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provenance", sa.String(50), nullable=False),
        sa.Column("usage_permission", sa.String(255)),
        sa.Column("is_demo", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True),
        sa.Column("role", sa.String(50), server_default="reviewer"),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- reports ---
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("source_report_id", sa.String(255)),
        sa.Column("current_revision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("current_analysis_id", postgresql.UUID(as_uuid=True)),
        sa.Column("supplied_site", sa.String(255)),
        sa.Column("report_type", sa.String(100)),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reports_dataset_id", "reports", ["dataset_id"])
    op.create_unique_constraint("uq_reports_dataset_source", "reports", ["dataset_id", "source_report_id"])

    # --- report_revisions ---
    op.create_table(
        "report_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("revision_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("source_kind", sa.String(50), server_default="original"),
        sa.Column("author_id", postgresql.UUID(as_uuid=True)),
        sa.Column("text_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_revision_number", "report_revisions", ["report_id", "revision_number"])
    op.create_index("ix_revisions_report_id", "report_revisions", ["report_id"])

    # --- source_segments ---
    op.create_table(
        "source_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("report_revisions.id"), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- analyses ---
    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("report_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("report_revisions.id"), nullable=False),
        sa.Column("input_fingerprint", sa.String(128), nullable=False),
        sa.Column("analysis_mode", sa.String(50), server_default="live"),
        sa.Column("model_version", sa.String(100)),
        sa.Column("prompt_version", sa.String(100)),
        sa.Column("policy_version", sa.String(100)),
        sa.Column("taxonomy_version", sa.String(100)),
        sa.Column("processing_status", sa.String(50), server_default="queued"),
        sa.Column("candidate_label", sa.String(50)),
        sa.Column("interpretation", sa.String(50)),
        sa.Column("payload_json", postgresql.JSONB),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_analysis_fingerprint", "analyses", ["input_fingerprint"])
    op.create_index("ix_analyses_report_id", "analyses", ["report_id"])
    op.create_index("ix_analyses_status", "analyses", ["processing_status"])

    # --- reviews ---
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id"), nullable=False),
        sa.Column("review_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("corrected_label", sa.String(50)),
        sa.Column("corrected_facts", postgresql.JSONB),
        sa.Column("corrected_rules", postgresql.JSONB),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reviews_report_id", "reviews", ["report_id"])
    op.create_index("ix_reviews_analysis_id", "reviews", ["analysis_id"])

    # --- clarifications ---
    op.create_table(
        "clarifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id"), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_segment_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- import_batches ---
    op.create_table(
        "import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("file_hash", sa.String(64)),
        sa.Column("column_mapping", postgresql.JSONB),
        sa.Column("validation_status", sa.String(50), server_default="pending"),
        sa.Column("total_rows", sa.Integer, server_default="0"),
        sa.Column("accepted_rows", sa.Integer, server_default="0"),
        sa.Column("rejected_rows", sa.Integer, server_default="0"),
        sa.Column("duplicate_rows", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- import_rows ---
    op.create_table(
        "import_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_batches.id"), nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("raw_fields", postgresql.JSONB),
        sa.Column("row_status", sa.String(50), server_default="pending"),
        sa.Column("error_codes", postgresql.JSONB),
        sa.Column("report_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_import_rows_batch_id", "import_rows", ["batch_id"])

    # --- jobs ---
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("idempotency_key", sa.String(128), unique=True),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("attempts", sa.Integer, server_default="0"),
        sa.Column("max_attempts", sa.Integer, server_default="3"),
        sa.Column("lease_owner", sa.String(100)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_error_code", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_jobs_status_available", "jobs", ["status", "available_at"])

    # --- duplicate_links ---
    op.create_table(
        "duplicate_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("canonical_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("resolution_status", sa.String(50), server_default="suspected"),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- audit_events ---
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("before_ref", postgresql.JSONB),
        sa.Column("after_ref", postgresql.JSONB),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_entity", "audit_events", ["entity_type", "entity_id"])

    # --- evaluation_runs ---
    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True)),
        sa.Column("split_manifest_hash", sa.String(64)),
        sa.Column("model_versions", postgresql.JSONB),
        sa.Column("label_provenance", sa.String(50)),
        sa.Column("metrics_json", postgresql.JSONB),
        sa.Column("support_counts", postgresql.JSONB),
        sa.Column("run_timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- lab_runs ---
    op.create_table(
        "lab_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("left_text", sa.Text, nullable=False),
        sa.Column("right_text", sa.Text, nullable=False),
        sa.Column("left_analysis_id", postgresql.UUID(as_uuid=True)),
        sa.Column("right_analysis_id", postgresql.UUID(as_uuid=True)),
        sa.Column("mode", sa.String(50), server_default="live"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("lab_runs")
    op.drop_table("evaluation_runs")
    op.drop_table("audit_events")
    op.drop_table("duplicate_links")
    op.drop_table("jobs")
    op.drop_table("import_rows")
    op.drop_table("import_batches")
    op.drop_table("clarifications")
    op.drop_table("reviews")
    op.drop_table("analyses")
    op.drop_table("source_segments")
    op.drop_table("report_revisions")
    op.drop_table("reports")
    op.drop_table("users")
    op.drop_table("datasets")
