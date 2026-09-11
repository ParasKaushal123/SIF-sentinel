"""Dataset endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dataset
from app.db.session import get_db
from app.schemas.api import DatasetResponse

router = APIRouter()


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).order_by(Dataset.created_at))
    datasets = result.scalars().all()
    return [
        DatasetResponse(
            id=d.id,
            name=d.name,
            provenance=d.provenance,
            is_demo=d.is_demo,
            created_at=d.created_at,
        )
        for d in datasets
    ]
