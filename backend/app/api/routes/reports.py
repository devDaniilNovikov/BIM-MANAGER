"""Reports endpoints — structured data for tables."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.report_builder import build_report

router = APIRouter()

VALID_REPORTS = {"spaces", "doors-windows", "walls", "slabs", "quantities", "summary"}


@router.get("/{project_id}/reports/{report_type}")
async def get_report(
    project_id: uuid.UUID,
    report_type: str,
    db: AsyncSession = Depends(get_db),
):
    if report_type not in VALID_REPORTS:
        raise HTTPException(status_code=400, detail=f"Invalid report type. Valid: {', '.join(VALID_REPORTS)}")

    data = await build_report(db, project_id, report_type)
    if data is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return data
