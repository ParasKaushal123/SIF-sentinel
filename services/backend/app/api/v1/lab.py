"""Lab endpoints — side-by-side narrative comparison (Luck Lab).

The Lab runs two narratives through the analysis pipeline and diffs the
results. This is the demonstration surface for the Luck Test: paste a
near-miss and its would-be-injury twin and watch the classification stay
the same (outcome resistance); add a control and watch it flip (control
sensitivity).

With the fixture adapter the pipeline is fast and deterministic, so the
Lab runs both analyses inline and returns results immediately.
"""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.pipeline import run_analysis
from app.config import settings
from app.db.models import LabRun
from app.db.session import get_db
from app.schemas.api import LabComparisonRequest, LabComparisonResponse

router = APIRouter()


def _diff_analyses(left: dict, right: dict) -> list[dict]:
    """Compute the differences between two analysis results."""
    changes: list[dict] = []

    if left.get("candidate_label") != right.get("candidate_label"):
        changes.append({
            "field": "candidate_label",
            "left": left.get("candidate_label"),
            "right": right.get("candidate_label"),
            "significance": "high",
        })

    if left.get("interpretation") != right.get("interpretation"):
        changes.append({
            "field": "interpretation",
            "left": left.get("interpretation"),
            "right": right.get("interpretation"),
            "significance": "medium",
        })

    # Compare hazard kinds
    left_hazards = {f["hazard_kind"] for f in left.get("facts", [])}
    right_hazards = {f["hazard_kind"] for f in right.get("facts", [])}
    if left_hazards != right_hazards:
        changes.append({
            "field": "hazards",
            "left": sorted(left_hazards),
            "right": sorted(right_hazards),
            "significance": "medium",
        })

    # Compare LSRs
    left_rules = {r["rule_id"] for r in left.get("lsr_findings", [])}
    right_rules = {r["rule_id"] for r in right.get("lsr_findings", [])}
    if left_rules != right_rules:
        changes.append({
            "field": "life_saving_rules",
            "left": sorted(left_rules),
            "right": sorted(right_rules),
            "significance": "low",
        })

    return changes


@router.post("/compare", response_model=LabComparisonResponse, status_code=201)
async def submit_comparison(
    body: LabComparisonRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze two narratives and return both results plus a diff."""
    lab_run = LabRun(
        left_text=body.left_text,
        right_text=body.right_text,
        mode=body.mode,
    )
    db.add(lab_run)
    await db.flush()

    # Run both analyses inline
    left_result, _ = await run_analysis(
        body.left_text,
        analysis_id=str(uuid.uuid4()),
        report_revision_id=str(lab_run.id),
        provider=settings.model_provider,
        mode=body.mode,
    )
    right_result, _ = await run_analysis(
        body.right_text,
        analysis_id=str(uuid.uuid4()),
        report_revision_id=str(lab_run.id),
        provider=settings.model_provider,
        mode=body.mode,
    )

    changed_facts = _diff_analyses(
        left_result.model_dump(mode="json"),
        right_result.model_dump(mode="json"),
    )

    await db.commit()
    await db.refresh(lab_run)

    return LabComparisonResponse(
        comparison_id=lab_run.id,
        left_analysis=left_result,
        right_analysis=right_result,
        changed_facts=changed_facts,
        created_at=lab_run.created_at,
    )


@router.get("/{run_id}", response_model=LabComparisonResponse)
async def get_comparison(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Re-run and return a stored lab comparison by ID."""
    result = await db.execute(select(LabRun).where(LabRun.id == run_id))
    lab_run = result.scalar_one_or_none()
    if not lab_run:
        raise HTTPException(status_code=404, detail="Lab run not found")

    left_result, _ = await run_analysis(
        lab_run.left_text,
        analysis_id=str(uuid.uuid4()),
        report_revision_id=str(lab_run.id),
        provider=settings.model_provider,
        mode=lab_run.mode,
    )
    right_result, _ = await run_analysis(
        lab_run.right_text,
        analysis_id=str(uuid.uuid4()),
        report_revision_id=str(lab_run.id),
        provider=settings.model_provider,
        mode=lab_run.mode,
    )

    changed_facts = _diff_analyses(
        left_result.model_dump(mode="json"),
        right_result.model_dump(mode="json"),
    )

    return LabComparisonResponse(
        comparison_id=lab_run.id,
        left_analysis=left_result,
        right_analysis=right_result,
        changed_facts=changed_facts,
        created_at=lab_run.created_at,
    )
