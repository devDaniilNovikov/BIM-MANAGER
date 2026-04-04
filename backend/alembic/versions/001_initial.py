"""Initial schema — all tables.

Revision ID: 001
Revises:
Create Date: 2026-04-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("ifc_schema", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "buildings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("global_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
    )

    op.create_table(
        "storeys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("building_id", UUID(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("global_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("elevation", sa.Float, nullable=True),
    )

    op.create_table(
        "spaces",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("storey_id", UUID(as_uuid=True), sa.ForeignKey("storeys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("global_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("long_name", sa.String(500), nullable=True),
        sa.Column("area", sa.Float, nullable=True),
        sa.Column("volume", sa.Float, nullable=True),
    )

    op.create_table(
        "elements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("global_id", sa.String(64), nullable=False),
        sa.Column("ifc_class", sa.String(200), nullable=False, index=True),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("type_name", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("material", sa.String(500), nullable=True),
        sa.Column("storey_name", sa.String(500), nullable=True, index=True),
        sa.Column("space_name", sa.String(500), nullable=True),
        sa.Column("length", sa.Float, nullable=True),
        sa.Column("width", sa.Float, nullable=True),
        sa.Column("height", sa.Float, nullable=True),
        sa.Column("area", sa.Float, nullable=True),
        sa.Column("volume", sa.Float, nullable=True),
        sa.Column("weight", sa.Float, nullable=True),
        sa.Column("has_name", sa.Boolean, nullable=True),
        sa.Column("has_type", sa.Boolean, nullable=True),
        sa.Column("has_storey", sa.Boolean, nullable=True),
        sa.Column("has_material", sa.Boolean, nullable=True),
        sa.Column("has_quantities", sa.Boolean, nullable=True),
        sa.Column("is_problematic", sa.Boolean, default=False, index=True),
        sa.Column("properties_json", sa.Text, nullable=True),
    )

    op.create_table(
        "issues",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("element_id", UUID(as_uuid=True), sa.ForeignKey("elements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("severity", sa.String(20), default="warning"),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("issues")
    op.drop_table("elements")
    op.drop_table("spaces")
    op.drop_table("storeys")
    op.drop_table("buildings")
    op.drop_table("projects")
