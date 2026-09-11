"""Worker main loop — polls the jobs table and processes analysis jobs.

Uses PostgreSQL row-level locking (SELECT ... FOR UPDATE SKIP LOCKED) to
lease jobs safely across multiple worker processes. No Redis/Celery — the
jobs table IS the queue.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import socket
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Job
from app.worker.processor import process_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
)
logger = logging.getLogger("worker")

WORKER_ID = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
LEASE_DURATION = timedelta(minutes=5)

_shutdown = asyncio.Event()


async def claim_job(session: AsyncSession) -> Job | None:
    """Atomically claim the next available pending job.

    Uses FOR UPDATE SKIP LOCKED so concurrent workers never grab the same job.
    """
    now = datetime.now(timezone.utc)

    result = await session.execute(
        select(Job)
        .where(
            Job.status == "pending",
            Job.available_at <= now,
            Job.attempts < Job.max_attempts,
        )
        .order_by(Job.available_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = result.scalar_one_or_none()
    if not job:
        return None

    # Lease it
    job.status = "claimed"
    job.lease_owner = WORKER_ID
    job.lease_until = now + LEASE_DURATION
    job.attempts += 1
    await session.commit()
    await session.refresh(job)
    return job


async def complete_job(session: AsyncSession, job: Job) -> None:
    job.status = "succeeded"
    job.completed_at = datetime.now(timezone.utc)
    job.lease_owner = None
    job.lease_until = None
    await session.commit()


async def fail_job(session: AsyncSession, job: Job, error: str) -> None:
    job.last_error_code = error[:255]
    if job.attempts >= job.max_attempts:
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        logger.error("Job %s permanently failed after %d attempts: %s", job.id, job.attempts, error)
    else:
        # Retry with backoff
        job.status = "pending"
        backoff = timedelta(seconds=2 ** job.attempts)
        job.available_at = datetime.now(timezone.utc) + backoff
        logger.warning("Job %s failed (attempt %d), retrying in %ds: %s", job.id, job.attempts, 2 ** job.attempts, error)
    job.lease_owner = None
    job.lease_until = None
    await session.commit()


async def worker_loop(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Single worker coroutine — polls and processes jobs until shutdown."""
    logger.info("Worker %s started (poll interval %ds)", WORKER_ID, settings.worker_poll_interval)

    while not _shutdown.is_set():
        try:
            async with session_factory() as session:
                job = await claim_job(session)

            if job is None:
                await asyncio.sleep(settings.worker_poll_interval)
                continue

            logger.info("Processing job %s (kind=%s, attempt=%d)", job.id, job.kind, job.attempts)

            try:
                async with session_factory() as session:
                    # Re-fetch job in this session
                    result = await session.execute(select(Job).where(Job.id == job.id))
                    fresh_job = result.scalar_one()
                    await process_job(session, fresh_job)

                async with session_factory() as session:
                    result = await session.execute(select(Job).where(Job.id == job.id))
                    fresh_job = result.scalar_one()
                    await complete_job(session, fresh_job)

                logger.info("Job %s succeeded", job.id)
            except Exception as e:  # noqa: BLE001
                logger.exception("Job %s processing error", job.id)
                async with session_factory() as session:
                    result = await session.execute(select(Job).where(Job.id == job.id))
                    fresh_job = result.scalar_one()
                    await fail_job(session, fresh_job, str(e))

        except Exception as e:  # noqa: BLE001
            # Keep this calm — a transient DB hiccup shouldn't dump a stack trace
            # every poll. The readiness gate in main() already waits for the schema.
            logger.warning("Worker loop error (will retry): %s", str(e).splitlines()[0])
            await asyncio.sleep(settings.worker_poll_interval)


async def wait_for_schema(
    session_factory: async_sessionmaker[AsyncSession], timeout: int = 120
) -> bool:
    """Block until the `jobs` table exists (the API container runs migrations).

    Returns True once ready, False if the timeout elapses. Logs one line per
    wait, not a stack trace, so startup stays readable.
    """
    waited = 0
    interval = 2
    while not _shutdown.is_set() and waited < timeout:
        try:
            async with session_factory() as session:
                await session.execute(text("SELECT 1 FROM jobs LIMIT 1"))
            logger.info("Database schema is ready — starting workers.")
            return True
        except Exception:  # noqa: BLE001
            logger.info("Waiting for database schema (migrations)… %ds", waited)
            await asyncio.sleep(interval)
            waited += interval
    return False


async def reclaim_expired_leases(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Background task: reset jobs whose lease expired (crashed worker)."""
    while not _shutdown.is_set():
        try:
            async with session_factory() as session:
                now = datetime.now(timezone.utc)
                await session.execute(
                    update(Job)
                    .where(
                        Job.status == "claimed",
                        Job.lease_until < now,
                    )
                    .values(status="pending", lease_owner=None, lease_until=None)
                )
                await session.commit()
        except Exception:  # noqa: BLE001
            logger.exception("Lease reclaim error")
        await asyncio.sleep(30)


def _handle_signal(*_args) -> None:
    logger.info("Shutdown signal received")
    _shutdown.set()


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False, pool_size=10)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    # Wait for the API container to create the schema before polling, so the
    # startup logs don't fill with "relation does not exist" errors.
    ready = await wait_for_schema(session_factory)
    if not ready:
        if _shutdown.is_set():
            await engine.dispose()
            return
        logger.warning("Schema not ready after timeout — starting anyway; loop will retry.")

    # Launch concurrent worker coroutines + lease reclaimer
    tasks = [
        asyncio.create_task(worker_loop(session_factory))
        for _ in range(settings.worker_concurrency)
    ]
    tasks.append(asyncio.create_task(reclaim_expired_leases(session_factory)))

    await _shutdown.wait()
    logger.info("Draining workers…")
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await engine.dispose()
    logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
