"""
CSV upload route: POST /upload-csv
- Validates MIME type and size
- Infers column types via pandas
- Creates table in 'uploads' schema
- Stores metadata in UploadedDataset model
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.upload import UploadResponse
from app.services.csv_processor import csv_processor

log = structlog.get_logger(__name__)
router = APIRouter()

MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME = {"text/csv", "text/plain", "application/csv", "application/vnd.ms-excel"}


@router.post("/upload-csv", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    session_id: str = Form(default="anonymous"),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME and not (
        file.filename and file.filename.lower().endswith(".csv")
    ):
        raise HTTPException(
            status_code=415,
            detail="Only CSV files are supported. Detected MIME: " + str(file.content_type),
        )

    content = await file.read()

    # Validate size
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit")

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    log.info("CSV upload received", filename=file.filename, size=len(content), session=session_id)

    try:
        result = await csv_processor.process(
            content=content,
            filename=file.filename or "upload.csv",
            session_id=session_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        log.error("CSV processing failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to process CSV file")

    return result
