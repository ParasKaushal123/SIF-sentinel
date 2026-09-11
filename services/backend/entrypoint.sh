#!/usr/bin/env bash
# API container entrypoint: wait for DB, run migrations, seed demo data once,
# then start the API server. Safe to re-run — seeding is skipped if data exists.
set -e

# Ensure the app package is importable. The image installs the package, but the
# compose bind-mount of the host folder over /app shadows that metadata, so we add
# /app to PYTHONPATH explicitly.
export PYTHONPATH="/app:${PYTHONPATH}"

# Only the API container runs migrations + seed (RUN_MIGRATIONS=true), so the API
# and worker don't race to create the schema. The worker's poll loop tolerates the
# brief window before tables exist.
if [ "${RUN_MIGRATIONS}" = "true" ]; then
  echo "[entrypoint] Running database migrations…"
  alembic upgrade head

  if [ "${DEMO_MODE}" = "true" ] || [ "${DEMO_MODE}" = "1" ]; then
    echo "[entrypoint] DEMO_MODE on — seeding demo data if empty…"
    python -m app.cli.seed_if_empty || echo "[entrypoint] seed skipped"
  fi
fi

echo "[entrypoint] Starting API…"
exec "$@"
