"""Report endpoints — list, detail, create, review, clarify."""

from uuid import UUID

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Analysis, Report, Review, Clarification
from app.db.session import get_db
from app.schemas.api import (
    ClarificationCreateRequest,
    ClarificationResponse,
    ReportCreateRequest,
    ReportDetailResponse,
    ReportListResponse,
    ReportSummary,
    ReviewCreateRequest,
    ReviewResponse,
)
from app.schemas.enums import ReviewStatus
from app.services import report_service

router = APIRouter()


# ---------------------------------------------------------------------------
# List reports
# ---------------------------------------------------------------------------
@router.get("", response_model=ReportListResponse)
async def list_reports(
    dataset_id: UUID | None = None,
    candidate_label: str | None = None,
    interpretation: str | None = None,
    review_status: str | None = None,
    site: str | None = None,
    search: str | None = None,
    hazard_kind: str | None = None,
    control_state: str | None = None,
    rule: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated, filterable report list with cohort counts."""
    reports, total = await report_service.list_reports(
        db,
        dataset_id=dataset_id,
        candidate_label=candidate_label,
        interpretation=interpretation,
        review_status_filter=review_status,
        site=site,
        search=search,
        cursor=cursor,
        limit=limit,
    )

    cohort_counts = await report_service.count_by_cohort(db, dataset_id=dataset_id)

    items: list[ReportSummary] = []
    for r in reports:
        revision = await report_service.get_latest_revision(db, r.id)
        preview = ""
        if revision:
            text = revision.original_text
            preview = (text[:200] + "…") if len(text) > 200 else text

        rev_status = await report_service.derive_review_status(db, r)

        analysis = await report_service.get_current_analysis(db, r)
        candidate = analysis.candidate_label if analysis else None
        interp = analysis.interpretation if analysis else None
        processing = analysis.processing_status if analysis else None
        key_finding = report_service.derive_key_finding(analysis)

        items.append(
            ReportSummary(
                id=r.id,
                dataset_id=r.dataset_id,
                source_report_id=r.source_report_id,
                narrative_preview=preview,
                site=r.supplied_site,
                report_type=r.report_type,
                occurred_at=r.occurred_at,
                created_at=r.created_at,
                candidate_label=candidate,
                interpretation=interp,
                review_status=rev_status,
                processing_status=processing,
                key_finding=key_finding,
            )
        )

    next_cursor = None
    if items and len(items) == limit:
        next_cursor = items[-1].created_at.isoformat()

    return ReportListResponse(
        items=items,
        total_count=total,
        cohort_counts=cohort_counts,
        next_cursor=next_cursor,
    )


# ---------------------------------------------------------------------------
# Export cohort (CSV / JSON)
# ---------------------------------------------------------------------------
@router.get("/export")
async def export_reports(
    dataset_id: UUID | None = None,
    candidate_label: str | None = None,
    interpretation: str | None = None,
    site: str | None = None,
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
):
    """Export the filtered report cohort as CSV or JSON.

    Registered before the `/{report_id}` route so "export" is not captured
    as a report id.
    """
    reports, _ = await report_service.list_reports(
        db,
        dataset_id=dataset_id,
        candidate_label=candidate_label,
        interpretation=interpretation,
        site=site,
        limit=10000,
    )

    rows: list[dict] = []
    for r in reports:
        analysis = await report_service.get_current_analysis(db, r)
        review_status = await report_service.derive_review_status(db, r)
        rows.append({
            "report_id": str(r.id),
            "source_report_id": r.source_report_id or "",
            "site": r.supplied_site or "",
            "report_type": r.report_type or "",
            "candidate_label": analysis.candidate_label if analysis else "",
            "interpretation": analysis.interpretation if analysis else "",
            "review_status": review_status.value,
            "occurred_at": r.occurred_at.isoformat() if r.occurred_at else "",
            "created_at": r.created_at.isoformat(),
        })

    if format == "json":
        return JSONResponse(content={"reports": rows, "count": len(rows)})

    # CSV
    buf = io.StringIO()
    fieldnames = [
        "report_id", "source_report_id", "site", "report_type",
        "candidate_label", "interpretation", "review_status",
        "occurred_at", "created_at",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sif_sentinel_export.csv"},
    )


# ---------------------------------------------------------------------------
# Get single report
# ---------------------------------------------------------------------------
@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    """Return full report detail with current analysis and review."""
    report = await report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    revision = await report_service.get_latest_revision(db, report_id)
    narrative = revision.original_text if revision else ""
    revision_count = await report_service.get_revision_count(db, report_id)

    # Parse analysis payload
    current_analysis = None
    analysis = await report_service.get_current_analysis(db, report)
    if analysis and analysis.payload_json:
        from app.schemas.analysis import AnalysisResult
        try:
            current_analysis = AnalysisResult(**analysis.payload_json)
        except Exception:
            pass

    # Get latest review
    review_status = await report_service.derive_review_status(db, report)
    latest_review_row = await report_service.get_latest_review(db, report_id)
    latest_review = None
    if latest_review_row:
        latest_review = ReviewResponse(
            id=latest_review_row.id,
            report_id=latest_review_row.report_id,
            analysis_id=latest_review_row.analysis_id,
            review_version=latest_review_row.review_version,
            decision=latest_review_row.decision,
            corrected_label=latest_review_row.corrected_label,
            corrected_facts=latest_review_row.corrected_facts,
            reason=latest_review_row.reason,
            author_id=latest_review_row.author_id,
            created_at=latest_review_row.created_at,
        )

    return ReportDetailResponse(
        id=report.id,
        dataset_id=report.dataset_id,
        source_report_id=report.source_report_id,
        narrative=narrative,
        site=report.supplied_site,
        report_type=report.report_type,
        occurred_at=report.occurred_at,
        created_at=report.created_at,
        current_analysis=current_analysis,
        review_status=review_status,
        latest_review=latest_review,
        revision_count=revision_count,
    )


# ---------------------------------------------------------------------------
# Create report
# ---------------------------------------------------------------------------
@router.post("", response_model=ReportSummary, status_code=201)
async def create_report(body: ReportCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a new report, initial revision, and enqueue analysis."""
    report, revision, job_id = await report_service.create_report(db, body)

    return ReportSummary(
        id=report.id,
        dataset_id=report.dataset_id,
        source_report_id=report.source_report_id,
        narrative_preview=body.narrative[:200],
        site=body.site,
        report_type=body.report_type,
        occurred_at=body.occurred_at,
        created_at=report.created_at,
        processing_status="queued" if job_id else None,
    )


# ---------------------------------------------------------------------------
# Submit review
# ---------------------------------------------------------------------------
@router.post("/{report_id}/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(
    report_id: UUID,
    body: ReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a human review for a report's analysis."""
    report = await report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Get current review version
    count_result = await db.execute(
        select(func.count()).where(Review.report_id == report_id)
    )
    current_version = count_result.scalar() or 0

    if body.expected_review_version != current_version:
        raise HTTPException(status_code=409, detail="Review version conflict")

    review = Review(
        report_id=report_id,
        analysis_id=body.analysis_id,
        review_version=current_version + 1,
        decision=body.decision.value,
        corrected_label=body.corrected_label.value if body.corrected_label else None,
        corrected_facts=body.corrected_facts,
        reason=body.reason,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return ReviewResponse(
        id=review.id,
        report_id=review.report_id,
        analysis_id=review.analysis_id,
        review_version=review.review_version,
        decision=body.decision,
        corrected_label=body.corrected_label,
        corrected_facts=body.corrected_facts,
        reason=review.reason,
        author_id=review.author_id,
        created_at=review.created_at,
    )


# ---------------------------------------------------------------------------
# Submit clarification
# ---------------------------------------------------------------------------
@router.post("/{report_id}/clarifications", response_model=ClarificationResponse, status_code=201)
async def create_clarification(
    report_id: UUID,
    body: ClarificationCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a clarification, create new revision, and re-analyze."""
    report = await report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    clarification = Clarification(
        report_id=report_id,
        analysis_id=body.analysis_id,
        question=body.question,
        answer=body.answer,
    )
    db.add(clarification)

    # Create new revision with clarification appended
    revision = await report_service.get_latest_revision(db, report_id)
    if revision:
        import hashlib
        from app.db.models import ReportRevision, SourceSegment

        new_text = f"{revision.original_text}\n\n[Clarification]\nQ: {body.question}\nA: {body.answer}"
        text_hash = hashlib.sha256(new_text.encode()).hexdigest()
        new_revision = ReportRevision(
            report_id=report_id,
            revision_number=revision.revision_number + 1,
            original_text=new_text,
            source_kind="clarification",
            text_hash=text_hash,
        )
        db.add(new_revision)
        await db.flush()

        # Add clarification segment
        segment = SourceSegment(
            report_revision_id=new_revision.id,
            kind="clarification",
            text=body.answer,
        )
        db.add(segment)

        report.current_revision_id = new_revision.id

        # Enqueue re-analysis
        from app.db.models import Job
        idempotency_key = f"analyze:{report_id}:rev:{new_revision.id}"
        job = Job(
            kind="analyze_report",
            payload={
                "report_id": str(report_id),
                "revision_id": str(new_revision.id),
                "text_hash": text_hash,
            },
            idempotency_key=idempotency_key,
            status="pending",
        )
        db.add(job)
        await db.flush()
        job_id = job.id
    else:
        job_id = None

    await db.commit()
    await db.refresh(clarification)

    return ClarificationResponse(
        id=clarification.id,
        report_id=clarification.report_id,
        analysis_id=clarification.analysis_id,
        question=clarification.question,
        answer=clarification.answer,
        author_id=clarification.author_id,
        created_at=clarification.created_at,
        new_analysis_job_id=job_id,
    )
