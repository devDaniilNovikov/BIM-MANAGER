"""Export endpoints — Excel / CSV / PDF."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.export_service import export_report

router = APIRouter()

VALID_REPORTS = {"spaces", "doors-windows", "walls", "slabs", "quantities", "summary", "issues"}
VALID_FORMATS = {"xlsx", "csv", "pdf"}


@router.get("/{project_id}/export/{report_type}")
async def export_data(
    project_id: uuid.UUID,
    report_type: str,
    format: str = Query("xlsx"),
    db: AsyncSession = Depends(get_db),
):
    if report_type not in VALID_REPORTS:
        raise HTTPException(status_code=400, detail=f"Invalid report type. Valid: {', '.join(VALID_REPORTS)}")
    if format not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"Invalid format. Valid: {', '.join(VALID_FORMATS)}")

    result = await export_report(db, project_id, report_type, format)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found or no data")

    content_types = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv; charset=utf-8",
        "pdf": "application/pdf",
    }
    filename = f"{report_type}.{format}"

    return StreamingResponse(
        result,
        media_type=content_types[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
