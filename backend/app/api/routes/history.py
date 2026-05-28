"""
Query history routes.
GET  /history          — paginated history list
DELETE /history/{id}   — soft delete
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QueryHistory
from app.db.session import get_db
from app.schemas.history import HistoryItem, HistoryListResponse

router = APIRouter()


@router.get("/history", response_model=HistoryListResponse)
async def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    schema_name: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> HistoryListResponse:
    offset = (page - 1) * page_size

    base_query = select(QueryHistory).where(QueryHistory.is_deleted.is_(False))
    count_query = select(func.count()).select_from(QueryHistory).where(QueryHistory.is_deleted.is_(False))

    if schema_name:
        base_query = base_query.where(QueryHistory.schema_used == schema_name)
        count_query = count_query.where(QueryHistory.schema_used == schema_name)

    if session_id:
        base_query = base_query.where(QueryHistory.session_id == session_id)
        count_query = count_query.where(QueryHistory.session_id == session_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    items_result = await db.execute(
        base_query.order_by(QueryHistory.created_at.desc()).offset(offset).limit(page_size)
    )
    items = items_result.scalars().all()

    return HistoryListResponse(
        items=[HistoryItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.delete("/history/{history_id}")
async def delete_history(
    history_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QueryHistory).where(
            QueryHistory.id == history_id,
            QueryHistory.is_deleted.is_(False),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="History record not found")

    record.is_deleted = True
    await db.commit()
    return {"success": True, "message": "Record deleted"}
