"""
FastAPI application entry-point.
- Lifespan context manager (startup/shutdown)
- CORS middleware (strict origin whitelist)
- Structured JSON logging
- Rate-limiting via slowapi
- Router registration
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.routes import health, history, query, schema, upload
from app.config import settings
from app.db.session import create_db_and_tables, engine
from app.services.cache import cache_service
from app.core.schema_selector import schema_selector
from app.utils.logger import configure_logging

log = structlog.get_logger(__name__)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup / shutdown logic."""
    configure_logging()
    log.info("QueryMind starting up", environment=settings.ENVIRONMENT)

    # 1. Database tables + migrations
    await create_db_and_tables()
    log.info("Database initialised")

    # 2. Redis connection
    await cache_service.connect()
    log.info("Redis connected", url=settings.REDIS_URL)

    # 3. Pre-compute schema embeddings (sentence-transformers)
    await schema_selector.initialise()
    log.info("Schema embeddings ready")

    yield  # ← app is live

    # Graceful shutdown
    await cache_service.disconnect()
    await engine.dispose()
    log.info("QueryMind shut down cleanly")


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Natural Language to SQL AI Agent with self-healing capabilities",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Session-ID"],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next) -> Response:  # type: ignore[type-arg]
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response

    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = settings.API_PREFIX
    app.include_router(health.router, prefix=prefix, tags=["health"])
    app.include_router(query.router, prefix=prefix, tags=["query"])
    app.include_router(schema.router, prefix=prefix, tags=["schema"])
    app.include_router(history.router, prefix=prefix, tags=["history"])
    app.include_router(upload.router, prefix=prefix, tags=["upload"])

    return app


app = create_app()
