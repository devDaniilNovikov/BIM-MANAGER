"""Elements endpoints with filtering, pagination, search."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.project import Element, Issue
from app.schemas.project import ElementDetail, ElementOut

router = APIRouter()


@router.get("/{project_id}/elements")
async def list_elements(
    project_id: uuid.UUID,
    ifc_class: str | None = Query(None, max_length=100),
    storey_name: str | None = Query(None, max_length=200),
    search: str | None = Query(None, max_length=200),
    has_issues: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Element).where(Element.project_id == project_id)

    if ifc_class:
        stmt = stmt.where(Element.ifc_class == ifc_class)
    if storey_name:
        stmt = stmt.where(Element.storey_name == storey_name)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            Element.name.ilike(pattern)
            | Element.type_name.ilike(pattern)
            | Element.global_id.ilike(pattern)
        )
    if has_issues is True:
        stmt = stmt.where(Element.is_problematic == True)
    elif has_issues is False:
        stmt = stmt.where(Element.is_problematic == False)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0

    # Paginate
    stmt = stmt.order_by(Element.ifc_class, Element.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [ElementOut.model_validate(el).model_dump() for el in items],
    }


@router.get("/{project_id}/elements/{element_id}", response_model=ElementDetail)
async def get_element(
    project_id: uuid.UUID,
    element_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Element)
        .where(Element.id == element_id, Element.project_id == project_id)
        .options(selectinload(Element.issues))
    )
    result = await db.execute(stmt)
    elem = result.scalar_one_or_none()
    if not elem:
        raise HTTPException(status_code=404, detail="Element not found")

    return elem


@router.get("/{project_id}/elements/{element_id}/properties")
async def get_element_properties(
    project_id: uuid.UUID,
    element_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return all property sets for an element as structured JSON."""
    elem = await db.get(Element, element_id)
    if not elem or elem.project_id != project_id:
        raise HTTPException(status_code=404, detail="Element not found")

    properties = {}
    if elem.properties_json:
        try:
            properties = json.loads(elem.properties_json)
        except (json.JSONDecodeError, TypeError):
            properties = {}

    return {
        "element_id": str(elem.id),
        "global_id": elem.global_id,
        "ifc_class": elem.ifc_class,
        "property_sets": properties,
    }


@router.get("/{project_id}/element-classes")
async def element_classes(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Element.ifc_class, func.count().label("count"))
        .where(Element.project_id == project_id)
        .group_by(Element.ifc_class)
        .order_by(func.count().desc())
    )
    result = await db.execute(stmt)
    return [{"ifc_class": row[0], "count": row[1]} for row in result.all()]
