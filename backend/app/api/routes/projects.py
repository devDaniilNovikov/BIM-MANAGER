"""Projects CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.project import ProjectDetail, ProjectOut
from app.services.project_service import delete_project, get_project, get_projects

router = APIRouter()


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    rows = await get_projects(db)
    return [
        ProjectOut(
            id=r["project"].id,
            name=r["project"].name,
            description=r["project"].description,
            file_name=r["project"].file_name,
            file_size=r["project"].file_size,
            ifc_schema=r["project"].ifc_schema,
            created_at=r["project"].created_at,
            element_count=r["element_count"],
            issue_count=r["issue_count"],
        )
        for r in rows
    ]


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project_detail(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def remove_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ok = await delete_project(db, project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}
