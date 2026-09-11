"""Import service — CSV intake, validation, and commit pipeline."""

import csv
import hashlib
import io
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Dataset,
    ImportBatch,
    ImportRow,
    Job,
    Report,
    ReportRevision,
    SourceSegment,
)
from app.schemas.api import ColumnMapping


async def parse_csv(contents: bytes) -> tuple[list[str], list[dict], int]:
    """Parse CSV contents, return (headers, all_rows, total_count)."""
    text = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = list(reader.fieldnames or [])
    rows = [dict(row) for row in reader]
    return headers, rows, len(rows)


async def create_preview(
    db: AsyncSession,
    dataset_id: uuid.UUID,
    contents: bytes,
) -> tuple[ImportBatch, list[str], list[dict], int]:
    """Upload CSV and create preview batch."""
    file_hash = hashlib.sha256(contents).hexdigest()
    headers, all_rows, total = await parse_csv(contents)

    batch = ImportBatch(
        dataset_id=dataset_id,
        file_hash=file_hash,
        total_rows=total,
        validation_status="preview",
    )
    db.add(batch)
    await db.flush()

    # Store all rows for later processing
    for i, row in enumerate(all_rows):
        import_row = ImportRow(
            batch_id=batch.id,
            row_number=i + 1,
            raw_fields=row,
            row_status="pending",
        )
        db.add(import_row)

    await db.commit()
    await db.refresh(batch)

    sample = all_rows[:10]
    return batch, headers, sample, total


async def validate_mapping(
    db: AsyncSession,
    batch_id: uuid.UUID,
    mapping: ColumnMapping,
) -> tuple[int, int, int, list[dict]]:
    """Validate each row against the column mapping.

    Returns (valid, invalid, duplicate, errors).
    """
    result = await db.execute(select(ImportBatch).where(ImportBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise ValueError("Batch not found")

    batch.column_mapping = mapping.model_dump()

    # Fetch all rows
    rows_result = await db.execute(
        select(ImportRow)
        .where(ImportRow.batch_id == batch_id)
        .order_by(ImportRow.row_number)
    )
    rows = list(rows_result.scalars().all())

    valid = 0
    invalid = 0
    duplicate = 0
    errors: list[dict] = []
    seen_hashes: set[str] = set()

    for row in rows:
        fields = row.raw_fields or {}
        row_errors: list[str] = []

        # Check required narrative field
        narrative_col = mapping.narrative
        narrative = fields.get(narrative_col, "").strip()
        if not narrative:
            row_errors.append(f"missing_narrative: column '{narrative_col}' is empty")
        elif len(narrative) > 20000:
            row_errors.append("narrative_too_long: exceeds 20000 chars")

        # Check for duplicates within batch
        if narrative:
            h = hashlib.sha256(narrative.encode()).hexdigest()
            if h in seen_hashes:
                row.row_status = "duplicate"
                duplicate += 1
                continue
            seen_hashes.add(h)

        if row_errors:
            row.row_status = "rejected"
            row.error_codes = row_errors
            invalid += 1
            errors.append({
                "row_number": row.row_number,
                "errors": row_errors,
            })
        else:
            row.row_status = "accepted"
            valid += 1

    batch.accepted_rows = valid
    batch.rejected_rows = invalid
    batch.duplicate_rows = duplicate
    batch.validation_status = "validated"

    await db.commit()
    return valid, invalid, duplicate, errors


async def commit_import(
    db: AsyncSession,
    batch_id: uuid.UUID,
) -> tuple[int, int, int, int]:
    """Commit validated batch: create reports and enqueue analysis jobs.

    Returns (accepted, rejected, duplicate, jobs_created).
    """
    result = await db.execute(select(ImportBatch).where(ImportBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise ValueError("Batch not found")

    if batch.validation_status != "validated":
        raise ValueError("Batch not yet validated")

    mapping = ColumnMapping(**batch.column_mapping)

    # Get accepted rows
    rows_result = await db.execute(
        select(ImportRow)
        .where(ImportRow.batch_id == batch_id, ImportRow.row_status == "accepted")
        .order_by(ImportRow.row_number)
    )
    rows = list(rows_result.scalars().all())

    jobs_created = 0

    for row in rows:
        fields = row.raw_fields or {}
        narrative = fields.get(mapping.narrative, "").strip()
        if not narrative:
            continue

        source_report_id = fields.get(mapping.source_report_id) if mapping.source_report_id else None
        site = fields.get(mapping.site) if mapping.site else None
        report_type = fields.get(mapping.report_type) if mapping.report_type else None
        occurred_at = None
        if mapping.occurred_at and fields.get(mapping.occurred_at):
            try:
                occurred_at = datetime.fromisoformat(fields[mapping.occurred_at])
            except (ValueError, TypeError):
                pass

        # Check for cross-batch duplicates
        text_hash = hashlib.sha256(narrative.encode()).hexdigest()

        # Create report
        report = Report(
            dataset_id=batch.dataset_id,
            source_report_id=source_report_id,
            supplied_site=site,
            report_type=report_type,
            occurred_at=occurred_at,
        )
        db.add(report)
        await db.flush()

        # Create revision
        revision = ReportRevision(
            report_id=report.id,
            revision_number=1,
            original_text=narrative,
            source_kind="original",
            text_hash=text_hash,
        )
        db.add(revision)
        await db.flush()

        # Source segment
        segment = SourceSegment(
            report_revision_id=revision.id,
            kind="original",
            text=narrative,
        )
        db.add(segment)

        report.current_revision_id = revision.id

        # Link import row to report
        row.report_id = report.id

        # Enqueue analysis
        job = Job(
            kind="analyze_report",
            payload={
                "report_id": str(report.id),
                "revision_id": str(revision.id),
                "text_hash": text_hash,
            },
            idempotency_key=f"analyze:{report.id}:rev:{revision.id}",
            status="pending",
        )
        db.add(job)
        jobs_created += 1

    batch.validation_status = "committed"
    await db.commit()

    return batch.accepted_rows, batch.rejected_rows, batch.duplicate_rows, jobs_created
