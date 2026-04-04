from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """IFC project / uploaded model."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    ifc_schema: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    buildings: Mapped[list["Building"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    elements: Mapped[list["Element"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    issues: Mapped[list["Issue"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Building(Base):
    """Building extracted from IFC spatial structure."""

    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    global_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)

    project: Mapped["Project"] = relationship(back_populates="buildings")
    storeys: Mapped[list["Storey"]] = relationship(back_populates="building", cascade="all, delete-orphan")


class Storey(Base):
    """Building storey (floor)."""

    __tablename__ = "storeys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("buildings.id", ondelete="CASCADE"))
    global_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(500))
    elevation: Mapped[float | None] = mapped_column(Float)

    building: Mapped["Building"] = relationship(back_populates="storeys")
    spaces: Mapped[list["Space"]] = relationship(back_populates="storey", cascade="all, delete-orphan")


class Space(Base):
    """Room / space within a storey."""

    __tablename__ = "spaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storey_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("storeys.id", ondelete="CASCADE"))
    global_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(500))
    long_name: Mapped[str | None] = mapped_column(String(500))
    area: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)

    storey: Mapped["Storey"] = relationship(back_populates="spaces")


class Element(Base):
    """Any IFC building element (wall, door, window, slab, etc.)."""

    __tablename__ = "elements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    global_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ifc_class: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(500))
    type_name: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    material: Mapped[str | None] = mapped_column(String(500))
    storey_name: Mapped[str | None] = mapped_column(String(500), index=True)
    space_name: Mapped[str | None] = mapped_column(String(500))

    # Quantities
    length: Mapped[float | None] = mapped_column(Float)
    width: Mapped[float | None] = mapped_column(Float)
    height: Mapped[float | None] = mapped_column(Float)
    area: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float)

    # Quality flags
    has_name: Mapped[bool | None] = mapped_column(default=None)
    has_type: Mapped[bool | None] = mapped_column(default=None)
    has_storey: Mapped[bool | None] = mapped_column(default=None)
    has_material: Mapped[bool | None] = mapped_column(default=None)
    has_quantities: Mapped[bool | None] = mapped_column(default=None)
    is_problematic: Mapped[bool] = mapped_column(default=False, index=True)

    # Raw property sets stored as JSON text
    properties_json: Mapped[str | None] = mapped_column(Text)

    project: Mapped["Project"] = relationship(back_populates="elements")
    issues: Mapped[list["Issue"]] = relationship(back_populates="element", cascade="all, delete-orphan")


class Issue(Base):
    """Quality issue / remark linked to an element."""

    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    element_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("elements.id", ondelete="SET NULL"))
    issue_type: Mapped[str] = mapped_column(String(50), default="manual")  # missing_property, invalid_value, no_storey, anomaly, manual
    severity: Mapped[str] = mapped_column(String(20), default="warning")  # error / warning / info
    category: Mapped[str] = mapped_column(String(100))  # missing_name, missing_storey, etc.
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open / in_progress / resolved / ignored
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(back_populates="issues")
    element: Mapped["Element | None"] = relationship(back_populates="issues")


class QCRule(Base):
    """Configurable quality check rule."""

    __tablename__ = "qc_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ifc_class: Mapped[str] = mapped_column(String(100), default="*")  # * = applies to all
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)  # required_property, value_range, has_quantity, has_storey
    check_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON config
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

