import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ── Project ──────────────────────────────────────────
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectOut(ProjectBase):
    id: uuid.UUID
    file_name: str
    file_size: int
    ifc_schema: Optional[str] = None
    created_at: datetime
    element_count: Optional[int] = None
    issue_count: Optional[int] = None

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectOut):
    buildings: List["BuildingOut"] = []


# ── Building ─────────────────────────────────────────
class BuildingOut(BaseModel):
    id: uuid.UUID
    global_id: str
    name: Optional[str]
    storeys: List["StoreyOut"] = []

    model_config = {"from_attributes": True}


# ── Storey ───────────────────────────────────────────
class StoreyOut(BaseModel):
    id: uuid.UUID
    global_id: str
    name: Optional[str]
    elevation: Optional[float]
    spaces: List["SpaceOut"] = []

    model_config = {"from_attributes": True}


# ── Space ────────────────────────────────────────────
class SpaceOut(BaseModel):
    id: uuid.UUID
    global_id: str
    name: Optional[str]
    long_name: Optional[str]
    area: Optional[float]
    volume: Optional[float]

    model_config = {"from_attributes": True}


# ── Element ──────────────────────────────────────────
class ElementOut(BaseModel):
    id: uuid.UUID
    global_id: str
    ifc_class: str
    name: Optional[str]
    type_name: Optional[str]
    description: Optional[str]
    material: Optional[str]
    storey_name: Optional[str]
    space_name: Optional[str]
    length: Optional[float]
    width: Optional[float]
    height: Optional[float]
    area: Optional[float]
    volume: Optional[float]
    weight: Optional[float]
    is_problematic: bool

    model_config = {"from_attributes": True}


class ElementDetail(ElementOut):
    properties_json: Optional[str] = None
    has_name: Optional[bool]
    has_type: Optional[bool]
    has_storey: Optional[bool]
    has_material: Optional[bool]
    has_quantities: Optional[bool]
    issues: List["IssueOut"] = []


# ── Issue ────────────────────────────────────────────
class IssueCreate(BaseModel):
    element_id: Optional[uuid.UUID] = None
    issue_type: str = "manual"
    severity: str = "warning"
    category: str
    title: Optional[str] = None
    message: str


class IssueUpdate(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    title: Optional[str] = None
    severity: Optional[str] = None


class IssueOut(BaseModel):
    id: uuid.UUID
    element_id: Optional[uuid.UUID]
    issue_type: str
    severity: str
    category: str
    title: Optional[str]
    message: str
    recommendation: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── QC Rule ──────────────────────────────────────────
class QCRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ifc_class: str = "*"
    check_type: str
    check_config: Optional[str] = None  # JSON string
    severity: str = "warning"
    is_active: bool = True


class QCRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ifc_class: Optional[str] = None
    check_type: Optional[str] = None
    check_config: Optional[str] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None


class QCRuleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    ifc_class: str
    check_type: str
    check_config: Optional[str]
    severity: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Analytics ────────────────────────────────────────
class CategoryStats(BaseModel):
    ifc_class: str
    count: int
    with_issues: int


class StoreyStats(BaseModel):
    storey_name: str
    element_count: int
    problematic_count: int


class QualityReport(BaseModel):
    total_elements: int
    problematic_elements: int
    missing_name: int
    missing_type: int
    missing_storey: int
    missing_material: int
    missing_quantities: int
    issues_open: int
    issues_resolved: int


class DashboardData(BaseModel):
    quality: QualityReport
    by_category: List[CategoryStats]
    by_storey: List[StoreyStats]
