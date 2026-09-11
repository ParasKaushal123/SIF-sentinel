"""Seed demo data only if the database has no demo dataset yet.

Idempotent wrapper around `seed.seed_demo_data` so the container can seed on
every startup without creating duplicates.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.models import Dataset
from app.cli.seed import seed_demo_data


async def _already_seeded() -> bool:
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(Dataset).where(Dataset.is_demo == True))  # noqa: E712
        existing = result.scalars().first()
    await engine.dispose()
    return existing is not None


def main():
    if asyncio.run(_already_seeded()):
        print("Demo data already present — skipping seed.")
        return
    asyncio.run(seed_demo_data())


if __name__ == "__main__":
    main()
