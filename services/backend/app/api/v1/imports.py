"""Import endpoints — CSV upload, preview, validate, commit, status."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Analysis, ImportBatch, ImportRow
from app.db.session import get_db
from app.schemas.api import (
    ImportCommitResponse,
    ImportPreviewResponse,
    ImportStatusResponse,
    ImportValidateRequest,
    ImportValidateResponse,
)
from app.services import import_service

router = APIRouter()


@router.post("/upload", response_model=ImportPreviewResponse)
async def upload_csv(
    dataset_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV and return preview with detected headers."""
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    batch, headers, sample, total = await import_service.create_preview(
        db, dataset_id, contents
    )

    return ImportPreviewResponse(
        preview_id=batch.id,
        headers=headers,
        row_count=total,
        sample_rows=sample,
    )


@router.post("/{batch_id}/validate", response_model=ImportValidateResponse)
async def validate_import(
    batch_id: UUID,
    body: ImportValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate column mapping against batch rows."""
    try:
        valid, invalid, duplicate, errors = await import_service.validate_mapping(
            db, batch_id, body.column_mapping
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ImportValidateResponse(
        valid_rows=valid,
        invalid_rows=invalid,
        duplicate_rows=duplicate,
        row_errors=errors,
    )


@router.post("/{batch_id}/commit", response_model=ImportCommitResponse)
async def commit_import(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Commit validated import: create reports and enqueue analysis."""
    try:
        accepted, rejected, duplicate, jobs = await import_service.commit_import(
            db, batch_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ImportCommitResponse(
        batch_id=batch_id,
        accepted=accepted,
        rejected=rejected,
        duplicate=duplicate,
        jobs_created=jobs,
    )


@router.get("/{batch_id}/status", response_model=ImportStatusResponse)
async def get_import_status(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Poll import batch progress including analysis status."""
    result = await db.execute(select(ImportBatch).where(ImportBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    # Count analysis statuses for reports in this batch
    rows_result = await db.execute(
        select(ImportRow.report_id)
        .where(ImportRow.batch_id == batch_id, ImportRow.report_id.is_not(None))
    )
    report_ids = [r[0] for r in rows_result.all()]

    queued = succeeded = failed = 0
    if report_ids:
        from app.db.models import Report
        for rid in report_ids:
            report_result = await db.execute(select(Report).where(Report.id == rid))
            report = report_result.scalar_one_or_none()
            if report and report.current_analysis_id:
                analysis_result = await db.execute(
                    select(Analysis).where(Analysis.id == report.current_analysis_id)
                )
                analysis = analysis_result.scalar_one_or_none()
                if analysis:
                    if analysis.processing_status == "succeeded":
                        succeeded += 1
                    elif analysis.processing_status in ("failed", "error"):
                        failed += 1
                    else:
                        queued += 1
            else:
                queued += 1

    return ImportStatusResponse(
        batch_id=batch.id,
        validation_status=batch.validation_status,
        total_rows=batch.total_rows,
        accepted=batch.accepted_rows,
        rejected=batch.rejected_rows,
        duplicate=batch.duplicate_rows,
        analyses_queued=queued,
        analyses_succeeded=succeeded,
        analyses_failed=failed,
    )
