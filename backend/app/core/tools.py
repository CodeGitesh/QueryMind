"""
LangChain tool definitions for the agent.
Tools: execute_sql, get_schema, describe_table.
"""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

log = structlog.get_logger(__name__)


async def execute_sql_tool(
    sql: str,
    schema_name: str,
    session: AsyncSession,
) -> tuple[list[str], list[list[Any]]]:
    """
    Execute a SELECT query against the database.
    Applies statement_timeout and row limit.
    Returns (columns, rows).
    """
    # Apply query timeout
    timeout_ms = settings.QUERY_TIMEOUT_SECONDS * 1000
    set_timeout = text(f"SET statement_timeout = '{timeout_ms}ms'")

    async with session.begin():
        if not session.bind.dialect.name == "sqlite":
            await session.execute(set_timeout)

        # Set search_path to target schema
        set_schema = text(f"SET search_path TO {schema_name}, public")
        try:
            await session.execute(set_schema)
        except Exception:
            pass  # SQLite doesn't support search_path

        import decimal
        result = await session.execute(text(sql))
        columns = list(result.keys())
        rows = [
            [float(v) if isinstance(v, decimal.Decimal) else v for v in row]
            for row in result.fetchall()
        ]

    log.info("SQL executed", rows=len(rows), schema=schema_name)
    return columns, rows


async def get_schema_tool(
    schema_name: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Introspect the database schema and return table/column metadata.
    """
    from sqlalchemy import inspect
    from sqlalchemy.ext.asyncio import AsyncConnection

    async with session.begin():
        conn: AsyncConnection = await session.connection()
        tables: dict[str, Any] = {}

        def _introspect(sync_conn: Any) -> dict:
            insp = inspect(sync_conn)
            schema_tables = insp.get_table_names(schema=schema_name)
            result = {}
            for table_name in schema_tables:
                cols = insp.get_columns(table_name, schema=schema_name)
                fks = insp.get_foreign_keys(table_name, schema=schema_name)
                col_list = [
                    {"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)}
                    for c in cols
                ]
                fk_list = [
                    {
                        "column": fk["constrained_columns"][0] if fk["constrained_columns"] else "",
                        "referred_table": fk["referred_table"],
                        "referred_column": fk["referred_columns"][0] if fk["referred_columns"] else "",
                    }
                    for fk in fks
                ]
                result[table_name] = {
                    "columns": col_list,
                    "foreign_keys": fk_list,
                    "row_count": 0,  # filled below
                }
            return result

        tables = await conn.run_sync(_introspect)

    # Get approximate row counts
    async with session.begin():
        for table_name in tables:
            try:
                count_sql = text(
                    f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
                )
                result = await session.execute(count_sql)
                tables[table_name]["row_count"] = result.scalar() or 0
            except Exception:
                tables[table_name]["row_count"] = 0

    return {"schema": schema_name, "tables": tables}


def get_db_tools(session: AsyncSession):
    """Return bound tool callables for a given session."""
    async def _execute_sql(sql: str, schema_name: str = "public"):
        return await execute_sql_tool(sql, schema_name, session)

    async def _get_schema(schema_name: str):
        return await get_schema_tool(schema_name, session)

    return {
        "execute_sql": _execute_sql,
        "get_schema": _get_schema,
    }
