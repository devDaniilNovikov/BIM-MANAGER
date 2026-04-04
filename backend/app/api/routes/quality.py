"""Quality control endpoints — run checks, view results."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Element, Issue, Project, QCRule
from app.services.quality_checker import check_all, check_with_custom_rules
from app.services.ifc_parser import parse_ifc
from app.services.anomaly_detector import detect_anomalies

router = APIRouter()


@router.post("/{project_id}/qc/run")
async def run_qc(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Re-parse IFC to get fresh element data
    parsed = parse_ifc(project.file_path)

    # Run built-in checks
    quality_issues = check_all(parsed.elements)

    # Run anomaly detection
    anomaly_issues = detect_anomalies(parsed.elements)
    quality_issues.extend(anomaly_issues)

    # Run custom QC rules from DB
    rules_result = await db.execute(select(QCRule).where(QCRule.is_active == True))
    rules = rules_result.scalars().all()
    if rules:
        rule_dicts = [
            {
                "name": r.name,
                "ifc_class": r.ifc_class,
                "check_type": r.check_type,
                "check_config": r.check_config,
                "severity": r.severity,
                "is_active": r.is_active,
            }
            for r in rules
        ]
        custom_issues = check_with_custom_rules(parsed.elements, rule_dicts)
        quality_issues.extend(custom_issues)

    # Clear old auto-generated issues
    old_issues = await db.execute(
        select(Issue).where(
            Issue.project_id == project_id,
            Issue.category != "manual",
        )
    )
    for issue in old_issues.scalars():
        await db.delete(issue)
    await db.flush()

    # Reset all element flags
    all_elements = await db.execute(
        select(Element).where(Element.project_id == project_id)
    )
    gid_to_elem = {}
    for elem in all_elements.scalars():
        elem.is_problematic = False
        gid_to_elem[elem.global_id] = elem

    # Save new issues
    for qi in quality_issues:
        elem = gid_to_elem.get(qi.element_global_id)
        if elem:
            elem.is_problematic = True
        issue = Issue(
            project_id=project_id,
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

    # Summary
    errors = sum(1 for q in quality_issues if q.severity == "error")
    warnings = sum(1 for q in quality_issues if q.severity == "warning")
    infos = sum(1 for q in quality_issues if q.severity == "info")

    return {
        "status": "completed",
        "total_issues": len(quality_issues),
        "errors": errors,
        "warnings": warnings,
        "info": infos,
    }


@router.get("/{project_id}/qc/results")
async def qc_results(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Issue.severity, func.count().label("count"))
        .where(Issue.project_id == project_id)
        .group_by(Issue.severity)
    )
    result = await db.execute(stmt)
    summary = {row[0]: row[1] for row in result.all()}

    stmt_issues = (
        select(Issue)
        .where(Issue.project_id == project_id)
        .order_by(Issue.severity, Issue.created_at.desc())
        .limit(500)
    )
    result = await db.execute(stmt_issues)
    issues = result.scalars().all()

    return {
        "summary": summary,
        "issues": [
            {
                "id": str(i.id),
                "element_id": str(i.element_id) if i.element_id else None,
                "severity": i.severity,
                "category": i.category,
                "message": i.message,
                "status": i.status,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in issues
        ],
    }
