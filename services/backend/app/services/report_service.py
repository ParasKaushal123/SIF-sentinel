"""Report service — persistence layer for report CRUD operations."""

import hashlib
import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Analysis,
    Job,
    Report,
    ReportRevision,
    Review,
    SourceSegment,
)
from app.schemas.api import ReportCreateRequest, ReportSummary
from app.schemas.enums import CandidateLabel, Interpretation, ReviewStatus


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------
async def create_report(
    db: AsyncSession,
    body: ReportCreateRequest,
    *,
    enqueue_analysis: bool = True,
) -> tuple[Report, ReportRevision, uuid.UUID | None]:
    """Create report + initial revision + source segment, optionally enqueue analysis.

    Returns (report, revision, job_id | None).
    """
    report = Report(
        dataset_id=body.dataset_id,
        source_report_id=body.source_report_id,
        supplied_site=body.site,
        report_type=body.report_type,
        occurred_at=body.occurred_at,
    )
    db.add(report)
    await db.flush()

    # Create revision
    text_hash = hashlib.sha256(body.narrative.encode()).hexdigest()
    revision = ReportRevision(
        report_id=report.id,
        revision_number=1,
        original_text=body.narrative,
        source_kind="original",
        text_hash=text_hash,
    )
    db.add(revision)
    await db.flush()

    # Create source segment
    segment = SourceSegment(
        report_revision_id=revision.id,
        kind="original",
        text=body.narrative,
    )
    db.add(segment)

    # Link revision
    report.current_revision_id = revision.id

    # Enqueue analysis job
    job_id = None
    if enqueue_analysis:
        idempotency_key = f"analyze:{report.id}:rev:{revision.id}"
        job = Job(
            kind="analyze_report",
            payload={
                "report_id": str(report.id),
                "revision_id": str(revision.id),
                "text_hash": text_hash,
            },
            idempotency_key=idempotency_key,
            status="pending",
        )
        db.add(job)
        await db.flush()
        job_id = job.id

    await db.commit()
    await db.refresh(report)
    return report, revision, job_id


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------
async def get_report_by_id(db: AsyncSession, report_id: uuid.UUID) -> Report | None:
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Get latest revision
# ---------------------------------------------------------------------------
async def get_latest_revision(
    db: AsyncSession, report_id: uuid.UUID
) -> ReportRevision | None:
    result = await db.execute(
        select(ReportRevision)
        .where(ReportRevision.report_id == report_id)
        .order_by(ReportRevision.revision_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Get current analysis
# ---------------------------------------------------------------------------
async def get_current_analysis(
    db: AsyncSession, report: Report
) -> Analysis | None:
    if not report.current_analysis_id:
        return None
    result = await db.execute(
        select(Analysis).where(Analysis.id == report.current_analysis_id)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Get latest review
# ---------------------------------------------------------------------------
async def get_latest_review(
    db: AsyncSession, report_id: uuid.UUID
) -> Review | None:
    result = await db.execute(
        select(Review)
        .where(Review.report_id == report_id)
        .order_by(Review.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Derive review status
# ---------------------------------------------------------------------------
# Map a review decision to the corresponding review status
_DECISION_TO_STATUS = {
    "confirmed": ReviewStatus.CONFIRMED,
    "corrected": ReviewStatus.CORRECTED,
    "needs_information": ReviewStatus.NEEDS_INFORMATION,
}


async def derive_review_status(
    db: AsyncSession, report: Report
) -> ReviewStatus:
    """Derive the review status for a report based on its analysis and reviews."""
    if not report.current_analysis_id:
        return ReviewStatus.UNREVIEWED

    analysis = await get_current_analysis(db, report)
    if not analysis:
        return ReviewStatus.UNREVIEWED

    if analysis.processing_status in ("queued", "running"):
        return ReviewStatus.UNREVIEWED

    review = await get_latest_review(db, report.id)
    if not review:
        return ReviewStatus.UNREVIEWED

    # A review for a superseded analysis is stale — the report needs re-review
    if review.analysis_id != report.current_analysis_id:
        return ReviewStatus.STALE

    return _DECISION_TO_STATUS.get(review.decision, ReviewStatus.CONFIRMED)


# ---------------------------------------------------------------------------
# Derive a one-line "key finding" from an analysis payload
# ---------------------------------------------------------------------------
_HAZARD_PHRASES = {
    "gravity": "Fall / working-at-height energy",
    "mechanical": "Mechanical / lifting energy",
    "electrical": "Electrical energy exposure",
    "pressure": "Stored-pressure / release energy",
    "fire_explosion": "Fire / explosion potential",
    "toxic_asphyxiation": "Toxic / asphyxiation exposure",
    "vehicle": "Vehicle / transport energy",
    "other": "Hazardous energy present",
}

_CONTROL_PHRASES = {
    "failed": "control failed",
    "absent": "control absent",
    "bypassed": "control bypassed",
    "effective_reported": "control reported effective",
    "present_unverified": "control unverified",
    "unknown": "control state unclear",
}


def derive_key_finding(analysis) -> str | None:
    """Summarise an analysis into a single reviewer-facing phrase.

    Comes from the analysis payload (top hazard + its control state), not a
    frontend guess. Falls back to the interpretation when no hazard is present.
    """
    if not analysis or not analysis.payload_json:
        return None
    payload = analysis.payload_json
    facts = payload.get("facts") or []
    if facts:
        top = facts[0]
        hazard = top.get("hazard_kind", "other")
        controls = top.get("controls") or []
        state = controls[0].get("state", "unknown") if controls else "unknown"
        hz = _HAZARD_PHRASES.get(hazard, "Hazardous energy present")
        ctl = _CONTROL_PHRASES.get(state, "control state unclear")
        return f"{hz} — {ctl}"
    interp = (analysis.interpretation or "").replace("_", " ")
    return interp.capitalize() or None


# ---------------------------------------------------------------------------
# List with filters
# ---------------------------------------------------------------------------
async def list_reports(
    db: AsyncSession,
    *,
    dataset_id: uuid.UUID | None = None,
    candidate_label: str | None = None,
    interpretation: str | None = None,
    review_status_filter: str | None = None,
    site: str | None = None,
    search: str | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> tuple[list[Report], int]:
    """List reports with filtering and pagination.

    Returns (reports, total_count).
    """
    query = select(Report).order_by(Report.created_at.desc())

    # Apply filters
    if dataset_id:
        query = query.where(Report.dataset_id == dataset_id)
    if site:
        query = query.where(Report.supplied_site == site)

    # For label/interpretation filtering, join to analyses
    if candidate_label or interpretation:
        query = query.join(
            Analysis,
            and_(
                Analysis.id == Report.current_analysis_id,
                Analysis.processing_status == "succeeded",
            ),
        )
        if candidate_label:
            query = query.where(Analysis.candidate_label == candidate_label)
        if interpretation:
            query = query.where(Analysis.interpretation == interpretation)

    # Search in narrative text
    if search:
        query = query.join(
            ReportRevision,
            ReportRevision.id == Report.current_revision_id,
        ).where(
            ReportRevision.original_text.ilike(f"%{search}%")
        )

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply cursor-based pagination
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Report.created_at < cursor_dt)
        except ValueError:
            pass

    query = query.limit(limit)

    result = await db.execute(query)
    reports = list(result.scalars().all())

    return reports, total


# ---------------------------------------------------------------------------
# Count by cohort
# ---------------------------------------------------------------------------
async def count_by_cohort(
    db: AsyncSession, dataset_id: uuid.UUID | None = None
) -> dict[str, int]:
    """Count reports by candidate label cohort."""
    base = select(
        Analysis.candidate_label,
        func.count(func.distinct(Report.id)),
    ).join(
        Report,
        and_(
            Report.current_analysis_id == Analysis.id,
            Analysis.processing_status == "succeeded",
        ),
    )

    if dataset_id:
        base = base.where(Report.dataset_id == dataset_id)

    base = base.group_by(Analysis.candidate_label)
    result = await db.execute(base)

    counts: dict[str, int] = {}
    for label, count in result.all():
        if label:
            counts[label] = count

    return counts


# ---------------------------------------------------------------------------
# Revision count
# ---------------------------------------------------------------------------
async def get_revision_count(
    db: AsyncSession, report_id: uuid.UUID
) -> int:
    result = await db.execute(
        select(func.count()).where(ReportRevision.report_id == report_id)
    )
    return result.scalar() or 1
