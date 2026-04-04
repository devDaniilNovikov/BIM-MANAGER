"""Upload IFC model endpoint and file download."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.project import Element, Issue, Project
from app.schemas.project import ProjectOut
from app.services.project_service import create_project

router = APIRouter()


@router.post("/upload", response_model=ProjectOut)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=400, detail="Only .ifc files are allowed")

    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit")

    project = await create_project(
        db=db,
        name=name,
        description=description,
        file_name=file.filename,
        file_content=content,
    )

    el_count = await db.scalar(select(func.count()).where(Element.project_id == project.id))
    iss_count = await db.scalar(select(func.count()).where(Issue.project_id == project.id))

    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        file_name=project.file_name,
        file_size=project.file_size,
        ifc_schema=project.ifc_schema,
        created_at=project.created_at,
        element_count=el_count or 0,
        issue_count=iss_count or 0,
    )

@router.get("/{project_id}/file")
async def download_file(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Download the original IFC file."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    file_path = Path(project.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=project.file_name,
        media_type="application/octet-stream",
    )

