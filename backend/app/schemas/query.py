"""
Pydantic v2 request/response models for the query endpoint.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural language query")
    schema_name: str = Field(default="ecommerce", description="Target database schema")
    stream: bool = Field(default=False, description="Enable streaming response")
    session_id: Optional[str] = Field(default=None, max_length=100)

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()

    @field_validator("schema_name")
    @classmethod
    def validate_schema(cls, v: str) -> str:
        allowed = {"ecommerce", "hr", "finance"}
        if not v.startswith("uploads_") and v not in allowed:
            raise ValueError(f"Schema must be one of {allowed} or start with 'uploads_'")
        return v.lower().strip()


class ResultData(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int


class ChartConfig(BaseModel):
    type: str  # bar, line, pie, scalar, table
    x_key: Optional[str] = None
    y_key: Optional[str] = None
    y_keys: Optional[list[str]] = None
    title: Optional[str] = None
    layout: Optional[str] = None   # horizontal for list charts
    value: Optional[Any] = None    # for scalar type
    label: Optional[str] = None    # for scalar type


class AttemptRecord(BaseModel):
    attempt: int
    sql: str
    error: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    query_id: str
    generated_sql: Optional[str] = None
    explanation: Optional[str] = None
    result: Optional[ResultData] = None
    chart_config: Optional[ChartConfig] = None
    attempt_count: int = 1
    execution_time_ms: int = 0
    cached: bool = False
    error: Optional[str] = None
    attempts: Optional[list[AttemptRecord]] = None
