"""
ORM models: QueryHistory, UploadedDataset.
All models use SQLAlchemy 2.0 mapped columns.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class QueryHistory(Base):
    __tablename__ = "query_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid, index=True
    )
    natural_language: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    schema_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UploadedDataset(Base):
    __tablename__ = "uploaded_datasets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_name: Mapped[str] = mapped_column(String(100), nullable=False, default="uploads")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)
    columns_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
