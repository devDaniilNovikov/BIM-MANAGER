"""Add qc_rules table and extend issues with new fields.

Revision ID: 002
Revises: 001
Create Date: 2026-04-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New columns on issues table
    op.add_column("issues", sa.Column("issue_type", sa.String(50), server_default="manual"))
    op.add_column("issues", sa.Column("title", sa.String(500), nullable=True))
    op.add_column("issues", sa.Column("recommendation", sa.Text, nullable=True))
    op.add_column("issues", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))

    # QC Rules table
    op.create_table(
        "qc_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("ifc_class", sa.String(100), server_default="*"),
        sa.Column("check_type", sa.String(50), nullable=False),
        sa.Column("check_config", sa.Text, nullable=True),
        sa.Column("severity", sa.String(20), server_default="warning"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_table("qc_rules")
    op.drop_column("issues", "updated_at")
    op.drop_column("issues", "recommendation")
    op.drop_column("issues", "title")
    op.drop_column("issues", "issue_type")

