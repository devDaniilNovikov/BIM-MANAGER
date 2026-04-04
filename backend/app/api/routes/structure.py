"""Structure / tree endpoints — buildings, storeys, spaces."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.project import Building, Project, Space, Storey
from app.schemas.project import BuildingOut, SpaceOut, StoreyOut

router = APIRouter()


@router.get("/{project_id}/tree")
async def get_tree(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.buildings)
            .selectinload(Building.storeys)
            .selectinload(Storey.spaces)
        )
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "buildings": [
            BuildingOut.model_validate(b).model_dump()
            for b in project.buildings
        ],
    }


@router.get("/{project_id}/buildings", response_model=list[BuildingOut])
async def list_buildings(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Building)
        .where(Building.project_id == project_id)
        .options(selectinload(Building.storeys).selectinload(Storey.spaces))
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{project_id}/storeys", response_model=list[StoreyOut])
async def list_storeys(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Storey)
        .join(Building)
        .where(Building.project_id == project_id)
        .options(selectinload(Storey.spaces))
        .order_by(Storey.elevation)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{project_id}/spaces", response_model=list[SpaceOut])
async def list_spaces(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Space)
        .join(Storey)
        .join(Building)
        .where(Building.project_id == project_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
