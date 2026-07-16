"""readiness_scores

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-16
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "readiness_scores",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("overall", sa.SmallInteger(), nullable=True),
        sa.Column("components", sa.JSON(), nullable=True),
        sa.Column("target_role_slug", sa.String(length=120), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_readiness_profile", "readiness_scores", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_readiness_profile", table_name="readiness_scores")
    op.drop_table("readiness_scores")
