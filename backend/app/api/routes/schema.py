"""
Schema introspection routes.
GET /schema          — list available schemas
GET /schema/{name}   — full schema with tables, columns, types, row counts
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.tools import get_schema_tool
from app.core.schema_selector import SCHEMA_DEFINITIONS
from app.services.cache import cache_service

router = APIRouter()

VALID_SCHEMAS = set(SCHEMA_DEFINITIONS.keys())


@router.get("/schema")
async def list_schemas():
    return {
        "schemas": [
            {"name": name, "table_count": len(tables)}
            for name, tables in SCHEMA_DEFINITIONS.items()
        ]
    }


@router.get("/schema/{schema_name}")
async def get_schema(
    schema_name: str,
    db: AsyncSession = Depends(get_db),
):
    if schema_name not in VALID_SCHEMAS and not schema_name.startswith("uploads"):
        raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found")

    # Check cache first
    cached = await cache_service.get_schema(schema_name)
    if cached:
        return cached

    schema_data = await get_schema_tool(schema_name, db)
    await cache_service.set_schema(schema_name, schema_data)
    return schema_data
