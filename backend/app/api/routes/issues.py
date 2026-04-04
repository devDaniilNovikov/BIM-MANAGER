"""Issues CRUD endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Issue
from app.schemas.project import IssueCreate, IssueOut, IssueUpdate
from app.services.recommendation import get_recommendation

router = APIRouter()


@router.get("/{project_id}/issues")
async def list_issues(
    project_id: uuid.UUID,
    status: str | None = Query(None, max_length=50),
    severity: str | None = Query(None, max_length=50),
    category: str | None = Query(None, max_length=100),
    issue_type: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Issue).where(Issue.project_id == project_id)

    if status:
        stmt = stmt.where(Issue.status == status)
    if severity:
        stmt = stmt.where(Issue.severity == severity)
    if category:
        stmt = stmt.where(Issue.category == category)
    if issue_type:
        stmt = stmt.where(Issue.issue_type == issue_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0

    stmt = stmt.order_by(Issue.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [IssueOut.model_validate(i).model_dump() for i in items],
    }


@router.post("/{project_id}/issues", response_model=IssueOut)
async def create_issue(
    project_id: uuid.UUID,
    body: IssueCreate,
    db: AsyncSession = Depends(get_db),
):
    issue = Issue(
        project_id=project_id,
        element_id=body.element_id,
        issue_type=body.issue_type,
        severity=body.severity,
        category=body.category,
        title=body.title,
        message=body.message,
        recommendation=get_recommendation(body.category),
    )
    db.add(issue)
    await db.flush()
    return issue


@router.get("/{project_id}/issues/{issue_id}", response_model=IssueOut)
async def get_issue(
    project_id: uuid.UUID,
    issue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    issue = await db.get(Issue, issue_id)
    if not issue or issue.project_id != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.put("/{project_id}/issues/{issue_id}", response_model=IssueOut)
async def update_issue(
    project_id: uuid.UUID,
    issue_id: uuid.UUID,
    body: IssueUpdate,
    db: AsyncSession = Depends(get_db),
):
    issue = await db.get(Issue, issue_id)
    if not issue or issue.project_id != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")

    if body.status is not None:
        issue.status = body.status
    if body.message is not None:
        issue.message = body.message
    if body.title is not None:
        issue.title = body.title
    if body.severity is not None:
        issue.severity = body.severity

    issue.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return issue


@router.delete("/{project_id}/issues/{issue_id}")
async def delete_issue(
    project_id: uuid.UUID,
    issue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    issue = await db.get(Issue, issue_id)
    if not issue or issue.project_id != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")

    await db.delete(issue)
    return {"status": "deleted"}
