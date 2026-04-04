"""Analytics endpoints — dashboards and statistics."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Building, Element, Issue, Project, Space, Storey

router = APIRouter()


@router.get("/{project_id}/analytics/overview")
async def analytics_overview(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total_elements = await db.scalar(
        select(func.count()).where(Element.project_id == project_id)
    ) or 0

    total_buildings = await db.scalar(
        select(func.count()).where(Building.project_id == project_id)
    ) or 0

    total_storeys = await db.scalar(
        select(func.count())
        .select_from(Storey)
        .join(Building)
        .where(Building.project_id == project_id)
    ) or 0

    total_spaces = await db.scalar(
        select(func.count())
        .select_from(Space)
        .join(Storey)
        .join(Building)
        .where(Building.project_id == project_id)
    ) or 0

    total_issues = await db.scalar(
        select(func.count()).where(Issue.project_id == project_id)
    ) or 0

    total_area = await db.scalar(
        select(func.sum(Element.area)).where(Element.project_id == project_id)
    ) or 0

    total_volume = await db.scalar(
        select(func.sum(Element.volume)).where(Element.project_id == project_id)
    ) or 0

    return {
        "total_elements": total_elements,
        "total_buildings": total_buildings,
        "total_storeys": total_storeys,
        "total_spaces": total_spaces,
        "total_issues": total_issues,
        "total_area": round(float(total_area), 2),
        "total_volume": round(float(total_volume), 2),
    }


@router.get("/{project_id}/analytics/by-class")
async def analytics_by_class(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Element.ifc_class,
            func.count().label("count"),
            func.sum(Element.area).label("total_area"),
            func.sum(Element.volume).label("total_volume"),
        )
        .where(Element.project_id == project_id)
        .group_by(Element.ifc_class)
        .order_by(func.count().desc())
    )
    result = await db.execute(stmt)
    return [
        {
            "ifc_class": row[0],
            "count": row[1],
            "total_area": round(float(row[2] or 0), 2),
            "total_volume": round(float(row[3] or 0), 2),
        }
        for row in result.all()
    ]


@router.get("/{project_id}/analytics/by-storey")
async def analytics_by_storey(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Element.storey_name,
            func.count().label("count"),
            func.sum(case((Element.is_problematic == True, 1), else_=0)).label("problematic"),
        )
        .where(Element.project_id == project_id)
        .group_by(Element.storey_name)
        .order_by(Element.storey_name)
    )
    result = await db.execute(stmt)
    return [
        {
            "storey_name": row[0] or "Не назначен",
            "element_count": row[1],
            "problematic_count": row[2],
        }
        for row in result.all()
    ]


@router.get("/{project_id}/analytics/issues-summary")
async def analytics_issues(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Issue.severity, Issue.status, func.count().label("count"))
        .where(Issue.project_id == project_id)
        .group_by(Issue.severity, Issue.status)
    )
    result = await db.execute(stmt)
    rows = result.all()

    by_severity = {}
    by_status = {}
    for sev, status, cnt in rows:
        by_severity[sev] = by_severity.get(sev, 0) + cnt
        by_status[status] = by_status.get(status, 0) + cnt

    return {"by_severity": by_severity, "by_status": by_status}


@router.get("/{project_id}/analytics/completeness")
async def analytics_completeness(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    total = await db.scalar(
        select(func.count()).where(Element.project_id == project_id)
    ) or 0

    if total == 0:
        return {"total": 0, "with_name": 0, "with_type": 0, "with_storey": 0, "with_material": 0, "with_quantities": 0}

    with_name = await db.scalar(
        select(func.count()).where(Element.project_id == project_id, Element.has_name == True)
    ) or 0
    with_type = await db.scalar(
        select(func.count()).where(Element.project_id == project_id, Element.has_type == True)
    ) or 0
    with_storey = await db.scalar(
        select(func.count()).where(Element.project_id == project_id, Element.has_storey == True)
    ) or 0
    with_material = await db.scalar(
        select(func.count()).where(Element.project_id == project_id, Element.has_material == True)
    ) or 0
    with_quantities = await db.scalar(
        select(func.count()).where(Element.project_id == project_id, Element.has_quantities == True)
    ) or 0

    return {
        "total": total,
        "with_name": with_name,
        "with_type": with_type,
        "with_storey": with_storey,
        "with_material": with_material,
        "with_quantities": with_quantities,
        "pct_name": round(with_name / total * 100, 1),
        "pct_type": round(with_type / total * 100, 1),
        "pct_storey": round(with_storey / total * 100, 1),
        "pct_material": round(with_material / total * 100, 1),
        "pct_quantities": round(with_quantities / total * 100, 1),
    }
