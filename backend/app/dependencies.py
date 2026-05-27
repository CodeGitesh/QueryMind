"""
FastAPI dependency injectors.
"""
from __future__ import annotations

from app.db.session import get_db  # noqa: F401 — re-exported for convenience

__all__ = ["get_db"]
