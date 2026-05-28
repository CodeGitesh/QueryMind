"""
Pydantic v2 models for CSV upload endpoint.
"""
from __future__ import annotations

from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    original_name: str
    dtype: str
    sql_type: str
    nullable: bool


class UploadResponse(BaseModel):
    success: bool
    schema_name: str
    table_name: str
    original_filename: str
    row_count: int
    column_count: int
    columns: list[ColumnInfo]
    message: str
