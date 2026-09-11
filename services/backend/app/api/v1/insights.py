"""Insights endpoints — aggregated analytics over reports and analyses."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.api import (
    InsightsOverviewResponse,
    InsightsPatternsResponse,
    PatternGroup,
    SpatialOverviewResponse,
)
from app.services import insights_service

router = APIRouter()


@router.get("/overview", response_model=InsightsOverviewResponse)
async def get_insights_overview(
    dataset_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate counts and distributions for the insights dashboard."""
    data = await insights_service.compute_overview(db, dataset_id=dataset_id)
    return InsightsOverviewResponse(**data)


@router.get("/patterns", response_model=InsightsPatternsResponse)
async def get_insights_patterns(
    dataset_id: UUID | None = None,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Return grouped hazard/control patterns, failure patterns first."""
    patterns = await insights_service.compute_patterns(
        db, dataset_id=dataset_id, limit=limit
    )
    return InsightsPatternsResponse(
        patterns=[PatternGroup(**p) for p in patterns]
    )

@router.get("/spatial", response_model=SpatialOverviewResponse)
async def get_spatial_overview(
    dataset_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Return per-site report counts and states for the map view."""
    data = await insights_service.compute_spatial(db, dataset_id=dataset_id)
    return SpatialOverviewResponse(**data)

@router.get("/patterns/{pattern_key}/reports")
async def get_pattern_reports(
    pattern_key: str,
    dataset_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Return member reports for a specific pattern."""
    reports = await insights_service.get_pattern_reports(db, pattern_key, dataset_id=dataset_id)
    return {"items": reports}
