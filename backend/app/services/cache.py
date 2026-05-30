"""
Redis caching service.
- Query result caching (TTL 300s)
- Schema metadata caching (TTL 600s)
- Cache-hit/miss ratio logging
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

import structlog
from redis.asyncio import Redis, from_url

from app.config import settings

log = structlog.get_logger(__name__)

# Time-sensitive keywords — skip cache for these
_TIME_SENSITIVE = frozenset(
    ["latest", "today", "current", "now", "yesterday", "this week", "this month", "this year", "recent"]
)


class CacheService:
    def __init__(self) -> None:
        self._redis: Optional[Redis] = None
        self._hits = 0
        self._misses = 0

    async def connect(self) -> None:
        self._redis = from_url(settings.REDIS_URL, decode_responses=True)
        await self._redis.ping()

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.aclose()

    @property
    def redis(self) -> Redis:
        if self._redis is None:
            raise RuntimeError("Redis not connected — call connect() first")
        return self._redis

    # ── Query cache ───────────────────────────────────────────────────────────

    def _is_time_sensitive(self, query: str) -> bool:
        lower = query.lower()
        return any(kw in lower for kw in _TIME_SENSITIVE)

    def _make_query_key(self, query: str, schema_name: str) -> str:
        normalized = " ".join(query.lower().split())
        raw = f"{schema_name}::{normalized}"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"qm:query:{digest}"

    async def get_query_result(self, query: str, schema_name: str) -> Optional[dict[str, Any]]:
        if self._is_time_sensitive(query):
            log.debug("Skipping cache — time-sensitive query")
            return None
        key = self._make_query_key(query, schema_name)
        try:
            value = await self.redis.get(key)
            if value:
                self._hits += 1
                log.info("Cache HIT", key=key, hit_ratio=self._hit_ratio)
                return json.loads(value)
            self._misses += 1
            log.debug("Cache MISS", key=key)
            return None
        except Exception as exc:
            log.warning("Cache get failed", error=str(exc))
            return None

    async def set_query_result(self, query: str, schema_name: str, result: dict[str, Any]) -> None:
        if self._is_time_sensitive(query):
            return
        key = self._make_query_key(query, schema_name)
        try:
            await self.redis.setex(key, settings.CACHE_TTL_SECONDS, json.dumps(result))
        except Exception as exc:
            log.warning("Cache set failed", error=str(exc))

    # ── Schema cache ──────────────────────────────────────────────────────────

    def _make_schema_key(self, schema_name: str) -> str:
        return f"qm:schema:{schema_name}"

    async def get_schema(self, schema_name: str) -> Optional[dict[str, Any]]:
        key = self._make_schema_key(schema_name)
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as exc:
            log.warning("Schema cache get failed", error=str(exc))
            return None

    async def set_schema(self, schema_name: str, schema_data: dict[str, Any]) -> None:
        key = self._make_schema_key(schema_name)
        try:
            await self.redis.setex(key, settings.SCHEMA_CACHE_TTL_SECONDS, json.dumps(schema_data))
        except Exception as exc:
            log.warning("Schema cache set failed", error=str(exc))

    async def invalidate_schema(self, schema_name: str) -> None:
        key = self._make_schema_key(schema_name)
        await self.redis.delete(key)

    @property
    def _hit_ratio(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / total, 3) if total else 0.0


cache_service = CacheService()
