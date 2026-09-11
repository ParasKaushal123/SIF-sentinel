"""API v1 router — mounts all endpoint modules."""

from fastapi import APIRouter

from app.api.v1 import health, reports, imports, insights, lab, datasets

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(lab.router, prefix="/lab", tags=["lab"])
