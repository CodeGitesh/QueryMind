"""
Pydantic v2 models for query history endpoint.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HistoryItem(BaseModel):
    id: str
    natural_language: str
    generated_sql: Optional[str] = None
    success: bool
    attempt_count: int
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    result_row_count: Optional[int] = None
    schema_used: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int
    has_next: bool
