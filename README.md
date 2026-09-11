# SIF Sentinel (New UI Branch)

> **Note:** The frontend has been entirely replaced with a new vanilla HTML/JS implementation featuring a Spatial Command Centre and Pattern Observatory.
> The Next.js frontend has been removed. The new frontend is served directly by the FastAPI backend at http://localhost:8000/.

# SIF Sentinel

**Luck Test: outcome-resistant, control-sensitive SIF classification for Oil India Limited**
SIH 2026 · Challenge SIH26165 (Oil India SIF Precursor Engine)

SIF Sentinel triages safety reports by their *potential* for a Serious Injury or
Fatality — not by whether harm actually occurred. A near-miss where a worker was
6 m up without a harness is treated the same as if he had fallen, because the
outcome turned on luck, not on effective barriers. Add the harness back and the
same report flips to non-SIF. That is the **Luck Test**.

## What's built (v0.1)

- **Backend** (FastAPI + async SQLAlchemy + PostgreSQL): 14 endpoints, 14 tables,
  Alembic migration, a PostgreSQL-backed job queue, and a polling worker.
- **Analysis engine**: a replaceable model-adapter interface with a deterministic
  fixture adapter (7 hazard-energy classes, exposure + control-state detection,
  9 IOGP Life-Saving Rule mapping) and the **Luck Test policy engine**.
- **Frontend** (Next.js 14 + Tailwind + TanStack Query + Recharts): Review Inbox,
  Report Workbench, Insights, Import wizard, and the **Luck Lab** — a side-by-side
  comparison that demonstrates outcome resistance and control sensitivity live.

The fixture adapter means the whole system runs and demos with **zero API keys**.

## Quick start (Docker)

```bash
cd infra
cp .env.example .env
docker compose up --build
```

Then in another terminal, seed the demo data and start classifying:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.cli.seed
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Quick start (local, no Docker)

Backend:

```bash
cd services/backend
pip install -e ".[dev,ml]"
export DATABASE_URL="postgresql+asyncpg://sif_user:sif_pass@localhost:5432/sif_sentinel"
alembic upgrade head
python -m app.cli.seed
uvicorn app.main:app --reload          # terminal 1
WORKER_ENABLED=true python -m app.worker.main   # terminal 2
```

Frontend:

```bash
cd services/frontend
npm install
npm run dev
```

## Tests

```bash
cd services/backend
pytest                     # Luck Test property suite
```

The suite verifies the two defining properties: **outcome resistance**
(near-miss == injury for the same hazard/control scenario) and **control
sensitivity** (effective controls flip SIF → non-SIF).

## Architecture

Modular monolith. The PostgreSQL `jobs` table *is* the queue — no Redis/Celery.
The worker leases jobs with `FOR UPDATE SKIP LOCKED`, so multiple workers scale
horizontally without collisions. The model adapter is swappable at runtime via
`MODEL_PROVIDER` (`fixture` | `openai` | `anthropic`).

See `../SIF_Sentinel_Project_Guide.md` for the full architecture and build plan,
and the project's `BUILD_STATUS.md` for current progress.
