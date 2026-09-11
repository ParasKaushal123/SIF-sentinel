"""Job processor — runs a single analysis job end to end."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.pipeline import run_analysis
from app.config import settings
from app.db.models import Analysis, Job, Report, ReportRevision


async def process_analyze_report(db: AsyncSession, job: Job) -> None:
    """Process an analyze_report job.

    Steps:
      1. Load the revision text
      2. Check for an existing analysis with the same fingerprint (idempotency)
      3. Run the analysis pipeline
      4. Persist the Analysis row
      5. Link it as the report's current analysis
    """
    payload = job.payload
    report_id = uuid.UUID(payload["report_id"])
    revision_id = uuid.UUID(payload["revision_id"])
    text_hash = payload["text_hash"]

    # Load revision
    rev_result = await db.execute(
        select(ReportRevision).where(ReportRevision.id == revision_id)
    )
    revision = rev_result.scalar_one_or_none()
    if not revision:
        raise ValueError(f"Revision {revision_id} not found")

    # Fingerprint = hash of (text + model + policy versions)
    fingerprint = f"{text_hash}:{settings.model_provider}:luck-test-policy-v1"

    # Idempotency: reuse existing analysis if fingerprint matches
    existing_result = await db.execute(
        select(Analysis).where(Analysis.input_fingerprint == fingerprint)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        # Link and return
        report_result = await db.execute(select(Report).where(Report.id == report_id))
        report = report_result.scalar_one_or_none()
        if report:
            report.current_analysis_id = existing.id
        await db.commit()
        return

    # Create analysis row (queued → running)
    analysis = Analysis(
        report_id=report_id,
        report_revision_id=revision_id,
        input_fingerprint=fingerprint,
        analysis_mode="live",
        processing_status="running",
        model_version=None,
    )
    db.add(analysis)
    await db.flush()
    analysis_id = analysis.id

    # Run pipeline
    result, duration_ms = await run_analysis(
        revision.original_text,
        analysis_id=str(analysis_id),
        report_revision_id=str(revision_id),
        provider=settings.model_provider,
        mode="live",
    )

    # Persist results
    analysis.processing_status = result.processing_status.value
    analysis.candidate_label = result.candidate_label.value if result.candidate_label else None
    analysis.interpretation = result.interpretation.value if result.interpretation else None
    analysis.payload_json = result.model_dump(mode="json")
    analysis.model_version = result.versions.model
    analysis.prompt_version = result.versions.prompt
    analysis.policy_version = result.versions.policy
    analysis.taxonomy_version = result.versions.taxonomy
    analysis.duration_ms = duration_ms

    # Link as current analysis
    report_result = await db.execute(select(Report).where(Report.id == report_id))
    report = report_result.scalar_one_or_none()
    if report:
        report.current_analysis_id = analysis_id

    await db.commit()


PROCESSORS = {
    "analyze_report": process_analyze_report,
}


async def process_job(db: AsyncSession, job: Job) -> None:
    """Dispatch a job to its processor."""
    processor = PROCESSORS.get(job.kind)
    if not processor:
        raise ValueError(f"No processor for job kind: {job.kind}")
    await processor(db, job)
