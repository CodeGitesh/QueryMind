"""
Health check routes.
GET /health   — liveness probe
GET /ready    — readiness probe (checks DB + Redis)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.cache import cache_service

router = APIRouter()


@router.get("/health")
async def liveness() -> ORJSONResponse:
    return ORJSONResponse({"status": "ok"})


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> ORJSONResponse:
    checks: dict = {}

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Redis check
    try:
        await cache_service.redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    return ORJSONResponse(
        {"status": "ready" if all_ok else "degraded", "checks": checks},
        status_code=status_code,
    )
