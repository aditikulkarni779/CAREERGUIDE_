"""profiles, skills, user_skills, roles, role_skill_requirements

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-15
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("education", sa.JSON(), nullable=True),
        sa.Column("learning_style", sa.String(length=50), nullable=True),
        sa.Column("weekly_hours", sa.Integer(), nullable=True),
        sa.Column("target_companies", sa.JSON(), nullable=True),
        sa.Column("expected_salary", sa.Integer(), nullable=True),
        sa.Column("interests", sa.JSON(), nullable=True),
        sa.Column("career_goal", sa.String(length=200), nullable=True),
        sa.Column("twin_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_profile_user"),
    )

    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=True),
        sa.Column("esco_id", sa.String(length=60), nullable=True),
        sa.Column("onet_id", sa.String(length=60), nullable=True),
    )
    op.create_index("ix_skills_slug", "skills", ["slug"], unique=True)

    op.create_table(
        "user_skills",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("proficiency", sa.SmallInteger(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("profile_id", "skill_id", name="uq_user_skill"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_roles_slug", "roles", ["slug"], unique=True)

    op.create_table(
        "role_skill_requirements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("importance", sa.SmallInteger(), nullable=True),
        sa.Column("typical_proficiency", sa.SmallInteger(), nullable=True),
        sa.Column("difficulty", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("role_id", "skill_id", name="uq_role_skill"),
    )


def downgrade() -> None:
    op.drop_table("role_skill_requirements")
    op.drop_index("ix_roles_slug", table_name="roles")
    op.drop_table("roles")
    op.drop_table("user_skills")
    op.drop_index("ix_skills_slug", table_name="skills")
    op.drop_table("skills")
    op.drop_table("profiles")
