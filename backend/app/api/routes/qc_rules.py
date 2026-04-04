"""QC Rules CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import QCRule
from app.schemas.project import QCRuleCreate, QCRuleOut, QCRuleUpdate

router = APIRouter()


@router.get("", response_model=list[QCRuleOut])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QCRule).order_by(QCRule.name))
    return result.scalars().all()


@router.post("", response_model=QCRuleOut)
async def create_rule(body: QCRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = QCRule(
        name=body.name,
        description=body.description,
        ifc_class=body.ifc_class,
        check_type=body.check_type,
        check_config=body.check_config,
        severity=body.severity,
        is_active=body.is_active,
    )
    db.add(rule)
    await db.flush()
    return rule


@router.get("/{rule_id}", response_model=QCRuleOut)
async def get_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rule = await db.get(QCRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="QC Rule not found")
    return rule


@router.put("/{rule_id}", response_model=QCRuleOut)
async def update_rule(
    rule_id: uuid.UUID,
    body: QCRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    rule = await db.get(QCRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="QC Rule not found")

    if body.name is not None:
        rule.name = body.name
    if body.description is not None:
        rule.description = body.description
    if body.ifc_class is not None:
        rule.ifc_class = body.ifc_class
    if body.check_type is not None:
        rule.check_type = body.check_type
    if body.check_config is not None:
        rule.check_config = body.check_config
    if body.severity is not None:
        rule.severity = body.severity
    if body.is_active is not None:
        rule.is_active = body.is_active

    await db.flush()
    return rule


@router.delete("/{rule_id}")
async def delete_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rule = await db.get(QCRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="QC Rule not found")

    await db.delete(rule)
    return {"status": "deleted"}

