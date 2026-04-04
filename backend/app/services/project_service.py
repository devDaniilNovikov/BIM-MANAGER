"""Project service: upload, parse, store IFC data."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.project import Building, Element, Issue, Project, Space, Storey
from app.services.anomaly_detector import detect_anomalies
from app.services.ifc_parser import ParsedModel, parse_ifc
from app.services.quality_checker import check_all

logger = logging.getLogger(__name__)



async def create_project(
    db: AsyncSession,
    name: str,
    description: str | None,
    file_name: str,
    file_content: bytes,
) -> Project:
    """Save uploaded IFC file, parse it, and store data in DB."""

    # 1. Save file to disk
    safe_name = f"{uuid.uuid4().hex}_{file_name}"
    file_path = settings.UPLOAD_DIR / safe_name
    file_path.write_bytes(file_content)
    file_size = len(file_content)

    # 2. Parse IFC
    parsed: ParsedModel = parse_ifc(file_path)

    # 3. Create project record
    project = Project(
        name=name,
        description=description,
        file_name=file_name,
        file_path=str(file_path),
        file_size=file_size,
        ifc_schema=parsed.schema,
    )
    db.add(project)
    await db.flush()

    # 4. Store spatial structure
    for pb in parsed.buildings:
        building = Building(
            project_id=project.id,
            global_id=pb.global_id,
            name=pb.name,
            description=pb.description,
        )
        db.add(building)
        await db.flush()

        for ps in pb.storeys:
            storey = Storey(
                building_id=building.id,
                global_id=ps.global_id,
                name=ps.name,
                elevation=ps.elevation,
            )
            db.add(storey)
            await db.flush()

            for psp in ps.spaces:
                space = Space(
                    storey_id=storey.id,
                    global_id=psp.global_id,
                    name=psp.name,
                    long_name=psp.long_name,
                    area=psp.area,
                    volume=psp.volume,
                )
                db.add(space)

    # 5. Store elements
    gid_to_element: dict[str, Element] = {}
    for pe in parsed.elements:
        has_quantities = any([pe.length, pe.width, pe.height, pe.area, pe.volume, pe.weight])
        elem = Element(
            project_id=project.id,
            global_id=pe.global_id,
            ifc_class=pe.ifc_class,
            name=pe.name,
            type_name=pe.type_name,
            description=pe.description,
            material=pe.material,
            storey_name=pe.storey_name,
            space_name=pe.space_name,
            length=pe.length,
            width=pe.width,
            height=pe.height,
            area=pe.area,
            volume=pe.volume,
            weight=pe.weight,
            has_name=bool(pe.name),
            has_type=bool(pe.type_name),
            has_storey=bool(pe.storey_name),
            has_material=bool(pe.material),
            has_quantities=has_quantities,
            properties_json=json.dumps(pe.properties, ensure_ascii=False) if pe.properties else None,
        )
        db.add(elem)
        gid_to_element[pe.global_id] = elem

    await db.flush()

    # 6. Run quality checks and anomaly detection, then store issues
    quality_issues = check_all(parsed.elements)
    anomaly_issues = detect_anomalies(parsed.elements)
    all_issues = quality_issues + anomaly_issues

    for qi in all_issues:
        elem = gid_to_element.get(qi.element_global_id)
        if elem:
            elem.is_problematic = True
        issue = Issue(
            project_id=project.id,
            element_id=elem.id if elem else None,
            issue_type=qi.issue_type,
            severity=qi.severity,
            category=qi.category,
            title=qi.title,
            message=qi.message,
            recommendation=qi.recommendation,
        )
        db.add(issue)

    await db.flush()
    logger.info(f"Project '{name}' created: {len(parsed.elements)} elements, {len(all_issues)} issues")
    return project


async def get_projects(db: AsyncSession) -> list[dict]:
    """List all projects with element/issue counts."""
    stmt = (
        select(
            Project,
            func.count(Element.id.distinct()).label("element_count"),
            func.count(Issue.id.distinct()).label("issue_count"),
        )
        .outerjoin(Element, Element.project_id == Project.id)
        .outerjoin(Issue, Issue.project_id == Project.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "project": row[0],
            "element_count": row[1],
            "issue_count": row[2],
        }
        for row in rows
    ]


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Get a project with spatial structure."""
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
    return result.scalar_one_or_none()


async def delete_project(db: AsyncSession, project_id: uuid.UUID) -> bool:
    """Delete a project and its file."""
    project = await db.get(Project, project_id)
    if not project:
        return False

    # Remove file
    file_path = Path(project.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(project)
    return True
