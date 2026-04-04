"""Report builder — generates structured table data for various report types."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Building, Element, Issue, Project, Space, Storey


async def build_report(db: AsyncSession, project_id: uuid.UUID, report_type: str) -> dict | None:
    project = await db.get(Project, project_id)
    if not project:
        return None

    builders = {
        "spaces": _report_spaces,
        "doors-windows": _report_doors_windows,
        "walls": _report_walls,
        "slabs": _report_slabs,
        "quantities": _report_quantities,
        "summary": _report_summary,
    }
    builder = builders[report_type]
    return await builder(db, project_id)


async def _report_spaces(db: AsyncSession, project_id: uuid.UUID) -> dict:
    stmt = (
        select(Space, Storey.name.label("storey_name"))
        .join(Storey)
        .join(Building)
        .where(Building.project_id == project_id)
        .order_by(Storey.elevation, Space.name)
    )
    result = await db.execute(stmt)
    rows = []
    for i, (space, storey_name) in enumerate(result.all(), 1):
        rows.append([
            i,
            storey_name or "—",
            space.name or "—",
            space.long_name or "—",
            round(space.area, 2) if space.area else "—",
            round(space.volume, 2) if space.volume else "—",
        ])
    return {
        "title": "Ведомость помещений",
        "columns": ["№", "Этаж", "Наименование", "Полное наименование", "Площадь, м²", "Объём, м³"],
        "rows": rows,
    }


async def _report_doors_windows(db: AsyncSession, project_id: uuid.UUID) -> dict:
    stmt = (
        select(Element)
        .where(
            Element.project_id == project_id,
            Element.ifc_class.in_(["IfcDoor", "IfcWindow"]),
        )
        .order_by(Element.ifc_class, Element.storey_name, Element.name)
    )
    result = await db.execute(stmt)
    rows = []
    for i, el in enumerate(result.scalars(), 1):
        rows.append([
            i,
            el.ifc_class.replace("Ifc", ""),
            el.name or "—",
            el.type_name or "—",
            el.storey_name or "—",
            el.space_name or "—",
            round(el.width, 3) if el.width else "—",
            round(el.height, 3) if el.height else "—",
            el.material or "—",
        ])
    return {
        "title": "Ведомость дверей и окон",
        "columns": ["№", "Тип", "Наименование", "Тип элемента", "Этаж", "Помещение", "Ширина, м", "Высота, м", "Материал"],
        "rows": rows,
    }


async def _report_walls(db: AsyncSession, project_id: uuid.UUID) -> dict:
    stmt = (
        select(Element)
        .where(
            Element.project_id == project_id,
            Element.ifc_class.in_(["IfcWall", "IfcWallStandardCase"]),
        )
        .order_by(Element.storey_name, Element.name)
    )
    result = await db.execute(stmt)
    rows = []
    for i, el in enumerate(result.scalars(), 1):
        rows.append([
            i,
            el.type_name or "—",
            el.name or "—",
            el.storey_name or "—",
            round(el.length, 3) if el.length else "—",
            round(el.height, 3) if el.height else "—",
            round(el.area, 2) if el.area else "—",
            round(el.volume, 3) if el.volume else "—",
            el.material or "—",
        ])
    return {
        "title": "Ведомость стен",
        "columns": ["№", "Тип", "Наименование", "Этаж", "Длина, м", "Высота, м", "Площадь, м²", "Объём, м³", "Материал"],
        "rows": rows,
    }


async def _report_slabs(db: AsyncSession, project_id: uuid.UUID) -> dict:
    stmt = (
        select(Element)
        .where(
            Element.project_id == project_id,
            Element.ifc_class == "IfcSlab",
        )
        .order_by(Element.storey_name, Element.name)
    )
    result = await db.execute(stmt)
    rows = []
    for i, el in enumerate(result.scalars(), 1):
        rows.append([
            i,
            el.type_name or "—",
            el.storey_name or "—",
            round(el.area, 2) if el.area else "—",
            round(el.volume, 3) if el.volume else "—",
            el.material or "—",
        ])
    return {
        "title": "Ведомость перекрытий",
        "columns": ["№", "Тип", "Этаж", "Площадь, м²", "Объём, м³", "Материал"],
        "rows": rows,
    }


async def _report_quantities(db: AsyncSession, project_id: uuid.UUID) -> dict:
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
    rows = []
    for row in result.all():
        rows.append([
            row[0].replace("Ifc", ""),
            row[1],
            round(float(row[2] or 0), 2),
            round(float(row[3] or 0), 3),
        ])
    return {
        "title": "Сводная таблица количественных показателей",
        "columns": ["Категория", "Количество", "Общая площадь, м²", "Общий объём, м³"],
        "rows": rows,
    }


async def _report_summary(db: AsyncSession, project_id: uuid.UUID) -> dict:
    total_elements = await db.scalar(
        select(func.count()).where(Element.project_id == project_id)
    ) or 0

    total_issues = await db.scalar(
        select(func.count()).where(Issue.project_id == project_id)
    ) or 0

    problematic = await db.scalar(
        select(func.count()).where(Element.project_id == project_id, Element.is_problematic == True)
    ) or 0

    total_area = await db.scalar(
        select(func.sum(Element.area)).where(Element.project_id == project_id)
    ) or 0

    total_volume = await db.scalar(
        select(func.sum(Element.volume)).where(Element.project_id == project_id)
    ) or 0

    # Classes breakdown
    stmt = (
        select(Element.ifc_class, func.count())
        .where(Element.project_id == project_id)
        .group_by(Element.ifc_class)
        .order_by(func.count().desc())
    )
    result = await db.execute(stmt)
    class_breakdown = [[row[0], row[1]] for row in result.all()]

    return {
        "title": "Сводный аналитический отчёт",
        "sections": [
            {
                "title": "Общие показатели",
                "columns": ["Показатель", "Значение"],
                "rows": [
                    ["Всего элементов", total_elements],
                    ["Проблемных элементов", problematic],
                    ["Замечаний", total_issues],
                    ["Суммарная площадь, м²", round(float(total_area), 2)],
                    ["Суммарный объём, м³", round(float(total_volume), 3)],
                ],
            },
            {
                "title": "Распределение по категориям",
                "columns": ["Категория IFC", "Количество"],
                "rows": class_breakdown,
            },
        ],
    }
