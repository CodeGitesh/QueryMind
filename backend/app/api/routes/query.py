"""
Query routes — POST /query and WebSocket /ws/query.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent import agent
from app.core.tools import execute_sql_tool, get_schema_tool
from app.db.models import QueryHistory
from app.db.session import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.cache import cache_service

log = structlog.get_logger(__name__)

router = APIRouter()


async def _run_query(
    request_data: QueryRequest,
    db: AsyncSession,
    client_ip: str = "unknown",
    stream_callback: Any = None,
) -> dict:
    query_id = str(uuid.uuid4())

    # Check cache
    cached = await cache_service.get_query_result(request_data.query, request_data.schema_name)
    if cached:
        cached["cached"] = True
        cached["query_id"] = query_id
        return cached

    # Get schema info
    schema_info = await cache_service.get_schema(request_data.schema_name)
    if not schema_info:
        schema_info = await get_schema_tool(request_data.schema_name, db)
        await cache_service.set_schema(request_data.schema_name, schema_info)

    # Define SQL executor bound to this session
    async def db_execute(sql: str, schema_name: str):
        return await execute_sql_tool(sql, schema_name, db)

    # Run agent
    result = await agent.run(
        query=request_data.query,
        schema_name=request_data.schema_name,
        db_execute=db_execute,
        schema_info=schema_info,
        stream_callback=stream_callback,
    )

    result["query_id"] = query_id
    result["cached"] = False

    # Persist to history
    history_entry = QueryHistory(
        id=query_id,
        natural_language=request_data.query,
        generated_sql=result.get("generated_sql"),
        success=result.get("success", False),
        attempt_count=result.get("attempt_count", 1),
        error_message=result.get("error") if not result.get("success") else None,
        execution_time_ms=result.get("execution_time_ms"),
        result_row_count=result.get("result", {}).get("row_count") if result.get("result") else None,
        schema_used=request_data.schema_name,
        session_id=request_data.session_id,
    )
    db.add(history_entry)
    await db.commit()

    # Cache successful results
    if result.get("success"):
        await cache_service.set_query_result(request_data.query, request_data.schema_name, result)

    return result


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    body: QueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ORJSONResponse:
    client_ip = request.client.host if request.client else "unknown"
    log.info("Query received", query=body.query[:100], schema=body.schema_name, ip=client_ip)

    result = await _run_query(body, db, client_ip)
    return ORJSONResponse(result)


@router.websocket("/ws/query")
async def ws_query(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """WebSocket endpoint that streams agent thinking steps in real time."""
    await websocket.accept()

    try:
        raw = await websocket.receive_text()
        data = json.loads(raw)
        request_data = QueryRequest(**data)

        steps: list[str] = []

        async def stream_step(step: str) -> None:
            steps.append(step)
            await websocket.send_json({"type": "step", "step": step, "steps": steps})

        result = await _run_query(request_data, db, stream_callback=stream_step)
        await websocket.send_json({"type": "result", "data": result})

    except WebSocketDisconnect:
        log.info("WebSocket disconnected")
    except Exception as exc:
        log.error("WebSocket error", error=str(exc))
        try:
            await websocket.send_json({"type": "error", "error": "Internal server error"})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
