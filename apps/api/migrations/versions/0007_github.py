"""github_profiles

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-17
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("bio", sa.String(length=500), nullable=True),
        sa.Column("followers", sa.Integer(), nullable=False),
        sa.Column("public_repos", sa.Integer(), nullable=False),
        sa.Column("health_score", sa.SmallInteger(), nullable=False),
        sa.Column("repo_score", sa.SmallInteger(), nullable=False),
        sa.Column("diversity_score", sa.SmallInteger(), nullable=False),
        sa.Column("recruiter_score", sa.SmallInteger(), nullable=False),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("top_repos", sa.JSON(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_github_profiles_profile", "github_profiles", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_github_profiles_profile", table_name="github_profiles")
    op.drop_table("github_profiles")
