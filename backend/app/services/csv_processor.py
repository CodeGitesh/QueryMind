"""
CSV processing service.
- Parses CSV with pandas
- Infers column types and maps to PostgreSQL types
- Sanitizes column names
- Creates table dynamically in uploads schema
- Stores metadata in UploadedDataset model
"""
from __future__ import annotations

import io
import json
import re
import time
from typing import Any

import pandas as pd
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UploadedDataset
from app.schemas.upload import ColumnInfo, UploadResponse
from app.utils.sanitizer import sanitize_column_name, validate_csv_cell

log = structlog.get_logger(__name__)

# pandas dtype → PostgreSQL type mapping
_DTYPE_MAP: dict[str, str] = {
    "int64": "INTEGER",
    "int32": "INTEGER",
    "int16": "INTEGER",
    "int8": "INTEGER",
    "float64": "NUMERIC",
    "float32": "NUMERIC",
    "bool": "BOOLEAN",
    "datetime64[ns]": "TIMESTAMP",
    "datetime64[ns, UTC]": "TIMESTAMPTZ",
    "object": "TEXT",
    "string": "TEXT",
    "category": "TEXT",
}


class CSVProcessor:

    async def process(
        self,
        content: bytes,
        filename: str,
        session_id: str,
        db: AsyncSession,
    ) -> UploadResponse:
        # Parse CSV
        try:
            df = pd.read_csv(io.BytesIO(content), parse_dates=True, infer_datetime_format=True)
        except Exception as exc:
            raise ValueError(f"Could not parse CSV: {exc}") from exc

        if df.empty or len(df.columns) == 0:
            raise ValueError("CSV must have at least 1 row and 1 column")

        # Sanitize column names (handle duplicates)
        seen: dict[str, int] = {}
        column_infos: list[ColumnInfo] = []
        col_rename_map: dict[str, str] = {}

        for orig_col in df.columns:
            clean = sanitize_column_name(str(orig_col))
            if clean in seen:
                seen[clean] += 1
                clean = f"{clean}_{seen[clean]}"
            else:
                seen[clean] = 0
            col_rename_map[str(orig_col)] = clean

            dtype_str = str(df[orig_col].dtype)
            sql_type = _DTYPE_MAP.get(dtype_str, "TEXT")

            column_infos.append(
                ColumnInfo(
                    name=clean,
                    original_name=str(orig_col),
                    dtype=dtype_str,
                    sql_type=sql_type,
                    nullable=True,
                )
            )

        df = df.rename(columns=col_rename_map)

        # CSV injection protection
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].apply(lambda v: validate_csv_cell(str(v)) if pd.notna(v) else v)

        # Generate table name from filename (timestamp + sanitized name)
        base_name = re.sub(r"[^a-z0-9]", "_", filename.lower().replace(".csv", ""))[:40]
        table_name = f"upload_{int(time.time())}_{base_name}"
        schema = "uploads"

        # Create table and insert data
        await self._create_table_and_insert(df, table_name, schema, column_infos, db)

        # Persist metadata
        dataset = UploadedDataset(
            original_filename=filename,
            table_name=table_name,
            schema_name=schema,
            row_count=len(df),
            column_count=len(df.columns),
            columns_json=json.dumps([c.model_dump() for c in column_infos]),
            session_id=session_id,
        )
        db.add(dataset)
        await db.commit()

        log.info(
            "CSV processed",
            table=f"{schema}.{table_name}",
            rows=len(df),
            cols=len(df.columns),
        )

        return UploadResponse(
            success=True,
            schema_name=f"{schema}.{table_name}",
            table_name=table_name,
            original_filename=filename,
            row_count=len(df),
            column_count=len(df.columns),
            columns=column_infos,
            message=f"Table '{table_name}' created with {len(df)} rows.",
        )

    async def _create_table_and_insert(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: str,
        column_infos: list[ColumnInfo],
        db: AsyncSession,
    ) -> None:
        async with db.begin():
            # Ensure schema exists
            await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

            # Build CREATE TABLE
            col_defs = ", ".join(
                f'"{ci.name}" {ci.sql_type}' for ci in column_infos
            )
            create_sql = (
                f'CREATE TABLE IF NOT EXISTS {schema}."{table_name}" '
                f"(id SERIAL PRIMARY KEY, {col_defs}, "
                f"created_at TIMESTAMPTZ DEFAULT NOW())"
            )
            await db.execute(text(create_sql))

            # Bulk insert using executemany
            col_names = ", ".join(f'"{ci.name}"' for ci in column_infos)
            placeholders = ", ".join(f":{ci.name}" for ci in column_infos)
            insert_sql = (
                f'INSERT INTO {schema}."{table_name}" ({col_names}) VALUES ({placeholders})'
            )

            records = df.where(pd.notna(df), None).to_dict(orient="records")
            for batch_start in range(0, len(records), 500):
                batch = records[batch_start : batch_start + 500]
                await db.execute(text(insert_sql), batch)


csv_processor = CSVProcessor()
