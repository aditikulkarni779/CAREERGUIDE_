"""roadmaps, roadmap_items

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-16
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roadmaps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("target_role_slug", sa.String(length=120), nullable=False),
        sa.Column("target_role_name", sa.String(length=120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("rationale", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_roadmaps_profile", "roadmaps", ["profile_id"])

    op.create_table(
        "roadmap_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("roadmap_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("skill_name", sa.String(length=120), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("milestone", sa.Integer(), nullable=False),
        sa.Column("est_hours", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.SmallInteger(), nullable=False),
        sa.Column("importance", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=True),
        sa.Column("resources", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmaps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_roadmap_items_roadmap", "roadmap_items", ["roadmap_id"])


def downgrade() -> None:
    op.drop_index("ix_roadmap_items_roadmap", table_name="roadmap_items")
    op.drop_table("roadmap_items")
    op.drop_index("ix_roadmaps_profile", table_name="roadmaps")
    op.drop_table("roadmaps")
